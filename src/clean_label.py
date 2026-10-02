"""Phase 2: filter junk, remove (near-)duplicates, star labels, gold sample to label by hand.

Run: python -m src.clean_label
In : data/raw/reviews.jsonl
Out: data/interim/reviews_clean.csv
     data/gold/gold_to_label.csv   (500 reviews, star hidden, to be labelled by hand)
     results/metrics/clean_stats.json
"""
import json
import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import GOLD, INTERIM, RANDOM_STATE, RAW, RESULTS

MIN_WORDS = 3
NEAR_DUP = 0.9  # cosine similarity on TF-IDF (Ch.5)
STAR2LABEL = {1: "Negative", 2: "Negative", 3: "Neutral", 4: "Positive", 5: "Positive"}
# gold quota per star: ~170 Neg / 150 Neu / 180 Pos
GOLD_QUOTA = {1: 100, 2: 70, 3: 150, 4: 80, 5: 100}
GOLD_MAX_PER_PRODUCT = 15
N_DOUBLE = 100  # first rows (G001-G100) also labelled by member 2

VI_CHARS = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", re.I)
# common Vietnamese words typed without diacritics
VI_NOACCENT = set("""san pham sp tot rat may xai sai dung duoc dc hai long mua nhan vien giao lap
dat gia khong ko k chua cung on qua lam nen minh toi em anh chi noi tu quat nhe
voi cam on hoi thay moi biet ban phuc vu ho tro tuyet voi chat luong""".split())
STAFF = re.compile(r"^\s*(?:dạ\s*,?\s*)?(?:điện máy xanh|đmx|dmx)\s+(?:xin|rất|chân thành|cảm ơn)|quản trị viên", re.I)


def norm(t: str) -> str:
    t = unicodedata.normalize("NFC", str(t)).lower()
    return re.sub(r"\s+", " ", t).strip(" .,!?~-")


def is_vietnamese(t: str) -> bool:
    if VI_CHARS.search(t):
        return True
    return any(w in VI_NOACCENT for w in re.findall(r"[a-z]+", t.lower()))


def dedup_exact(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Keep one copy per identical text; if copies disagree on label, keep the majority
    label, and drop the text entirely on a tie. Returns (df, n_conflict_groups_dropped)."""
    keep, dropped = [], 0
    for _, g in df.groupby("text_norm", sort=False):
        if len(g) == 1:
            keep.append(g.index[0])
            continue
        counts = g["label_star"].value_counts()
        if len(counts) > 1 and counts.iloc[0] == counts.iloc[1]:
            dropped += 1
            continue
        keep.append(g[g["label_star"] == counts.index[0]].index[0])
    return df.loc[sorted(keep)], dropped


def dedup_near(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple]]:
    """Drop later reviews whose TF-IDF cosine with an earlier kept one is > NEAR_DUP.
    TF-IDF here only measures text similarity (no labels, no model) so fitting on the
    whole pool is not a leak."""
    vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    X = vec.fit_transform(df["text_norm"])  # rows are L2-normalised -> dot = cosine
    S = (X @ X.T).tocsr()
    removed, pairs = np.zeros(len(df), bool), []
    for i in range(len(df)):
        if removed[i]:
            continue
        row = S.getrow(i)
        for j, v in zip(row.indices, row.data):
            if j > i and v > NEAR_DUP and not removed[j]:
                removed[j] = True
                pairs.append((i, j, round(float(v), 3)))
    return df[~removed], [(df.index[i], df.index[j], v) for i, j, v in pairs]


def sample_gold(df: pd.DataFrame) -> pd.DataFrame:
    """Random pass over the shuffled pool: take a review if its star quota is not full
    and its product has < GOLD_MAX_PER_PRODUCT reviews in gold. Rejected reviews stay in pool."""
    need, per_prod, take = dict(GOLD_QUOTA), {}, []
    for idx, r in df.sample(frac=1, random_state=RANDOM_STATE).iterrows():
        if need[r["star"]] > 0 and per_prod.get(r["product_id"], 0) < GOLD_MAX_PER_PRODUCT:
            take.append(idx)
            need[r["star"]] -= 1
            per_prod[r["product_id"]] = per_prod.get(r["product_id"], 0) + 1
    assert not any(need.values()), f"quota not filled: {need}"
    gold = df.loc[take].sample(frac=1, random_state=RANDOM_STATE)  # shuffle: stars mixed
    gold = gold.reset_index(drop=True)
    gold.insert(0, "gold_id", [f"G{i + 1:03d}" for i in range(len(gold))])
    return gold


def main() -> None:
    raw = pd.read_json(RAW / "reviews.jsonl", lines=True)
    stats = {"raw": len(raw)}
    df = raw.copy()
    df["text"] = df["text"].fillna("").map(lambda t: unicodedata.normalize("NFC", t).strip())
    df["text_norm"] = df["text"].map(norm)
    df["n_words"] = df["text"].str.split().str.len()
    df["label_star"] = df["star"].map(STAR2LABEL)

    steps = [
        ("drop_empty", df["text_norm"] == ""),
        ("drop_short_lt3_words", df["n_words"] < MIN_WORDS),
        ("drop_non_vietnamese", ~df["text"].map(is_vietnamese)),
        ("drop_staff_reply", df["text"].str.contains(STAFF)),
    ]
    for name, mask in steps:
        mask = mask.reindex(df.index)
        stats[name] = int(mask.sum())
        df = df[~mask]

    n = len(df)
    df, stats["exact_dup_conflict_groups_dropped"] = dedup_exact(df)
    stats["drop_exact_dup"] = n - len(df)

    n = len(df)
    df, pairs = dedup_near(df)
    stats["drop_near_dup_cos_gt_0.9"] = n - len(df)
    diff = [(a, b, v) for a, b, v in pairs if raw.loc[a, "star"] != raw.loc[b, "star"]]
    stats["near_dup_pairs_with_different_star"] = len(diff)

    cols = ["review_id", "product_id", "category", "star", "label_star", "text", "n_words",
            "verified_purchase"]
    clean = df[cols].reset_index(drop=True)
    INTERIM.mkdir(parents=True, exist_ok=True)
    clean.to_csv(INTERIM / "reviews_clean.csv", index=False, encoding="utf-8")

    gold = sample_gold(clean)
    # master list of the gold set (no star); labelling files are made by src.gold_llm
    GOLD.mkdir(parents=True, exist_ok=True)
    gold[["gold_id", "review_id", "product_id", "category", "text"]].to_csv(
        GOLD / "gold_to_label.csv", index=False, encoding="utf-8-sig")  # Excel-friendly
    pool = clean[~clean["review_id"].isin(gold["review_id"])]

    stats.update({
        "clean": len(clean),
        "clean_by_star": {int(k): int(v) for k, v in clean["star"].value_counts().sort_index().items()},
        "clean_by_label": clean["label_star"].value_counts().to_dict(),
        "clean_by_category": clean["category"].value_counts().to_dict(),
        "n_categories": int(clean["category"].nunique()),
        "n_products": int(clean["product_id"].nunique()),
        "words_median": float(clean["n_words"].median()),
        "gold": len(gold),
        "gold_by_star": {int(k): int(v) for k, v in gold["star"].value_counts().sort_index().items()},
        "gold_by_label_star": gold["label_star"].value_counts().to_dict(),
        "gold_double_labelled": N_DOUBLE,
        "gold_max_per_product": int(gold["product_id"].value_counts().max()),
        "gold_n_products": int(gold["product_id"].nunique()),
        "gold_n_categories": int(gold["category"].nunique()),
        "pool_after_gold": len(pool),
        "pool_n_categories": int(pool["category"].nunique()),
        "pool_by_label_star": pool["label_star"].value_counts().to_dict(),
    })
    (RESULTS / "metrics").mkdir(parents=True, exist_ok=True)
    (RESULTS / "metrics" / "clean_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({k: v for k, v in stats.items() if k != "clean_by_category"},
                     ensure_ascii=False, indent=1))
    print("\nNear-duplicate examples (kept | dropped | cosine):")
    for a, b, v in pairs[:: max(1, len(pairs) // 8)][:8]:
        print(f"  {v}  {raw.loc[a, 'text'][:60]!r}\n        {raw.loc[b, 'text'][:60]!r}")


if __name__ == "__main__":
    main()
