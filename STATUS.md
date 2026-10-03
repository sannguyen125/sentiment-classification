# STATUS — BTL phân loại cảm xúc review ĐMX

_Cập nhật: 03/10/2026. Mọi số liệu lấy từ `results/` (số của thí nghiệm A nằm ở `results/archive_star/`)._

## 1. Hiện tại: thí nghiệm B, gán lại nhãn train/val theo nội dung chữ
Đang làm dở **bước 4 (gán nhãn)** trong `docs/KE_HOACH_NHAN_CHU.md`; dừng lại vì hết lượt dùng, chưa đến checkpoint.

| Bước | Trạng thái |
|---|---|
| 0. Commit + tag `v1-star-labels` (thí nghiệm A), push GitHub | xong |
| 1. Lưu trữ kết quả A vào `results/archive_star/` (kèm notebook `02_phobert_colab_star.ipynb`, `README.md`) | xong |
| 2. Teencode: bỏ `kh`, thêm `nhg → nhưng`; chạy lại Phase 3 (21 review đổi `text_clean`/`text_seg`) | xong |
| 3. `split.py` (giữ đúng thành viên các tập như v1) loại **16 review** train/val có `text_clean` trùng test (14 train, 2 val; khớp với 11 câu test). Train **5.120**, val **904**, test 500. Hiện `data/processed/` đang ở chế độ `--labels star` | xong |
| 4. Gán nhãn chữ bằng `gold-labeler` (nguyên văn hướng dẫn, chỉ `id,text`): **120/121 lô xong = 6.000/6.024 review**; **còn lô 121 (24 review)** | đang làm |
| 4b. `data/pool_llm/train100_member.csv`: 100 review train cho thành viên gán độc lập | chờ thành viên điền |
| Checkpoint: phân bố nhãn mới, tỷ lệ `label_text ≠ label_star` theo từng mức sao | chưa |
| 5–8. Chạy lại Phase 4–6 (B), A′, bảng so sánh A/A′/B, gán lại nhóm lỗi, hạn chế | chưa |

**File để chạy tiếp:** `data/pool_llm/batches/batch_XXX.csv` (đầu vào) và `batch_XXX_out.csv` (kết quả), cùng `data/pool_llm/id_map.csv` (P0001 → review_id).
**Lệnh chạy tiếp:**
1. `python -m src.pool_llm todo` để liệt kê các lô còn thiếu.
2. Chạy `gold-labeler` cho lô 121.
3. `python -m src.pool_llm merge` (ra `pool_llm.csv`, `results/label_noise_pool.csv`, `pool_llm_stats.json`), rồi **CHECKPOINT**.

## 2. Các phase
| Phase | Trạng thái | Đầu ra chính |
|---|---|---|
| 0–2 Khởi tạo, thu thập, làm sạch + gold | xong | `data/interim/reviews_clean.csv`, `data/gold/gold_test.csv`, `docs/HUONG_DAN_GAN_NHAN.md` |
| 3 Tiền xử lý | xong (chạy lại với teencode mới) | `data/interim/reviews_prep.csv` |
| 4–6 với nhãn sao (A) | xong, đã lưu trữ | `results/archive_star/` |
| 4–6 với nhãn chữ (B, kết quả chính) | chưa | `results/` |
| 7 Báo cáo | chưa | `reports/BAO_CAO.md` + `slide-reviewer` |

## 3. Quyết định đã chốt khác kế hoạch ban đầu
- Crawl giới hạn theo sao (lấy hết 1–3★, 4★ ≤ 60, 5★ ≤ 100, ≤ 300/sản phẩm); có lưu phân bố sao thật.
- Chọn sản phẩm theo "Đã bán" + nhóm điểm thấp nhất mỗi ngành, vì chỉ 5/~2.370 sản phẩm có điểm < 4.5.
- Giữ 6.540 review sạch, không crawl thêm.
- Gold 500, ≤ 15 review/sản phẩm; nhãn gold do LLM gán, người duyệt (chấp nhận hàng loạt 189/191 dòng gắn cờ).
- Mô hình chính dùng `text_clean`; biến thể không bỏ stopword chỉ báo trên test để tham khảo.
- PhoBERT chạy trên máy (RTX 3060, batch 16, fp16), RDRSegmenter; notebook vẫn chạy được trên Colab. Seed 42 dùng cho test; seed 43/44 để đo dao động.
- **(02/10) Train/val đổi sang nhãn theo nội dung chữ (B = kết quả chính)**; giữ `label_star` song song; kết quả nhãn sao (A) lưu trữ, không xóa.
- **(02/10) Không sửa `docs/HUONG_DAN_GAN_NHAN.md`** trong suốt quá trình (tránh tinh chỉnh bằng test).
- **(02/10) Sửa teencode** (bỏ `kh` đa nghĩa, thêm `nhg`); **loại khỏi train/val các review trùng `text_clean` với test**.
- **(02/10) Làm thêm A′** (nhãn sao + tiền xử lý mới, cho TF-IDF+NB và PhoBERT seed 42), để so sánh A′ với B chỉ khác nhãn.
- **(02/10) Làm 4b**: 1 thành viên gán 100 review train để đo kappa trên nhãn train.

## 4. Số liệu chính (thí nghiệm A, nhãn sao, `results/archive_star/`)
- Thô 9.481 → sạch 6.540 (19 ngành, 72 sản phẩm) → gold 500 + pool 6.040.
- Test 500 (gold): Neg 57,8% · Pos 32,8% · Neu 9,4% (47 mẫu). Kappa LLM vs thành viên 2 = **0,80**. Nhãn sao khác nhãn gold 31,2% (3★: 83,3%).
- Test macro-F1 (A): TF-IDF+NB **0,633**, PhoBERT 0,632, TF-IDF+SVM 0,626, W2V+NB 0,583, BoW+SVM 0,581, W2V+SVM 0,571, BoW+NB 0,568, baseline 0,165.
- Val macro-F1 (A): PhoBERT 0,781 (3 seed: 0,7778 ± 0,0044), TF-IDF+NB 0,738.

## 5. Vấn đề mở / cần ghi trong báo cáo
- Kết quả A tụt từ val sang test vì train học nhãn sao, còn test chấm theo nhãn chữ; đây là lý do làm thí nghiệm B.
- **Hạn chế:** nhãn train, val và test đều do cùng một LLM gán, nên điểm có thể cao hơn thực tế. Kiểm chứng bằng kappa 0,80 với người trên 100 câu gold, cộng kappa trên 100 câu train (4b). **[Ngoài slide]**
- Ba ghi chú bắt buộc: phân bố nhãn test khác train/val (`label_transition.csv`); Neutral test chỉ 47 mẫu; pool 6.040 < mục tiêu 8–10k.
- Cả 71 sản phẩm của test đều có review trong train.
- Câu demo "máy giặt chạy êm nhưng vắt không khô": cả hai mô hình (A) đều đoán Positive.
- `models/` hiện vẫn là mô hình của A; sẽ bị ghi đè khi chạy B.
