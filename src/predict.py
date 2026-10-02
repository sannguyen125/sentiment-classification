"""Demo: predict the sentiment of new reviews.

Run: python -m src.predict "máy giặt chạy êm nhưng vắt không khô" ["..."]
Uses the best classic model on val (TF-IDF + NB) and, if the checkpoint exists and torch /
transformers are installed, PhoBERT (models/phobert_best, RDRSegmenter or underthesea input).
"""
import os
import sys

import joblib

from src.config import MODELS
from src.preprocess import to_text_clean, to_text_seg

DEFAULT = ["máy giặt chạy êm nhưng vắt không khô",
           "Tủ lạnh dùng tốt, giao hàng nhanh, nhân viên nhiệt tình",
           "Mới mua 1 tuần đã hư, gọi bảo hành mãi không ai tới",
           "Sản phẩm tạm được, không có gì nổi bật"]


def phobert_predictor():
    path = MODELS / "phobert_best"
    if not path.exists():
        return None
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        return None
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path).eval()
    seg = lambda t: to_text_seg(t)  # underthesea fallback
    vn = MODELS / "vncorenlp"
    if (vn / "VnCoreNLP-1.2.jar").exists():
        try:
            import py_vncorenlp
            cwd = os.getcwd()
            rdr = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir=str(vn.resolve()))
            os.chdir(cwd)
            seg = lambda t: " ".join(rdr.word_segment(to_text_seg(t).replace("_", " ")))
        except Exception:
            pass

    def predict(texts):
        enc = tok([seg(t) for t in texts], truncation=True, max_length=128, padding=True, return_tensors="pt")
        with torch.no_grad():
            p = torch.softmax(model(**enc).logits, -1)
        return [(model.config.id2label[int(i)], float(v)) for v, i in zip(*p.max(-1))]
    return predict


def main() -> None:
    texts = sys.argv[1:] or DEFAULT
    nb = joblib.load(MODELS / "TFIDF_NB.joblib")
    clean = [to_text_clean(t) for t in texts]
    nb_pred, nb_prob = nb.predict(clean), nb.predict_proba(clean).max(1)
    pho = phobert_predictor()
    pho_pred = pho(texts) if pho else [("-", 0.0)] * len(texts)
    for t, c, p, pr, (pl, pp) in zip(texts, clean, nb_pred, nb_prob, pho_pred):
        print(f"\nReview : {t}\ntext_clean: {c}\n  TF-IDF+NB: {p} ({pr:.2f})"
              + (f"\n  PhoBERT  : {pl} ({pp:.2f})" if pho else ""))


if __name__ == "__main__":
    main()
