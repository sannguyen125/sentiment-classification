# Hướng dẫn gán nhãn tay tập test (gold)

Tập test gồm 500 review (`data/gold/gold_to_label.csv`). Quy trình: **LLM gán nhãn trước, người duyệt sau** **[Ngoài slide]** (chi tiết ở mục 4). Cả LLM và người đều theo cùng các quy tắc dưới đây.

Mục đích: tập test được gán theo **nội dung chữ**, **không** theo số sao. Số sao đã bị ẩn, bạn cũng không cần tra lại. Từ tập này, báo cáo sẽ đo được tỷ lệ "sao nói một đằng, chữ nói một nẻo".

## 1. Ba nhãn

| Nhãn | Khi nào dùng | Dấu hiệu thường gặp |
|---|---|---|
| **Positive** | Người viết nhìn chung **hài lòng** với sản phẩm hoặc dịch vụ | tốt, ổn, ok, êm, mát, hài lòng, đáng tiền, nên mua, giao nhanh, nhân viên nhiệt tình |
| **Negative** | Người viết nhìn chung **không hài lòng**: chê, báo lỗi, hư hỏng, phàn nàn về giao hàng, lắp đặt, bảo hành, giá | tệ, lỗi, hư, kêu to, rò nước, không lạnh, thất vọng, không ai hỗ trợ, đừng mua |
| **Neutral** | **Không có cảm xúc rõ ràng**, hoặc **khen chê cân bằng** | câu hỏi thuần thông tin; chưa dùng nên chưa đánh giá; "bình thường", "tạm được", "tàm tạm" |

## 2. Quy tắc

1. **Chỉ đọc chữ.** Không đoán số sao. Emoji và viết tắt đọc theo nghĩa ("ko" = không, "đc" = được).
2. **Tính cả sản phẩm lẫn dịch vụ** (giao hàng, lắp đặt, bảo hành, giá của ĐMX). Chê dịch vụ vẫn là Negative, khen dịch vụ vẫn là Positive.
3. **Khen chê lẫn lộn:** nếu hai bên **cân bằng** thì chọn **Neutral**. Nếu **nghiêng** về bên nào thì chọn nhãn của bên đó. Cách cân: lỗi làm sản phẩm hỏng hoặc không dùng được thì nặng hơn một lời khen chung chung; một lời chê nhỏ kiểu "hơi ồn chút" thì nhẹ hơn nhiều lời khen cụ thể.
4. **"ổn", "ok", "tốt" là Positive.** Còn **"bình thường", "tạm được", "tàm tạm"** đứng một mình là **Neutral**.
5. **Câu hỏi:** hỏi thông tin thuần túy (cách dùng, phụ kiện) là **Neutral**. Hỏi vì **đang gặp sự cố** ("máy kêu vậy là bị gì?") là **Negative**.
6. **Mỉa mai:** gán theo nghĩa thật ("Tuyệt vời, mới mua 3 hôm đã hỏng" là Negative).
7. **Phàn nàn ngầm** (bị hớ giá, chờ lâu…) vẫn tính là không hài lòng. Nó nặng hay nhẹ thì cân theo quy tắc 3.
8. Chuỗi `<phone>` là số điện thoại đã được che, bỏ qua.
9. Gặp câu **thật sự khó** thì vẫn chọn một nhãn, rồi ghi "khó" kèm lý do ngắn vào cột `ghi_chu`.

## 3. Mười ví dụ biên

Các ví dụ lấy từ dữ liệu crawl, **không nằm trong 500 review cần gán**.

| # | Review | Nhãn | Lý do |
|---|---|---|---|
| 1 | không mát bằng máy lạnh nhưng mà có máy này vô thì cảm giác đỡ khô với ngộp hơn với đỡ tốn điện. nhân viên dễ thương lắm | Positive | Có 1 ý chê nhẹ, sau đó 3 ý khen: nghiêng khen (quy tắc 3) |
| 2 | Oke nhưng mua trúng đợi sale ít nên giờ hơi ít vui | Neutral | Hài lòng sản phẩm nhưng tiếc về giá, hai bên cân nhau |
| 3 | Sản phẩm có một đèn báo chế độ nấu (rán) ko sáng. Nhưng thôi kệ vẫn sử dụng bình thường | Neutral | Có lỗi nhỏ, người viết chấp nhận, không khen cũng không bức xúc |
| 4 | Máy hơi ồn. Tạm được | Neutral | Chê nhẹ đi kèm "tạm được", không có ý khen nào (quy tắc 4) |
| 5 | Mua từ 23.04 xài tạm ổn, máy chạy êm, giao hàng cũng khá nhanh. | Positive | "tạm ổn" đi kèm 2 ý khen cụ thể: nghiêng khen |
| 6 | Cho mình hỏi nước giặt chính xác là để ngăn I hay ngăn II vậy | Neutral | Hỏi thông tin thuần túy (quy tắc 5) |
| 7 | E mua tủ này bữa 10/10 đến nay tối nào e cũng nghe nó nhiễu nước ở phía sau khoảng 5p 10p vậy tủ e đang bị gì ạk ? | Negative | Hỏi vì đang gặp sự cố (quy tắc 5) |
| 8 | Mới mua 12tr nay giảm còn 10tr | Negative | Phàn nàn ngầm về giá, không có ý khen nào (quy tắc 7) |
| 9 | Mát thật, êm cũng thật, mà mới mua máy hôm sao thấy lỗi rồi 😂 | Negative | Lỗi ngay khi mới mua nặng hơn lời khen; emoji không đổi nghĩa |
| 10 | tủ xài bình thường, tốt ạ | Positive | "bình thường" ở đây nghĩa là chạy ổn, và có thêm "tốt": không phải "bình thường" đứng một mình |

## 4. Cách làm

1. **LLM** (subagent `gold-labeler`) gán cả 500 review, theo lô 50, kết quả ở `data/gold/gold_llm.csv`. LLM chỉ thấy `id` và `text`.
2. **Nhóm duyệt `data/gold/review_needed.csv`.** File này gồm các dòng mà nhãn LLM khác nhãn suy ra từ số sao, hoặc LLM tự đánh giá độ tin cậy thấp. File có nhãn và lý do của LLM để tham khảo, nhưng **không** có số sao. Đọc chữ rồi điền nhãn đúng vào cột `label_human` cho **mọi dòng**; nếu đồng ý với LLM thì chép lại nhãn đó.
3. **Thành viên 2** điền cột `label_human_2` trong `data/gold/g100_member2.csv` (G001–G100). File này **không** có nhãn LLM. Làm **độc lập**: không xem `gold_llm.csv` hay `review_needed.csv` trước khi xong. Dữ liệu này dùng để đo độ đồng thuận giữa LLM và người (Cohen's kappa).
4. Giá trị hợp lệ: `Positive`, `Neutral`, `Negative` (viết tắt `Pos`, `Neu`, `Neg` cũng được). **Không** sửa các cột khác.
5. Lưu **đè đúng tên file cũ**, định dạng **CSV UTF-8**. Trong Excel: *Save As, chọn "CSV UTF-8 (Comma delimited)"*. Trong Google Sheets: *File, Download, chọn .csv*. Nếu lưu kiểu CSV thường, Excel sẽ làm hỏng chữ tiếng Việt.
6. Sau đó chạy `python -m src.gold_llm final`. Nhãn cuối lấy `label_human` nếu có, không thì lấy `label_llm`, rồi ghi ra `data/gold/gold_test.csv`.
