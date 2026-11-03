# Yêu cầu viết báo cáo (Phase 7)

_Soạn 03/11/2026. File này thay cho mọi mô tả cũ về báo cáo trong CLAUDE.md, PHAN_TICH_DE.md. Khi có file mẫu báo cáo của PTIT (`reports/template/`), làm theo mẫu về hình thức; phần nội dung vẫn theo file này._

## 1. Đề bài của giảng viên (nguyên văn)

> Các bước thực hiện:
> 1. Thu thập dữ liệu: Tìm kiếm thu thập dataset bình luận/sản phẩm.
> 2. Tiền xử lý dữ liệu: Áp dụng các kỹ thuật đã học (tách từ, loại bỏ stop words, ...).
> 3. Trích chọn đặc trưng: Thử nghiệm với ít nhất 2 phương pháp (BoW, TF-IDF, Word Embeddings).
> 4. Xây dựng và huấn luyện mô hình:
>    - Sử dụng 2 thuật toán phân loại (Naive Bayes, SVM).
>    - Chia dữ liệu thành tập huấn luyện và tập kiểm tra.
> 5. Đánh giá mô hình:
>    - Sử dụng các chỉ số: Accuracy, Precision, Recall, F1-Score, Confusion Matrix.
>    - So sánh hiệu suất giữa các phương pháp trích chọn đặc trưng và các thuật toán.
>
> Viết báo cáo: Tiêu đề, 1. Giới thiệu về bài toán, 2. Cơ sở lý thuyết, 3. Thực nghiệm và kết quả, Tài liệu tham khảo.

## 2. Sản phẩm

- **File nộp: `reports/BAO_CAO.docx`** (Word).
- File nguồn: `reports/BAO_CAO.md` (Markdown, công thức viết bằng LaTeX `$...$`), dựng ra docx bằng `python reports/build_docx.py` (pandoc qua `pypandoc_binary`, `--reference-doc=reports/template/reference.docx` nếu có). Sửa nội dung thì sửa file `.md` rồi dựng lại, không sửa tay file docx.
- Hình lấy từ `results/figures/`; nếu cần hình mới thì sinh bằng code (lưu `results/figures/report_*.png`), không vẽ tay.
- Hình thức mặc định (khi chưa có mẫu PTIT): A4; Times New Roman 13; giãn dòng 1,3; lề trên 2 cm, dưới 2 cm, trái 3 cm, phải 2 cm; đánh số trang ở giữa chân trang; tiêu đề mục đánh số 1, 1.1, 1.1.1; bảng và hình đánh số theo chương (Bảng 3.1, Hình 3.2), chú thích bảng đặt trên bảng, chú thích hình đặt dưới hình.

## 3. Bố cục (đúng và đủ các mục của đề, không thêm mục lớn)

**Trang bìa** (Tiêu đề): Học viện Công nghệ Bưu chính Viễn thông; tên môn "Phân tích và khai phá dữ liệu văn bản"; BÁO CÁO BÀI TẬP LỚN; tên đề tài "Phân loại cảm xúc bình luận sản phẩm trên Điện Máy Xanh"; giảng viên; nhóm, họ tên và mã sinh viên các thành viên; Hà Nội, tháng 11/2026. Thông tin còn thiếu để dạng `[...]` cho người dùng điền. Sau bìa là mục lục (trường TOC của Word).

**1. Giới thiệu về bài toán** (khoảng 1–1,5 trang)
- Bối cảnh: bình luận sản phẩm trên sàn thương mại điện tử, ích lợi của việc phân loại cảm xúc tự động.
- Phát biểu bài toán: đầu vào là một bình luận tiếng Việt trên dienmayxanh.com, đầu ra là một trong 3 nhãn Tích cực / Trung tính / Tiêu cực.
- Khó khăn: viết tắt, teencode, thiếu dấu; khen chê lẫn lộn trong một câu; số sao nhiều khi không khớp nội dung (nhất là 3 sao); dữ liệu lệch về Tích cực.
- Mục tiêu và phạm vi: tự thu thập dữ liệu; so sánh 3 cách trích đặc trưng (BoW, TF-IDF, Word2Vec) với 2 thuật toán (Naive Bayes, SVM); thêm PhoBERT làm mốc so sánh.
- Một đoạn ngắn nói bố cục báo cáo.

**2. Cơ sở lý thuyết** (khoảng 5–6 trang; chỉ lý thuyết của những gì thực sự dùng)
- 2.1 Quy trình phân loại văn bản (tiền xử lý → trích chọn đặc trưng → huấn luyện → đánh giá).
- 2.2 Tiền xử lý văn bản tiếng Việt: làm sạch; chuẩn hóa Unicode và vị trí dấu; chuẩn hóa từ viết tắt; tách từ (vì sao tiếng Việt cần tách từ, từ ghép); loại bỏ từ dừng và lý do giữ lại từ phủ định / mức độ; vì sao không cần stemming, lemmatization.
- 2.3 Trích chọn đặc trưng: BoW và n-gram; TF-IDF (công thức tf, idf, tf-idf); Word2Vec Skip-gram (ý tưởng, hàm mục tiêu ngắn gọn); vector câu bằng trung bình có trọng số TF-IDF (công thức).
- 2.4 Thuật toán phân loại: Naive Bayes (định lý Bayes, giả thiết độc lập, Multinomial NB, làm trơn Laplace có công thức; Gaussian NB cho đặc trưng liên tục); SVM (siêu phẳng lề cực đại, lề mềm và tham số C, hàm nhân RBF, cách mở rộng cho nhiều lớp: LinearSVC dùng one-vs-rest, SVC dùng one-vs-one).
- 2.5 PhoBERT (ngắn, khoảng nửa trang): Transformer, tiền huấn luyện trên dữ liệu tiếng Việt, tinh chỉnh cho phân loại.
- 2.6 Đánh giá mô hình: chia tập huấn luyện / kiểm định / kiểm tra; ma trận nhầm lẫn; Accuracy, Precision, Recall, F1 (có công thức); macro-F1 và lý do dùng khi dữ liệu lệch lớp (ví dụ mô hình luôn đoán lớp đông nhất).

**3. Thực nghiệm và kết quả** (khoảng 8–10 trang)
- 3.1 Môi trường và công cụ: Python, scikit-learn, gensim, underthesea, VnCoreNLP, PyTorch + transformers, Playwright; GPU dùng huấn luyện PhoBERT; link GitHub mã nguồn.
- 3.2 Thu thập dữ liệu: nguồn dienmayxanh.com, cách lấy (danh sách sản phẩm từ sitemap, trang đánh giá render bằng trình duyệt tự động, tôn trọng robots.txt, giãn cách truy cập, không lưu tên hay số điện thoại người bình luận); cách chọn sản phẩm và giới hạn theo số sao; số lượng thu được, số ngành hàng, số sản phẩm. Hình có sẵn từ notebook EDA: `eda_categories.png`, `eda_stars.png`, `eda_cleaning.png`, `eda_label_distribution.png`, `eda_length_by_label.png`, `eda_text_label_by_star.png`, `eda_top_terms.png` (chọn 3–4 hình cần nhất, không đưa hết).
- 3.3 Làm sạch và gán nhãn: các bước lọc và số lượng còn lại (lọc ngắn, trùng, gần trùng bằng cosine); gán nhãn: thử nhãn theo số sao trước, thấy lệch nhiều so với nội dung nên chuyển sang gán theo nội dung; tập kiểm tra 500 bình luận và cách gán, độ đồng thuận (kappa); phân bố nhãn 3 tập (bảng). **Phải nói thật cách gán nhãn**: nhãn theo nội dung do mô hình ngôn ngữ lớn gán theo một hướng dẫn cố định, nhóm duyệt lại các trường hợp nghi ngờ và một thành viên gán độc lập 100 câu để đo độ đồng thuận.
- 3.4 Tiền xử lý: các bước đã áp dụng theo đúng thứ tự trong `src/preprocess.py`, số liệu chính (số từ viết tắt được sửa, tỷ lệ token bị loại khi bỏ từ dừng…), bảng 2–3 ví dụ trước/sau.
- 3.5 Trích chọn đặc trưng và huấn luyện: cách chia tập (85/15 cho huấn luyện/kiểm định, 500 câu kiểm tra riêng, loại câu trùng); cấu hình từng đặc trưng; lưới tham số và tiêu chí chọn trên tập kiểm định; xử lý lệch lớp; siêu tham số PhoBERT.
- 3.6 Kết quả: bảng chính (Accuracy, Precision, Recall, F1 macro, F1 lớp Trung tính trên tập kiểm tra, kèm macro-F1 trên tập kiểm định); bảng so sánh 3 đặc trưng × 2 thuật toán (macro-F1); biểu đồ cột; ma trận nhầm lẫn của mô hình cổ điển tốt nhất và PhoBERT; nhận xét so sánh đặc trưng và thuật toán; thí nghiệm có/không bỏ từ dừng (1–2 câu); so sánh nhãn theo sao và nhãn theo nội dung (bảng ngắn); kiểm tra độ tin cậy (khoảng tin cậy bootstrap, chấm lại bằng nhãn của người) ngắn gọn.
- 3.7 Phân tích lỗi: bảng nhóm lỗi, 3–4 ví dụ tiêu biểu, câu thử "máy giặt chạy êm nhưng vắt không khô".
- 3.8 Kết luận và hướng phát triển (khoảng nửa trang đến 1 trang): kết quả chính, hạn chế (xem `STATUS.md` mục 5), hướng phát triển.

**Tài liệu tham khảo** (xem mục 6).

Tổng độ dài phần nội dung (không tính bìa, mục lục, tài liệu tham khảo): **khoảng 15–20 trang**. Không có phụ lục code.

## 4. Nội dung: đưa gì, bỏ gì

- **Mọi con số phải đọc từ `results/`** (`comparison.csv`, `robustness.csv`, `val_comparison.csv`, `metrics/*.json`, `label_noise*.csv`, `error_groups.csv`, `archive_star/comparison.csv`) hoặc `STATUS.md`. Không làm tròn khác với file (dùng 3 chữ số thập phân, dấu phẩy thập phân kiểu Việt Nam: 0,902).
- Kết quả chính là thí nghiệm B. Thí nghiệm A (nhãn theo sao) chỉ trình bày như lý do đổi cách gán nhãn, 1 bảng ngắn.
- Hạn chế phải có (viết gọn, không giấu): cùng một mô hình ngôn ngữ gán nhãn cả 3 tập; lớp Trung tính trong tập kiểm tra chỉ 47 mẫu; phân bố nhãn tập kiểm tra khác tập huấn luyện; dữ liệu khoảng 6.500 bình luận, ít hơn dự kiến; việc đổi cách gán nhãn được quyết định sau khi đã xem kết quả trên tập kiểm tra (hướng dẫn gán nhãn giữ nguyên); phân nhóm lỗi chỉ do một người làm, chưa đo độ đồng thuận.
- Khi so sánh hai mô hình TF-IDF: macro-F1 trên tập kiểm tra gần bằng nhau (0,804 và 0,799, khoảng tin cậy chồng nhau), còn khi chấm lại bằng nhãn của người trên 100 câu thì TF-IDF + NB (0,770) đứng trên TF-IDF + SVM (0,705). Vì vậy chỉ kết luận TF-IDF là cách trích đặc trưng tốt nhất trong nhóm cổ điển, không khẳng định SVM hơn NB. Số lấy từ `results/robustness.csv`.
- **Không đưa vào**: chi tiết kỹ thuật nội bộ (tên subagent, Claude Code, tên file batch, tên cột CSV, đường dẫn thư mục, lệnh chạy), các ký hiệu nội bộ như `[Ngoài slide]`, `(Ch.x §y)`, "thí nghiệm A/A′/B" (gọi là "nhãn theo số sao" và "nhãn theo nội dung"), phần làm dở bị bỏ (A′, 100 câu train), danh sách siêu tham số lặp lại hai lần, code.
- Có thể nhắc một lần ở 3.1: dữ liệu, mã nguồn và notebook có trong repo GitHub.

## 5. Văn phong

Viết như một sinh viên năm 4 tự viết báo cáo bài tập lớn:
- Tiếng Việt tự nhiên, ngôi "nhóm em" / "nhóm", giọng mô tả việc đã làm và lý do ("nhóm chọn…", "nhóm nhận thấy…").
- Chủ yếu viết đoạn văn; chỉ dùng gạch đầu dòng khi liệt kê thật sự (các bước, các công cụ). Không in đậm rải rác giữa câu.
- Câu rõ, độ dài câu đa dạng, đi thẳng vào ý. Mỗi nhận xét gắn với con số cụ thể.
- Tránh: câu mở/đóng sáo rỗng ("Trong thời đại công nghệ 4.0…", "Tóm lại…", "Có thể thấy rằng…" lặp lại), dấu gạch ngang dài để chèn ý, cấu trúc "không chỉ… mà còn…" lặp, liệt kê ba ý cho đủ nhịp, từ ngữ khoa trương ("vượt trội", "toàn diện", "mạnh mẽ"), câu hỏi tu từ, emoji, chú thích tiếng Anh thừa (chỉ để thuật ngữ tiếng Anh trong ngoặc ở lần đầu xuất hiện, ví dụ "từ dừng (stop words)").
- Thuật ngữ thống nhất trong toàn bài: tập huấn luyện / tập kiểm định / tập kiểm tra; Tích cực / Trung tính / Tiêu cực (lần đầu ghi kèm Positive / Neutral / Negative); ma trận nhầm lẫn.
- **Không có trích dẫn trong thân bài** (không [1], không "(Mikolov, 2013)", không ghi chương slide). Tài liệu chỉ liệt kê ở mục Tài liệu tham khảo.

## 6. Tài liệu tham khảo

Chỉ dùng tài liệu có thật, thông tin chính xác; chỉ liệt kê tài liệu liên quan trực tiếp tới nội dung báo cáo (khoảng 10–14 mục). Danh sách dưới đây đã kiểm tra, ưu tiên dùng; nếu muốn thêm tài liệu khác thì phải chắc chắn nó tồn tại và ghi đúng thông tin, không chắc thì không thêm. Trình bày theo kiểu IEEE, đánh số [1], [2], … theo thứ tự dưới đây hoặc theo thứ tự xuất hiện chủ đề.

1. Bài giảng môn Phân tích và khai phá dữ liệu văn bản, Học viện Công nghệ Bưu chính Viễn thông. _(tên giảng viên: người dùng bổ sung nếu muốn)_
2. C. D. Manning, P. Raghavan, H. Schütze, *Introduction to Information Retrieval*. Cambridge University Press, 2008.
3. B. Liu, *Sentiment Analysis and Opinion Mining*. Morgan & Claypool, 2012.
4. G. Salton, C. Buckley, "Term-weighting approaches in automatic text retrieval," *Information Processing & Management*, vol. 24, no. 5, pp. 513–523, 1988.
5. T. Mikolov, K. Chen, G. Corrado, J. Dean, "Efficient estimation of word representations in vector space," arXiv:1301.3781, 2013.
6. T. Mikolov, I. Sutskever, K. Chen, G. Corrado, J. Dean, "Distributed representations of words and phrases and their compositionality," in *Advances in Neural Information Processing Systems 26*, 2013, pp. 3111–3119.
7. A. McCallum, K. Nigam, "A comparison of event models for naive Bayes text classification," in *AAAI-98 Workshop on Learning for Text Categorization*, 1998, pp. 41–48.
8. C. Cortes, V. Vapnik, "Support-vector networks," *Machine Learning*, vol. 20, no. 3, pp. 273–297, 1995.
9. T. Joachims, "Text categorization with support vector machines: Learning with many relevant features," in *Proc. ECML-98*, LNCS 1398, Springer, 1998, pp. 137–142.
10. D. Q. Nguyen, A. T. Nguyen, "PhoBERT: Pre-trained language models for Vietnamese," in *Findings of the Association for Computational Linguistics: EMNLP 2020*, 2020, pp. 1037–1042.
11. J. Devlin, M.-W. Chang, K. Lee, K. Toutanova, "BERT: Pre-training of deep bidirectional transformers for language understanding," in *Proc. NAACL-HLT 2019*, 2019, pp. 4171–4186.
12. T. Vu, D. Q. Nguyen, D. Q. Nguyen, M. Dras, M. Johnson, "VnCoreNLP: A Vietnamese natural language processing toolkit," in *Proc. NAACL-HLT 2018: Demonstrations*, 2018, pp. 56–60.
13. F. Pedregosa et al., "Scikit-learn: Machine learning in Python," *Journal of Machine Learning Research*, vol. 12, pp. 2825–2830, 2011.
14. R. Řehůřek, P. Sojka, "Software framework for topic modelling with large corpora," in *Proc. LREC 2010 Workshop on New Challenges for NLP Frameworks*, 2010, pp. 45–50.
15. Underthesea: Vietnamese NLP toolkit. https://github.com/undertheseanlp/underthesea
16. J. Cohen, "A coefficient of agreement for nominal scales," *Educational and Psychological Measurement*, vol. 20, no. 1, pp. 37–46, 1960.

## 7. Thông tin người dùng cần cung cấp (để `[...]` nếu chưa có)

- Tên giảng viên; tên/số nhóm, lớp; họ tên và mã sinh viên các thành viên.
- Link repo GitHub (mặc định `https://github.com/sannguyen125/sentiment-classification`, cần để public trước khi nộp).
- File mẫu báo cáo PTIT (sẽ đặt ở `reports/template/`).

## 8. Rà soát

Sau khi dựng `BAO_CAO.docx`, gọi subagent `slide-reviewer` (nay là người rà soát báo cáo) theo `.claude/agents/slide-reviewer.md`, sửa theo mục "Phải sửa", dựng lại docx, rồi mới báo người dùng.
