"""Build data/raw/products.csv from the DMX product sitemap (robots.txt compliant).

Run: python -m src.crawl.sitemap
"""
import hashlib
import random
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
from tqdm import tqdm

from src.config import HTML_CACHE, RAW

BASE = "https://www.dienmayxanh.com"
SITEMAP_INDEX = f"{BASE}/newsitemap/sitemap-product"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
CACHE = HTML_CACHE / "sitemap"
OUT = RAW / "products.csv"

# Categories to prioritise (large appliances with many reviews)
PRIORITY = [
    "may-giat", "tu-lanh", "may-lanh", "tivi", "noi-com-dien", "may-loc-nuoc",
    "quat-dieu-hoa", "quat", "lo-vi-song", "may-nuoc-nong", "bep-tu",
    "bep-hong-ngoai", "may-say-quan-ao", "may-rua-chen", "noi-chien-khong-dau",
    "may-loc-khong-khi", "robot-hut-bui", "may-hut-bui", "tu-dong",
]  # all checked allowed by robots.txt (2026-09-30); bep-dien, tu-mat: 0 in sitemap


class Blocked(Exception):
    pass


def load_robots() -> RobotFileParser:
    """Always re-download robots.txt (no cache). RobotFileParser.read() uses the
    default Python UA, which DMX answers with 403 -> treated as disallow-all,
    so we fetch with our UA and parse ourselves."""
    req = urllib.request.Request(f"{BASE}/robots.txt", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        lines = r.read().decode("utf-8", "replace").splitlines()
    rp = RobotFileParser()
    rp.parse(lines)
    return rp


def fetch(url: str) -> str:
    """Fetch with disk cache; polite delay only on network hits."""
    key = hashlib.sha1(url.encode()).hexdigest()[:16]
    path = CACHE / f"{key}.xml"
    if path.exists():
        return path.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise Blocked(f"HTTP {e.code} at {url}")
        raise
    if "captcha" in text.lower():
        raise Blocked(f"captcha at {url}")
    path.write_text(text, encoding="utf-8")
    time.sleep(random.uniform(2, 4))
    return text


def locs(xml: str) -> list[str]:
    return [u.replace("&amp;", "&").strip() for u in re.findall(r"<loc>(.*?)</loc>", xml)]


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    rp = load_robots()
    children = locs(fetch(SITEMAP_INDEX))
    print(f"{len(children)} child sitemaps")
    rows = []
    try:
        for sm in tqdm(children, desc="sitemaps"):
            for url in locs(fetch(sm)):
                parts = urlparse(url).path.strip("/").split("/")
                if len(parts) != 2:
                    continue
                rows.append({
                    "product_url": url,
                    "category": parts[0],
                    "slug": parts[1],
                    "allowed": rp.can_fetch(UA, url) and rp.can_fetch(UA, url + "/danh-gia"),
                })
    except Blocked as e:
        print(f"STOP: {e}. Blocked - report to user, do not retry.")
        sys.exit(1)
    df = pd.DataFrame(rows).drop_duplicates("product_url")
    df["priority"] = df["category"].isin(PRIORITY)
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"Saved {len(df)} products -> {OUT}")
    print(f"Disallowed by robots: {(~df['allowed']).sum()}")
    print(df[df["allowed"]]["category"].value_counts().head(30).to_string())


if __name__ == "__main__":
    main()
