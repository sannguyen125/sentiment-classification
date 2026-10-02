"""Phase 6: evaluation on the gold test set (Ch.3 "Đánh giá các mô hình phân loại").

Run: python -m src.evaluate
- Accuracy, Precision/Recall/F1 per class + macro, confusion matrix (counts + row-normalised)
  for baseline, 6 classic configs and PhoBERT (seed 42, epoch chosen on val).
- TF-IDF+NB without stopword removal is reported on test FOR REFERENCE ONLY (not used to choose).
- Label noise: star label vs gold label per star; LLM/member-2 agreement (gold_agreement.json).
- PhoBERT seed variance on val (seeds 42/43/44).
- errors.csv: 15 errors of the best classic model (chosen on val) + 15 of PhoBERT;
  error groups come from results/error_groups.csv (manual analysis) when present.
Out: results/comparison.csv, results/metrics/{test_metrics,phobert_seeds,eval_notes}.json,
     results/label_noise.csv, results/label_transition.csv, results/errors.csv,
     results/predictions/classic_test.csv, results/figures/*.png
"""
import json
import re
import unicodedata

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from src.config import GOLD, LABELS, MODELS, PROCESSED, RANDOM_STATE, RESULTS

MET, FIG, PRED = RESULTS / "metrics", RESULTS / "figures", RESULTS / "predictions"
CLASSIC = [("BoW", "NB"), ("BoW", "SVM"), ("TF-IDF", "NB"), ("TF-IDF", "SVM"), ("W2V", "NB"), ("W2V", "SVM")]
N_ERR = 15
# palette (dataviz reference instance, validated): series blue/orange, ink, blue sequential ramp
BLUE, ORANGE, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
SEQ = LinearSegmentedColormap.from_list("seq", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])


def slug(name: str) -> str:
    name = unicodedata.normalize("NFKD", name.lower().replace("đ", "d"))
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")


def metrics(y, pred) -> dict:
    p, r, f, s = precision_recall_fscore_support(y, pred, labels=LABELS, zero_division=0)
    mp, mr, mf, _ = precision_recall_fscore_support(y, pred, labels=LABELS, average="macro", zero_division=0)
    out = {"accuracy": accuracy_score(y, pred), "macro_precision": mp, "macro_recall": mr, "macro_f1": mf}
    for i, lab in enumerate(LABELS):
        out.update({f"precision_{lab}": p[i], f"recall_{lab}": r[i], f"f1_{lab}": f[i], f"support_{lab}": int(s[i])})
    return {k: (round(float(v), 4) if isinstance(v, float) else v) for k, v in out.items()}


def plot_cm(y, pred, title: str, path) -> list:
    cm = confusion_matrix(y, pred, labels=LABELS)
    norm = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4), facecolor=SURF)
    for ax, mat, fmt, sub in ((axes[0], cm, "{:d}", "Số đếm"), (axes[1], norm, "{:.0%}", "Chuẩn hóa theo hàng (recall)")):
        ax.imshow(norm, cmap=SEQ, vmin=0, vmax=1)  # colour = row share in both panels
        for i in range(3):
            for j in range(3):
                ax.text(j, i, fmt.format(mat[i, j]), ha="center", va="center", fontsize=11,
                        color="#ffffff" if norm[i, j] > 0.55 else INK)
        ax.set_xticks(range(3), LABELS, color=INK2)
        ax.set_yticks(range(3), LABELS, color=INK2)
        ax.set_xlabel("Dự đoán", color=INK2)
        ax.set_ylabel("Nhãn gold", color=INK2)
        ax.set_title(sub, fontsize=10, color=INK2)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle(title, color=INK, fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURF)
    plt.close(fig)
    return cm.tolist()


def plot_bars(comp: pd.DataFrame, path) -> None:
    d = comp[~comp["is_reference"]].reset_index(drop=True)
    y = np.arange(len(d))[::-1]
    h = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 5.2), facecolor=SURF)
    ax.set_facecolor(SURF)
    ax.barh(y + h / 2, d["val_macro_f1"], h - 0.04, color=BLUE, label="Val (nhãn sao)")
    ax.barh(y - h / 2, d["test_macro_f1"], h - 0.04, color=ORANGE, label="Test (nhãn gold)")
    for yi, v in zip(y, d["test_macro_f1"]):
        ax.text(v + 0.008, yi - h / 2, f"{v:.3f}", va="center", fontsize=9, color=INK)
    ax.set_yticks(y, d["model"], color=INK)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Macro-F1", color=INK2)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors=INK2, length=0)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False)
    ax.set_title("Macro-F1 theo mô hình: val (nhãn sao) và test (nhãn gold)", color=INK, fontsize=12,
                 loc="left", pad=28)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURF)
    plt.close(fig)


def phobert_seeds() -> dict:
    runs = {}
    for seed, f in ((42, "phobert.json"), (43, "phobert_seed43.json"), (44, "phobert_seed44.json")):
        if (MET / f).exists():
            m = json.loads((MET / f).read_text(encoding="utf-8"))
            ep3 = next(h for h in m["history"] if h["epoch"] == 3)
            runs[seed] = {"best_epoch": m["best_epoch"], "val_macro_f1_best": m["val_best"]["macro_f1"],
                          "val_macro_f1_epoch3": ep3["val_macro_f1"],
                          "history_val_macro_f1": [h["val_macro_f1"] for h in m["history"]]}
    best = np.array([r["val_macro_f1_best"] for r in runs.values()])
    ep3 = np.array([r["val_macro_f1_epoch3"] for r in runs.values()])
    sd = lambda a: round(float(a.std(ddof=1)), 4) if len(a) > 1 else None
    return {"seeds": runs, "n_seeds": len(runs),
            "val_macro_f1_best_epoch_mean": round(float(best.mean()), 4), "val_macro_f1_best_epoch_std": sd(best),
            "val_macro_f1_epoch3_mean": round(float(ep3.mean()), 4), "val_macro_f1_epoch3_std": sd(ep3),
            "note": "std = sample std (ddof=1); model used on test = seed 42, epoch 3"}


def main() -> None:
    for d in (MET, FIG, PRED):
        d.mkdir(parents=True, exist_ok=True)
    test = pd.read_csv(PROCESSED / "test.csv").fillna({"text_clean": "", "text_nostop": ""})
    y = test["label"]
    val_cmp = pd.read_csv(RESULTS / "val_comparison.csv")
    val_cls = json.loads((MET / "val_classic.json").read_text(encoding="utf-8"))
    pho = json.loads((MET / "phobert.json").read_text(encoding="utf-8"))

    # ---- predictions ----
    preds, val_f1 = {}, {}
    preds["Baseline (lớp đông nhất)"] = joblib.load(MODELS / "baseline.joblib").predict(test["text_clean"])
    val_f1["Baseline (lớp đông nhất)"] = float(val_cmp.loc[val_cmp["feature"] == "-", "macro_f1"].iloc[0])
    for feat, algo in CLASSIC:
        name = f"{feat} + {algo}"
        preds[name] = joblib.load(MODELS / f"{feat}_{algo}.joblib".replace("-", "")).predict(test["text_clean"])
        val_f1[name] = float(val_cmp.query("feature == @feat and algo == @algo")["macro_f1"].iloc[0])
    ph = pd.read_csv(PRED / "phobert_test.csv").set_index("review_id").loc[test["review_id"], "pred"].to_numpy()
    preds["PhoBERT"] = ph
    val_f1["PhoBERT"] = pho["val_best"]["macro_f1"]
    ref = "TF-IDF + NB, không bỏ stopword [tham khảo]"
    preds[ref] = joblib.load(MODELS / "TFIDF_NB_nostop.joblib").predict(test["text_nostop"])
    val_f1[ref] = val_cls["stopword_experiment"]["without_stopword_removal"]["macro_f1"]
    pd.DataFrame({"review_id": test["review_id"], "label": y, **{f"pred_{slug(k)}": v for k, v in preds.items()}}
                 ).to_csv(PRED / "classic_test.csv", index=False, encoding="utf-8")

    # ---- metrics + confusion matrices ----
    rows, all_m = [], {}
    for name, p in preds.items():
        m = metrics(y, p)
        hit_gold, hit_star = (p == y), (p == test["label_star"])
        m["accuracy_by_star"] = {int(s): round(float(hit_gold[test["star"] == s].mean()), 4) for s in range(1, 6)}
        m["agree_with_star_label_by_star"] = {int(s): round(float(hit_star[test["star"] == s].mean()), 4) for s in range(1, 6)}
        m["confusion_matrix"] = plot_cm(y, p, f"{name} (test gold, n={len(y)})", FIG / f"cm_{slug(name)}.png")
        all_m[name] = m
        rows.append({"model": name, "is_reference": name == ref, "val_macro_f1": round(val_f1[name], 4),
                     "test_macro_f1": m["macro_f1"], "test_accuracy": m["accuracy"],
                     "test_macro_precision": m["macro_precision"], "test_macro_recall": m["macro_recall"],
                     **{f"test_{k}_{lab}": m[f"{k}_{lab}"] for lab in LABELS for k in ("precision", "recall", "f1")}})
    comp = pd.DataFrame(rows)
    comp.to_csv(RESULTS / "comparison.csv", index=False, encoding="utf-8")
    plot_bars(comp, FIG / "macro_f1_val_test.png")

    # ---- label noise (star label vs gold label) ----
    ct = pd.crosstab(test["star"], test["label"]).reindex(columns=LABELS, fill_value=0)
    noise = ct.copy()
    noise["n"] = ct.sum(axis=1)
    noise["label_star"] = [{1: "Negative", 2: "Negative", 3: "Neutral", 4: "Positive", 5: "Positive"}[s] for s in ct.index]
    noise["pct_star_label_differs"] = [round(1 - ct.loc[s, noise.loc[s, "label_star"]] / noise.loc[s, "n"], 4) for s in ct.index]
    noise.to_csv(RESULTS / "label_noise.csv", encoding="utf-8")
    trans = pd.crosstab(test["label_star"], test["label"], margins=True, margins_name="Tổng").reindex(
        index=LABELS + ["Tổng"], columns=LABELS + ["Tổng"], fill_value=0)
    trans.to_csv(RESULTS / "label_transition.csv", encoding="utf-8")
    agree = json.loads((MET / "gold_agreement.json").read_text(encoding="utf-8"))

    # ---- errors: best classic (chosen on VAL) + PhoBERT ----
    best_classic = max((f"{f} + {a}" for f, a in CLASSIC), key=lambda n: val_f1[n])
    rng_seed = RANDOM_STATE
    frames, used = [], set()
    for model, other in ((best_classic, "PhoBERT"), ("PhoBERT", best_classic)):
        wrong = test[preds[model] != y].assign(pred=preds[model][preds[model] != y],
                                               pred_other_model=preds[other][preds[model] != y])
        wrong = wrong[~wrong["review_id"].isin(used)]
        pick = wrong.sample(min(N_ERR, len(wrong)), random_state=rng_seed)
        used |= set(pick["review_id"])
        frames.append(pick.assign(model=model, other_model=other))
    err = pd.concat(frames)
    err["both_wrong"] = err["pred_other_model"] != err["label"]
    err = err[["model", "review_id", "text", "label", "pred", "other_model", "pred_other_model", "both_wrong",
               "star", "label_star", "label_source"]]
    gpath = RESULTS / "error_groups.csv"
    if gpath.exists():
        g = pd.read_csv(gpath, encoding="utf-8")
        err = err.merge(g[["review_id", "nhom_loi", "ghi_chu"]], on="review_id", how="left")
    else:
        err["nhom_loi"], err["ghi_chu"] = "", ""
    err.to_csv(RESULTS / "errors.csv", index=False, encoding="utf-8")
    err_summary = (err.groupby(["model", "nhom_loi"]).size().unstack(fill_value=0).to_dict("index")
                   if err["nhom_loi"].notna().any() and (err["nhom_loi"] != "").any() else {})

    # ---- notes for the report ----
    split = json.loads((MET / "split_stats.json").read_text(encoding="utf-8"))
    clean = json.loads((MET / "clean_stats.json").read_text(encoding="utf-8"))
    notes = {
        "label_distribution_pct": {k: split[k]["label_pct"] for k in ("train", "val", "test")},
        "label_distribution_note": "train/val = star labels, test = gold labels (text-based) -> distributions differ",
        "test_neutral_support": int((y == "Neutral").sum()),
        "pool_reviews": clean["pool_after_gold"], "clean_reviews": clean["clean"], "raw_reviews": clean["raw"],
        "target_reviews": "8000-10000",
    }
    seeds = phobert_seeds()
    (MET / "phobert_seeds.json").write_text(json.dumps(seeds, ensure_ascii=False, indent=2), encoding="utf-8")
    (MET / "eval_notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    (MET / "test_metrics.json").write_text(json.dumps(
        {"models": all_m, "best_classic_by_val": best_classic, "reference_only": ref,
         "label_noise_overall_pct_differs": round(float((test["label_star"] != y).mean()), 4),
         "gold_agreement": agree, "error_groups": err_summary}, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- print ----
    show = ["model", "val_macro_f1", "test_macro_f1", "test_accuracy", "test_f1_Negative", "test_f1_Neutral", "test_f1_Positive"]
    print(comp[show].to_string(index=False))
    print(f"\nBest classic (by val): {best_classic}")
    print("\nStar -> gold label (test):\n", noise.to_string())
    print("\nlabel_star -> gold label:\n", trans.to_string())
    print("\nPhoBERT seeds:", json.dumps(seeds, ensure_ascii=False))
    print("\nNotes:", json.dumps(notes, ensure_ascii=False))
    print(f"\nerrors.csv: {len(err)} rows | both models wrong: {int(err['both_wrong'].sum())}")


if __name__ == "__main__":
    main()
