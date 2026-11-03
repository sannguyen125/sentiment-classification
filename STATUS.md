# STATUS — BTL phân loại cảm xúc review ĐMX

_Cập nhật: 04/11/2026. Mọi số liệu lấy từ `results/` (thí nghiệm A ở `results/archive_star/`). Làm tròn: half-up theo giá trị ghi trong file (0.7905 → 0,791; 0.7505 → 0,751)._

## 1. Trạng thái
**Phase 0–6 xong. Phase 7: xong bản nháp 1 (04/11/2026), chờ người dùng điền `[...]` và gửi mẫu báo cáo PTIT.**
Kết quả cuối = **thí nghiệm B**: train/val gán nhãn theo nội dung chữ (LLM, cùng hướng dẫn với gold), test = 500 review gold.

| Phase | Trạng thái | Đầu ra chính |
|---|---|---|
| 0–2 Khởi tạo, thu thập, làm sạch, gold | xong | `data/interim/reviews_clean.csv`, `data/gold/gold_test.csv`, `docs/HUONG_DAN_GAN_NHAN.md`, `results/metrics/clean_stats.json`, `gold_agreement.json` |
| EDA | xong (03/11) | `notebooks/01_eda.ipynb`, `results/figures/eda_*.png` |
| 3 Tiền xử lý | xong (teencode mới: bỏ `kh`, thêm `nhg`) | `data/interim/reviews_prep.csv` |
| Nhãn chữ train/val | xong | `data/pool_llm/pool_llm.csv`, `results/label_noise_pool.csv`, `pool_llm_stats.json` |
| 4 Chia tập, NB + SVM (B) | xong | `data/processed/`, `results/val_comparison.csv`, `metrics/val_classic.json` |
| 5 PhoBERT (B, seed 42/43/44, chạy trên máy) | xong | `results/metrics/phobert*.json`, `results/predictions/phobert*.csv` |
| 6 Đánh giá (B) + robustness + nhóm lỗi | xong | `results/comparison.csv`, `robustness.csv`, `errors.csv`, `error_groups.csv`, `metrics/test_metrics.json`, `figures/` |
| 4–6 với nhãn sao (A, đối chứng) | xong, lưu trữ | `results/archive_star/` (tag `v1-star-labels`) |
| 7 Báo cáo | **bản nháp 1 xong** (04/11), đã rà soát bằng `slide-reviewer` | `reports/BAO_CAO.docx` (nộp), `reports/BAO_CAO.md` (nguồn), `reports/build_docx.py`, `reports/make_figures.py`, `results/figures/report_*.png`, `results/metrics/crawl_stats.json` |

**Lệnh chạy lại toàn bộ:** xem `README.md` (crawl → clean_label → gold_llm → preprocess → split --labels star → pool_llm → split --labels text → train_classic → notebook PhoBERT → evaluate → predict; EDA).

## 1b. Phase 7: báo cáo (bản nháp 1)
- Dựng: `python reports/make_figures.py` (hình `report_*.png`, chỉ đọc kết quả đã có) → `python reports/build_docx.py` → `reports/BAO_CAO.docx`. Sửa nội dung ở `BAO_CAO.md` rồi dựng lại, không sửa tay docx. Khi mở docx bằng Word: chấp nhận cập nhật trường (mục lục có số trang).
- Bố cục theo `docs/YEU_CAU_BAO_CAO.md`: bìa, mục lục, 1. Giới thiệu, 2. Cơ sở lý thuyết, 3. Thực nghiệm và kết quả (3.1–3.8), Tài liệu tham khảo (15 mục). 9 bảng, 5 hình. Không ghi link GitHub (theo yêu cầu người dùng).
- Độ dài (Word xuất PDF): tổng 25 trang; nội dung 20 trang (mục 1 ≈ 1,5; mục 2 ≈ 5; mục 3 ≈ 12,5), tài liệu tham khảo 2 trang.
- Đối chiếu số liệu: `reports/_so_lieu.md` (nháp, không commit) liệt kê mọi con số kèm nguồn; mọi số trong báo cáo và mọi ô của Bảng 3.1, 3.2, 3.5–3.9 đã so khớp với `results/`.
- **Người dùng cần điền `[...]` trên bìa:** giảng viên hướng dẫn; nhóm; lớp; mã sinh viên của Nguyễn Văn Ngọc San; họ tên và mã sinh viên các thành viên còn lại (đang để 2 dòng, thêm/bớt theo số thành viên). Tài liệu [1] đang ghi TS. Nguyễn Thị Mai Trang (tên trên slide), chưa có năm.
- **Việc chờ:** mẫu báo cáo PTIT → đặt vào `reports/template/` (dạng `reference.docx` cho pandoc: chỉ style được dùng) rồi chạy lại `build_docx.py`. `reports/template/reference.docx` hiện là bản tự sinh (có dấu `auto-generated` trong thuộc tính comments); file người dùng đặt vào sẽ được dùng nguyên.
- Báo cáo nói phân nhóm lỗi "do một mô hình ngôn ngữ lớn đề xuất, chỉ làm một lượt" (đúng thực tế: Claude gán). Nếu thành viên tự duyệt lại `results/error_groups.csv` thì sửa câu ở 3.7 và hạn chế ở 3.8.

## 2. Kết quả B (`results/comparison.csv`, `results/robustness.csv`)
Val chấm bằng nhãn chữ, test chấm bằng nhãn gold. CI 95% = bootstrap 2.000 lần trên 500 câu test (seed 42, cùng mẫu cho mọi mô hình). "So với người" = chấm trên 100 câu G001–G100 bằng nhãn thành viên 2.

| Mô hình | Val macro-F1 | Test macro-F1 [CI 95%] | Test acc | F1 Neutral | Người: acc / macro-F1 |
|---|---|---|---|---|---|
| **PhoBERT** (seed 42, epoch 2) | 0,875 | **0,902** [0,864; 0,935] | 0,948 | 0,771 | 0,89 / 0,850 |
| **TF-IDF + SVM** (cổ điển tốt nhất theo val) | 0,791 | **0,804** [0,751; 0,853] | 0,890 | 0,590 | 0,80 / 0,705 |
| TF-IDF + NB | 0,776 | 0,799 [0,751; 0,846] | 0,878 | 0,571 | 0,86 / 0,770 |
| BoW + SVM | 0,786 | 0,760 [0,708; 0,809] | 0,862 | 0,500 | 0,76 / 0,631 |
| W2V + SVM | 0,735 | 0,718 [0,672; 0,763] | 0,812 | 0,425 | 0,75 / 0,655 |
| BoW + NB | 0,756 | 0,711 [0,657; 0,761] | 0,852 | 0,366 | 0,80 / 0,642 |
| W2V + NB | 0,665 | 0,623 [0,579; 0,668] | 0,720 | 0,301 | 0,71 / 0,644 |
| Baseline (lớp đông nhất) | 0,236 | 0,165 [0,149; 0,179] | 0,328 | 0 | 0,31 / 0,158 |
| *TF-IDF + SVM, không bỏ stopword [tham khảo]* | 0,793 | 0,812 [0,760; 0,859] | 0,888 | 0,625 | 0,79 / 0,679 |
| *Mốc: nhãn gold (LLM) vs thành viên 2* | | | | | 0,88 / 0,818 |

- PhoBERT 3 seed trên val: 0,8807 ± 0,0151 (`phobert_seeds.json`); seed 42 chọn epoch 2, seed 43/44 chọn epoch 4.
- Thí nghiệm stopword (Ch.2 §2.3) trên cấu hình tốt nhất TF-IDF+SVM: val 0,7905 (bỏ) vs 0,7931 (không bỏ), gần như bằng nhau.
- Robustness: số tự tính của người dùng khớp phần chấm theo người; CI bootstrap lệch ≤ 0,002 ở cận (do cách sinh số ngẫu nhiên).
- So với người, PhoBERT (0,850) cao hơn cả mốc gold-LLM (0,818); khoảng cách PhoBERT – cổ điển vẫn còn khi chấm bằng nhãn người. Trong nhóm cổ điển, TF-IDF+NB (0,770) vượt TF-IDF+SVM (0,705) khi chấm bằng người.
- Nhóm lỗi (30 mẫu sai, 15 TF-IDF+SVM + 15 PhoBERT, **do Claude gán**, `results/error_groups.csv`): khen chê lẫn lộn 14 (7 + 7), phủ định 4 (đều TF-IDF+SVM), câu cụt/viết tắt 3, chê/báo lỗi bị đoán Positive 3, mỗi nhóm còn lại 1 (câu hỏi thông tin, chê bị đoán Neutral, chưa dùng, câu hỏi vì sự cố, phàn nàn dịch vụ, nhãn gold tranh cãi).
- Demo "máy giặt chạy êm nhưng vắt không khô": TF-IDF+SVM → Positive, PhoBERT → Negative (0,62). Bỏ chữ "giặt": PhoBERT → Neutral (0,68), ví dụ cho nhóm lỗi khen chê lẫn lộn.

## 3. So sánh A (nhãn sao) và B (nhãn chữ), test macro-F1
| Mô hình | A (val / test) | B (val / test) |
|---|---|---|
| PhoBERT | 0,781 / 0,632 | 0,875 / 0,902 |
| TF-IDF + NB | 0,738 / 0,633 | 0,776 / 0,799 |
| TF-IDF + SVM | 0,723 / 0,626 | 0,791 / 0,804 |
| BoW + SVM | 0,708 / 0,581 | 0,786 / 0,760 |
| W2V + SVM | 0,717 / 0,571 | 0,735 / 0,718 |

A tụt mạnh từ val sang test vì train học nhãn sao, test chấm theo nhãn chữ; B hết tụt. **Không chạy A′ nên chưa tách được phần do nhãn** (xem hạn chế).

## 4. Số liệu dữ liệu
- Thô 9.481 → sạch 6.540 (19 ngành, 72 sản phẩm) → gold 500 + pool 6.040 → loại 16 câu trùng test (14 train, 2 val) → train **5.120**, val **904**, test 500.
- Nhãn chữ train: Pos 2.696 · Neg 2.024 · Neu 400; val: Pos 496 · Neg 343 · Neu 65. Test (gold): Neg 289 · Pos 164 · Neu 47.
- Nhãn chữ khác nhãn sao (train+val) 20,9%; 3★ 81,7%, 4★ 29,4% (`label_noise_pool.csv`). Trên test: nhãn sao khác gold 31,2%, 3★ 83,3% (`label_noise.csv`).
- Gold: 191 dòng gắn cờ, 2 dòng người duyệt từng dòng, 189 chấp nhận nhãn LLM hàng loạt; kappa LLM vs thành viên 2 = **0,7975** (G001–G100).

## 5. Hạn chế phải ghi trong báo cáo
1. **Cùng một LLM gán nhãn train, val và test** → điểm có thể cao hơn thực tế (mô hình học "khẩu vị" của LLM). Đối trọng: kappa 0,80 LLM vs người; bảng chấm mô hình bằng nhãn người (`robustness.csv`): PhoBERT vẫn đứng đầu và TF-IDF vẫn là nhóm cổ điển tốt nhất, nhưng thứ tự trong nhóm cổ điển thay đổi (TF-IDF+NB 0,770 > TF-IDF+SVM 0,705; chỉ 100 câu). **[Ngoài slide]**
2. **B khác A ở 3 chỗ**: nhãn train/val, teencode mới, 16 câu trùng test bị loại. Không chạy A′ nên chưa tách riêng được tác động của nhãn.
3. Neutral test chỉ 47 câu (CI rộng, F1 Neutral dao động mạnh); phân bố nhãn test khác train/val (gold lấy mẫu phân tầng theo sao); pool 6.040 < mục tiêu 8–10k; cả 71/71 sản phẩm của test đều có review trong train.
4. **Thí nghiệm B được đề xuất sau khi thấy kết quả A trên test.** Giảm rủi ro: giữ nguyên văn `docs/HUONG_DAN_GAN_NHAN.md`, không gán lại test, không dùng test chọn mô hình/tham số.
5. Gold: chỉ 2/191 dòng gắn cờ được người duyệt từng dòng (189 chấp nhận hàng loạt); dòng LLM trùng nhãn sao không được duyệt → tỷ lệ nhiễu nhãn sao là cận dưới.
6. Nhóm lỗi do Claude gán (một người gán, không đo đồng thuận).

**Điểm tốt nên ghi:** bỏ gần trùng (cosine TF-IDF > 0,9, Ch.5) chạy trên toàn bộ dữ liệu **trước** khi lấy mẫu gold, nên không có rò rỉ câu gần trùng giữa test và train; thêm bước loại câu train/val trùng `text_clean` với test.

## 6. Quyết định đã chốt
- Crawl giới hạn theo sao (lấy hết 1–3★, 4★ ≤ 60, 5★ ≤ 100, ≤ 300/sản phẩm); có lưu phân bố sao thật. Chọn sản phẩm theo "Đã bán" + nhóm điểm thấp nhất mỗi ngành. Giữ 6.540 review sạch, không crawl thêm.
- Gold 500, ≤ 15 review/sản phẩm; nhãn gold do LLM gán, người duyệt.
- Mô hình chính dùng `text_clean`; biến thể không bỏ stopword chỉ báo trên test để tham khảo.
- PhoBERT chạy trên máy (RTX 3060, batch 16, fp16), RDRSegmenter; notebook vẫn chạy được trên Colab. Seed 42 dùng cho test; seed 43/44 đo dao động. Checkpoint seed 43/44 đã xóa (dự đoán val còn trong `results/predictions/`).
- (02/10) Train/val đổi sang nhãn chữ; (03/11) **chốt B là kết quả cuối**. Nhãn sao chỉ còn là đối chứng A.
- Không sửa `docs/HUONG_DAN_GAN_NHAN.md` trong suốt quá trình.
- **(03/11) Bỏ, không làm:** A′ (bước 5b), bảng A/A′/B (bước 6), gán tay 100 câu train (bước 4b; file `train100_member.csv` trống đã xóa ngày 03/11, bỏ lệnh `pool_llm agree`).
- (03/11) EDA không làm K-means và word cloud.
- (03/11) Đã xóa `data/pool_llm/batches/` (sau khi đối chiếu `pool_llm.csv` khớp từng dòng) và `PROMPT.md`.
