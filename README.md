# KHDL-ASS-C2

Thu thập ít nhất 500 bài báo công khai từ nhiều chuyên mục của VnExpress.

## Cài đặt

```powershell
python -m pip install -r requirements.txt
```

## Thu thập dữ liệu

```powershell
python src/collect_news.py
```

## Ghi chú

phát triển code từ bản thử nghiệm ban đầu. Code dùng ba thư viện có trong `requirements.txt`.

Khi chạy, chương trình kiểm tra các URL đã có trong file CSV. Bài nào không đạt thì bị bỏ qua và lấy bài khác để đủ 500 bài. Các URL bị lỗi hoặc bị loại được lưu trong `Data/Raw/failed_urls.csv`.

Tên tác giả được lấy từ paragraph `p.Normal` cuối cùng của bài. Nếu paragraph cuối không giống tên tác giả thì bài đó không được đưa vào dataset.

## Kiểm tra dữ liệu

```powershell
python src/checkdata.py
```

Dataset đạt yêu cầu khi có ít nhất 500 bài và không có lỗi trọng yếu về missing value, URL/title/content trùng hoặc paragraph trùng.

## Robots.txt

Robots.txt được kiểm tra tại <https://vnexpress.net/robots.txt> ngày 20/09/2026. Quy tắc cho `User-agent: *` cho phép truy cập `/`; crawler dùng User-Agent riêng, chỉ đọc trang công khai và nghỉ một giây giữa các request.
