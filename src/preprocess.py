"""Phase 3: text preprocessing (Ch.2).

Run: python -m src.preprocess
In : data/interim/reviews_clean.csv
Out: data/interim/reviews_prep.csv   (review_id, text, text_clean, text_seg, text_nostop)
     results/metrics/preprocess_stats.json, results/preprocess_examples.csv

text_clean: clean -> normalise -> lowercase -> word correction -> segment -> drop special
            chars + stopwords (keep_words kept). For BoW / TF-IDF / Word2Vec.
text_seg  : clean -> normalise -> word correction -> segment. Case, punctuation and
            stopwords kept. For PhoBERT.
No stemming/lemmatisation (Ch.2 §2.5): Vietnamese is isolating, words do not inflect.
Every step works on one text at a time (nothing is fitted), so running it on train,
val and test together leaks nothing.
"""
import json
import re
import unicodedata
from functools import lru_cache

import pandas as pd
from tqdm import tqdm
from underthesea import word_tokenize

from src.config import INTERIM, RANDOM_STATE, RESOURCES, RESULTS


# ---------- resources ----------
def _read_list(name: str) -> list[str]:
    lines = (RESOURCES / name).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


@lru_cache
def teencode() -> dict[str, str]:
    return dict(ln.split("\t") for ln in _read_list("teencode.txt"))


@lru_cache
def stopwords() -> frozenset[str]:
    return frozenset(_read_list("stopwords_vi.txt")) - keep_words()


@lru_cache
def keep_words() -> frozenset[str]:
    return frozenset(_read_list("keep_words.txt"))


@lru_cache
def teencode_re() -> re.Pattern:
    keys = sorted(teencode(), key=len, reverse=True)
    return re.compile(r"(?<!\w)(" + "|".join(map(re.escape, keys)) + r")(?!\w)", re.I)


# ---------- 1. cleaning (Ch.2 §2.1) ----------
HTML_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
PHONE_TAG = "<phone>"  # phone numbers were masked at crawl time
ODD_CHARS_RE = re.compile(r"[^\w\s.,!?;:()\-/%'\"]")  # emoji, icons, odd symbols


def clean(text: str) -> str:
    text = str(text).replace(PHONE_TAG, " ")
    text = HTML_RE.sub(" ", text)
    text = URL_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)
    text = ODD_CHARS_RE.sub(" ", text).replace("_", " ")
    text = re.sub(r"([.,!?;:])(?=[^\W\d_])", r"\1 ", text)  # "tốt.máy" -> "tốt. máy"
    return re.sub(r"\s+", " ", text).strip()


# ---------- 2. Vietnamese normalisation (Ch.2 §2) ----------
# old-style tone placement at the end of a syllable -> new style: hoà -> hòa, thuỷ -> thủy
_TONE = {"à": "ò", "á": "ó", "ả": "ỏ", "ã": "õ", "ạ": "ọ",
         "è": "ò", "é": "ó", "ẻ": "ỏ", "ẽ": "õ", "ẹ": "ọ"}
_TONE_Y = {"ỳ": "ù", "ý": "ú", "ỷ": "ủ", "ỹ": "ũ", "ỵ": "ụ"}
OA_RE = re.compile(r"o([àáảãạèéẻẽẹ])(?!\w)")
UY_RE = re.compile(r"(?<![qQ])u([ỳýỷỹỵ])(?!\w)")
REPEAT_RE = re.compile(r"([^\W\d_])\1{2,}")  # letters repeated 3+ times ("tốtttt")
PUNCT_REPEAT_RE = re.compile(r"([^\w\s])\1+")  # "!!!" -> "!"


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = OA_RE.sub(lambda m: _TONE[m.group(1)] + ("a" if m.group(1) in "àáảãạ" else "e"), text)
    text = UY_RE.sub(lambda m: _TONE_Y[m.group(1)] + "y", text)
    text = REPEAT_RE.sub(r"\1", text)
    return PUNCT_REPEAT_RE.sub(r"\1", text)


# ---------- 4. word correction (Ch.2 §2.4) ----------
def correct_words(text: str) -> str:
    tc = teencode()
    return teencode_re().sub(lambda m: tc[m.group(1).lower()], text)


# ---------- 5. word segmentation (Ch.2 §1, §2.2; Ch.1 Underthesea) ----------
def segment(text: str) -> str:
    return word_tokenize(text, format="text") if text else ""


# ---------- 6. special chars + stopwords (Ch.2 §2.3) ----------
TOKEN_CLEAN_RE = re.compile(r"[^\w]")


def drop_special_and_stopwords(seg: str, remove_stopwords: bool = True) -> str:
    out = []
    for tok in seg.split():
        tok = TOKEN_CLEAN_RE.sub("", tok).strip("_")
        if len(tok) < 2 or not re.search(r"[^\W\d_]", tok):  # punctuation, numbers, stray letters
            continue
        if remove_stopwords and tok in stopwords():
            continue
        out.append(tok)
    return " ".join(out)


# ---------- pipelines ----------
def to_text_clean(text: str, remove_stopwords: bool = True) -> str:
    t = normalize(clean(text)).lower()
    t = correct_words(t)
    return drop_special_and_stopwords(segment(t), remove_stopwords)


def to_text_seg(text: str) -> str:
    return segment(correct_words(normalize(clean(text))))


# ---------- main ----------
def main() -> None:
    df = pd.read_csv(INTERIM / "reviews_clean.csv")
    tqdm.pandas()
    print("text_clean ...")
    df["text_clean"] = df["text"].progress_map(to_text_clean)
    print("text_seg ...")
    df["text_seg"] = df["text"].progress_map(to_text_seg)
    df["text_nostop"] = df["text"].progress_map(lambda t: to_text_clean(t, remove_stopwords=False))

    empty = df["text_clean"].str.len() == 0
    # text_nostop = text_clean without stopword removal (for the Phase 4 stopword experiment)
    out = df[["review_id", "text", "text_clean", "text_seg", "text_nostop"]]
    out.to_csv(INTERIM / "reviews_prep.csv", index=False, encoding="utf-8")

    n_tok = lambda s: s.str.split().str.len()
    vocab = lambda s: len({w for t in s for w in t.split()})
    n_teen = df["text"].map(lambda t: len(teencode_re().findall(normalize(clean(t)).lower())))
    stats = {
        "n_reviews": len(df),
        "empty_text_clean": int(empty.sum()),
        "tokens_mean": {"text_seg": round(n_tok(df["text_seg"]).mean(), 2),
                        "text_nostop": round(n_tok(df["text_nostop"]).mean(), 2),
                        "text_clean": round(n_tok(df["text_clean"]).mean(), 2)},
        "vocab_size": {"text_nostop": vocab(df["text_nostop"]), "text_clean": vocab(df["text_clean"])},
        "pct_tokens_removed_as_stopwords": round(
            1 - n_tok(df["text_clean"]).sum() / n_tok(df["text_nostop"]).sum(), 4),
        "reviews_with_word_correction": int((n_teen > 0).sum()),
        "word_corrections_total": int(n_teen.sum()),
        "n_stopwords": len(stopwords()),
        "n_keep_words": len(keep_words()),
        "n_teencode_entries": len(teencode()),
        "segmented_multi_syllable_tokens_pct": round(
            df["text_clean"].str.split().explode().dropna().str.contains("_").mean(), 4),
    }
    (RESULTS / "metrics").mkdir(parents=True, exist_ok=True)
    (RESULTS / "metrics" / "preprocess_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))

    # 10 before/after examples: 6 where word correction fired, 4 random
    has_teen = df[(n_teen > 0) & df["text"].str.split().str.len().between(6, 35)]
    rest = df[~df.index.isin(has_teen.index) & df["text"].str.split().str.len().between(6, 35)]
    ex = pd.concat([has_teen.sample(6, random_state=RANDOM_STATE), rest.sample(4, random_state=RANDOM_STATE)])
    ex[["review_id", "text", "text_seg", "text_clean"]].to_csv(
        RESULTS / "preprocess_examples.csv", index=False, encoding="utf-8")
    for i, r in enumerate(ex.itertuples(), 1):
        print(f"\n[{i}] GỐC : {r.text}\n    SEG : {r.text_seg}\n    CLEAN: {r.text_clean}")


if __name__ == "__main__":
    main()
