# PROMPT khởi động cho Claude Code

> Cách dùng:
> 1. Giải nén thư mục `btl-dmx/`. Nên copy thêm 6 file PDF slide vào `btl-dmx/slides/` để subagent đối chiếu.
> 2. Mở terminal trong `btl-dmx/` và chạy `claude`.
> 3. Dán nguyên phần trong khung dưới đây vào.
> 4. Mỗi lần Claude Code dừng ở checkpoint, kiểm tra kết quả rồi gõ "tiếp tục Phase N".

---

```
Bạn đang làm bài tập lớn môn "Phân tích và khai phá dữ liệu văn bản":
xây dựng hệ thống phân loại cảm xúc (Positive / Neutral / Negative)
cho review sản phẩm trên Điện Máy Xanh.

Trước khi làm gì:
1. Đọc kỹ CLAUDE.md và PHAN_TICH_DE.md. Đây là nguồn sự thật về đề bài,
   phạm vi, quy trình và cách trích dẫn slide.
2. Tóm tắt lại cho tôi (tiếng Việt, tối đa 15 dòng):
   - 5 bước của đề;
   - cách tạo nhãn đã chọn;
   - kế hoạch 8 Phase;
   - những gì cố ý KHÔNG làm.
3. Hỏi tôi nếu có điểm nào mâu thuẫn hoặc thiếu thông tin.

Sau đó thực hiện Phase 0 và Phase 1 theo CLAUDE.md.
- Ở Phase 1, đọc skill dmx-crawler trước khi viết crawler.
- Bắt buộc khảo sát DOM trước, rồi chạy thử 3 sản phẩm.
- Dừng ở checkpoint đầu tiên và chờ tôi xác nhận.

Quy tắc xuyên suốt:
- Làm đúng phạm vi đề, không thêm mô hình/kỹ thuật ngoài kế hoạch
  nếu chưa hỏi tôi.
- Mỗi kỹ thuật phải biết nó thuộc chương/mục nào của slide (chương 1–5;
  chương 6 chỉ trích nhẹ); kỹ thuật ngoài slide gắn nhãn [Ngoài slide].
- Dừng ở MỌI checkpoint. Khi dừng, báo ngắn gọn:
  đã làm gì, file nào, con số chính, việc tiếp theo.
- Không bịa số liệu; không tự gán nhãn tay thay tôi ở Phase 2.
- Nếu crawler bị chặn (403/429/captcha), dừng và báo tôi,
  không tìm cách lách.
```
