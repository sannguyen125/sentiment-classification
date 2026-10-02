# Phân tích đề BTL: Phân loại cảm xúc review sản phẩm Điện Máy Xanh

> Môn: Phân tích và khai phá dữ liệu văn bản (PTIT).
> Nền tảng lý thuyết: **Chương 1–5**. Chương 6 chỉ tham khảo nhẹ.
> Ký hiệu **[Ngoài slide]** = kỹ thuật lấy từ thực tế, dùng khi slide không nói tới.

---

## 1. Đề bài thực sự yêu cầu gì

| # | Yêu cầu | Mức | Slide làm nền |
|---|---|---|---|
| 1 | Thu thập review **trên Điện Máy Xanh (ĐMX)**, có nội dung và nhãn (hoặc thông tin suy ra nhãn, ví dụ số sao) | Bắt buộc | Ch.3 "Giới thiệu phân loại văn bản" (ví dụ "phân loại bình luận sản phẩm") |
| 2 | Tiền xử lý: làm sạch, chữ thường, tách từ, bỏ stopword, bỏ ký tự đặc biệt/URL, chuẩn hóa tiếng Việt | Bắt buộc | Ch.2 §1 (Tách từ), §2 (Chuẩn hóa: 2.1–2.5); Ch.1 (Underthesea, VnCoreNLP) |
| 3 | **≥ 2** phương pháp đặc trưng trong BoW / TF-IDF / Word Embeddings | Bắt buộc | Ch.3 "Trích chọn đặc trưng" |
| 4 | **Naive Bayes** và **SVM**, chia train/test | Bắt buộc | Ch.3 "Các thuật toán phân loại", "Chia tập dữ liệu" |
| 4b | Thêm **1 mô hình hiện đại** (Claude đề xuất) | Bổ sung | Ch.1 (PhoBERT); Ch.3 (Transformer tạo vector ngữ cảnh) |
| 5 | Accuracy, Precision, Recall, F1, Confusion Matrix; so sánh đặc trưng × thuật toán × mô hình hiện đại | Bắt buộc | Ch.3 "Đánh giá các mô hình phân loại" |
| — | Chọn 1 trong 4 cách tạo nhãn, độ khó vừa phải | Bắt buộc | (xem mục 2) |

Đề này trùng khít **quy trình phân loại văn bản 4 bước ở Chương 3**:
Tiền xử lý → Trích chọn đặc trưng → Xây dựng mô hình → Đánh giá.
Đề thêm **Bước 0: Thu thập và gán nhãn dữ liệu** đứng trước.

---

## 2. Chọn cách tạo nhãn

### Chọn: **Cách 1, 3 nhãn Positive / Neutral / Negative**, có thêm tập test gold gán theo nội dung chữ (LLM gán, người duyệt)

Nếu chỉ quy số sao thành nhãn thì bài dễ. Độ khó được nâng ở 3 điểm mà không làm bài phình to:

1. **Nhãn từ số sao cho train/val.** 1–2★ → Negative, 3★ → Neutral, 4–5★ → Positive. Nhanh nhưng nhiễu.
2. **Tập test gold 500 review gán nhãn theo nội dung chữ**, không nhìn số sao. Nhãn do **LLM gán, người duyệt** **[Ngoài slide]**: LLM (subagent `gold-labeler`) gán cả 500 review; nhóm duyệt lại các dòng LLM khác nhãn sao hoặc LLM tự đánh giá độ tin cậy thấp; thành viên 2 gán độc lập G001–G100 để đo Cohen's kappa với LLM. Tập gold cho phép đo tỷ lệ "sao nói một đằng, chữ nói một nẻo". Ví dụ thật trên ĐMX: review 5★ nhưng nội dung báo máy đang lỗi, nhờ shop khắc phục. Hạn chế: dòng LLM trùng nhãn sao không được người duyệt, nên tỷ lệ nhiễu nhãn sao đo được là cận dưới.
3. **Mất cân bằng nặng.** Review ĐMX phần lớn là 5★, nên phải xử lý mất cân bằng và lấy **macro-F1** làm chỉ số chính. Ch.3 nói F1 hữu ích khi Precision và Recall lệch nhau. Ví dụ "mô hình lười" trong Ch.6 (luôn đoán Tích cực, Accuracy 99% mà vô dụng) chỉ dẫn nhẹ.

Lớp **Neutral** (3★, khen chê lẫn lộn) là lớp khó nhất. Đây là chỗ để phân tích lỗi có chiều sâu.

### Vì sao không chọn 3 cách còn lại

| Cách | Lý do loại |
|---|---|
| 2. Điểm −1 → 1 | Là bài **hồi quy**, trong khi đề bắt buộc Naive Bayes, SVM, Accuracy và Confusion Matrix (đều là phân loại). Cuối cùng vẫn phải rời rạc hóa thành nhãn. |
| 3. Theo khía cạnh | ĐMX có hàng chục ngành hàng, mỗi ngành một bộ khía cạnh. Phải gán tay từng khía cạnh cho hàng nghìn review, quá sức một BTL. |
| 4. Đa nhãn cảm xúc | Review điện máy gần như chỉ có hài lòng hoặc bực bội; sợ hãi, bất ngờ… hầu như không có. Phải gán tay toàn bộ, và Confusion Matrix đa nhãn không còn dạng chuẩn. |

---

## 3. Có crawl được dữ liệu không?

**Kết luận: CÓ, nhưng phải dùng trình duyệt tự động (Playwright) và tuân thủ robots.txt.** Không có dataset công khai nào ghi rõ nguồn ĐMX, nên phải tự crawl.

| Kiểm tra (29/09/2026) | Kết quả |
|---|---|
| `robots.txt` | **Không chặn** trang sản phẩm và trang đánh giá `/{ngành-hàng}/{sản-phẩm}/danh-gia`. **Chặn** `/aj/`, `/support/`, `/Services`, `/cart`, `/tu-van`… và vài ngành hàng (`/may-tinh-tin-hoc`, `/balo-laptop`, `/loa-nghe-nhac-da-nang`…). |
| Sitemap | Có sẵn danh sách sản phẩm: `https://www.dienmayxanh.com/newsitemap/sitemap-product` |
| Trang đánh giá | Danh sách review nạp bằng JavaScript, nên `requests` + BeautifulSoup không đủ. Cần **Playwright** để render như trình duyệt thật. |
| Dataset có sẵn | Không tìm thấy bộ nào của ĐMX trên Kaggle/HuggingFace. |

### Quy tắc crawl (bắt buộc)
- Lấy URL sản phẩm từ sitemap. **Không** vào các ngành hàng bị chặn.
- **Không gọi trực tiếp endpoint `/aj/...`**, kể cả khi thấy trong tab Network. Chỉ để trang tự nạp khi bấm "Xem thêm" hoặc chuyển trang.
- 1 luồng, nghỉ 2–4 giây mỗi lần tải; cache HTML; dừng ngay khi gặp 403/429/captcha.
- **Không lưu họ tên, số điện thoại người review** (Nghị định 13/2023 về dữ liệu cá nhân). Bỏ phần trả lời của nhân viên ĐMX.

### Mục tiêu dữ liệu
- ~**8.000–10.000 review** từ **≥ 6 ngành hàng** (máy giặt, tủ lạnh, điều hòa, tivi, nồi cơm, máy lọc nước…).
- Chủ động săn review sao thấp: mục tiêu ≥ 1.000 Negative, ≥ 600 Neutral. Cách làm: ưu tiên sản phẩm nhiều review và sản phẩm điểm trung bình thấp; dùng bộ lọc số sao nếu trang có.
- Dự phòng nếu bị chặn: chạy từ máy cá nhân, giảm tốc độ. Chỉ khi thật cần mới bổ sung dữ liệu ngoài ĐMX cho train (ví dụ UIT-ViSFD) và phải ghi rõ trong báo cáo; **tập test phải 100% ĐMX**.

---

## 4. Các bước phân loại văn bản, chi tiết từng bước

### Bước 0. Thu thập và gán nhãn

| Bước con | Làm gì | Slide |
|---|---|---|
| 0.1 Lấy danh sách sản phẩm | Parse sitemap, lọc ngành hàng hợp lệ | [Ngoài slide] |
| 0.2 Crawl review | Playwright mở `.../danh-gia`, bấm xem thêm/chuyển trang, lấy: nội dung, số sao, ngày, ngành hàng, mã sản phẩm | [Ngoài slide] |
| 0.3 Lưu dữ liệu thô | `data/raw/reviews.jsonl` | — |
| 0.4 Lọc rác | Bỏ rỗng, quá ngắn (< 3 từ), không phải tiếng Việt, phản hồi nhân viên | Ch.2 §2 ("loại bỏ nhiễu") |
| 0.5 Bỏ trùng | Trùng y hệt: so chuỗi. **Gần trùng**: cosine similarity trên TF-IDF > 0.9 | **Ch.5** (độ tương tự cosine) |
| 0.6 Gán nhãn theo sao | 1–2★ Neg, 3★ Neu, 4–5★ Pos | — |
| 0.7 Tập test gold | Lấy 500 review phân tầng theo sao (1★100 / 2★70 / 3★150 / 4★80 / 5★100, mỗi sản phẩm ≤ 15). LLM gán nhãn, người duyệt các dòng lệch nhãn sao hoặc độ tin cậy thấp; thành viên 2 gán độc lập 100 mẫu để đo kappa với LLM | [Ngoài slide] |
| 0.8 Khám phá dữ liệu (EDA) | Phân bố nhãn, theo ngành hàng, độ dài review, top từ mỗi lớp, word cloud. Tùy chọn: K-means trên TF-IDF để xem review tự gom thành nhóm chủ đề nào | Ch.3; **Ch.5** (K-means, Elbow) |

### Bước 1. Tiền xử lý (Ch.2)

| Bước con | Làm gì | Slide |
|---|---|---|
| 1.1 Làm sạch | Bỏ HTML, URL, email, SĐT, emoji, ký tự lạ, khoảng trắng thừa | Ch.2 §2.1 |
| 1.2 Chuẩn hóa tiếng Việt | Unicode NFC; thống nhất vị trí dấu (hoà ↔ hòa); rút ký tự lặp ("tốtttt" → "tốt") | Ch.2 §2 |
| 1.3 Chữ thường | `lower()` | Ch.2 §2.1 |
| 1.4 Chỉnh sửa từ | Từ điển viết tắt/teencode: ko, k, hok → không; dc, đc → được; sp → sản phẩm; nv → nhân viên… | Ch.2 §2.4 (có đúng ví dụ "ko" → "không") |
| 1.5 Tách từ | `underthesea.word_tokenize(..., format="text")` → "máy_giặt chạy êm" | Ch.2 §1, §2.2; Ch.1 |
| 1.6 Bỏ ký tự đặc biệt và stopword | Danh sách stopword tiếng Việt **nhưng giữ** từ phủ định/mức độ/tương phản: không, chưa, chẳng, rất, quá, hơi, nhưng, bị, được… vì bỏ đi sẽ làm "không tốt" thành "tốt" | Ch.2 §2.3 ("có thể tùy chỉnh") |
| 1.7 Lấy từ gốc | **Không áp dụng**, giải thích: tiếng Việt đơn lập, không biến hình | Ch.2 §2.5 |
| 1.8 Kiểm chứng | So sánh kết quả khi có và không bỏ stopword | Ch.2 §2.3 |

Đầu ra có 2 cột:
- `text_clean`: đủ các bước, dùng cho BoW, TF-IDF, Word2Vec.
- `text_seg`: chỉ chuẩn hóa và tách từ, giữ stopword, dùng cho PhoBERT.

### Bước 2. Trích chọn đặc trưng (Ch.3), làm cả 3 cách

| Đặc trưng | Cấu hình | Slide |
|---|---|---|
| **BoW** | `CountVectorizer`, unigram và unigram+bigram (bigram giữ được "không tốt") | Ch.3 "Túi từ" |
| **TF-IDF** | `TfidfVectorizer`, n-gram (1,2), `min_df` | Ch.3 "TF-IDF" |
| **Word Embeddings** | Word2Vec (gensim, Skip-gram, 100–300 chiều) huấn luyện trên tập train. Vector câu = **trung bình có trọng số TF-IDF** | Ch.3 "Word2Vec", "Vector từ trung bình có trọng số TF-IDF" |

Chống rò rỉ dữ liệu: mọi vectorizer và Word2Vec **chỉ fit trên train**.

### Bước 3. Xây dựng mô hình (Ch.3)

| Hạng mục | Chi tiết | Slide |
|---|---|---|
| Chia dữ liệu | Dữ liệu nhãn-sao chia stratified **train 85% / val 15%**. **Test = 500 review gold** (loại khỏi train/val) | Ch.3 "Chia tập dữ liệu" (train/val/test) |
| Naive Bayes | `MultinomialNB(alpha)` cho BoW/TF-IDF (alpha chính là làm mịn Laplace); `GaussianNB` cho Word2Vec (vector có giá trị âm) | Ch.3 NB + Laplace smoothing |
| SVM | `LinearSVC` cho BoW/TF-IDF (không gian nhiều chiều); `SVC(kernel="rbf")` cho Word2Vec | Ch.3 SVM |
| Mất cân bằng | `class_weight="balanced"` cho SVM; NB thử `fit_prior` | Ch.3 (nhược điểm NB với dữ liệu lệch) |
| Tinh chỉnh | Grid nhỏ trên val: `alpha`, `C`, `ngram_range`, `min_df` | Ch.3 (vai trò validation set) |
| Ma trận thí nghiệm | 3 đặc trưng × 2 thuật toán = **6 cấu hình** + baseline "luôn đoán lớp đông nhất" | — |

### Bước 3b. Mô hình hiện đại: **Fine-tune PhoBERT** (`vinai/phobert-base-v2`)
- **Lý do chọn:** Ch.1 liệt kê PhoBERT là công cụ NLP tiếng Việt; Ch.3 nói Transformer tạo vector ngữ cảnh động, khắc phục điểm yếu bỏ qua thứ tự từ của BoW/TF-IDF. PhoBERT được pretrain trên tiếng Việt nên tốt hơn BERT đa ngôn ngữ **[Ngoài slide phần fine-tune]**.
- **Đầu vào:** `text_seg` (tách từ bằng VnCoreNLP RDRSegmenter như PhoBERT khuyến nghị; nếu cài không được thì dùng underthesea và ghi chú), `max_len=128`.
- **Huấn luyện:** lr 2e-5, batch 16, 3–4 epoch, cross-entropy có trọng số lớp, giữ checkpoint tốt nhất theo macro-F1 trên val. Chạy trên **Google Colab/Kaggle GPU** (notebook riêng).

### Bước 4. Đánh giá và so sánh (Ch.3)

| Hạng mục | Chi tiết |
|---|---|
| Chỉ số | Accuracy; Precision, Recall, F1 theo từng lớp + macro. **Chỉ số chính: macro-F1** |
| Confusion Matrix | Cho mọi mô hình (số đếm + chuẩn hóa theo hàng) |
| Bảng so sánh | 6 cấu hình cổ điển + PhoBERT + baseline, biểu đồ cột macro-F1 |
| Nhiễu nhãn | Trên 500 review gold: tỷ lệ nhãn-sao khác nhãn gold, theo từng mức sao (cận dưới, xem mục 2); kappa LLM vs thành viên 2, tỷ lệ nhãn LLM bị người sửa |
| Phân tích lỗi | Lấy ~30 mẫu sai, nhóm theo: phủ định, khen chê lẫn lộn, châm biếm, sao lệch nội dung, viết tắt, Neutral |
| Demo | `predict("máy giặt chạy êm nhưng vắt không khô")` |

---

## 5. Những thứ cố ý KHÔNG làm (để khỏi phình bài)
- Không so sánh thêm Logistic Regression, Random Forest, KNN.
- Không làm ABSA hay đa nhãn cảm xúc.
- Không làm LSTM/CNN riêng (PhoBERT đã là mô hình hiện đại).
- Không K-fold CV đầy đủ, không ROC-AUC (Ch.3 có, nhưng đề không yêu cầu).
- Chương 4 (LDA/NMF) không dùng; chỉ nhắc như hướng phát triển.

## 6. Sản phẩm nộp
1. Code chạy lại được (`src/`, `requirements.txt`, seed 42).
2. Dữ liệu đã xử lý (không có thông tin cá nhân) + tập test gold (nhãn LLM, nhãn người duyệt, nhãn cuối).
3. Notebook EDA + notebook PhoBERT (Colab).
4. `results/`: bảng chỉ số, confusion matrix, biểu đồ.
5. Báo cáo `reports/BAO_CAO.md` theo đúng 5 bước của đề, mỗi kỹ thuật ghi chương slide.
