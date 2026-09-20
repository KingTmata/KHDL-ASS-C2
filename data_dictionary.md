# Data dictionary: VnExpress news dataset

Mỗi hàng trong `Data/Raw/vnexpress_news.parquet` đại diện cho một bài báo công khai. File dùng nén Snappy, gồm 8 cột. Sáu cột gốc giữ nguyên, bao gồm `published_at` dạng chuỗi.

| Trường | Kiểu dữ liệu | Cho phép thiếu | Mô tả |
| --- | --- | --- | --- |
| `title` | string | Không | Tiêu đề chính của bài báo. |
| `description` | string | Không | Đoạn mô tả ngắn hoặc sapo của bài báo. |
| `published_at` | string | Không | Thời gian đăng theo văn bản hiển thị trên trang nguồn. Giữ nguyên để bảo toàn dữ liệu thô. |
| `author` | string | Không | Paragraph cuối của danh sách `p.Normal`. Bài chỉ được nhận khi paragraph này ngắn, không chứa số, không kết thúc như một câu và phần lớn từ bắt đầu bằng chữ hoa. |
| `url` | string | Không | URL chuẩn hóa của bài báo; là khóa định danh duy nhất trong dataset. |
| `content` | string | Không | Nội dung bài báo, các paragraph nối bằng ký tự xuống dòng và đã loại paragraph trùng hoàn toàn trong cùng bài. |
| `category` | string | Không | Chủ đề do AI suy luận chỉ từ tiêu đề; chưa đối chiếu chuyên mục chính thức trên VnExpress. |
| `crawled_at` | timestamp có múi giờ | Không | Gán đồng loạt 20/09/2026 05:00:00, múi giờ Asia/Ho_Chi_Minh (UTC+7), theo yêu cầu người dùng. Đây là thời gian bổ sung hồi tố, không phải log đo riêng từng bài. |

Các mô tả suy luận và gán giờ ở trên áp dụng cho dataset hiện có. Khi chạy crawler mới, `category` được lấy từ breadcrumb hoặc `article:section`; `crawled_at` ghi thời điểm tải thực tế từng bài. Metadata ghi đúng phương pháp của mỗi lần tạo dataset.

10 nhóm hợp lệ: Thời sự, Thế giới, Kinh doanh, Pháp luật, Khoa học - Công nghệ, Sức khỏe, Đời sống, Giáo dục, Du lịch, Ôtô - Xe máy. Nguồn chuẩn của danh sách là `src/schema.py`. Hai bài chạy cộng đồng trong bản suy luận được xếp vào Đời sống theo phạm vi 10 nhóm.

## Quy tắc chất lượng

- Dataset cuối phải có ít nhất 500 hàng.
- `url`, `title` và `content` không được trùng hoàn toàn.
- `title`, `description`, `published_at`, `url` và `content` không được thiếu.
- `author` không được phép thiếu; bài không tách được tác giả từ paragraph `p.Normal` cuối sẽ bị loại và được thay bằng bài khác.
- Bài có `content` dưới 100 ký tự hoặc không quá một paragraph không được tính vào dataset cuối.
