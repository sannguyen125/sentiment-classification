"""Phase 4a: train / val / test split (Ch.3 "Chia tập dữ liệu").

Run: python -m src.split [--labels text|star]
Pool = clean reviews minus the gold set -> stratified 85/15 train/val on the STAR label
(seed 42; identical membership to tag v1-star-labels). Then reviews whose text_clean also
appears in the test set are dropped from train/val (exact-duplicate guard).
Train/val label: --labels text (default, main result B) = label_text from
data/pool_llm/pool_llm.csv (LLM, text-based, same guideline as gold);
--labels star (control experiment A, also needed once before `src.pool_llm prepare`) = label_star.
Test = gold set (label = final gold label `label`), label_star kept to measure label noise.
Out: data/processed/{train,val,test}.csv, results/metrics/split_stats.json
"""
import argparse
import json

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import DATA, GOLD, INTERIM, PROCESSED, RANDOM_STATE, RESULTS

VAL_SIZE = 0.15
POOL_LLM = DATA / "pool_llm" / "pool_llm.csv"
COLS = ["review_id", "product_id", "category", "star", "label_star", "label_text", "label",
        "text", "text_clean", "text_seg", "text_nostop"]


def split_pool(df: pd.DataFrame, gold: pd.DataFrame):
    """Return (train, val, test, dropped) with the v1 membership minus test duplicates."""
    pool = df[~df["review_id"].isin(gold["review_id"])].copy()
    train, val = train_test_split(pool, test_size=VAL_SIZE, stratify=pool["label_star"],
                                  random_state=RANDOM_STATE)
    test = df.merge(gold[["review_id", "label", "label_source"]], on="review_id", validate="1:1")
    test_texts = set(test["text_clean"].fillna(""))
    dup = lambda d: d["text_clean"].fillna("").isin(test_texts)
    dropped = pd.concat([train[dup(train)].assign(split="train"), val[dup(val)].assign(split="val")])
    return train[~dup(train)], val[~dup(val)], test, dropped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", choices=["text", "star"], default="text")
    args = ap.parse_args()

    clean = pd.read_csv(INTERIM / "reviews_clean.csv")
    prep = pd.read_csv(INTERIM / "reviews_prep.csv").drop(columns="text")
    gold = pd.read_csv(GOLD / "gold_test.csv")
    df = clean.merge(prep, on="review_id", validate="1:1")
    if POOL_LLM.exists():
        lab = pd.read_csv(POOL_LLM, encoding="utf-8-sig")[["review_id", "label_text"]]
        df = df.merge(lab, on="review_id", how="left")
    else:
        df["label_text"] = pd.NA
        if args.labels == "text":
            raise SystemExit(f"{POOL_LLM} not found: run src.pool_llm first or use --labels star")

    train, val, test, dropped = split_pool(df, gold)
    for d in (train, val):
        if args.labels == "text" and d["label_text"].isna().any():
            raise SystemExit(f"{d['label_text'].isna().sum()} train/val reviews have no label_text")
        d["label"] = d["label_text"] if args.labels == "text" else d["label_star"]
    assert len(test) == len(gold) and not set(test["review_id"]) & (set(train["review_id"]) | set(val["review_id"]))

    PROCESSED.mkdir(parents=True, exist_ok=True)
    train[COLS].to_csv(PROCESSED / "train.csv", index=False, encoding="utf-8")
    val[COLS].to_csv(PROCESSED / "val.csv", index=False, encoding="utf-8")
    test[COLS + ["label_source"]].to_csv(PROCESSED / "test.csv", index=False, encoding="utf-8")

    stats = {name: {"n": len(d), "label": d["label"].value_counts().to_dict(),
                    "label_pct": (d["label"].value_counts(normalize=True) * 100).round(1).to_dict()}
             for name, d in [("train", train), ("val", val), ("test", test)]}
    stats["train_val_labels"] = args.labels
    stats["dropped_test_duplicates"] = {"n": len(dropped), "by_split": dropped["split"].value_counts().to_dict(),
                                        "texts": dropped["text_clean"].tolist()}
    stats["note"] = (f"train/val label = {'label_text (LLM, text-based)' if args.labels == 'text' else 'star label'}; "
                     "test label = gold label (LLM-labelled, human-checked)")
    (RESULTS / "metrics").mkdir(parents=True, exist_ok=True)
    (RESULTS / "metrics" / "split_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "dropped_test_duplicates"}, ensure_ascii=False, indent=1))
    print("dropped (text_clean duplicates of test):", len(dropped), dropped["split"].value_counts().to_dict())
    for t in dropped["text_clean"]:
        print("  -", t)


if __name__ == "__main__":
    main()
