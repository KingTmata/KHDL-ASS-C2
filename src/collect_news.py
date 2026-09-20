import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from schema import CATEGORY_BY_SLUG, CATEGORIES, COLUMNS, TIMEZONE


# Các chuyên mục dùng để lấy bài đa dạng hơn.
CATEGORY_URLS = [f"https://vnexpress.net/{slug}" for slug in CATEGORY_BY_SLUG]

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "Data/Raw/vnexpress_news.parquet"
FAILED_FILE = ROOT / "Data/Raw/failed_urls.csv"
METADATA_FILE = ROOT / "Data/Raw/metadata.json"

TARGET_ARTICLES = 500
TARGET_URLS = 1000
MAX_PAGES = 5
REQUEST_DELAY = 1

HEADERS = {
    "User-Agent": "KHDLStudentCollector/1.0 (educational data collection)"
}


def is_valid_author(text):
    """Kiểm tra paragraph cuối có thể là tên tác giả hay không."""
    text = " ".join(str(text).split())
    words = text.replace("-", " ").split()

    if not words or len(words) > 10 or len(text) > 100:
        return False
    if any(character.isdigit() for character in text):
        return False
    if text.endswith((".", "?", "!", ":", ";")):
        return False

    uppercase_words = sum(
        word[0].isupper() for word in words if word[0].isalpha()
    )
    return uppercase_words / len(words) >= 0.6


def get_soup(url):
    """Tải một trang và chuyển HTML thành BeautifulSoup."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as error:
        print("Lỗi request:", url, "-", error)
        return None


def extract_category(soup):
    """Lấy chuyên mục từ breadcrumb hoặc article:section; không suy đoán từ link liên quan."""
    for link in soup.select(".breadcrumb a[href], .breadcrumbs a[href]"):
        slug = urlparse(link["href"]).path.strip("/").split("/")[0]
        if slug in CATEGORY_BY_SLUG:
            return CATEGORY_BY_SLUG[slug]
    section = soup.find("meta", property="article:section")
    if section is None:
        section = soup.find("meta", attrs={"name": "article:section"})
    if section:
        name = " ".join(section.get("content", "").split()).casefold()
        aliases = {value.casefold(): value for value in CATEGORIES}
        aliases.update({"khoa học công nghệ": "Khoa học - Công nghệ",
                        "ô tô - xe máy": "Ôtô - Xe máy", "xe": "Ôtô - Xe máy"})
        return aliases.get(name)
    return None


def scrape_article(url):
    """Lấy một bài báo; trả về None nếu bài không đạt tiêu chí."""
    soup = get_soup(url)
    if soup is None:
        return None
    crawled_at = pd.Timestamp.now(tz=TIMEZONE)
    category = extract_category(soup)
    if category is None:
        print("Không xác định được chuyên mục thuộc 10 nhóm:", url)
        return None

    title = soup.find("h1", class_="title-detail")
    description = soup.find("p", class_="description")
    published_at = soup.find("span", class_="date")
    paragraphs = soup.find_all("p", class_="Normal")

    if not title or not description or not published_at:
        print("Thiếu title, description hoặc date:", url)
        return None

    # Bỏ paragraph trùng trong cùng bài.
    content_paragraphs = []
    for paragraph in paragraphs:
        text = paragraph.get_text(" ", strip=True)
        if text and text not in content_paragraphs:
            content_paragraphs.append(text)

    # Quy tắc duy nhất của dự án: p.Normal cuối là tác giả.
    if len(content_paragraphs) <= 1:
        print("Không đủ content để tách tác giả:", url)
        return None

    author = content_paragraphs[-1]
    if not is_valid_author(author):
        print("Paragraph cuối không giống tên tác giả:", url)
        return None

    content = "\n".join(content_paragraphs[:-1]).strip()
    if len(content) < 100:
        print("Nội dung quá ngắn:", url)
        return None

    return {
        "title": title.get_text(" ", strip=True),
        "description": description.get_text(" ", strip=True),
        "published_at": published_at.get_text(" ", strip=True),
        "author": author,
        "url": url,
        "content": content,
        "category": category,
        "crawled_at": crawled_at,
    }


def collect_article_urls():
    """Lấy URL bài báo từ nhiều trang chuyên mục."""
    article_urls = []
    pages_scanned = 0

    for page in range(1, MAX_PAGES + 1):
        for category_url in CATEGORY_URLS:
            page_url = category_url
            if page > 1:
                page_url += f"-p{page}"

            soup = get_soup(page_url)
            if soup is None:
                continue

            pages_scanned += 1
            old_count = len(article_urls)

            for link in soup.find_all("a", href=True):
                url = link["href"]
                if (
                    url.startswith("https://vnexpress.net/")
                    and url.endswith(".html")
                    and url not in article_urls
                ):
                    article_urls.append(url)

            print(
                page_url,
                "- URL mới:",
                len(article_urls) - old_count,
                "- Tổng URL:",
                len(article_urls),
            )

            if len(article_urls) >= TARGET_URLS:
                return article_urls, pages_scanned
            time.sleep(REQUEST_DELAY)

    return article_urls, pages_scanned


def load_existing_urls():
    """Đọc URL cũ để kiểm tra lại trước khi lấy bài mới."""
    if not os.path.exists(OUTPUT_FILE):
        return []

    dataframe = pd.read_parquet(OUTPUT_FILE, engine="pyarrow")
    if "url" not in dataframe.columns:
        return []

    return (
        dataframe["url"]
        .dropna()
        .drop_duplicates()
        .astype(str)
        .tolist()
    )


def save_results(articles, failed_urls, pages_scanned, candidate_count):
    """Lưu Parquet, danh sách lỗi CSV và metadata."""
    dataframe = pd.DataFrame(articles, columns=COLUMNS)
    if dataframe.empty:
        raise ValueError("Không có bài hợp lệ; giữ nguyên dataset hiện tại.")
    if not dataframe["category"].isin(CATEGORIES).all():
        raise ValueError("Chuyên mục phải thuộc 10 nhóm trong schema.py")
    if any(pd.Timestamp(value).tzinfo is None for value in dataframe["crawled_at"]):
        raise ValueError("crawled_at phải có múi giờ")
    dataframe["crawled_at"] = pd.to_datetime(
        dataframe["crawled_at"], utc=True, errors="raise"
    ).dt.tz_convert(TIMEZONE)
    if dataframe.isna().any().any():
        raise ValueError("Dataset thiếu dữ liệu; giữ nguyên file hiện tại.")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    dataframe.to_parquet(OUTPUT_FILE, index=False, engine="pyarrow", compression="snappy")

    pd.DataFrame(failed_urls, columns=["url", "reason"]).to_csv(
        FAILED_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    metadata = {
        "source": "VnExpress",
        "category": "Nhiều chuyên mục",
        "source_urls": CATEGORY_URLS,
        "robots_url": "https://vnexpress.net/robots.txt",
        "collected_at": pd.Timestamp.now(tz=TIMEZONE).isoformat(),
        "record_count": len(articles),
        "category_pages_scanned": pages_scanned,
        "candidate_url_count": candidate_count,
        "failed_url_count": len(failed_urls),
        "request_delay_seconds": REQUEST_DELAY,
        "output_file": "Data/Raw/vnexpress_news.parquet",
        "categories": CATEGORIES,
        "category_counts": {
            category: int(dataframe["category"].eq(category).sum())
            for category in CATEGORIES
        },
        "category_annotation": {
            "method": "Extracted from article breadcrumb or article:section metadata",
            "verified_against_source": True,
        },
        "crawled_at_annotation": {
            "method": "Actual time after each article was downloaded and parsed",
            "timezone": TIMEZONE,
        },
        "format": "parquet",
        "compression": "snappy",
        "text_encoding": "UTF-8",
        "columns": list(dataframe.columns),
        "missing_values": dataframe.isna().sum().to_dict(),
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)


def main():
    old_urls = load_existing_urls()
    new_urls, pages_scanned = collect_article_urls()
    old_url_set = set(old_urls)

    # Kiểm tra bài cũ trước, sau đó dùng bài mới để bù bài bị loại.
    urls_to_process = old_urls + [
        url for url in new_urls if url not in old_url_set
    ]

    articles = []
    failed_urls = []
    titles = set()
    contents = set()

    print("Số URL cũ cần kiểm tra lại:", len(old_urls))

    for url in urls_to_process:
        if len(articles) >= TARGET_ARTICLES:
            break

        article = scrape_article(url)
        if article is None:
            failed_urls.append({
                "url": url,
                "reason": "request lỗi hoặc HTML không được hỗ trợ",
            })
        elif article["title"] in titles:
            failed_urls.append({"url": url, "reason": "title trùng"})
        elif article["content"] in contents:
            failed_urls.append({"url": url, "reason": "content trùng"})
        else:
            articles.append(article)
            titles.add(article["title"])
            contents.add(article["content"])
            print(
                "Đã lấy:",
                len(articles),
                "/",
                TARGET_ARTICLES,
                "-",
                article["title"],
            )

        time.sleep(REQUEST_DELAY)

    if len(articles) < TARGET_ARTICLES:
        raise RuntimeError(
            f"Chỉ lấy được {len(articles)}/{TARGET_ARTICLES} bài; "
            "không ghi đè dataset hiện tại. Hãy tăng số trang chuyên mục."
        )
    save_results(articles, failed_urls, pages_scanned, len(new_urls))
    print("Hoàn thành:", len(articles), "bài hợp lệ")
    print("URL lỗi hoặc bị loại:", len(failed_urls))

if __name__ == "__main__":
    main()
