# STATUS — BTL phân loại cảm xúc review ĐMX

_Cập nhật: 03/10/2026. Mọi số liệu lấy từ `results/` (số của thí nghiệm A nằm ở `results/archive_star/`)._

## 1. Hiện tại: thí nghiệm B, gán lại nhãn train/val theo nội dung chữ
**Đang ở CHECKPOINT Phase 6 (B)** trong `docs/KE_HOACH_NHAN_CHU.md`: đã chạy lại Phase 4–6 với nhãn chữ (bước 5), chờ người dùng duyệt. Chưa làm 5b (A′), 6 (bảng A/A′/B), 7 (nhóm lỗi), 8.

| Bước | Trạng thái |
|---|---|
| 0. Commit + tag `v1-star-labels` (thí nghiệm A), push GitHub | xong |
| 1. Lưu trữ kết quả A vào `results/archive_star/` (kèm notebook `02_phobert_colab_star.ipynb`, `README.md`) | xong |
| 2. Teencode: bỏ `kh`, thêm `nhg → nhưng`; chạy lại Phase 3 (21 review đổi `text_clean`/`text_seg`) | xong |
| 3. `split.py` (giữ đúng thành viên các tập như v1) loại **16 review** train/val có `text_clean` trùng test (14 train, 2 val; khớp với 11 câu test). Train **5.120**, val **904**, test 500. Hiện `data/processed/` đang ở chế độ `--labels text` (03/10) | xong |
| 4. Gán nhãn chữ bằng `gold-labeler` (nguyên văn hướng dẫn, chỉ `id,text`): **121/121 lô xong = 6.024 review**; đã chạy `python -m src.pool_llm merge` | xong (03/10) |
| 4b. `data/pool_llm/train100_member.csv`: 100 review train cho thành viên gán độc lập | chờ thành viên điền |
| Checkpoint: phân bố nhãn mới, tỷ lệ `label_text ≠ label_star` theo từng mức sao | người dùng đã duyệt (03/10) |
| 5. Chạy lại Phase 4–6 (B): split `--labels text`, `train_classic`, PhoBERT seed 42/43/44 (nbconvert trên máy), `evaluate` | xong (03/10), **CHECKPOINT** |
| 5b. A′ (nhãn sao + tiền xử lý mới; TF-IDF+NB và PhoBERT seed 42) | chưa; phải chia lại `--labels star` → cần lưu đầu ra riêng để không ghi đè B |
| 6. `results/label_source_comparison.csv` (A / A′ / B) | chưa |
| 7. Gán lại nhóm lỗi cho `errors.csv` mới (30 dòng) → `results/error_groups.csv` | chưa (hiện cột `nhom_loi` trống) |
| 8. Hạn chế, cập nhật CLAUDE.md, PHAN_TICH_DE.md | chưa |

**Kết quả B** (`results/comparison.csv`, `results/metrics/test_metrics.json`, `phobert_seeds.json`):
- Val macro-F1 (nhãn chữ): PhoBERT **0,8749** (seed 42, chọn epoch 2; 3 seed: 0,8807 ± 0,0151), TF-IDF+SVM 0,7905, BoW+SVM 0,7858, TF-IDF+NB 0,7757, BoW+NB 0,7563, W2V+SVM 0,7352, W2V+NB 0,6651, baseline 0,2362.
- Test macro-F1 (gold): PhoBERT **0,9023** (acc 0,948; F1 Neu 0,771), TF-IDF+SVM **0,8038** (cổ điển tốt nhất theo val; acc 0,890; F1 Neu 0,590), TF-IDF+NB 0,7993, BoW+SVM 0,7599, W2V+SVM 0,7177, BoW+NB 0,7114, W2V+NB 0,6230, baseline 0,1647.
- Thí nghiệm stopword (trên TF-IDF+SVM): val 0,7905 (bỏ) vs 0,7931 (không bỏ); test [tham khảo] 0,8118.
- So với A (archive): TF-IDF+NB 0,633 → 0,799; PhoBERT 0,632 → 0,902. (Chưa tách được phần do nhãn với phần do teencode/loại trùng → cần A′.)
- Trọng số lớp PhoBERT mới: Neg 0,843 · Neu 4,267 · Pos 0,633.
- Demo "máy giặt chạy êm nhưng vắt không khô": TF-IDF+SVM → Positive, PhoBERT → Negative (0,62).
- Code sửa để không gắn cứng A: `train_classic` ghi đúng loại nhãn; `evaluate` lấy mô hình stopword theo cấu hình tốt nhất trên val, nhãn biểu đồ theo `split_stats.json`; `predict` dùng cổ điển tốt nhất trên val. Đã xóa `models/TFIDF_NB_nostop.joblib` (của A).

**Kết quả checkpoint gán nhãn** (`pool_llm_stats.json`, `results/label_noise_pool.csv`):
- 6.024 review: Pos **3.192 (53,0%)** · Neg **2.367 (39,3%)** · Neu **465 (7,7%)**; nhãn sao cũ: Pos 59,9% · Neg 24,9% · Neu 15,2%.
- Train 5.120: Pos 2.696 · Neg 2.024 · Neu 400. Val 904: Pos 496 · Neg 343 · Neu 65.
- Confidence: high 5.138 · low 886.
- `label_text ≠ label_star` chung **20,9%**; theo sao: 1★ 0,8% (957) · 2★ 0,7% (542) · **3★ 81,7%** (917: Neg 677, Neu 168, Pos 72) · 4★ 29,4% (1.219: Neu 200, Neg 158) · 5★ 5,8% (2.389: Neu 93, Neg 45).

**Lệnh chạy lại B:** `python -m src.split --labels text` → `python -m src.train_classic` → notebook PhoBERT (`PHOBERT_SEED=42/43/44`, `jupyter nbconvert --execute`) → `python -m src.evaluate`.
**Việc tiếp (sau khi người dùng duyệt):** 5b A′, 6 bảng so sánh, 7 nhóm lỗi, 8.

## 2. Các phase
| Phase | Trạng thái | Đầu ra chính |
|---|---|---|
| 0–2 Khởi tạo, thu thập, làm sạch + gold | xong | `data/interim/reviews_clean.csv`, `data/gold/gold_test.csv`, `docs/HUONG_DAN_GAN_NHAN.md` |
| 3 Tiền xử lý | xong (chạy lại với teencode mới) | `data/interim/reviews_prep.csv` |
| 4–6 với nhãn sao (A) | xong, đã lưu trữ | `results/archive_star/` |
| 4–6 với nhãn chữ (B, kết quả chính) | xong (03/10), chờ duyệt; còn A′ + nhóm lỗi | `results/` |
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
- `models/` hiện là mô hình của B (03/10); mô hình A chạy lại được từ tag `v1-star-labels`.
- B: Neutral vẫn là lớp yếu nhất (test F1: PhoBERT 0,771, TF-IDF+SVM 0,590; chỉ 47 mẫu). PhoBERT seed 42 chọn epoch 2, còn seed 43/44 chọn epoch 4.
