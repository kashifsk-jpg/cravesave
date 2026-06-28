"""
CraveSave Batch Generator
=========================
Fill deals.csv once → this script produces EVERYTHING for every channel:

  • Posts each deal to your Telegram channel  (if --post)
  • Writes whatsapp_captions.txt   (copy-paste into WhatsApp)
  • Writes website_cards.html      (drop into your Netlify single-file site)
  • Saves a QR png per deal        (qr/ folder)

deals.csv columns:  link,title,price,old_price,note

Run:
  python3 batch_post.py            # generate files only (safe, no posting)
  python3 batch_post.py --post     # also auto-post to Telegram
"""

import csv
import os
import sys
import time

import requests

from cravesave_links import (build_links, make_qr,
                             telegram_caption, whatsapp_caption,
                             facebook_post)

BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
CHANNEL   = os.environ.get("TG_CHANNEL", "")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ─── For the consolidated Facebook post ──────────────────────────────────
# Edit these once (your live Noon deal + where people can follow you).
FB_EXTRAS = {
    "noon_code": "ZOQJN",
    "noon_link": "https://s.noon.com/AUpJ2MynLlQ",
    "telegram":  os.environ.get("FB_TELEGRAM", "https://t.me/YourChannel"),
    "whatsapp":  os.environ.get("FB_WHATSAPP", "https://chat.whatsapp.com/YourInvite"),
}
# ─────────────────────────────────────────────────────────────────────────

CARD_TEMPLATE = """  <div class="deal-card">
    <span class="deal-app">Amazon.ae</span>
    <h3>{title}</h3>
    <p class="price">AED {price} {old}</p>
    <p class="note">{note}</p>
    <a class="cta" href="{web}" target="_blank" rel="nofollow sponsored">Grab it →</a>
  </div>"""


def post_to_telegram(caption: str, qr_path: str):
    with open(qr_path, "rb") as f:
        r = requests.post(f"{API}/sendPhoto", data={
            "chat_id": CHANNEL, "caption": caption, "parse_mode": "Markdown",
        }, files={"photo": f})
    r.raise_for_status()


def main():
    do_post = "--post" in sys.argv
    os.makedirs("qr", exist_ok=True)

    wa_blocks, html_cards, fb_deals = [], [], []

    with open("deals.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    skipped = 0
    for row in rows:
        if not row.get("link"):
            continue
        deal = {k: (row.get(k) or "").strip() for k in
                ("title", "price", "old_price", "note")}
        deal["link"] = row["link"].strip()
        if not deal["title"]:
            deal["title"] = "Amazon Deal"

        try:
            links = build_links(deal["link"])
        except ValueError as e:
            skipped += 1
            print(f"  SKIPPED bad row ({deal['title']}): {e}")
            continue
        qr_path = make_qr(links["web"], f"qr/{links['asin']}.png")

        # WhatsApp block
        wa_blocks.append(whatsapp_caption(deal, links))

        # Facebook (collected, combined into one post at the end)
        fb_deals.append((deal, links))

        # Website card
        old = f'<s>AED {deal["old_price"]}</s>' if deal.get("old_price") else ""
        html_cards.append(CARD_TEMPLATE.format(
            title=deal["title"], price=deal.get("price", ""),
            old=old, note=deal.get("note", ""), web=links["web"]))

        # Telegram
        if do_post:
            try:
                post_to_telegram(telegram_caption(deal, links), qr_path)
                print(f"posted {links['asin']}")
                time.sleep(3)   # be gentle with Telegram rate limits
            except Exception as e:
                print(f"FAILED {links['asin']}: {e}")

    with open("whatsapp_captions.txt", "w", encoding="utf-8") as f:
        f.write("\n\n———————————————\n\n".join(wa_blocks))
    with open("website_cards.html", "w", encoding="utf-8") as f:
        f.write("\n".join(html_cards))
    with open("facebook_post.txt", "w", encoding="utf-8") as f:
        f.write(facebook_post(fb_deals, FB_EXTRAS))

    print(f"\nDone. {len(rows)} deals → whatsapp_captions.txt, "
          f"website_cards.html, facebook_post.txt, qr/*.png"
          + (f"  ({skipped} bad row(s) skipped)" if skipped else "")
          + ("  (and posted to Telegram)" if do_post else ""))


if __name__ == "__main__":
    main()
