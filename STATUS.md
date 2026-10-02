# STATUS — BTL phân loại cảm xúc review ĐMX

_Cập nhật: 02/10/2026. Mọi số liệu lấy từ `results/`._

## 1. Hiện tại
- **Đã xong Phase 6** (checkpoint), chưa bắt đầu Phase 7.
- **Việc tiếp theo (chờ người dùng chốt):** thí nghiệm B, gán lại nhãn train/val theo nội dung chữ bằng subagent `gold-labeler`, dùng **nguyên văn** `docs/HUONG_DAN_GAN_NHAN.md`; 1 thành viên gán độc lập 100 review train để đo kappa; chạy lại Phase 4–6 với **cùng các review trong train/val/test**, so sánh A (nhãn sao) với B (nhãn theo chữ).
- Trạng thái này (nhãn sao cho train/val) đã được commit, gắn tag git `v1-star-labels`.

## 2. Các phase
| Phase | Trạng thái | Đầu ra chính |
|---|---|---|
| 0 Khởi tạo | xong | cây thư mục, `requirements.txt`, `README.md` |
| 1 Thu thập | xong | `data/raw/reviews.jsonl`, `product_stats.jsonl` (không commit) |
| 2 Làm sạch + gold | xong | `data/interim/reviews_clean.csv`, `data/gold/gold_test.csv`, `docs/HUONG_DAN_GAN_NHAN.md` |
| 3 Tiền xử lý | xong | `data/interim/reviews_prep.csv` (`text_clean`, `text_seg`, `text_nostop`) |
| 4 Chia tập + NB/SVM | xong | `data/processed/{train,val,test}.csv`, `results/val_comparison.csv` |
| 5 PhoBERT | xong | `notebooks/02_phobert_colab.ipynb`, `results/metrics/phobert*.json` |
| 6 Đánh giá | xong | `results/comparison.csv`, `figures/`, `label_noise.csv`, `errors.csv` |
| 7 Báo cáo | chưa | `reports/BAO_CAO.md` + rà soát bằng `slide-reviewer` |

## 3. Quyết định khác kế hoạch ban đầu
- Crawl giới hạn theo sao (lấy hết 1–3★, 4★ ≤ 60, 5★ ≤ 100, ≤ 300/sản phẩm): dồn công vào review sao thấp; có lưu phân bố sao thật.
- Chọn sản phẩm theo "Đã bán" + nhóm điểm thấp nhất mỗi ngành: điểm trên trang tính cả người mua không đánh giá, chỉ 5/~2.370 sản phẩm < 4.5.
- Giữ 6.540 review sạch, không crawl thêm (lựa chọn a): Neg/Neu đã vượt mục tiêu.
- Gold 500 lấy mẫu lại, ≤ 15 review/sản phẩm: tránh 1 sản phẩm chiếm 41 dòng.
- Nhãn gold do LLM (subagent `gold-labeler`) gán, người duyệt: nhóm chấp nhận nhãn LLM hàng loạt cho 189/191 dòng gắn cờ.
- Teencode chỉ gồm từ không đa nghĩa; giữ thứ tự "chữ thường rồi mới tách từ": thử cả hai cách, không cách nào tốt hơn rõ.
- Mô hình chính dùng `text_clean`; biến thể không bỏ stopword chỉ báo trên test để tham khảo.
- PhoBERT chạy trên máy (RTX 3060, batch 16, fp16), RDRSegmenter tải bằng curl; notebook vẫn chạy được trên Colab.
- PhoBERT chạy thêm seed 43/44 để đo dao động; mô hình dùng cho test là seed 42, epoch 3.

## 4. Số liệu chính
- Thô 9.481 → sạch 6.540 (19 ngành, 72 sản phẩm) → gold 500 + pool 6.040.
- Train 5.134 / val 906 (nhãn sao): Pos 60,0% · Neg 24,8% · Neu 15,2%.
- Test 500 (nhãn gold): Neg 57,8% · Pos 32,8% · Neu 9,4% (Neutral = 47 mẫu).
- Gold: kappa LLM vs thành viên 2 = **0,80** (trùng 88/100); nhãn sao khác nhãn gold 31,2% (3★: 83,3%).

| Mô hình | Val macro-F1 | Test macro-F1 | Test acc |
|---|---|---|---|
| Baseline (lớp đông nhất) | 0,250 | 0,165 | 0,328 |
| BoW + NB / SVM | 0,731 / 0,708 | 0,568 / 0,581 | 0,654 / 0,682 |
| TF-IDF + NB / SVM | **0,738** / 0,723 | **0,633** / 0,626 | **0,742** / 0,734 |
| W2V + NB / SVM | 0,656 / 0,717 | 0,583 / 0,571 | 0,646 / 0,616 |
| PhoBERT (seed 42) | **0,781** | 0,632 | 0,714 |
| TF-IDF + NB không bỏ stopword (tham khảo) | 0,749 | 0,639 | 0,714 |

PhoBERT 3 seed: val macro-F1 0,7778 ± 0,0044.

## 5. Vấn đề mở / cần ghi trong báo cáo
- Val→test tụt 0,10–0,15: train/val học theo nhãn sao, test chấm theo nhãn chữ (review 3★ phần lớn là chê). F1 Neutral trên test khoảng 0,25.
- Nhãn test do LLM quyết 500/500; người chỉ kiểm chứng qua kappa. Nhiễu nhãn sao đo được là cận dưới. **[Ngoài slide]**
- Ba ghi chú bắt buộc: phân bố nhãn test khác train/val (kèm `label_transition.csv`); Neutral test chỉ 47 mẫu; pool 6.040 < mục tiêu 8–10k.
- Cả 71 sản phẩm của test đều có review trong train: kết quả là dự đoán trên sản phẩm đã gặp. Có 11 review test trùng `text_clean` với pool (câu chung chung). Không phát hiện rò rỉ.
- Teencode: thiếu `nhg`, `kh` bị hiểu sai thành "không" (người dùng sẽ tự sửa sau, khi đó phải chạy lại Phase 3–6).
- Câu demo của đề "máy giặt chạy êm nhưng vắt không khô": cả hai mô hình đều đoán Positive (lỗi khen chê lẫn lộn).
- Nhóm lỗi trong `errors.csv` do Claude gán (`results/error_groups.csv`).
