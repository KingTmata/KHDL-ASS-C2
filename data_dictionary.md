# Data dictionary: VnExpress news dataset

Mỗi hàng trong `Data/Raw/vnexpress_news.csv` đại diện cho một bài báo công khai thuộc một trong nhiều chuyên mục của VnExpress.

| Trường | Kiểu dữ liệu | Cho phép thiếu | Mô tả |
| --- | --- | --- | --- |
| `title` | string | Không | Tiêu đề chính của bài báo. |
| `description` | string | Không | Đoạn mô tả ngắn hoặc sapo của bài báo. |
| `published_at` | string | Không | Thời gian đăng theo văn bản hiển thị trên trang nguồn. Giữ nguyên để bảo toàn dữ liệu thô. |
| `author` | string | Không | Paragraph cuối của danh sách `p.Normal`. Bài chỉ được nhận khi paragraph này ngắn, không chứa số, không kết thúc như một câu và phần lớn từ bắt đầu bằng chữ hoa. |
| `url` | string | Không | URL chuẩn hóa của bài báo; là khóa định danh duy nhất trong dataset. |
| `content` | string | Không | Nội dung bài báo, các paragraph nối bằng ký tự xuống dòng và đã loại paragraph trùng hoàn toàn trong cùng bài. |

## Quy tắc chất lượng

- Dataset cuối phải có ít nhất 500 hàng.
- `url`, `title` và `content` không được trùng hoàn toàn.
- `title`, `description`, `published_at`, `url` và `content` không được thiếu.
- `author` không được phép thiếu; bài không tách được tác giả từ paragraph `p.Normal` cuối sẽ bị loại và được thay bằng bài khác.
- Bài có `content` dưới 100 ký tự hoặc không quá một paragraph không được tính vào dataset cuối.
