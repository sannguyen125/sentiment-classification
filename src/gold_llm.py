"""Gold labelling: LLM labels (subagent gold-labeler), humans review. [Ngoài slide]

python -m src.gold_llm prepare  -> llm_batches/batch_XX.csv (id,text), g100_member2.csv
  (run subagent gold-labeler on each batch -> llm_batches/batch_XX_out.csv)
python -m src.gold_llm merge    -> gold_llm.csv, review_needed.csv
  (group fills review_needed.csv[label_human] and g100_member2.csv[label_human_2])
python -m src.gold_llm final    -> gold_test.csv, results/metrics/gold_agreement.json

Stars / label_star are never written to a file the LLM or the reviewers see.
After `merge`, llm_batches/ was deleted: batch inputs = gold_to_label.csv (id,text) and
batch outputs = gold_llm.csv row for row (verified), so gold_llm.csv is the canonical copy
(LLM output cannot be regenerated identically).
"""
import json
import sys

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from src.config import GOLD, INTERIM, LABELS, RESULTS

BATCH = 50
N_DOUBLE = 100
BATCH_DIR = GOLD / "llm_batches"
ALIASES = {"pos": "Positive", "positive": "Positive", "neu": "Neutral", "neutral": "Neutral",
           "neg": "Negative", "negative": "Negative"}


def norm_label(x) -> str | None:
    if pd.isna(x) or str(x).strip() == "":
        return None
    v = ALIASES.get(str(x).strip().lower())
    if v is None:
        raise ValueError(f"invalid label: {x!r}")
    return v


def load_gold() -> pd.DataFrame:
    gold = pd.read_csv(GOLD / "gold_to_label.csv", encoding="utf-8-sig")
    clean = pd.read_csv(INTERIM / "reviews_clean.csv")
    return gold.merge(clean[["review_id", "star", "label_star"]], on="review_id", how="left")


def prepare() -> None:
    gold = load_gold()
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    inp = gold[["gold_id", "text"]].rename(columns={"gold_id": "id"})
    for i in range(0, len(inp), BATCH):
        inp.iloc[i:i + BATCH].to_csv(BATCH_DIR / f"batch_{i // BATCH + 1:02d}.csv",
                                     index=False, encoding="utf-8")
    m2 = inp.head(N_DOUBLE).copy()
    m2["label_human_2"] = ""
    m2.to_csv(GOLD / "g100_member2.csv", index=False, encoding="utf-8-sig")
    print(f"{(len(inp) + BATCH - 1) // BATCH} batches of {BATCH} -> {BATCH_DIR}")
    print(f"g100_member2.csv: {len(m2)} rows")


def merge() -> None:
    gold = load_gold()
    outs = sorted(BATCH_DIR.glob("batch_*_out.csv"))
    llm = pd.concat([pd.read_csv(f, encoding="utf-8") for f in outs], ignore_index=True)
    llm["label_llm"] = llm["label_llm"].map(norm_label)
    llm["confidence"] = llm["confidence"].str.strip().str.lower()
    bad = llm[llm["label_llm"].isna() | ~llm["confidence"].isin(["high", "low"])]
    missing = set(gold["gold_id"]) - set(llm["id"])
    extra = set(llm["id"]) - set(gold["gold_id"])
    if len(bad) or missing or extra or llm["id"].duplicated().any():
        sys.exit(f"merge check failed: bad={len(bad)} missing={sorted(missing)[:10]} "
                 f"extra={sorted(extra)[:10]} dup={llm['id'].duplicated().sum()}")
    llm = llm[["id", "label_llm", "confidence", "reason"]]
    llm.to_csv(GOLD / "gold_llm.csv", index=False, encoding="utf-8-sig")

    m = gold.merge(llm, left_on="gold_id", right_on="id")
    need = m[(m["label_llm"] != m["label_star"]) | (m["confidence"] == "low")]
    rn = need[["id", "text", "label_llm", "reason"]].copy()
    rn["label_human"] = ""
    rn.to_csv(GOLD / "review_needed.csv", index=False, encoding="utf-8-sig")
    print(f"gold_llm.csv: {len(llm)} rows | label_llm: {llm['label_llm'].value_counts().to_dict()}"
          f" | confidence: {llm['confidence'].value_counts().to_dict()}")
    print(f"review_needed.csv: {len(rn)} rows "
          f"(LLM != star label: {(need['label_llm'] != need['label_star']).sum()}, "
          f"low confidence: {(need['confidence'] == 'low').sum()})")


def final() -> None:
    gold = load_gold()
    llm = pd.read_csv(GOLD / "gold_llm.csv", encoding="utf-8-sig")
    # index_col=False: spreadsheet editors may leave a trailing comma on each row
    rn = pd.read_csv(GOLD / "review_needed.csv", encoding="utf-8-sig", index_col=False)
    m2 = pd.read_csv(GOLD / "g100_member2.csv", encoding="utf-8-sig", index_col=False)
    if "nguon_nhan" not in rn:
        rn["nguon_nhan"] = "nguoi"
    rn["label_human"] = rn["label_human"].map(norm_label)
    m2["label_human_2"] = m2["label_human_2"].map(norm_label)
    if rn["label_human"].isna().any() or m2["label_human_2"].isna().any():
        sys.exit(f"unfilled rows: review_needed={rn['label_human'].isna().sum()}, "
                 f"g100_member2={m2['label_human_2'].isna().sum()}")

    t = (gold.merge(llm, left_on="gold_id", right_on="id").drop(columns="id")
         .merge(rn[["id", "label_human", "nguon_nhan"]], left_on="gold_id", right_on="id", how="left")
         .drop(columns="id")
         .merge(m2[["id", "label_human_2"]], left_on="gold_id", right_on="id", how="left").drop(columns="id"))
    t["label"] = t["label_human"].fillna(t["label_llm"])
    # human = reviewed row by row; llm_accepted = in review_needed but LLM label accepted
    # in bulk by the group; llm = not flagged for review
    t["label_source"] = t["nguon_nhan"].map({"nguoi": "human", "llm_chap_nhan": "llm_accepted"}).fillna("llm")
    t = t.drop(columns="nguon_nhan")
    t.to_csv(GOLD / "gold_test.csv", index=False, encoding="utf-8")

    reviewed = t[t["label_source"] == "human"]
    d = t[t["label_human_2"].notna()]
    stats = {
        "n_gold": len(t),
        "n_flagged_for_review": int(t["label_human"].notna().sum()),
        "n_reviewed_row_by_row": len(reviewed),
        "n_llm_accepted_in_bulk": int((t["label_source"] == "llm_accepted").sum()),
        "n_llm_corrected": int((reviewed["label_human"] != reviewed["label_llm"]).sum()),
        "pct_llm_corrected_of_reviewed": round(float((reviewed["label_human"] != reviewed["label_llm"]).mean()), 4)
        if len(reviewed) else None,
        "label_final": t["label"].value_counts().to_dict(),
        "label_source": t["label_source"].value_counts().to_dict(),
        "g100_n": len(d),
        "kappa_llm_vs_member2": round(float(cohen_kappa_score(d["label_llm"], d["label_human_2"], labels=LABELS)), 4),
        "agree_llm_vs_member2": round(float((d["label_llm"] == d["label_human_2"]).mean()), 4),
        "kappa_final_vs_member2": round(float(cohen_kappa_score(d["label"], d["label_human_2"], labels=LABELS)), 4),
        "pct_star_label_differs_from_final": round(float((t["label_star"] != t["label"]).mean()), 4),
    }
    (RESULTS / "metrics").mkdir(parents=True, exist_ok=True)
    (RESULTS / "metrics" / "gold_agreement.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"prepare": prepare, "merge": merge, "final": final}[sys.argv[1]]()
