# Kiểm tra robots.txt của VnExpress

- Đã kiểm tra <https://vnexpress.net/robots.txt> ngày 20/09/2026. Quy tắc dành cho `User-agent: *` cho phép truy cập đường dẫn `/`.
- Chương trình chỉ đọc các trang bài báo công khai thuộc các chuyên mục tin tức và không truy cập khu vực đăng nhập hay dữ liệu riêng tư.
- Crawler sử dụng User-Agent riêng, retry có giới hạn và nghỉ một giây giữa các request để hạn chế tải lên máy chủ nguồn.

Ảnh chụp `robots.txt` cần được lưu cùng bài nộp sau khi mở URL trên trong trình duyệt.
