"""Phase 4c: Naive Bayes + SVM on BoW / TF-IDF / Word2Vec (Ch.3).

Run: python -m src.train_classic
- 6 configs = 3 features x {NB, SVM}; small grid tuned on val by macro-F1 (Ch.3: role of
  the validation set). Models are fitted on train only; the test set is not touched here.
- NB : MultinomialNB(alpha = Laplace smoothing, fit_prior) for BoW/TF-IDF;
       GaussianNB for Word2Vec (dense vectors with negative values).
- SVM: LinearSVC for BoW/TF-IDF (high-dimensional sparse); RBF SVC + StandardScaler for W2V.
       class_weight="balanced" against class imbalance.
- Baseline: always predict the majority class.
- Extra: best config with vs without stopword removal (Ch.2 §2.3).
Out: results/metrics/val_grid.csv, results/metrics/val_classic.json, results/val_comparison.csv,
     models/<feature>_<algo>.joblib
"""
import itertools
import json
import time
import warnings

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, LinearSVC

from src.config import LABELS, MODELS, PROCESSED, RANDOM_STATE, RESULTS
from src.features import W2VTfidf, bow, tfidf

warnings.filterwarnings("ignore", category=UserWarning)

FEATURE_GRID = {
    "BoW": [{"ngram": n, "min_df": m} for n in [(1, 1), (1, 2)] for m in (1, 2)],
    "TF-IDF": [{"ngram": (1, 2), "min_df": m} for m in (1, 2, 3, 5)],
    "W2V": [{"vector_size": 200}],
}
SPARSE_NB = [{"alpha": a, "fit_prior": f} for a in (0.1, 0.3, 0.5, 1.0) for f in (True, False)]
SPARSE_SVM = [{"C": c} for c in (0.003, 0.01, 0.03, 0.1, 0.3, 1.0)]
DENSE_NB = [{"var_smoothing": v, "priors": p} for v in (1e-9, 1e-6, 1e-3) for p in (None, "uniform")]
DENSE_SVM = [{"C": c} for c in (0.1, 0.3, 1.0, 3.0, 10.0)]


def make_feature(name: str, p: dict):
    if name == "BoW":
        return bow(p["ngram"], p["min_df"])
    if name == "TF-IDF":
        return tfidf(p["ngram"], p["min_df"])
    return W2VTfidf(vector_size=p["vector_size"])


def make_clf(feat: str, algo: str, p: dict):
    if feat == "W2V" and algo == "NB":
        priors = [1 / 3] * 3 if p["priors"] == "uniform" else None
        return GaussianNB(var_smoothing=p["var_smoothing"], priors=priors)
    if feat == "W2V":
        return SVC(kernel="rbf", C=p["C"], gamma="scale", class_weight="balanced",
                   random_state=RANDOM_STATE)
    if algo == "NB":
        return MultinomialNB(**p)
    return LinearSVC(C=p["C"], class_weight="balanced", max_iter=10000, random_state=RANDOM_STATE)


def clf_grid(feat: str, algo: str) -> list[dict]:
    if feat == "W2V":
        return DENSE_NB if algo == "NB" else DENSE_SVM
    return SPARSE_NB if algo == "NB" else SPARSE_SVM


def scores(y, pred) -> dict:
    f1 = f1_score(y, pred, labels=LABELS, average=None, zero_division=0)
    return {"macro_f1": round(float(f1_score(y, pred, labels=LABELS, average="macro", zero_division=0)), 4),
            "accuracy": round(float(accuracy_score(y, pred)), 4),
            **{f"f1_{lab}": round(float(v), 4) for lab, v in zip(LABELS, f1)}}


def run_config(feat: str, algo: str, train: pd.DataFrame, val: pd.DataFrame, col: str,
               grid_rows: list | None = None) -> tuple[dict, Pipeline]:
    """Tune one config on val; return best row + fitted pipeline (fitted on train only)."""
    best, best_pipe = None, None
    for fp in FEATURE_GRID[feat]:
        vec = make_feature(feat, fp)
        Xtr, Xva = vec.fit_transform(train[col]), vec.transform(val[col])
        scaler = None
        if feat == "W2V" and algo == "SVM":
            scaler = StandardScaler().fit(Xtr)
            Xtr, Xva = scaler.transform(Xtr), scaler.transform(Xva)
        for cp in clf_grid(feat, algo):
            clf = make_clf(feat, algo, cp).fit(Xtr, train["label"])
            row = {"feature": feat, "algo": algo, "input": col,
                   "feat_params": json.dumps({k: list(v) if isinstance(v, tuple) else v for k, v in fp.items()}),
                   "clf_params": json.dumps(cp), **scores(val["label"], clf.predict(Xva))}
            if grid_rows is not None:
                grid_rows.append(row)
            if best is None or row["macro_f1"] > best["macro_f1"]:
                steps = [("feat", vec)] + ([("scale", scaler)] if scaler else []) + [("clf", clf)]
                best, best_pipe = row, Pipeline(steps)
    return best, best_pipe


def main() -> None:
    train = pd.read_csv(PROCESSED / "train.csv").fillna({"text_clean": "", "text_nostop": ""})
    val = pd.read_csv(PROCESSED / "val.csv").fillna({"text_clean": "", "text_nostop": ""})
    MODELS.mkdir(exist_ok=True)
    grid_rows, best_rows = [], []

    base = DummyClassifier(strategy="most_frequent").fit(train["text_clean"], train["label"])
    best_rows.append({"feature": "-", "algo": "Baseline (lớp đông nhất)", "input": "-",
                      "feat_params": "", "clf_params": "", **scores(val["label"], base.predict(val["text_clean"]))})
    joblib.dump(base, MODELS / "baseline.joblib")

    for feat, algo in itertools.product(FEATURE_GRID, ("NB", "SVM")):
        t0 = time.time()
        best, pipe = run_config(feat, algo, train, val, "text_clean", grid_rows)
        best_rows.append(best)
        joblib.dump(pipe, MODELS / f"{feat}_{algo}.joblib".replace("-", ""))
        print(f"{feat:7s} {algo:4s} macro-F1={best['macro_f1']:.4f} acc={best['accuracy']:.4f} "
              f"{best['feat_params']} {best['clf_params']} ({time.time() - t0:.0f}s)", flush=True)

    # stopword experiment on the best config (Ch.2 §2.3)
    top = max(best_rows[1:], key=lambda r: r["macro_f1"])
    no_stop, no_stop_pipe = run_config(top["feature"], top["algo"], train, val, "text_nostop")
    # saved only so Phase 6 can REPORT it on test for reference (never used to choose)
    joblib.dump(no_stop_pipe, MODELS / f"{top['feature']}_{top['algo']}_nostop.joblib".replace("-", ""))
    stop_exp = {"config": f"{top['feature']} + {top['algo']}",
                "with_stopword_removal": {k: top[k] for k in ("macro_f1", "accuracy", "f1_Negative", "f1_Neutral", "f1_Positive")},
                "without_stopword_removal": {k: no_stop[k] for k in ("macro_f1", "accuracy", "f1_Negative", "f1_Neutral", "f1_Positive")},
                "best_params_without": {"feat": no_stop["feat_params"], "clf": no_stop["clf_params"]}}

    (RESULTS / "metrics").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(grid_rows).to_csv(RESULTS / "metrics" / "val_grid.csv", index=False, encoding="utf-8")
    comp = pd.DataFrame(best_rows)
    comp.to_csv(RESULTS / "val_comparison.csv", index=False, encoding="utf-8")
    (RESULTS / "metrics" / "val_classic.json").write_text(json.dumps(
        {"best_per_config": best_rows, "stopword_experiment": stop_exp,
         "note": "val labels = star labels; tuned by macro-F1 on val; models fitted on train only"},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nMacro-F1 on val (label = star label):")
    print(comp[["feature", "algo", "macro_f1", "accuracy", "f1_Negative", "f1_Neutral", "f1_Positive",
                "feat_params", "clf_params"]].to_string(index=False))
    print("\nStopword experiment:", json.dumps(stop_exp, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
