"""
CraveSave Abu Dhabi - Link Engine
==================================
The core of the automation. Give it ANY Amazon.ae product URL (or ASIN)
and it returns everything you need to post a deal: tagged link, mobile
app deep links, an add-to-cart link (90-day window), a QR code, and
ready-to-paste Telegram + WhatsApp captions.

You only ever touch ONE thing: AFFILIATE_TAG below (paste your exact tag
from the Amazon.ae Associates dashboard, e.g. "cravesaveae-21").

Everything else is automatic.
"""

import os
import re
import urllib.parse

# ─── THE ONLY THING YOU MUST SET ─────────────────────────────────────────
AFFILIATE_TAG = os.environ.get("AMZN_TAG", "YOURTAG-21")   # <-- paste your real tag
MARKETPLACE   = "www.amazon.ae"                            # UAE storefront
ANDROID_PKG   = "com.amazon.mShop.android.shopping"        # Amazon app package
# ─────────────────────────────────────────────────────────────────────────


def extract_asin(url_or_asin: str) -> str | None:
    """Pull the 10-char ASIN out of any Amazon URL, or accept a bare ASIN."""
    s = url_or_asin.strip()

    # Already a bare ASIN?
    if re.fullmatch(r"[A-Z0-9]{10}", s):
        return s

    # Common URL shapes: /dp/ASIN, /gp/product/ASIN, /product/ASIN, /ASIN/
    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
        r"/gp/aws/cart/add\.html.*?ASIN\.1=([A-Z0-9]{10})",
        r"/([A-Z0-9]{10})(?:[/?]|$)",
    ]
    for p in patterns:
        m = re.search(p, s)
        if m:
            return m.group(1)
    return None


def resolve_short_link(url: str) -> str:
    """Follow an amzn.to / shortened link to its real URL (needs internet)."""
    try:
        import requests
        r = requests.head(url, allow_redirects=True, timeout=8,
                          headers={"User-Agent": "Mozilla/5.0"})
        return r.url
    except Exception:
        return url


def build_links(url_or_asin: str) -> dict:
    """Return every link variant you'd ever need for one product."""
    raw = url_or_asin.strip()
    if "amzn.to" in raw or "/short" in raw:           # expand short links first
        raw = resolve_short_link(raw)

    asin = extract_asin(raw)
    if not asin:
        raise ValueError(f"Could not find an ASIN in: {url_or_asin}")

    tag = AFFILIATE_TAG

    # 1. Canonical tagged web link.
    #    On iPhone (opened in Safari) this IS the universal link that
    #    auto-opens the Amazon app carrying your tag. Share THIS in chats.
    web = f"https://{MARKETPLACE}/dp/{asin}?tag={tag}"

    # 2. Android "intent" link — opens the app directly. Use ONLY in HTML
    #    buttons on your own website, never in plain chat text.
    intent = (
        f"intent://{MARKETPLACE}/dp/{asin}?tag={tag}"
        f"#Intent;scheme=https;package={ANDROID_PKG};"
        f"S.browser_fallback_url={urllib.parse.quote(web, safe='')};end"
    )

    # 3. Amazon app scheme — alternative app-opener (test on your devices).
    app_scheme = f"com.amazon.mobile.shopping.web://{MARKETPLACE}/dp/{asin}?tag={tag}"

    # 4. Add-to-cart link → if they add now, your window stretches to 90 days.
    #    EXPERIMENTAL on .ae: test before relying on it.
    add_to_cart = (
        f"https://{MARKETPLACE}/gp/aws/cart/add.html?"
        f"AssociateTag={tag}&ASIN.1={asin}&Quantity.1=1"
    )

    return {
        "asin": asin,
        "web": web,                 # ← share this one in Telegram/WhatsApp
        "intent": intent,           # ← website HTML buttons only
        "app_scheme": app_scheme,   # ← alternative app-opener
        "add_to_cart": add_to_cart, # ← "add now, buy later" 90-day play
    }


def make_qr(link: str, filename: str) -> str:
    """Generate a branded-ish QR PNG that opens the app+tag when scanned."""
    import qrcode
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=2)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    img.save(filename)
    return filename


# ─── Caption builders (your post templates, auto-filled) ─────────────────
def telegram_caption(deal: dict, links: dict) -> str:
    """deal keys: title, price, old_price, app, note (all optional except title)."""
    lines = [f"🔥 *{deal['title']}*", ""]
    if deal.get("price"):
        if deal.get("old_price"):
            lines.append(f"💸 *AED {deal['price']}*  ~~AED {deal['old_price']}~~")
        else:
            lines.append(f"💸 *AED {deal['price']}*")
    if deal.get("note"):
        lines.append(f"📝 {deal['note']}")
    lines += [
        "",
        f"🛒 [Grab it on Amazon]({links['web']})",
        "",
        "_Tip: tap *Add to Cart* — even if you buy later this week, the price is locked for you._",
        "",
        "🔗 Affiliate link · we earn a small commission at no extra cost to you.",
    ]
    return "\n".join(lines)


def whatsapp_caption(deal: dict, links: dict) -> str:
    """WhatsApp uses *bold* and plain links (no markdown link syntax)."""
    lines = [f"🔥 *{deal['title']}*"]
    if deal.get("price"):
        if deal.get("old_price"):
            lines.append(f"💸 AED {deal['price']} (was AED {deal['old_price']})")
        else:
            lines.append(f"💸 AED {deal['price']}")
    if deal.get("note"):
        lines.append(f"📝 {deal['note']}")
    lines += [
        "",
        f"🛒 {links['web']}",
        "",
        "Tip: tap Add to Cart now — price stays locked even if you buy later.",
        "",
        "🔗 Affiliate link · we earn a small commission at no extra cost to you.",
    ]
    return "\n".join(lines)


# ─── Quick self-test when run directly ───────────────────────────────────
if __name__ == "__main__":
    samples = [
        "https://www.amazon.ae/Apple-iPhone-15-128-GB/dp/B0CHX1W1XY/ref=sr_1_1?keywords=iphone",
        "https://www.amazon.ae/dp/B09G9FPHY6",
        "B07XJ8C8F5",
    ]
    for s in samples:
        print("\nINPUT:", s)
        L = build_links(s)
        for k, v in L.items():
            print(f"  {k:12}: {v}")

    print("\n--- Sample Telegram caption ---")
    deal = {"title": "Anker PowerCore 20000mAh", "price": "149",
            "old_price": "229", "note": "Lowest price in 60 days"}
    L = build_links("B07XJ8C8F5")
    print(telegram_caption(deal, L))
