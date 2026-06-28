"""
CraveSave Deal Finder — your own price tracker for amazon.ae
============================================================
Keepa doesn't cover amazon.ae, so this is your private mini-Keepa.

It keeps a price history for the products you watch and tells you which
ones are ACTUALLY at a low right now — then auto-appends the real deals
straight into deals.csv, ready for batch_post.py.

WHY THIS MATTERS
  Your "lowest in 60 days" claims become TRUE (it counts the days for you),
  which protects both your credibility and your Amazon account.

HOW YOU USE IT (about 1 minute/day)
  1. Open watch.csv and fill in today's price for each product you're
     watching (asin, title, price). Add/remove rows anytime.
  2. Run:  python deal_finder.py
  3. It records today's prices, finds genuine drops, and appends them to
     deals.csv with a truthful note like "Lowest in 73 days · 28% off".
  4. Run batch_post.py as usual to post them.

UPGRADE PATH (fully automatic later)
  Once you've made 3 sales and unlock the Amazon Product Advertising API
  (PA-API, which DOES support UAE), fill in fetch_price_paapi() below and
  the price entry becomes automatic — no manual typing at all.
"""

import csv
import json
import os
import statistics
from datetime import date, datetime, timedelta

HISTORY_FILE = "price_history.json"
WATCH_FILE   = "watch.csv"
DEALS_FILE   = "deals.csv"

# ─── Tune what counts as a "deal" ────────────────────────────────────────
LOOKBACK_DAYS = 90      # window for "lowest in X days"
MIN_DROP_PCT  = 10      # only flag if at least this % below the recent high
# ─────────────────────────────────────────────────────────────────────────


def load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(hist: dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2)


def _recent(points: list, days: int) -> list:
    """Return [price, ...] for points within the lookback window."""
    cutoff = (datetime.now() - timedelta(days=days)).date()
    out = []
    for d, p in points:
        try:
            if datetime.strptime(d, "%Y-%m-%d").date() >= cutoff:
                out.append(p)
        except ValueError:
            continue
    return out


def evaluate(points: list, current: float) -> dict | None:
    """Decide if `current` is a genuine deal vs the recorded history.

    Returns a dict with old_price + note if it's a deal, else None.
    """
    recent = _recent(points, LOOKBACK_DAYS)
    if len(recent) < 2:            # not enough history to judge yet
        return None

    recent_high = max(recent)
    prior_low   = min(recent[:-1]) if len(recent) > 1 else recent_high
    if recent_high <= 0:
        return None

    drop_pct = round((recent_high - current) / recent_high * 100)
    is_low   = current <= min(recent)        # matches/beats the lowest seen

    # Only a genuine drop counts as a deal. A new low that's barely cheaper
    # (or a flat price) is not worth posting.
    if drop_pct < MIN_DROP_PCT:
        return None

    # how many days of tracking this low covers
    first_date = datetime.strptime(points[0][0], "%Y-%m-%d").date()
    days_tracked = (date.today() - first_date).days or len(recent)

    if is_low:
        note = f"Lowest in {days_tracked} days · {drop_pct}% off"
    else:
        note = f"{drop_pct}% below recent high"

    return {"old_price": recent_high, "note": note, "drop_pct": drop_pct}


def fetch_price_paapi(asin: str) -> float | None:
    """STUB for later. Once you have PA-API keys (UAE is supported),
    call GetItems here and return the current price. Until then, returns
    None and the tool uses your manually-entered watch.csv prices."""
    return None


def existing_deal_asins() -> set:
    """ASINs already queued in deals.csv, so we don't add duplicates."""
    asins = set()
    if not os.path.exists(DEALS_FILE):
        return asins
    with open(DEALS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            link = row.get("link", "")
            m = [p for p in link.split("/") if len(p) == 10 and p.isalnum()]
            if m:
                asins.add(m[-1])
    return asins


def append_to_deals(rows: list):
    """Append flagged deals to deals.csv (creating header if needed)."""
    file_exists = os.path.exists(DEALS_FILE)
    with open(DEALS_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["link", "title", "price", "old_price", "note"])
        for r in rows:
            w.writerow([r["link"], r["title"], r["price"],
                        r["old_price"], r["note"]])


def main():
    if not os.path.exists(WATCH_FILE):
        print(f"Create {WATCH_FILE} first (columns: asin,title,price).")
        return

    history = load_history()
    today = date.today().isoformat()
    deals_found = []
    already_queued = existing_deal_asins()

    with open(WATCH_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            asin  = (row.get("asin") or "").strip()
            title = (row.get("title") or "").strip()
            if not asin:
                continue

            # price: PA-API if available, else manual from watch.csv
            price = fetch_price_paapi(asin)
            if price is None:
                try:
                    price = float((row.get("price") or "").strip())
                except ValueError:
                    print(f"  skip {asin}: no price")
                    continue

            # record today's point (avoid duplicate same-day entries)
            pts = history.setdefault(asin, [])
            if not pts or pts[-1][0] != today:
                pts.append([today, price])
            else:
                pts[-1] = [today, price]

            verdict = evaluate(pts, price)
            if verdict and asin not in already_queued:
                deals_found.append({
                    "link": f"https://www.amazon.ae/dp/{asin}",
                    "title": title or "Amazon Deal",
                    "price": price,
                    "old_price": verdict["old_price"],
                    "note": verdict["note"],
                })
                print(f"  DEAL  {asin}  {title[:30]:30}  {verdict['note']}")
            elif verdict:
                print(f"  dupe  {asin}  {title[:30]:30}  (already in deals.csv)")
            else:
                print(f"  watch {asin}  {title[:30]:30}  (no deal / building history)")

    save_history(history)

    if deals_found:
        append_to_deals(deals_found)
        print(f"\n{len(deals_found)} real deal(s) added to {DEALS_FILE}. "
              f"Run batch_post.py to post them.")
    else:
        print("\nNo genuine deals today. History updated.")


if __name__ == "__main__":
    main()
