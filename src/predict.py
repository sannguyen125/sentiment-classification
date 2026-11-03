"""Demo: predict the sentiment of new reviews.

Run: python -m src.predict "máy giặt chạy êm nhưng vắt không khô" ["..."]
Uses the best classic model on val (read from results/metrics/val_classic.json) and, if the
checkpoint exists and torch / transformers are installed, PhoBERT (models/phobert_best,
RDRSegmenter or underthesea input).
"""
import json
import os
import sys

import joblib

from src.config import MODELS, RESULTS
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


def best_classic() -> str:
    """Name of the best classic config on val, e.g. 'TF-IDF + SVM'."""
    val = json.loads((RESULTS / "metrics" / "val_classic.json").read_text(encoding="utf-8"))
    top = max(val["best_per_config"][1:], key=lambda r: r["macro_f1"])
    return f"{top['feature']} + {top['algo']}"


def main() -> None:
    texts = sys.argv[1:] or DEFAULT
    name = best_classic()
    clf = joblib.load(MODELS / (name.replace(" + ", "_").replace("-", "") + ".joblib"))
    clean = [to_text_clean(t) for t in texts]
    cl_pred = clf.predict(clean)
    # LinearSVC has no predict_proba -> show the label only
    cl_prob = clf.predict_proba(clean).max(1) if hasattr(clf, "predict_proba") else [None] * len(texts)
    pho = phobert_predictor()
    pho_pred = pho(texts) if pho else [("-", 0.0)] * len(texts)
    for t, c, p, pr, (pl, pp) in zip(texts, clean, cl_pred, cl_prob, pho_pred):
        print(f"\nReview : {t}\ntext_clean: {c}\n  {name}: {p}" + (f" ({pr:.2f})" if pr is not None else "")
              + (f"\n  PhoBERT  : {pl} ({pp:.2f})" if pho else ""))


if __name__ == "__main__":
    main()
