# BTL: Phân loại cảm xúc review Điện Máy Xanh

Môn **Phân tích và khai phá dữ liệu văn bản** (PTIT). Phân loại review sản phẩm trên dienmayxanh.com thành 3 nhãn **Positive / Neutral / Negative**.

Đề và kế hoạch chi tiết: [`PHAN_TICH_DE.md`](PHAN_TICH_DE.md). Quy ước làm bài: [`CLAUDE.md`](CLAUDE.md). Trạng thái và kết quả: [`STATUS.md`](STATUS.md).

## Nhãn dữ liệu
| Tập | Nhãn | Cách tạo |
|---|---|---|
| Test (500 review gold) | `label` của `data/gold/gold_test.csv` | LLM (subagent `gold-labeler`) gán theo nội dung chữ với `docs/HUONG_DAN_GAN_NHAN.md`, người duyệt; thành viên 2 gán độc lập 100 câu để đo kappa |
| Train/val (thí nghiệm **B**, kết quả chính) | `label_text` của `data/pool_llm/pool_llm.csv` | LLM gán theo nội dung chữ, **cùng hướng dẫn** với gold, không thấy số sao |
| Đối chứng (thí nghiệm **A**) | `label_star` | 1–2★ Negative, 3★ Neutral, 4–5★ Positive; kết quả lưu ở `results/archive_star/` |

Các review train/val có `text_clean` trùng với một câu test bị loại khỏi train/val (`src/split.py`).

## Cài đặt
```bash
pip install -r requirements.txt
python -m playwright install chromium          # chỉ cần cho bước crawl
```
PhoBERT cần thêm thư viện, xem ghi chú cuối `requirements.txt` (máy có GPU hoặc Colab).

## Chạy từng bước
| Phase | Lệnh |
|---|---|
| 1. Thu thập | `python -m src.crawl.sitemap` → `python -m src.crawl.reviews` |
| 2. Làm sạch, nhãn sao, lấy mẫu gold | `python -m src.clean_label` |
| 2. Nhãn gold (LLM gán, người duyệt) | `python -m src.gold_llm prepare` → subagent `gold-labeler` từng lô → `python -m src.gold_llm merge` → nhóm điền `review_needed.csv`, `g100_member2.csv` → `python -m src.gold_llm final` |
| 3. Tiền xử lý | `python -m src.preprocess` |
| 4. Chia tập (lần 1, để cố định thành viên train/val) | `python -m src.split --labels star` |
| 4. Nhãn chữ cho train/val | `python -m src.pool_llm prepare` → subagent `gold-labeler` từng lô (`python -m src.pool_llm todo` để resume) → `python -m src.pool_llm merge` |
| 4. Chia tập (nhãn chữ) | `python -m src.split --labels text` |
| 4. Đặc trưng, NB + SVM | `python -m src.train_classic` |
| 5. PhoBERT | `notebooks/02_phobert_colab.ipynb` trên máy có GPU hoặc Colab. Seed: biến môi trường `PHOBERT_SEED` (42 = mô hình dùng cho test; 43, 44 = đo dao động). Chạy không cần mở Jupyter: `PHOBERT_SEED=42 jupyter nbconvert --to notebook --execute --inplace notebooks/02_phobert_colab.ipynb` |
| 6. Đánh giá | `python -m src.evaluate` (cần `results/error_groups.csv` để có nhóm lỗi) |
| Demo | `python -m src.predict "máy giặt chạy êm nhưng vắt không khô"` |
| EDA | `notebooks/01_eda.ipynb` (`jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb`) |
| 7. Hình cho báo cáo | `python reports/make_figures.py` (chỉ đọc kết quả đã có → `results/figures/report_*.png`, `results/metrics/crawl_stats.json`) |
| 7. Dựng báo cáo | `python reports/build_docx.py` → `reports/BAO_CAO.docx` (nguồn `reports/BAO_CAO.md`; kiểu chữ theo `reports/template/reference.docx`, không cần cài Word) |

Ghi chú:
- Các lô LLM (`data/gold/llm_batches/`, `data/pool_llm/batches/`) đã xóa sau khi gộp và đối chiếu từng dòng; `gold_llm.csv` và `pool_llm.csv` là bản gốc, vì LLM không sinh lại được y hệt.
- Mọi bước dùng `random_state=42`. Mô hình lưu ở `models/` (không commit).

## Cấu trúc thư mục
```
btl-dmx/
├── CLAUDE.md, STATUS.md, PHAN_TICH_DE.md, README.md, requirements.txt
├── .claude/        agents/gold-labeler.md, agents/slide-reviewer.md, skills/dmx-crawler/
├── data/
│   ├── raw/        reviews.jsonl, html_cache/                     (không commit)
│   ├── interim/    reviews_clean.csv, reviews_prep.csv
│   ├── gold/       gold_to_label.csv, gold_llm.csv, review_needed.csv, g100_member2.csv, gold_test.csv
│   ├── pool_llm/   pool_llm.csv (nhãn chữ train/val), id_map.csv
│   └── processed/  train.csv, val.csv, test.csv
├── docs/           HUONG_DAN_GAN_NHAN.md, KE_HOACH_NHAN_CHU.md
├── resources/      stopwords_vi.txt, keep_words.txt, teencode.txt
├── src/
│   ├── crawl/      sitemap.py, selectors.py, reviews.py
│   ├── config.py, clean_label.py, gold_llm.py, preprocess.py, split.py, pool_llm.py
│   ├── features.py, train_classic.py, evaluate.py, predict.py
├── notebooks/      01_eda.ipynb, 02_phobert_colab.ipynb
├── models/         *.joblib, phobert_best/, vncorenlp/                (không commit)
├── results/        comparison.csv, robustness.csv, errors.csv, error_groups.csv, label_noise*.csv,
│                   metrics/*.json, predictions/*.csv, figures/*.png, archive_star/ (thí nghiệm A)
├── slides/         slide môn học                                      (không commit)
└── reports/        BAO_CAO.md (nguồn), BAO_CAO.docx (nộp), build_docx.py, make_figures.py,
                    template/reference.docx (tự sinh; thay bằng mẫu PTIT khi có)
```

## Dữ liệu cá nhân
Không lưu tên, số điện thoại, avatar người review. `review_id = sha1(product_id + date + text)[:16]`. Không commit `data/raw/`.
