# Kế hoạch: đổi nhãn train/val sang nhãn theo nội dung chữ (thí nghiệm B)

_Soạn 02/10/2026. Điểm xuất phát: commit `0cb60b0`, tag `v1-star-labels` (thí nghiệm A: train/val dùng nhãn sao)._

## Mục tiêu
Train, val và test dùng **cùng một định nghĩa nhãn** (theo nội dung chữ). Kết quả B là **kết quả chính**; A giữ làm đối chứng để đo tác động của nhiễu nhãn sao.

## Nguyên tắc chống rò rỉ (áp dụng suốt quá trình)
- **Không sửa `docs/HUONG_DAN_GAN_NHAN.md`.** Hướng dẫn đã được dùng cho gold; nếu chỉnh sau khi xem lỗi trên test thì chính là tinh chỉnh bằng test.
- LLM chỉ thấy `id` và `text`, không thấy số sao hay nhãn khác. Mỗi review được gán độc lập.
- Test (gold) giữ nguyên: không gán lại nhãn, không dùng để chọn mô hình hay tham số. Chỉ đánh giá trên test một lần, ở bước cuối.
- Mỗi tập giữ nguyên các review của nó, chỉ đổi cột nhãn (trừ các câu bị loại ở bước 3).

## Các bước

| # | Việc | Lệnh / file | Ghi chú |
|---|---|---|---|
| 0 | Commit + tag `v1-star-labels` | **đã xong** | Push lên GitHub khi người dùng đồng ý |
| 1 | Lưu trữ kết quả A vào `results/archive_star/` (chép, không xóa) | `comparison.csv`, `val_comparison.csv`, `errors.csv`, `error_groups.csv`, `metrics/` (các file của mô hình), `predictions/`, `figures/` | Giữ ở `results/`: `label_noise.csv`, `label_transition.csv`, `gold_agreement.json`, `clean_stats.json` (không phụ thuộc nhãn train) |
| 2 | Sửa teencode: bỏ `kh`, thêm `nhg → nhưng`; **chạy lại Phase 3** | `resources/teencode.txt`, `python -m src.preprocess` | `text_clean` và `text_seg` của cả 3 tập đều thay đổi |
| 3 | Loại khỏi train/val các review có `text_clean` trùng với test | `src/split.py` | Làm **sau** bước 2, vì `text_clean` mới có thể khác 11 câu đã đếm. Báo số câu bị loại |
| 4 | Gán nhãn chữ cho toàn bộ train+val bằng `gold-labeler` | `src/pool_llm.py prepare / merge` → `data/pool_llm/` | Lô 50 dòng, id dạng `P0001`, có resume (bỏ qua lô đã có file out), chạy song song khoảng 10 lô một đợt. Lưu `label_text`, `label_text_conf` cạnh `label_star` |
| 4b | (đề xuất) 1 thành viên gán độc lập 100 review train ngẫu nhiên | `data/pool_llm/train100_member.csv` | Đo kappa trên **chính nhãn train**, không chỉ trên gold |
| ✋ | **CHECKPOINT** | | Báo phân bố nhãn mới, tỷ lệ `label_text ≠ label_star` theo từng mức sao (trên khoảng 6.000 review), số câu bị loại |
| 5 | Chạy lại Phase 4–6 với nhãn chữ (**B**) | split, train_classic, notebook (3 seed), evaluate | Baseline, 6 cấu hình cổ điển, PhoBERT 42/43/44, biến thể không bỏ stopword. Trọng số lớp của PhoBERT tính lại theo phân bố mới |
| 5b | (đề xuất) Chạy lại A với **tiền xử lý mới** (A′) cho TF-IDF+NB và PhoBERT seed 42 | | Để bảng so sánh A/B chỉ khác **nhãn** (xem rủi ro R1) |
| 6 | Bảng so sánh test macro-F1: nhãn sao vs nhãn chữ, cho TF-IDF+NB và PhoBERT | `results/label_source_comparison.csv` | Cột A (archive), A′, B |
| 7 | Gán lại nhóm lỗi cho `errors.csv` mới | `results/error_groups.csv` | Các mẫu sai mới khác các mẫu cũ |
| 8 | Ghi hạn chế, cập nhật STATUS.md, CLAUDE.md, PHAN_TICH_DE.md | | Dừng trước Phase 7 |

## Rủi ro và cách xử lý
- **R1. So sánh A với B bị lẫn ba thay đổi.** B khác A ở nhãn, teencode và 11 câu bị loại. Nếu chỉ lấy số trong archive thì không biết phần tăng giảm đến từ đâu. → Bước 5b (A′) chỉ mất khoảng 1 phút cho mô hình cổ điển và 4 phút cho PhoBERT.
- **R2. Cùng một LLM gán nhãn train, val và test.** Điểm có thể cao hơn thực tế vì mô hình học "khẩu vị" của LLM. → Ghi vào hạn chế; kiểm chứng bằng kappa 0,80 trên gold, và bằng bước 4b nếu làm.
- **R3. Phân bố val lệch nhẹ so với train.** Train/val được chia phân tầng theo nhãn sao, không theo nhãn chữ. → Chấp nhận để giữ nguyên review trong từng tập; báo phân bố của cả hai tập.
- **R4. Neutral có thể còn rất ít** (khoảng 8%). → Weighted CE / `class_weight` vẫn giữ; báo F1 từng lớp.
- **R5. Chi phí.** 121 lần gọi subagent, mỗi lần khoảng 19k token (tổng khoảng 2,3 triệu), khoảng 15–25 phút.
- **R6. Ghi đè mô hình.** `models/*.joblib` và `models/phobert_best/` sẽ bị ghi đè. Số liệu A vẫn còn trong archive, và tag `v1-star-labels` cho phép chạy lại.
- **R7. Hướng dẫn gán nhãn viết cho gold** (nói đến "test"). Nội dung quy tắc vẫn dùng chung được; giữ nguyên văn.
