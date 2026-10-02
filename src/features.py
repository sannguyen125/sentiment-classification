"""Phase 4b: feature extractors (Ch.3 "Trích chọn đặc trưng").

- BoW    : CountVectorizer, ngram (1,1) or (1,2)            (Ch.3 "Túi từ")
- TF-IDF : TfidfVectorizer, ngram (1,2), min_df tuned        (Ch.3 "TF-IDF")
- W2V    : gensim Word2Vec Skip-gram 200-d trained on train, sentence vector =
           TF-IDF-weighted average of word vectors           (Ch.3 "Word2Vec",
           "Vector từ trung bình có trọng số TF-IDF")
Every extractor is fitted on train only (no leakage).
Input texts are `text_clean`: space-separated tokens, compound words joined by "_".
"""
import hashlib

import numpy as np
from gensim.models import Word2Vec
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from src.config import RANDOM_STATE

TOKEN = r"\S+"  # tokens are already segmented; keep "máy_giặt" as one token


def bow(ngram=(1, 1), min_df=1) -> CountVectorizer:
    return CountVectorizer(token_pattern=TOKEN, lowercase=False, ngram_range=ngram, min_df=min_df)


def tfidf(ngram=(1, 2), min_df=1) -> TfidfVectorizer:
    return TfidfVectorizer(token_pattern=TOKEN, lowercase=False, ngram_range=ngram, min_df=min_df,
                           sublinear_tf=True)


def _stable_hash(s: str) -> int:
    """Deterministic replacement for Python's salted hash() so Word2Vec is reproducible."""
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16)


class W2VTfidf(BaseEstimator, TransformerMixin):
    """Word2Vec (Skip-gram) + TF-IDF-weighted average sentence vectors."""

    def __init__(self, vector_size=200, window=5, min_count=2, epochs=20):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.epochs = epochs

    def fit(self, texts, y=None):
        sents = [t.split() for t in texts]
        self.w2v_ = Word2Vec(sents, vector_size=self.vector_size, window=self.window,
                             min_count=self.min_count, sg=1, epochs=self.epochs,
                             workers=1, seed=RANDOM_STATE, hashfxn=_stable_hash)
        self.tfidf_ = TfidfVectorizer(token_pattern=TOKEN, lowercase=False).fit(texts)
        return self

    def transform(self, texts):
        W = self.tfidf_.transform(texts).tocsr()
        vocab = self.tfidf_.get_feature_names_out()
        kv = self.w2v_.wv
        out = np.zeros((W.shape[0], self.vector_size), dtype=np.float32)
        for i in range(W.shape[0]):
            row = W.getrow(i)
            vecs, ws = [], []
            for j, w in zip(row.indices, row.data):
                tok = vocab[j]
                if tok in kv:
                    vecs.append(kv[tok])
                    ws.append(w)
            if ws:  # no known word -> zero vector
                out[i] = np.average(vecs, axis=0, weights=ws)
        return out
