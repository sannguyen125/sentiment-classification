"""Crawl DMX product reviews with Playwright (1 browser, 1 tab, polite, resumable).

Trial:  python -m src.crawl.reviews --limit-products 3 --print-sample 10
Full:   python -m src.crawl.reviews

Candidates: priority category pages (only clicking "Xem thêm" in the browser),
intersected with data/raw/products.csv (sitemap). Per category, low-rated products
(avg < 4.5, or the lowest-rated ones if too few) alternate with best-sellers.
Per product: click star filters 1★ -> 5★, paginate by clicking page links.
Outputs: data/raw/reviews.jsonl (reviews), data/raw/product_stats.jsonl (real star
distribution per product), data/raw/crawl_state.json (resume).
"""
import argparse
import hashlib
import json
import random
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

from src.config import HTML_CACHE, RAW
from src.crawl import selectors as S
from src.crawl.sitemap import BASE, PRIORITY, UA, Blocked, load_robots

OUT = RAW / "reviews.jsonl"
STATS = RAW / "product_stats.jsonl"
STATE = RAW / "crawl_state.json"
PRODUCTS = RAW / "products.csv"
PER_PAGE = 20
LOW_VOTE = 4.5
MIN_LOW_PER_CAT = 3
# phone numbers (incl. partly masked "xxxx231245"); lookbehind avoids prices like 10.000.000
PHONE_RE = re.compile(r"(?<![\w.,])(?:\+?84|0|x{2,})[\d\s.\-x]{7,12}\d", re.I)


# ---------- helpers ----------
def pause(lo: float = 2, hi: float = 4) -> None:
    time.sleep(random.uniform(lo, hi))


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"done": {}}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def append_jsonl(path, rows: list[dict]) -> None:
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def check_page(resp, page) -> None:
    """Stop on 403/429 or a page that is not what we expect (captcha, challenge...)."""
    if resp is not None and resp.status in (403, 429):
        raise Blocked(f"HTTP {resp.status} at {page.url}")
    body = page.locator("body").inner_text(timeout=10000).lower()
    if "captcha" in body or "xác minh bạn không phải" in body or "access denied" in body:
        raise Blocked(f"captcha/challenge at {page.url}")


def goto(page, url: str, rp):
    if not rp.can_fetch(UA, url):
        raise ValueError(f"robots.txt disallows {url}")
    resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PWTimeout:
        pass
    check_page(resp, page)
    pause()
    return resp


LIST_READY_JS = """([sel, starSel, prev, star]) => {
  const li = document.querySelector(sel);
  if (!li) return false;
  if (prev && li.id === prev) return false;
  return !star || li.querySelectorAll(starSel).length === star;
}"""


def first_id(page) -> str | None:
    li = page.locator(S.REVIEW_ITEM)
    return li.first.get_attribute("id") if li.count() else None


def click_and_wait(page, locator, star: int | None = None) -> bool:
    """Click an on-page control, wait for the list reload the page triggers itself,
    then until the list shows new items (of the filtered star). Empty list -> times out, ok."""
    prev = first_id(page)
    try:
        with page.expect_response(lambda r: S.LIST_RESPONSE_MARKER in r.url, timeout=20000) as info:
            locator.click()
        if info.value.status in (403, 429):
            raise Blocked(f"HTTP {info.value.status} after click at {page.url}")
    except PWTimeout:
        return False
    try:
        page.wait_for_function(LIST_READY_JS, arg=[S.REVIEW_ITEM, S.STAR_ON, prev, star], timeout=10000)
    except PWTimeout:
        pass  # e.g. no review with this star
    page.wait_for_timeout(500)
    check_page(None, page)
    pause()
    return True


def mask_phone(text: str) -> str:
    return PHONE_RE.sub("<phone>", text)


def strip_personal(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for sel in S.PERSONAL:
        for e in soup.select(sel):
            e.decompose()
    return str(soup)


def parse_reviews(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for li in soup.select(S.REVIEW_ITEM):
        txt = li.select_one(S.REVIEW_TEXT)
        used = li.select_one(S.USED_FOR)
        out.append({
            "rid": li.get("id", ""),
            "star": len(li.select(S.STAR_ON)),
            "text": " ".join(txt.get_text(" ").split()) if txt else "",
            "verified_purchase": li.select_one(S.VERIFIED) is not None,
            "used_for": used.get_text(" ", strip=True) if used else None,
        })
    return out


def to_float(s: str | None) -> float | None:
    try:
        return float(s.replace(",", ".")) if s else None
    except ValueError:
        return None


# ---------- candidates ----------
def sold_count(text: str) -> float:
    m = re.search(r"Đã bán ([\d.,]+)\s*(k?)", text)
    if not m:
        return 0.0
    v = float(m.group(1).replace(",", "."))
    return v * 1000 if m.group(2) else v


def category_candidates(page, rp, cat: str, more_clicks: int, log_net: list) -> list[dict]:
    cache = HTML_CACHE / "category" / f"{cat}.html"
    if cache.exists():
        html = cache.read_text(encoding="utf-8")
    else:
        resp = goto(page, f"{BASE}/{cat}", rp)
        if resp.status == 404:
            return []
        for _ in range(more_clicks):
            btn = page.locator(S.CATE_VIEW_MORE)
            if not btn.count() or not btn.first.is_visible():
                break
            n = page.locator(S.CATE_ITEM).count()
            reqs = []
            handler = lambda r: r.resource_type in ("xhr", "fetch") and reqs.append(f"{r.method} {urlparse(r.url).path}")
            page.on("request", handler)
            btn.first.click()  # the page loads more items itself; we never call its endpoint
            try:
                page.wait_for_function(
                    f"document.querySelectorAll('{S.CATE_ITEM}').length > {n}", timeout=20000)
            except PWTimeout:
                page.remove_listener("request", handler)
                break
            page.remove_listener("request", handler)
            log_net.extend(reqs)
            check_page(None, page)
            pause()
        html = page.content()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(html, encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for li in soup.select(S.CATE_ITEM):
        a = li.select_one(S.CATE_LINK)
        if not a or not a.get("href"):
            continue
        meta = li.select_one(S.CATE_META)
        vote = li.select_one(S.CATE_VOTE)
        rows.append({
            "url": BASE + urlparse(a["href"]).path,
            "sold": sold_count(meta.get_text(" ") if meta else ""),
            "vote": to_float(vote.get_text(strip=True) if vote else None),
        })
    return rows


def order_category(rows: list[dict]) -> list[dict]:
    """Alternate low-rated products with best-sellers inside one category."""
    rated = [r for r in rows if r["vote"] is not None]
    low = sorted([r for r in rated if r["vote"] < LOW_VOTE], key=lambda r: -r["sold"])
    for r in low:
        r["pick"] = "low_vote"
    if len(low) < MIN_LOW_PER_CAT:  # averages are inflated -> take the lowest-rated ones
        rest = sorted([r for r in rated if r not in low], key=lambda r: (r["vote"], -r["sold"]))
        extra = rest[: MIN_LOW_PER_CAT - len(low)]
        for r in extra:
            r["pick"] = "low_rank"
        low += extra
    top = sorted([r for r in rows if r not in low], key=lambda r: -r["sold"])
    for r in top:
        r["pick"] = "top_sold"
    out = []
    for i in range(max(len(low), len(top))):
        out += [x[i] for x in (low, top) if i < len(x)]
    return out


def build_candidates(page, rp, cats: list[str], more_clicks: int) -> list[dict]:
    sitemap = pd.read_csv(PRODUCTS)
    allowed = set(sitemap.loc[sitemap["allowed"], "product_url"])
    per_cat, log_net = [], []
    for cat in cats:
        rows = [r for r in category_candidates(page, rp, cat, more_clicks, log_net)
                if r["url"] in allowed and rp.can_fetch(UA, r["url"] + "/danh-gia")]
        rows = order_category(rows)
        for r in rows:
            r["category"] = cat
        n_low = sum(r["pick"] != "top_sold" for r in rows)
        print(f"  {cat}: {len(rows)} candidates in sitemap ({n_low} low-rated)")
        per_cat.append(rows)
    if log_net:
        print("  requests fired by the page on 'Xem thêm' clicks:", dict(Counter(log_net)))
    # interleave categories so the crawl stays diverse
    out, seen, i = [], set(), 0
    while any(i < len(r) for r in per_cat):
        for r in per_cat:
            if i < len(r) and r[i]["url"] not in seen:
                seen.add(r[i]["url"])
                out.append(r[i])
        i += 1
    return out


# ---------- one product ----------
def last_page(page) -> int:
    nums = [int(m) for t in page.locator(f"{S.PAGINATION} a, {S.PAGINATION} span").all_inner_texts()
            for m in re.findall(r"\d+", t)]
    return max(nums) if nums else 1


def page_summary(page) -> dict:
    avg = page.locator(S.PAGE_AVG)
    out = {"page_avg": to_float(avg.first.inner_text().strip()) if avg.count() else None}
    for t in page.locator(S.RATE_BARS).all_inner_texts():
        m = re.match(r"\s*([1-5])\D+([\d.,]+)\s*%", t)
        if m:
            out[f"bar_pct_{m.group(1)}"] = to_float(m.group(2))
    return out


def crawl_product(page, rp, cand: dict, args) -> tuple[str, list[dict], dict | None]:
    url = cand["url"]
    resp = goto(page, url + "/danh-gia", rp)
    if resp.status == 404:
        return "404", [], None
    m = re.match(r"\s*([\d.,]+)\s*đánh giá", page.title())
    if not m:
        raise Blocked(f"unexpected page (title={page.title()!r}) at {page.url}")
    n_total = int(re.sub(r"\D", "", m.group(1)))
    if n_total < args.min_reviews:
        return f"few:{n_total}", [], None

    pid_el = page.locator(S.PRODUCT_ID)
    pid = pid_el.first.get_attribute("data-objectid") if pid_el.count() else urlparse(url).path
    category = urlparse(url).path.strip("/").split("/")[0]
    stats = {"product_id": str(pid), "product_url": url, "category": category,
             "pick": cand["pick"], "cate_vote": cand["vote"], "cate_sold": cand["sold"],
             "n_text_reviews": n_total, **page_summary(page)}
    cache_dir = HTML_CACHE / "reviews" / str(pid)
    cache_dir.mkdir(parents=True, exist_ok=True)
    caps = {1: None, 2: None, 3: None, 4: args.cap_4, 5: args.cap_5}
    seen, rows, empty = set(), [], []

    for star in (1, 2, 3, 4, 5):
        stats[f"crawled_{star}"] = 0
        stats[f"text_count_{star}"] = None
        filt = page.locator(S.STAR_FILTER_ITEMS).nth(6 - star)  # 1..5 = 5★..1★
        if not click_and_wait(page, filt, star):
            continue
        n_last, got, pno = last_page(page), 0, 1
        n_items = page.locator(S.REVIEW_ITEM).count()  # page 1
        if n_items == 0:  # site sometimes answers a star filter with an empty list
            empty.append(star)
            continue
        # product cap reached: only count this star (page 1 + last page), collect nothing
        ran = False
        while len(rows) < args.max_per_product:
            if ran:
                n_items += page.locator(S.REVIEW_ITEM).count()
            ran = True
            html = strip_personal(page.locator(".boxrate").inner_html())
            (cache_dir / f"s{star}_p{pno}.html").write_text(html, encoding="utf-8")
            for r in parse_reviews(html):
                if r["rid"] in seen or r["star"] != star or not r["text"]:
                    continue
                seen.add(r["rid"])
                text = mask_phone(r["text"])
                rows.append({
                    "review_id": hashlib.sha1(f"{pid}|{r['rid']}|{text}".encode()).hexdigest()[:16],
                    "product_id": str(pid),
                    "product_url": url,
                    "category": category,
                    "star": star,
                    "text": text,
                    "date": None,  # not shown on DMX review list
                    "used_for": r["used_for"],
                    "verified_purchase": r["verified_purchase"],
                    "crawled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                })
                got += 1
            cap = caps[star]
            if (cap and got >= cap) or len(rows) >= args.max_per_product:
                break
            nxt = page.locator(S.PAGE_LINK.format(n=pno + 1))
            if not nxt.count() or not click_and_wait(page, nxt.first, star):
                break
            pno += 1
        stats[f"crawled_{star}"] = got
        if pno >= n_last:  # walked every page -> exact count
            stats[f"text_count_{star}"] = n_items
        else:  # jump to the last page once to get the exact count
            lastl = page.locator(S.PAGE_LINK.format(n=n_last))
            if lastl.count() and click_and_wait(page, lastl.first, star):
                stats[f"text_count_{star}"] = (n_last - 1) * PER_PAGE + page.locator(S.REVIEW_ITEM).count()
    # an empty filter may be a real 0 or a site glitch: if exactly one star is unknown,
    # derive it from the title total; otherwise leave it null
    stats["empty_filters"] = empty
    stats["derived_star"] = None
    known = [stats[f"text_count_{s}"] for s in range(1, 6) if s not in empty]
    if len(empty) == 1 and None not in known:
        stats[f"text_count_{empty[0]}"] = max(n_total - sum(known), 0)
        stats["derived_star"] = empty[0]
    return f"ok:{n_total}", rows[: args.max_per_product], stats


# ---------- main ----------
def print_counts(path) -> Counter:
    c, cats = Counter(), set()
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                c[r["star"]] += 1
                cats.add(r["category"])
    print("  stars:", dict(sorted(c.items())), "| total", sum(c.values()),
          "| 1-2★", c[1] + c[2], "| 3★", c[3], "| categories", len(cats))
    return c


def targets_met(c: Counter, args) -> bool:
    return (sum(c.values()) >= args.target_total and c[1] + c[2] >= args.target_neg
            and c[3] >= args.target_neu)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-products", type=int, default=0)
    ap.add_argument("--print-sample", type=int, default=0)
    ap.add_argument("--min-reviews", type=int, default=30)
    ap.add_argument("--max-per-product", type=int, default=300)
    ap.add_argument("--cap-4", type=int, default=60)
    ap.add_argument("--cap-5", type=int, default=100)
    ap.add_argument("--more-clicks", type=int, default=15, help="'Xem thêm' clicks per category page")
    ap.add_argument("--categories", nargs="*", default=PRIORITY)
    ap.add_argument("--target-total", type=int, default=9000)
    ap.add_argument("--target-neg", type=int, default=1000)
    ap.add_argument("--target-neu", type=int, default=600)
    args = ap.parse_args()

    cats = args.categories
    more = args.more_clicks
    if args.limit_products:  # trial: first N categories, no "Xem thêm"
        cats, more = cats[: args.limit_products], 0

    rp = load_robots()
    state = load_state()
    new_rows: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(locale="vi-VN", user_agent=UA,
                                   viewport={"width": 1366, "height": 900}).new_page()
        try:
            print("Building candidate list...")
            cands = build_candidates(page, rp, cats, more)
            todo = [c for c in cands if c["url"] not in state["done"]]
            print(f"{len(cands)} candidates, {len(todo)} not done yet")
            n_ok = 0
            for i, cand in enumerate(todo, 1):
                if args.limit_products and n_ok >= args.limit_products:
                    break
                status, rows, stats = crawl_product(page, rp, cand, args)
                append_jsonl(OUT, rows)
                if stats:
                    append_jsonl(STATS, [stats])
                new_rows += rows
                state["done"][cand["url"]] = {"status": status, "n": len(rows), "pick": cand["pick"]}
                save_state(state)
                n_ok += status.startswith("ok")
                print(f"[{i}/{len(todo)}] {status:>9} +{len(rows):3d} {cand['pick']:>8}  {cand['url']}",
                      flush=True)
                if i % 20 == 0 and targets_met(print_counts(OUT), args):
                    print("Targets reached, stopping.")
                    break
                if i % 50 == 0:
                    print("  resting 30-60s", flush=True)
                    pause(30, 60)
        except Blocked as e:
            print(f"\nSTOP: {e}\nBlocked - report to user, do not try to bypass.", flush=True)
            browser.close()
            sys.exit(2)
        browser.close()

    print("\nFinal counts (whole file):")
    print_counts(OUT)
    if args.print_sample and new_rows:
        random.seed(42)
        sample = random.sample(new_rows, min(args.print_sample, len(new_rows)))
        print(f"\n{len(sample)} sample rows from this run:")
        print(pd.DataFrame(sample)[["category", "star", "verified_purchase", "used_for", "text"]]
              .to_string(max_colwidth=90))


if __name__ == "__main__":
    main()
