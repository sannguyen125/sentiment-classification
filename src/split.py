"""Phase 4a: train / val / test split (Ch.3 "Chia tập dữ liệu").

Run: python -m src.split
Pool = clean reviews minus the gold set -> stratified 85/15 train/val (label = star label).
Test = gold set (label = final gold label `label`), label_star kept to measure label noise.
Out: data/processed/{train,val,test}.csv, results/metrics/split_stats.json
"""
import json

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import GOLD, INTERIM, PROCESSED, RANDOM_STATE, RESULTS

VAL_SIZE = 0.15
COLS = ["review_id", "product_id", "category", "star", "label_star", "label",
        "text", "text_clean", "text_seg", "text_nostop"]


def main() -> None:
    clean = pd.read_csv(INTERIM / "reviews_clean.csv")
    prep = pd.read_csv(INTERIM / "reviews_prep.csv").drop(columns="text")
    gold = pd.read_csv(GOLD / "gold_test.csv")
    df = clean.merge(prep, on="review_id", validate="1:1")

    pool = df[~df["review_id"].isin(gold["review_id"])].copy()
    pool["label"] = pool["label_star"]
    train, val = train_test_split(pool, test_size=VAL_SIZE, stratify=pool["label"],
                                  random_state=RANDOM_STATE)

    test = df.merge(gold[["review_id", "label", "label_source"]], on="review_id", validate="1:1")
    assert len(test) == len(gold) and not set(test["review_id"]) & set(pool["review_id"])

    PROCESSED.mkdir(parents=True, exist_ok=True)
    train[COLS].to_csv(PROCESSED / "train.csv", index=False, encoding="utf-8")
    val[COLS].to_csv(PROCESSED / "val.csv", index=False, encoding="utf-8")
    test[COLS + ["label_source"]].to_csv(PROCESSED / "test.csv", index=False, encoding="utf-8")

    stats = {name: {"n": len(d), "label": d["label"].value_counts().to_dict(),
                    "label_pct": (d["label"].value_counts(normalize=True) * 100).round(1).to_dict()}
             for name, d in [("train", train), ("val", val), ("test", test)]}
    stats["note"] = "train/val label = star label; test label = gold label (LLM-labelled, human-checked)"
    (RESULTS / "metrics").mkdir(parents=True, exist_ok=True)
    (RESULTS / "metrics" / "split_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
