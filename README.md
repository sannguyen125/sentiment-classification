# BTL: Phân loại cảm xúc review Điện Máy Xanh

Môn **Phân tích và khai phá dữ liệu văn bản** (PTIT). Phân loại review sản phẩm trên dienmayxanh.com thành 3 nhãn **Positive / Neutral / Negative**.

Đề và kế hoạch chi tiết: [`PHAN_TICH_DE.md`](PHAN_TICH_DE.md). Quy ước làm bài: [`CLAUDE.md`](CLAUDE.md).

## Cài đặt
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Chạy từng bước
| Phase | Lệnh |
|---|---|
| 1. Thu thập | `python -m src.crawl.sitemap` → `python -m src.crawl.reviews` |
| 2. Làm sạch, gán nhãn | `python -m src.clean_label` |
| 3. Tiền xử lý | `python -m src.preprocess` |
| 4. Chia tập, đặc trưng, NB + SVM | `python -m src.split` → `python -m src.train_classic` |
| 5. PhoBERT | `notebooks/02_phobert_colab.ipynb` (GPU) |
| 6. Đánh giá | `python -m src.evaluate` |
| Demo | `python -m src.predict "máy giặt chạy êm nhưng vắt không khô"` |

Mọi bước dùng `random_state=42`.

## Dữ liệu cá nhân
Không lưu tên, số điện thoại, avatar người review. `review_id = sha1(product_id + date + text)[:16]`. Không commit `data/raw/`.
