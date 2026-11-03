"""Text-based labels for train+val (experiment B) with subagent gold-labeler. [Ngoài slide]

python -m src.pool_llm prepare  -> data/pool_llm/batches/batch_XXX.csv (id,text only),
                                   id_map.csv (id -> review_id), train100_member.csv
python -m src.pool_llm todo     -> list batches without an _out file (resume)
  (run gold-labeler on each batch -> batches/batch_XXX_out.csv, SAME guideline as gold:
   docs/HUONG_DAN_GAN_NHAN.md, unchanged; no stars shown)
python -m src.pool_llm merge    -> data/pool_llm/pool_llm.csv (review_id, label_text, ...),
                                   results/label_noise_pool.csv, results/metrics/pool_llm_stats.json
python -m src.pool_llm agree    -> kappa LLM vs member on train100_member.csv
                                   (step 4b, dropped: the file was never filled; kept for reference)
Train/val membership comes from data/processed (run `python -m src.split --labels star` first,
then `python -m src.split --labels text` after `merge`).

After `merge`, batches/ was deleted: batch inputs = id_map.csv + `text` of data/processed
train/val, and batch outputs = pool_llm.csv row for row (id, label, confidence, reason; verified),
so pool_llm.csv is the canonical copy (LLM output cannot be regenerated identically).
`prepare` / `todo` / `merge` are kept to document how the labels were made.
"""
import json
import sys

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from src.config import DATA, LABELS, PROCESSED, RANDOM_STATE, RESULTS
from src.gold_llm import norm_label

DIR = DATA / "pool_llm"
BATCH_DIR = DIR / "batches"
BATCH = 50
N_MEMBER = 100


def pool() -> pd.DataFrame:
    tr = pd.read_csv(PROCESSED / "train.csv").assign(split="train")
    va = pd.read_csv(PROCESSED / "val.csv").assign(split="val")
    return pd.concat([tr, va]).sort_values("review_id").reset_index(drop=True)


def prepare() -> None:
    p = pool()
    p["id"] = [f"P{i + 1:04d}" for i in range(len(p))]
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    p[["id", "review_id", "split"]].to_csv(DIR / "id_map.csv", index=False, encoding="utf-8")
    for i in range(0, len(p), BATCH):
        f = BATCH_DIR / f"batch_{i // BATCH + 1:03d}.csv"
        if not f.exists():
            p.iloc[i:i + BATCH][["id", "text"]].to_csv(f, index=False, encoding="utf-8")
    m = p[p["split"] == "train"].sample(N_MEMBER, random_state=RANDOM_STATE)[["id", "text"]]
    m["label_human"] = ""
    if not (DIR / "train100_member.csv").exists():
        m.to_csv(DIR / "train100_member.csv", index=False, encoding="utf-8-sig")
    print(f"{len(p)} reviews -> {(len(p) + BATCH - 1) // BATCH} batches; train100_member.csv: {len(m)} rows")


def todo() -> list[str]:
    left = [f.stem for f in sorted(BATCH_DIR.glob("batch_???.csv"))
            if not (BATCH_DIR / f"{f.stem}_out.csv").exists()]
    print(len(left), "batches left:", " ".join(left))
    return left


def merge() -> None:
    idm = pd.read_csv(DIR / "id_map.csv")
    outs = sorted(BATCH_DIR.glob("batch_???_out.csv"))
    llm = pd.concat([pd.read_csv(f, encoding="utf-8") for f in outs], ignore_index=True)
    llm["label_text"] = llm["label_llm"].map(norm_label)
    llm["confidence"] = llm["confidence"].str.strip().str.lower()
    bad = llm[llm["label_text"].isna() | ~llm["confidence"].isin(["high", "low"])]
    missing, extra = set(idm["id"]) - set(llm["id"]), set(llm["id"]) - set(idm["id"])
    if len(bad) or missing or extra or llm["id"].duplicated().any():
        sys.exit(f"merge check failed: bad={len(bad)} missing={len(missing)} extra={len(extra)} "
                 f"dup={llm['id'].duplicated().sum()}  e.g. missing {sorted(missing)[:5]}")
    out = idm.merge(llm[["id", "label_text", "confidence", "reason"]], on="id")
    out.to_csv(DIR / "pool_llm.csv", index=False, encoding="utf-8-sig")

    p = pool()[["review_id", "star", "label_star"]].merge(out, on="review_id")
    ct = pd.crosstab(p["star"], p["label_text"]).reindex(columns=LABELS, fill_value=0)
    ct["n"] = ct.sum(axis=1)
    ct["pct_label_text_differs_from_star"] = [
        round(float((p.loc[p["star"] == s, "label_text"] != p.loc[p["star"] == s, "label_star"]).mean()), 4)
        for s in ct.index]
    ct.to_csv(RESULTS / "label_noise_pool.csv", encoding="utf-8")
    stats = {"n": len(p), "label_text": p["label_text"].value_counts().to_dict(),
             "label_text_pct": (p["label_text"].value_counts(normalize=True) * 100).round(1).to_dict(),
             "label_star_pct": (p["label_star"].value_counts(normalize=True) * 100).round(1).to_dict(),
             "by_split": {s: p[p["split"] == s]["label_text"].value_counts().to_dict() for s in ("train", "val")},
             "confidence": p["confidence"].value_counts().to_dict(),
             "pct_label_text_differs_from_star": round(float((p["label_text"] != p["label_star"]).mean()), 4)}
    (RESULTS / "metrics").mkdir(parents=True, exist_ok=True)
    (RESULTS / "metrics" / "pool_llm_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2),
                                                            encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    print(ct.to_string())


def agree() -> None:
    m = pd.read_csv(DIR / "train100_member.csv", encoding="utf-8-sig", index_col=False)
    m["label_human"] = m["label_human"].map(norm_label)
    if m["label_human"].isna().any():
        sys.exit(f"{m['label_human'].isna().sum()} rows not filled yet")
    llm = pd.read_csv(DIR / "pool_llm.csv", encoding="utf-8-sig")
    d = m.merge(llm[["id", "label_text"]], on="id")
    res = {"n": len(d), "kappa_llm_vs_member_train": round(float(cohen_kappa_score(d["label_text"], d["label_human"], labels=LABELS)), 4),
           "agree": round(float((d["label_text"] == d["label_human"]).mean()), 4),
           "crosstab": pd.crosstab(d["label_text"], d["label_human"]).to_dict()}
    (RESULTS / "metrics" / "pool_agreement.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"prepare": prepare, "todo": todo, "merge": merge, "agree": agree}[sys.argv[1]]()
