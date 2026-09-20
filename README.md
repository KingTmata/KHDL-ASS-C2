# KHDL-ASS-C2

Thu thập ít nhất 500 bài báo công khai từ nhiều chuyên mục của VnExpress.

## Cài đặt

```powershell
python -m pip install -r requirements.txt
```

## Thu thập dữ liệu

Crawler ghi đủ 8 cột. Khi bạn chủ động chạy lại, `category` được lấy từ breadcrumb hoặc metadata `article:section` trên trang bài và chuẩn hóa theo 10 nhóm trong `src/schema.py`. Bài không xác định được nhóm sẽ bị loại. `crawled_at` là thời điểm thực tế tải từng bài, có múi giờ Việt Nam; không gán lại mốc 05:00 cho lần chạy mới. Nếu chưa đủ 500 bài hợp lệ, chương trình báo lỗi và giữ nguyên dataset hiện tại.

```powershell
python src/collect_news.py
```

## Ghi chú

Code phát triển từ bản thử nghiệm ban đầu. Các thư viện cần thiết có trong `requirements.txt`; `pyarrow` dùng để đọc/ghi Parquet.

Khi chạy, chương trình kiểm tra các URL đã có trong file Parquet. Bài nào không đạt thì bị bỏ qua và lấy bài khác để đủ 500 bài. Các URL bị lỗi hoặc bị loại được lưu trong `Data/Raw/failed_urls.csv`.

## Dữ liệu

Dataset chính là `Data/Raw/vnexpress_news.parquet`. Parquet lưu được văn bản tiếng Việt, xuống dòng và schema; dùng nén Snappy. CSV cũng lưu được các nội dung này nếu đọc đúng cách.

```python
import pandas as pd

df = pd.read_parquet("Data/Raw/vnexpress_news.parquet")
print(df.shape)
print(df.head())
```

Chạy các lệnh từ thư mục gốc dự án. Dataset có 500 hàng, 8 cột. Sáu cột gốc giữ nguyên, bao gồm `published_at` dạng chuỗi.

`category` được AI suy luận chỉ từ tiêu đề, chưa xác minh với chuyên mục chính thức trên trang nguồn. `crawled_at` được gán đồng loạt là **20/09/2026 05:00:00 UTC+7**, kiểu timestamp có múi giờ `Asia/Ho_Chi_Minh`, theo yêu cầu người dùng; đây không phải thời điểm crawl đo riêng từng bài. Lần bổ sung này không truy cập mạng hoặc crawl lại. `collected_at` cũ trong metadata được giữ để bảo toàn lịch sử.

Đoạn trên mô tả dataset hiện có. Khi chạy crawler mới, metadata sẽ ghi phương pháp lấy chuyên mục từ trang và thời điểm tải thực tế. `source_urls` là 10 trang dùng để tìm URL, `categories` là 10 nhãn hợp lệ và `category_counts` là số bài thực tế mỗi nhãn (tổng bằng số hàng Parquet). Hai bài về hoạt động chạy cộng đồng được gộp vào Đời sống để tuân theo 10 nhóm của dự án; không thêm nhóm Thể thao.

Bản CSV sáu cột trước chuyển đổi và metadata gốc vẫn có thể khôi phục từ lịch sử Git trước commit chuyển sang Parquet.

CSV trùng dữ liệu đã được xóa sau khi đối chiếu thành công; `failed_urls.csv` vẫn giữ vì là nhật ký lỗi riêng. Muốn xuất CSV từ dataset chính để xem:

```python
df.to_csv("Data/Raw/vnexpress_news_export.csv", index=False, encoding="utf-8-sig")
```

Tên tác giả được lấy từ paragraph `p.Normal` cuối cùng của bài. Nếu paragraph cuối không giống tên tác giả thì bài đó không được đưa vào dataset.

## Kiểm tra dữ liệu

```powershell
python src/checkdata.py
```

Dataset đạt yêu cầu khi có ít nhất 500 bài và không có lỗi trọng yếu về missing value, URL/title/content trùng hoặc paragraph trùng.

## Robots.txt

Robots.txt được kiểm tra tại <https://vnexpress.net/robots.txt> ngày 20/09/2026. Quy tắc cho `User-agent: *` cho phép truy cập `/`; crawler dùng User-Agent riêng, chỉ đọc trang công khai và nghỉ một giây giữa các request.
