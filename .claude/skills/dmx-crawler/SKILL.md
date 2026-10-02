---
name: dmx-crawler
description: Quy tắc và cách crawl review sản phẩm dienmayxanh.com bằng Playwright một cách lịch sự, đúng robots.txt. Dùng khi viết hoặc chạy crawler ở Phase 1.
---

# Crawl review Điện Máy Xanh

## Luật cứng (không được vi phạm)
1. **Tuân thủ robots.txt** (đã kiểm tra 29/09/2026).
   - Cấm các đường dẫn: `/aj/`, `/support/`, `/Services`, `/cart`, `/tu-van`, `/chat`, `/price/`, `/tracking/`, `/uploads`, `/bin/`, `/cms/`.
   - Cấm các ngành hàng: `/may-nghe-nhac-mp3`, `/tu-dien-dien-tu`, `/may-mp4-mp5`, `/may-tinh-tin-hoc`, `/loa-nghe-nhac-da-nang`, `/balo-laptop`.
   - Đầu mỗi phiên chạy, tải lại robots.txt và kiểm tra bằng `urllib.robotparser` trước mỗi URL.
2. **Không gọi trực tiếp endpoint AJAX** (`/aj/...`) bằng `requests` hay `page.request`, kể cả khi thấy trong tab Network. Chỉ tương tác với trang như người dùng: bấm "Xem thêm", chuyển trang, dùng bộ lọc sao.
3. **Giới hạn tốc độ.**
   - 1 trình duyệt, 1 tab.
   - Nghỉ ngẫu nhiên 2–4 giây giữa các lần tải.
   - Sau mỗi 50 sản phẩm, nghỉ 30–60 giây.
   - Gặp HTTP 403/429, captcha hoặc trang lạ thì **dừng hẳn và báo người dùng**, không tìm cách lách.
4. **Không lưu dữ liệu cá nhân.** Bỏ tên, số điện thoại, avatar người review. Đặt `review_id = sha1(product_id + date + text)[:16]`.
5. **Bỏ phản hồi của Điện máy XANH / quản trị viên** (thường nằm lồng dưới review). Chỉ giữ review gốc của khách.

## Quy trình
1. **Lấy danh sách sản phẩm từ sitemap.**
   - Tải `https://www.dienmayxanh.com/newsitemap/sitemap-product`. Nếu đây là sitemap index thì tải tiếp các sitemap con.
   - Suy ra ngành hàng từ phần đầu của URL và lọc bỏ ngành bị cấm.
   - Ưu tiên: máy giặt, tủ lạnh, máy lạnh, tivi, nồi cơm điện, máy lọc nước, quạt, lò vi sóng, máy nước nóng, bếp điện.
   - Lưu vào `data/raw/products.csv`.
2. **Khảo sát DOM (bắt buộc trước khi viết selector).**
   - Mở 2–3 URL `{product_url}/danh-gia` bằng Playwright: headless Chromium, locale `vi-VN`, user agent trình duyệt bình thường.
   - Chờ trang tải xong, lưu HTML vào `data/raw/html_cache/_survey/`.
   - Xác định: khối từng review, số sao, nội dung, ngày, dấu "Đã mua tại", nút xem thêm/phân trang, bộ lọc theo số sao, khối phản hồi của shop.
   - Ghi selector vào `src/crawl/selectors.py` kèm comment, rồi **báo lại người dùng**.
3. **Chọn sản phẩm.**
   - Đọc số lượng đánh giá và điểm trung bình trên trang sản phẩm.
   - Ưu tiên sản phẩm có ≥ 30 đánh giá.
   - Chủ động lấy thêm sản phẩm có điểm trung bình thấp (< 4.5) để có review tiêu cực.
   - Lấy tối đa khoảng 300 review mỗi sản phẩm để dữ liệu không dồn vào vài sản phẩm.
4. **Crawl review.**
   - Nếu trang có bộ lọc sao: duyệt từng mức 1★ → 5★. Với 4★ và 5★ có thể dừng sớm khi chạm giới hạn.
   - Nếu không có bộ lọc: phân trang toàn bộ.
   - Mỗi review ghi 1 dòng JSONL:
     `{review_id, product_id, product_url, category, star, text, date, verified_purchase, crawled_at}`
5. **Chạy tiếp được khi bị ngắt.**
   - Lưu các sản phẩm đã xong vào `data/raw/crawl_state.json`; lần chạy sau bỏ qua chúng.
   - Cache HTML theo URL để không tải lại.
6. **Theo dõi mục tiêu.**
   - Sau mỗi 20 sản phẩm, in bảng đếm theo số sao.
   - Dừng khi đạt khoảng 8–10k review, trong đó ≥ 1.000 review 1–2★ và ≥ 600 review 3★, hoặc khi hết sản phẩm hợp lệ.

## Chạy thử trước
Lệnh: `python -m src.crawl.reviews --limit-products 3 --print-sample 10`

Lệnh này in 10 review mẫu. Dừng ở đây (checkpoint) để người dùng xem trước khi crawl đầy đủ.

## Khi không đủ review sao thấp
1. Mở rộng sang ngành hàng khác.
2. Hạ ngưỡng chọn sản phẩm từ ≥ 30 xuống ≥ 15 đánh giá.
3. Ưu tiên thêm sản phẩm điểm thấp.

Nếu vẫn thiếu, báo người dùng. **Không tự ý** lấy dữ liệu từ website khác.
