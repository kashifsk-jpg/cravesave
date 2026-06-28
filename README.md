# CraveSave Abu Dhabi — Affiliate Automation Kit

Turn one Amazon.ae link into a tagged, app-opening, QR-coded, captioned deal
across Telegram, WhatsApp, and your website — with almost no manual work.

## Files
| File | What it does |
|---|---|
| `cravesave_links.py` | Core engine. ASIN → tagged link + app deep links + QR + captions. |
| `telegram_bot.py` | **Easiest mode.** DM the bot a link, it posts the deal for you. |
| `batch_post.py` | Fill `deals.csv` → outputs Telegram posts + WhatsApp text + website cards + QRs. |
| `deals.csv` | The one file you edit. |
| `.github/workflows/daily-deals.yml` | Auto-posts at 11:15 & 17:30 Abu Dhabi, hands-off. |

## One-time setup
1. Install: `pip install requests qrcode pillow`
2. Get your Amazon.ae tag from Associates Central → set `AMZN_TAG`.
3. Telegram: `@BotFather` → `/newbot` → copy token. Add the bot as **admin**
   to your channel. Get your channel id + your own user id from `@userinfobot`.
4. Set environment variables:
   ```
   export AMZN_TAG="yourtag-21"
   export TG_BOT_TOKEN="123456:ABC..."
   export TG_CHANNEL="@YourChannel"
   export TG_OWNER_ID="your_numeric_id"
   ```

## Three ways to use it (pick your effort level)

**Mode A — Paste & post (lowest effort).** Run `python3 telegram_bot.py`,
then in the bot's DM paste:
`https://amazon.ae/dp/B0CHX1W1XY | Anker PowerCore | 99 | 159 | Bestseller`
It posts instantly.

**Mode B — Batch.** Fill `deals.csv`, run `python3 batch_post.py --post`.
All channels generated at once.

**Mode C — Fully automatic.** Push this folder to a GitHub repo, add
`AMZN_TAG`, `TG_BOT_TOKEN`, `TG_CHANNEL` as repo Secrets. Edit `deals.csv`
from the GitHub mobile app whenever; it posts at your two daily windows.

## Which link goes where
- **Telegram / WhatsApp chats →** the plain `web` link (auto-opens the app on
  iPhone, falls back to browser elsewhere). Never paste `intent://` links in chat.
- **Your website buttons →** you *can* use the `intent` link for guaranteed
  Android app-open; keep `web` as the iOS/desktop fallback (already built in).
- **Posters / WhatsApp status →** the QR png (scanning uses the real browser,
  so the app + your tag fire cleanly).

## Honest caveats
- **Test every link on a real iPhone AND Android**, from inside WhatsApp and
  Telegram, before trusting it. Deep-link behaviour shifts with app versions.
  If app-open ever fails, wrap the `web` link with Geniuslink/URLgenius.
- **WhatsApp has no clean free auto-post.** This kit generates ready WhatsApp
  text; you paste it (or use WhatsApp Channels manually). True automation needs
  the paid Meta Business API.
- **Add-to-cart link is experimental on .ae** — test before promoting it.
- Keep the affiliate disclosure on every post (already baked into captions).
- Finding the best-sellers themselves still needs you (or the Amazon Product
  Advertising API once you've made 3 qualifying sales). This kit automates
  everything *after* you've picked a product.
