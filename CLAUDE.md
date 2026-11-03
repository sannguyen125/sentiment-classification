# CLAUDE.md — BTL Phân loại cảm xúc review Điện Máy Xanh

## Bối cảnh
- Bài tập lớn môn **Phân tích và khai phá dữ liệu văn bản** (PTIT).
- Bài toán: phân loại cảm xúc review sản phẩm trên dienmayxanh.com thành **3 nhãn: Positive / Neutral / Negative**.
- Đề đầy đủ và phân tích chi tiết: `PHAN_TICH_DE.md`. **Đọc file này trước khi làm bất cứ việc gì.**
- Ngôn ngữ: code và comment tiếng Anh ngắn gọn được; báo cáo, notebook markdown, tin nhắn cho người dùng viết **tiếng Việt**.

## Nguyên tắc làm bài
1. **Bám đề, không làm phình.** Chỉ làm những gì có trong `PHAN_TICH_DE.md`. Muốn thêm gì thì hỏi trước.
2. **Bám slide chương 1–5.** Khi làm và khi báo cáo cho người dùng, mỗi kỹ thuật phải biết nó thuộc chương nào (xem Bản đồ slide bên dưới); kỹ thuật ngoài slide gắn nhãn **[Ngoài slide]** kèm 1 câu lý do. Riêng file báo cáo nộp (`reports/BAO_CAO.*`) **không** ghi chương slide hay `[Ngoài slide]`: theo `docs/YEU_CAU_BAO_CAO.md`.
3. **Làm theo từng Phase, dừng ở mỗi checkpoint** để người dùng kiểm tra. Không tự nhảy phase. Sau mỗi checkpoint, cập nhật `STATUS.md` trước khi dừng. Khi bắt đầu phiên mới, đọc `STATUS.md` trước.
4. **Chống rò rỉ dữ liệu:** chia tập trước; vectorizer, Word2Vec, scaler chỉ `fit` trên train. Tập test gold không bao giờ dùng để tinh chỉnh.
5. **Tái lập được:** `random_state=42` ở mọi chỗ; mọi bước chạy được bằng một lệnh `python -m src.<module>`.
6. **Không bịa số liệu.** Mọi con số trong báo cáo phải đọc từ file trong `results/`.

## Bản đồ slide → kỹ thuật (dùng để trích dẫn)
| Chương | Nội dung dùng trong bài |
|---|---|
| Ch.1 Cơ sở NLP | Công cụ tiếng Việt: Underthesea, VnCoreNLP, PhoBERT |
| Ch.2 Xử lý văn bản | §1 Tách từ (khoảng trắng, từ điển, học máy; thách thức tiếng Việt: từ ghép, viết tắt, dấu câu, số–đơn vị); §2 Chuẩn hóa: §2.1 làm sạch, §2.2 tách từ tiếng Việt, §2.3 ký tự đặc biệt + từ dừng (danh sách có thể tùy chỉnh), §2.4 chỉnh sửa từ ("ko" → "không"), §2.5 stemming/lemmatization (tiếng Việt đơn lập) |
| Ch.3 Phân loại văn bản | Quy trình 4 bước (tiền xử lý → đặc trưng → mô hình → đánh giá); BoW; TF-IDF; Word Embeddings (Word2Vec Skip-gram/CBOW, FastText, Transformer → vector ngữ cảnh); vector trung bình có trọng số TF-IDF; Naive Bayes + làm mịn Laplace; SVM; chia train/val/test (70–80% train); Confusion Matrix, Accuracy, Precision, Recall, F1 |
| Ch.4 Tóm tắt/chủ đề | Không dùng (chỉ nhắc LDA/NMF như hướng phát triển) |
| Ch.5 Tương tự & phân cụm | Cosine similarity (lọc review gần trùng); K-means + Elbow/Silhouette (EDA tùy chọn) |
| Ch.6 (nhẹ) | Ví dụ "mô hình lười" khi dữ liệu mất cân bằng → lý do chọn macro-F1 |

## Cấu trúc thư mục
```
btl-dmx/
├── CLAUDE.md, STATUS.md, PHAN_TICH_DE.md, requirements.txt, README.md
├── data/
│   ├── raw/        reviews.jsonl, html_cache/        (không commit)
│   ├── interim/    reviews_clean.csv                 (sau lọc + bỏ trùng + nhãn sao)
│   ├── gold/       gold_to_label.csv, gold_llm.csv (gộp llm_batches/, đã xóa), review_needed.csv,
│   │               g100_member2.csv, gold_test.csv   (tập test: LLM gán, người duyệt)
│   ├── pool_llm/   pool_llm.csv (nhãn chữ train/val, gộp batches/, đã xóa), id_map.csv
│   └── processed/  train.csv, val.csv, test.csv
├── resources/      stopwords_vi.txt, keep_words.txt, teencode.txt
├── src/
│   ├── crawl/      sitemap.py, reviews.py
│   ├── clean_label.py     lọc rác, bỏ trùng, gán nhãn sao, lấy mẫu tập gold
│   ├── gold_llm.py        prepare / merge / final cho nhãn gold (LLM gán, người duyệt)
│   ├── preprocess.py      text_clean + text_seg
│   ├── split.py           --labels star | text; loại câu train/val trùng text_clean với test
│   ├── pool_llm.py        prepare / todo / merge nhãn chữ cho train/val (LLM, cùng hướng dẫn gold)
│   ├── features.py        bow / tfidf / w2v
│   ├── train_classic.py   NB + SVM × 3 đặc trưng
│   ├── evaluate.py        chỉ số, confusion matrix, bảng so sánh, nhiễu nhãn, robustness
│   └── predict.py         demo
├── notebooks/  01_eda.ipynb, 02_phobert_colab.ipynb
├── docs/       HUONG_DAN_GAN_NHAN.md, KE_HOACH_NHAN_CHU.md
├── results/    metrics/*.json, figures/*.png, comparison.csv, robustness.csv, errors.csv,
│               error_groups.csv, archive_star/ (thí nghiệm A, nhãn sao)
└── reports/    BAO_CAO.md (nguồn) → BAO_CAO.docx (nộp), build_docx.py, template/ (mẫu PTIT)
```

## Các Phase và checkpoint

### Phase 0 — Khởi tạo
Tạo cấu trúc thư mục, `requirements.txt` (pandas, scikit-learn, underthesea, gensim, playwright, matplotlib, seaborn, tqdm; PhoBERT: transformers, torch, py_vncorenlp cài riêng khi chạy trên máy có GPU, notebook tự cài trên Colab), `README.md`.
**Checkpoint:** in cây thư mục.

### Phase 1 — Thu thập dữ liệu
Dùng skill **`dmx-crawler`** (đọc `.claude/skills/dmx-crawler/SKILL.md` trước khi viết crawler).
1. **Khảo sát trước:** mở 2–3 trang `.../danh-gia` bằng Playwright, lưu HTML mẫu, xác định selector và cách phân trang/lọc sao. Báo cáo lại cho người dùng.
2. Crawl **thử 3 sản phẩm**, in 10 dòng mẫu. **Checkpoint.**
3. Crawl đầy đủ (chạy nền, có resume từ cache). Mục tiêu ~8–10k review, ≥ 6 ngành hàng, ≥ 1.000 review 1–2★, ≥ 600 review 3★.
**Checkpoint:** thống kê số review theo ngành hàng và theo sao.

### Phase 2 — Làm sạch, gán nhãn, tập test gold
- `clean_label.py`: bỏ rỗng, < 3 từ, không phải tiếng Việt, phản hồi nhân viên; bỏ trùng y hệt; bỏ gần trùng bằng cosine TF-IDF > 0.9 (Ch.5) trên toàn bộ dữ liệu **trước** khi lấy mẫu gold (không rò rỉ câu gần trùng giữa test và train); nhãn sao 1–2 → Negative, 3 → Neutral, 4–5 → Positive (nay chỉ là nhãn đối chứng, xem Phase 4).
- Lấy mẫu phân tầng **500 review** → `data/gold/gold_to_label.csv`: đúng 1★100 / 2★70 / 3★150 / 4★80 / 5★100, **mỗi product_id tối đa 15 dòng**, seed 42; review bị loại trả về pool; **ẩn số sao**. Viết `docs/HUONG_DAN_GAN_NHAN.md` (định nghĩa 3 nhãn theo nội dung chữ, 10 ví dụ biên **không nằm trong gold**, quy tắc khen chê lẫn lộn → Neutral nếu cân bằng, nghiêng bên nào theo bên đó).
- **Gán nhãn gold: LLM gán, người duyệt [Ngoài slide]** (`src/gold_llm.py`):
  1. `python -m src.gold_llm prepare` → `data/gold/llm_batches/batch_XX.csv` (chỉ `id,text`) + `data/gold/g100_member2.csv` (G001–G100: `id,text,label_human_2` trống, không nhãn LLM).
  2. Subagent **`gold-labeler`** (`.claude/agents/gold-labeler.md`, chỉ Read + Write) gán từng lô 50 dòng → `batch_XX_out.csv` (`id,label_llm,confidence(high/low),reason`). Tuyệt đối không cho LLM thấy số sao.
  3. `python -m src.gold_llm merge` → `data/gold/gold_llm.csv` + `data/gold/review_needed.csv` (dòng có `label_llm ≠ label_star` hoặc `confidence = low`; cột `id,text,label_llm,reason,label_human` trống; **không** hiện sao/label_star).
  4. **Checkpoint — nhóm điền** `review_needed.csv[label_human]` và `g100_member2.csv[label_human_2]` (độc lập). **Đã làm (30/09/2026):** thành viên 2 điền đủ G001–G100; `review_needed` chỉ 2/191 dòng được người duyệt từng dòng, 189 dòng còn lại nhóm **chấp nhận nhãn LLM hàng loạt** (cột `nguon_nhan` = `nguoi` / `llm_chap_nhan`; `label_source` = `human` / `llm_accepted` / `llm`). Báo cáo phải nói rõ điều này.
  5. `python -m src.gold_llm final` → `data/gold/gold_test.csv`: nhãn cuối `label` = `label_human` nếu có, ngược lại `label_llm` (+ `label_source`); `results/metrics/gold_agreement.json`: kappa LLM vs thành viên 2 trên G001–G100, tỷ lệ nhãn LLM bị người sửa.
  - Báo cáo ghi rõ **[Ngoài slide]: "nhãn do LLM gán, người duyệt"**, và hạn chế: dòng LLM trùng nhãn sao không được người duyệt → tỷ lệ nhiễu nhãn sao là cận dưới.

### Phase 3 — Tiền xử lý
`preprocess.py` theo Ch.2, thứ tự: làm sạch → NFC + chuẩn dấu + rút ký tự lặp → chữ thường → chỉnh sửa từ (teencode) → tách từ underthesea → bỏ ký tự đặc biệt + stopword (**giữ** các từ trong `keep_words.txt`: không, chẳng, chưa, chả, đừng, rất, quá, lắm, hơi, khá, nhưng, tuy, mà, bị, được, tốt, kém…). Không stemming (ghi lý do).
Đầu ra 2 cột `text_clean`, `text_seg`. In 10 ví dụ trước/sau.
**Checkpoint.**

### Phase 4 — Chia tập, đặc trưng, NB + SVM
- `split.py`: loại các review thuộc gold khỏi pool; pool chia stratified (theo nhãn sao) 85/15 → train/val; test = gold (nhãn = cột `label` của `gold_test.csv`). Lưu thêm `label_star` trong test để đo nhiễu. **Loại khỏi train/val các review có `text_clean` trùng một câu test** (16 review).
- **Nhãn train/val = nhãn chữ (thí nghiệm B, kết quả chính, chốt 03/10/2026):** `python -m src.split --labels star` (cố định thành viên) → `python -m src.pool_llm prepare` → `gold-labeler` gán từng lô 50 câu, **nguyên văn** `docs/HUONG_DAN_GAN_NHAN.md`, chỉ thấy `id,text` → `python -m src.pool_llm merge` → `python -m src.split --labels text`. Nhãn sao (`label_star`) chỉ còn là đối chứng (thí nghiệm A, `results/archive_star/`). Báo cáo ghi **[Ngoài slide]**: train/val/test đều do cùng một LLM gán.
- `features.py`: BoW (1,1) và (1,2); TF-IDF (1,2), `min_df` tune; Word2Vec gensim Skip-gram 200 chiều train trên train, vector câu = trung bình có trọng số TF-IDF.
- `train_classic.py`: 6 cấu hình (3 đặc trưng × {NB, SVM}), tune grid nhỏ trên val theo macro-F1; baseline lớp đông nhất; thêm 1 thí nghiệm có/không bỏ stopword với cấu hình tốt nhất.
**Checkpoint:** bảng macro-F1 trên val.

### Phase 5 — PhoBERT (máy có GPU hoặc Colab)
`notebooks/02_phobert_colab.ipynb` chạy được trên máy có GPU (đã chạy trên RTX 3060 bằng `jupyter nbconvert --execute`, `PHOBERT_SEED=42/43/44`) hoặc độc lập trên Colab GPU: cài thư viện, tải `train/val/test.csv`, tách từ RDRSegmenter (py_vncorenlp; fallback underthesea, ghi chú), fine-tune `vinai/phobert-base-v2` (max_len 128, lr 2e-5, batch 16, 3–4 epoch, weighted CE, chọn epoch tốt nhất theo macro-F1 val), xuất `results/metrics/phobert.json` + `results/predictions/phobert_test.csv`.
Không chạy PhoBERT trên máy nếu không có GPU. Seed 42 = mô hình dùng cho test; seed 43/44 chỉ để đo dao động trên val. **Checkpoint:** kết quả nằm trong `results/` (chạy trên máy, hoặc người dùng chạy Colab và đưa file về).

### Phase 6 — Đánh giá và so sánh
`evaluate.py` trên test gold: Accuracy, P/R/F1 từng lớp + macro, confusion matrix (đếm + chuẩn hóa) cho mọi mô hình; `results/comparison.csv` + biểu đồ cột macro-F1; bảng nhiễu nhãn (nhãn sao vs nhãn gold, theo từng mức sao; Cohen's kappa LLM vs thành viên 2 và tỷ lệ nhãn LLM bị sửa, lấy từ `gold_agreement.json` **[Ngoài slide]**); `errors.csv` ~30 mẫu sai của mô hình tốt nhất cổ điển và PhoBERT, gắn nhóm lỗi (`results/error_groups.csv`, do Claude gán); **robustness** (chỉ đọc dự đoán đã có): bootstrap 2000 lần CI 95% macro-F1 và chấm theo nhãn thành viên 2 trên G001–G100 → `results/robustness.csv`, `results/metrics/robustness.json` **[Ngoài slide]**.
**Checkpoint.**

### Phase 7 — Báo cáo
**Làm đúng theo `docs/YEU_CAU_BAO_CAO.md`** (đề của giảng viên, bố cục, văn phong, tài liệu tham khảo, hình thức). Tóm tắt:
- Nộp `reports/BAO_CAO.docx`, dựng từ `reports/BAO_CAO.md` bằng `python reports/build_docx.py` (pandoc, mẫu `reports/template/reference.docx` nếu có).
- Bố cục đúng đề: Tiêu đề (bìa), 1. Giới thiệu về bài toán, 2. Cơ sở lý thuyết, 3. Thực nghiệm và kết quả, Tài liệu tham khảo. Khoảng 15–20 trang nội dung.
- Văn phong sinh viên tự viết, tiếng Việt tự nhiên; không trích dẫn trong thân bài, không ghi chương slide; tài liệu tham khảo có thật, thông tin đúng.
- Mọi số liệu lấy từ `results/` hoặc `STATUS.md`.
Sau đó gọi subagent **`slide-reviewer`** để rà soát; sửa theo góp ý, dựng lại docx rồi báo người dùng.

## Quy ước code
- Python 3.10+, type hints nhẹ, hàm nhỏ, không class thừa.
- Đường dẫn qua `pathlib`, cấu hình chung ở đầu file hoặc `src/config.py`.
- Log tiến trình bằng `tqdm`/`print`, không cần framework log.
- Không commit `data/raw/`, `html_cache/`, model > 50MB.

## Dữ liệu cá nhân
Không lưu tên, số điện thoại, avatar người review. ID review = hash. Không đưa dữ liệu thô chưa ẩn danh vào báo cáo.
