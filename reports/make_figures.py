"""Figures (and crawl counts) for the report, with Vietnamese labels.

Run: python reports/make_figures.py
Only reads data and results that already exist (no model is trained):
  results/metrics/clean_stats.json, results/label_noise_pool.csv, results/comparison.csv,
  results/predictions/classic_test.csv, data/processed/train.csv, data/raw/*.
Out: results/figures/report_*.png, results/metrics/crawl_stats.json
"""
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.features import tfidf  # noqa: E402  same TF-IDF settings as the models

RES, FIG, RAW = ROOT / "results", ROOT / "results" / "figures", ROOT / "data" / "raw"
LABELS = ["Negative", "Neutral", "Positive"]
VI = {"Negative": "Tiêu cực", "Neutral": "Trung tính", "Positive": "Tích cực"}
# dataviz reference palette (categorical slots 1-3 validated on the light surface; aqua has a
# contrast WARN -> bars always carry direct value labels)
COL = {"Negative": "#2a78d6", "Neutral": "#eb6834", "Positive": "#1baf7a"}
BLUE, ORANGE, INK, INK2, GRID, SURF = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e1e0d9", "#ffffff"
SEQ = LinearSegmentedColormap.from_list("seq", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
CATEGORY_VI = {
    "may-lanh": "Máy lạnh", "tu-lanh": "Tủ lạnh", "quat-dieu-hoa": "Quạt điều hòa",
    "bep-hong-ngoai": "Bếp hồng ngoại", "noi-com-dien": "Nồi cơm điện", "may-nuoc-nong": "Máy nước nóng",
    "may-giat": "Máy giặt", "quat": "Quạt", "tivi": "Tivi", "lo-vi-song": "Lò vi sóng",
    "may-hut-bui": "Máy hút bụi", "noi-chien-khong-dau": "Nồi chiên không dầu", "tu-dong": "Tủ đông",
    "robot-hut-bui": "Robot hút bụi", "may-say-quan-ao": "Máy sấy quần áo", "may-loc-nuoc": "Máy lọc nước",
    "may-rua-chen": "Máy rửa chén", "may-loc-khong-khi": "Máy lọc không khí", "bep-tu": "Bếp từ",
}
MODEL_VI = {"Baseline (lớp đông nhất)": "Luôn đoán lớp đông nhất", "W2V + NB": "Word2Vec + NB", "W2V + SVM": "Word2Vec + SVM"}
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "savefig.dpi": 200,
    "savefig.bbox": "tight", "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "xtick.major.size": 0, "ytick.major.size": 0})


def vnum(x: float, nd: int = 0) -> str:
    """Vietnamese number format (1.234 and 0,902); rounds half up on the value as written in
    the results file (0.7905 -> 0,791), the same rule as the report."""
    d = Decimal(str(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    s = f"{d:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def grid(ax, axis: str = "x") -> None:
    getattr(ax, f"{axis}axis").grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig, name: str) -> None:
    fig.savefig(FIG / f"report_{name}.png")
    plt.close(fig)
    print("saved", f"report_{name}.png")


def categories() -> None:
    cat = pd.Series(json.loads((RES / "metrics" / "clean_stats.json").read_text(encoding="utf-8"))
                    ["clean_by_category"]).rename(index=CATEGORY_VI).sort_values()
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.barh(cat.index, cat.values, height=0.65, color=BLUE)
    for y, v in enumerate(cat.values):
        ax.text(v + 8, y, vnum(v), va="center", fontsize=9, color=INK)
    grid(ax)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Số bình luận sau khi làm sạch")
    save(fig, "categories")


def label_by_star() -> None:
    noise = pd.read_csv(RES / "label_noise_pool.csv", index_col="star")
    share = noise[LABELS].div(noise["n"], axis=0) * 100
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    xs = [f"{s} sao\n(n = {vnum(n)})" for s, n in zip(share.index, noise["n"])]
    bottom = np.zeros(len(share))
    for lab in LABELS:
        v = share[lab].to_numpy()
        ax.bar(xs, v, 0.6, bottom=bottom, color=COL[lab], label=VI[lab], edgecolor=SURF, linewidth=2)
        for xi, (b, h) in enumerate(zip(bottom, v)):
            if h >= 6:
                ax.text(xi, b + h / 2, f"{vnum(h)}%", ha="center", va="center", fontsize=9, color="#ffffff")
        bottom += v
    ax.set_ylim(0, 100)
    ax.spines["left"].set_visible(False)
    ax.set_ylabel("% số bình luận của mức sao")
    ax.legend(ncol=3, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0))
    save(fig, "label_by_star")


def top_terms() -> None:
    train = pd.read_csv(ROOT / "data" / "processed" / "train.csv")
    vec = tfidf(ngram=(1, 2), min_df=5)
    X = vec.fit_transform(train["text_clean"].fillna(""))
    terms = np.array(vec.get_feature_names_out())
    y = train["label"].to_numpy()
    mean = np.vstack([np.asarray(X[y == lab].mean(axis=0)).ravel() for lab in LABELS])
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.8))
    for i, (ax, lab) in enumerate(zip(axes, LABELS)):
        score = mean[i] - np.delete(mean, i, axis=0).max(axis=0)
        order = np.argsort(-score)[:12][::-1]
        ax.barh(terms[order], score[order], height=0.65, color=COL[lab])
        grid(ax)
        ax.spines["left"].set_visible(False)
        ax.set_title(VI[lab], fontsize=11, color=INK, loc="left")
        ax.tick_params(axis="x", labelsize=8)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: vnum(round(v, 6), 3)))
    fig.supxlabel("TF-IDF trung bình trong lớp trừ giá trị lớn nhất ở hai lớp còn lại", color=INK2, fontsize=10)
    fig.tight_layout()
    save(fig, "top_terms")


def macro_f1() -> None:
    comp = pd.read_csv(RES / "comparison.csv")
    d = comp[~comp["is_reference"]].reset_index(drop=True)
    names = d["model"].map(lambda m: MODEL_VI.get(m, m))
    y = np.arange(len(d))[::-1]
    h = 0.38
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.barh(y + h / 2, d["val_macro_f1"], h - 0.04, color=BLUE, label="Tập kiểm định")
    ax.barh(y - h / 2, d["test_macro_f1"], h - 0.04, color=ORANGE, label="Tập kiểm tra")
    for yi, v, t in zip(y, d["val_macro_f1"], d["test_macro_f1"]):
        ax.text(v + 0.008, yi + h / 2, vnum(v, 3), va="center", fontsize=8, color=INK2)
        ax.text(t + 0.008, yi - h / 2, vnum(t, 3), va="center", fontsize=8, color=INK)
    ax.set_yticks(y, names, color=INK)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Macro-F1")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: vnum(round(v, 6), 1)))
    grid(ax)
    ax.spines["left"].set_visible(False)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False)
    save(fig, "macro_f1")


def confusion() -> None:
    pred = pd.read_csv(RES / "predictions" / "classic_test.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.1))
    for ax, (col, title) in zip(axes, (("pred_tf_idf_svm", "(a) TF-IDF + SVM"), ("pred_phobert", "(b) PhoBERT"))):
        cm = confusion_matrix(pred["label"], pred[col], labels=LABELS)
        norm = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
        ax.imshow(norm, cmap=SEQ, vmin=0, vmax=1)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{cm[i, j]}\n({vnum(norm[i, j] * 100)}%)", ha="center", va="center",
                        fontsize=10, color="#ffffff" if norm[i, j] > 0.55 else INK)
        ticks = [VI[lab] for lab in LABELS]
        ax.set_xticks(range(3), ticks, color=INK2)
        ax.set_yticks(range(3), ticks, color=INK2)
        ax.set_xlabel("Nhãn dự đoán")
        ax.set_ylabel("Nhãn thực tế")
        ax.set_title(title, fontsize=11, color=INK)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.tight_layout()
    save(fig, "confusion")


def crawl_stats() -> None:
    """Counts about the crawl that are not in clean_stats.json (raw data is not committed)."""
    products = pd.read_csv(RAW / "products.csv")
    stats = pd.read_json(RAW / "product_stats.jsonl", lines=True)
    out = {"sitemap_products_allowed": int(products["allowed"].sum()),
           "sitemap_categories_allowed": int(products.loc[products["allowed"], "category"].nunique()),
           "products_crawled": len(stats), "categories_crawled": int(stats["category"].nunique()),
           "products_by_pick": {k: int(v) for k, v in stats["pick"].value_counts().items()},
           "note": "pick: top_sold = best-sellers of the category page, low_rank = lowest-rated"}
    (RES / "metrics" / "crawl_stats.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("crawl_stats:", out)


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    categories()
    label_by_star()
    top_terms()
    macro_f1()
    confusion()
    if (RAW / "products.csv").exists():
        crawl_stats()
