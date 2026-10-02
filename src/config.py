"""Shared paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
HTML_CACHE = RAW / "html_cache"
INTERIM = DATA / "interim"
GOLD = DATA / "gold"
PROCESSED = DATA / "processed"
RESOURCES = ROOT / "resources"
RESULTS = ROOT / "results"
MODELS = ROOT / "models"  # fitted models (not committed)

RANDOM_STATE = 42
LABELS = ["Negative", "Neutral", "Positive"]
