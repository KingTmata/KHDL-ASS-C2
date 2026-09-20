from pathlib import Path

import pandas as pd
import json
from schema import CATEGORIES, COLUMNS, TIMEZONE


DATA_FILE = Path(__file__).resolve().parent.parent / "Data/Raw/vnexpress_news.parquet"
TARGET_RECORDS = 500
REQUIRED_COLUMNS = COLUMNS


def is_valid_author(text):
    """Dùng cùng quy tắc tác giả với collect_news.py."""
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


def duplicate_paragraph_titles(dataframe):
    """Trả về title của các bài có paragraph bị lặp."""
    titles = []

    for _, row in dataframe.dropna(subset=["content"]).iterrows():
        paragraphs = [
            paragraph.strip()
            for paragraph in str(row["content"]).split("\n")
            if paragraph.strip()
        ]
        if len(paragraphs) != len(set(paragraphs)):
            titles.append(row["title"])

    return titles


def author_still_in_content(row):
    paragraphs = {
        paragraph.strip()
        for paragraph in str(row["content"]).split("\n")
        if paragraph.strip()
    }
    return str(row["author"]).strip() in paragraphs


def main():
    dataframe = pd.read_parquet(DATA_FILE, engine="pyarrow")

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError("Thiếu cột: " + ", ".join(missing_columns))

    duplicate_paragraphs = duplicate_paragraph_titles(dataframe)
    if not isinstance(dataframe["crawled_at"].dtype, pd.DatetimeTZDtype):
        raise ValueError("crawled_at phải là datetime có múi giờ")
    if str(dataframe["crawled_at"].dt.tz) != TIMEZONE:
        raise ValueError("crawled_at phải dùng múi giờ " + TIMEZONE)
    metadata = json.loads(DATA_FILE.with_name("metadata.json").read_text(encoding="utf-8"))
    actual_counts = {category: int(dataframe["category"].eq(category).sum()) for category in CATEGORIES}
    if metadata.get("categories") != CATEGORIES or metadata.get("category_counts") != actual_counts:
        raise ValueError("Danh sách hoặc số bài mỗi category trong metadata không khớp Parquet")
    if metadata.get("columns") != list(dataframe.columns) or metadata.get("record_count") != len(dataframe):
        raise ValueError("Schema hoặc số bản ghi trong metadata không khớp Parquet")
    checks = {
        "Số bản ghi": len(dataframe),
        "Thiếu category": dataframe["category"].fillna("").str.strip().eq("").sum(),
        "Category ngoài 10 nhóm": (~dataframe["category"].isin(CATEGORIES)).sum(),
        "Thiếu crawled_at": dataframe["crawled_at"].isna().sum(),
        "Thiếu title": dataframe["title"].isna().sum(),
        "Thiếu description": dataframe["description"].isna().sum(),
        "Thiếu published_at": dataframe["published_at"].isna().sum(),
        "Thiếu author": dataframe["author"].isna().sum(),
        "Author không hợp lệ": (
            ~dataframe["author"].fillna("").map(is_valid_author)
        ).sum(),
        "Author còn lặp trong content": dataframe.apply(
            author_still_in_content, axis=1
        ).sum(),
        "Thiếu content": dataframe["content"].isna().sum(),
        "URL trùng": dataframe["url"].duplicated().sum(),
        "Title trùng": dataframe["title"].duplicated().sum(),
        "Content trùng hoàn toàn": dataframe["content"].duplicated().sum(),
        "Bài có paragraph trùng": len(duplicate_paragraphs),
        "Bài có content dưới 100 ký tự": (
            dataframe["content"].fillna("").astype(str).str.len() < 100
        ).sum(),
    }

    print("KẾT QUẢ KIỂM TRA DỮ LIỆU")
    for label, value in checks.items():
        print(f"{label}: {int(value)}")

    failures = [
        label
        for label, value in checks.items()
        if label != "Số bản ghi" and value != 0
    ]
    if len(dataframe) < TARGET_RECORDS:
        failures.append(f"chưa đủ {TARGET_RECORDS} bản ghi")

    if failures:
        print("\nCHƯA ĐẠT:", ", ".join(failures))
        raise SystemExit(1)

    print("\nĐẠT: Dataset có ít nhất 500 bài hợp lệ và không có lỗi trọng yếu.")


if __name__ == "__main__":
    main()
