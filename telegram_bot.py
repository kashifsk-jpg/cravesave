"""
CraveSave Telegram Auto-Poster Bot
==================================
THE minimal-effort tool. You DM the bot one line, it posts a polished
deal to your channel — tagged link, QR, caption, disclosure, done.

HOW YOU USE IT (your entire daily effort):
  Paste into the bot's private chat, pipe-separated (only the link is required):

    https://amazon.ae/dp/B0CHX1W1XY | Anker PowerCore 20000 | 149 | 229 | Lowest in 60 days

  Fields:  LINK | TITLE | PRICE | OLD_PRICE | NOTE
  Bare link also works:  https://amazon.ae/dp/B0CHX1W1XY

SETUP (once):
  1. Telegram → @BotFather → /newbot → copy the token.
  2. Add the bot as ADMIN to your channel (so it can post).
  3. Get your channel id: forward any channel msg to @userinfobot, or use
     @YourChannelUsername.
  4. Get YOUR user id (so only you can trigger posts): DM @userinfobot.
  5. Fill the env vars below and run:  python3 telegram_bot.py

No paid services. Runs on any laptop, Raspberry Pi, or free cloud box.
"""

import os
import time
import requests

from cravesave_links import build_links, make_qr, telegram_caption

BOT_TOKEN  = os.environ["TG_BOT_TOKEN"]              # from @BotFather
CHANNEL    = os.environ["TG_CHANNEL"]               # e.g. "@CraveSaveAD" or "-100123..."
OWNER_ID   = int(os.environ.get("TG_OWNER_ID", "0")) # only this user can post
SEND_QR    = os.environ.get("SEND_QR", "1") == "1"   # attach a QR image too

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def parse_input(text: str) -> dict | None:
    """Turn 'LINK | TITLE | PRICE | OLD | NOTE' into a deal dict."""
    parts = [p.strip() for p in text.split("|")]
    link = parts[0]
    if "amazon" not in link and "amzn" not in link and not link.startswith("B"):
        return None
    deal = {"link": link, "title": "Today's Amazon Deal"}
    if len(parts) > 1 and parts[1]:
        deal["title"] = parts[1]
    if len(parts) > 2 and parts[2]:
        deal["price"] = parts[2]
    if len(parts) > 3 and parts[3]:
        deal["old_price"] = parts[3]
    if len(parts) > 4 and parts[4]:
        deal["note"] = parts[4]
    return deal


def post_deal(deal: dict) -> str:
    links = build_links(deal["link"])
    caption = telegram_caption(deal, links)

    if SEND_QR:
        qr_path = make_qr(links["web"], f"/tmp/qr_{links['asin']}.png")
        with open(qr_path, "rb") as f:
            r = requests.post(f"{API}/sendPhoto", data={
                "chat_id": CHANNEL,
                "caption": caption,
                "parse_mode": "Markdown",
            }, files={"photo": f})
    else:
        r = requests.post(f"{API}/sendMessage", data={
            "chat_id": CHANNEL,
            "text": caption,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        })
    r.raise_for_status()
    return links["asin"]


def reply(chat_id: int, text: str):
    requests.post(f"{API}/sendMessage", data={"chat_id": chat_id, "text": text})


def main():
    print("CraveSave bot running. Paste an Amazon link in your bot DM.")
    offset = None
    while True:
        try:
            resp = requests.get(f"{API}/getUpdates",
                                params={"timeout": 50, "offset": offset},
                                timeout=60).json()
            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message") or {}
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                user_id = msg.get("from", {}).get("id")

                if not text:
                    continue
                if OWNER_ID and user_id != OWNER_ID:
                    reply(chat_id, "Not authorised to post.")
                    continue
                if text.startswith("/"):
                    reply(chat_id, "Paste:  LINK | TITLE | PRICE | OLD | NOTE")
                    continue

                deal = parse_input(text)
                if not deal:
                    reply(chat_id, "That doesn't look like an Amazon link.")
                    continue
                try:
                    asin = post_deal(deal)
                    reply(chat_id, f"✅ Posted to channel (ASIN {asin}).")
                except Exception as e:
                    reply(chat_id, f"⚠️ Failed: {e}")
        except Exception as e:
            print("loop error:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
