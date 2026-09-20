"""Schema và 10 chuyên mục thống nhất cho dataset."""

CATEGORY_BY_SLUG = {
    "thoi-su": "Thời sự",
    "the-gioi": "Thế giới",
    "kinh-doanh": "Kinh doanh",
    "phap-luat": "Pháp luật",
    "khoa-hoc-cong-nghe": "Khoa học - Công nghệ",
    "suc-khoe": "Sức khỏe",
    "doi-song": "Đời sống",
    "giao-duc": "Giáo dục",
    "du-lich": "Du lịch",
    "oto-xe-may": "Ôtô - Xe máy",
}
CATEGORIES = list(CATEGORY_BY_SLUG.values())
COLUMNS = [
    "title", "description", "published_at", "author", "url", "content",
    "category", "crawled_at",
]
TIMEZONE = "Asia/Ho_Chi_Minh"
