"""
TrustMRR Scraper (v4 - Stealth + Infinite Scroll)
---------------------------------------------------
- Playwright stealth mode: Cloudflare bypass
- Infinite scroll: tüm kartları yükler
- Güncel selektörler: Revenue(30d), Asking Price, Multiple, Growth
"""
import sys, json, os, re, time
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://trustmrr.com"
APPS_URL = f"{BASE_URL}/acquire"
OUTPUT   = os.path.join(os.path.dirname(__file__), "..", "data", "apps_raw.json")

# Keyword → kategori eşleştirmesi
CATEGORY_KEYWORDS = {
    "video": "video-generation",
    "image": "image-generation",
    "logo": "image-generation",
    "photo": "image-generation",
    "audio": "audio-generation",
    "voice": "audio-generation",
    "music": "audio-generation",
    "code": "code-generation",
    "developer": "developer-tools",
    "github": "developer-tools",
    "api": "developer-tools",
    "marketing": "marketing",
    "seo": "marketing",
    "email": "marketing",
    "lead": "sales",
    "crm": "sales",
    "sales": "sales",
    "analytics": "analytics",
    "data": "analytics",
    "dashboard": "analytics",
    "pdf": "document-ai",
    "document": "document-ai",
    "text": "text-generation",
    "writing": "text-generation",
    "content": "text-generation",
    "chat": "chatbot",
    "bot": "chatbot",
    "customer": "customer-support",
    "support": "customer-support",
    "translation": "translation",
    "translate": "translation",
    "language": "translation",
    "invoice": "fintech",
    "payment": "fintech",
    "finance": "fintech",
    "accounting": "fintech",
    "health": "health",
    "fitness": "health",
    "medical": "health",
    "saas": "saas",
    "subscription": "saas",
    "automation": "automation",
    "workflow": "automation",
    "dropshipping": "ecommerce",
    "ecommerce": "ecommerce",
    "shop": "ecommerce",
}


def infer_category(text: str) -> str:
    """Açıklama metninden kategori çıkar."""
    text_lower = text.lower()
    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword in text_lower:
            return category
    return "saas"  # varsayılan


def clean_mrr(text: str) -> str:
    """$4.2k → $4,200  |  $72k → $72,000  |  $1.1M → $1,100,000"""
    if not text:
        return ""
    text = text.strip()
    match = re.search(r"\$?([\d,.]+)([KkMm]?)", text)
    if not match:
        return text
    num, suffix = match.groups()
    num = num.replace(",", "")
    try:
        val = float(num)
        if suffix.upper() == "K":
            val *= 1_000
        elif suffix.upper() == "M":
            val *= 1_000_000
        return f"${int(val):,}"
    except ValueError:
        return text


def parse_html(html: str) -> list[dict]:
    """Sayfanın HTML'ini parse et, startup kartlarını çıkar."""
    soup = BeautifulSoup(html, "html.parser")
    apps = []

    cards = soup.select("a[href*='/startup/']")
    print(f"  [Parser] {len(cards)} kart bulundu")

    for card in cards:
        # --- İsim ---
        name_tag = card.find("h3")
        name = name_tag.get_text(strip=True) if name_tag else ""
        if not name:
            continue

        # --- Kategori (badge span) ---
        badge = card.select_one("span.rounded-full")
        site_category = badge.get_text(strip=True) if badge else ""

        # --- Açıklama ---
        desc_tag = card.select_one("p.line-clamp-2")
        if not desc_tag:
            # Fallback: ilk p tag (h3'den sonraki)
            desc_tag = card.find("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # --- Metrikler (grid-cols-3 alanı) ---
        metrics_grid = card.select_one("div.grid-cols-3")

        revenue_text = ""
        asking_price_text = ""
        multiple_text = ""
        growth_text = ""

        if metrics_grid:
            cols = metrics_grid.find_all("div", recursive=False)
            # Kolon 1: Revenue (30d)
            if len(cols) >= 1:
                rev_val = cols[0].select_one("p.font-bold, p.font-mono, span.font-bold")
                if rev_val:
                    revenue_text = rev_val.get_text(strip=True)
                # Growth (span içinde ↑/↓ yüzde)
                growth_span = cols[0].find("span", class_=lambda c: c and ("text-green" in c or "text-red" in c))
                if not growth_span:
                    growth_span = cols[0].find("span")
                if growth_span:
                    growth_text = growth_span.get_text(strip=True)

            # Kolon 2: Asking Price
            if len(cols) >= 2:
                price_val = cols[1].select_one("p.font-bold, p.font-mono, span.font-bold")
                if price_val:
                    asking_price_text = price_val.get_text(strip=True)

            # Kolon 3: Multiple
            if len(cols) >= 3:
                mult_val = cols[2].select_one("p.font-bold, p.font-mono, span.font-bold")
                if mult_val:
                    multiple_text = mult_val.get_text(strip=True)

        # Fallback: grid yoksa, kartın tüm metninden MRR çıkar
        if not revenue_text:
            card_text = card.get_text(" ", strip=True)
            mrr_match = re.search(r'\$([\d,.]+)\s*([KkMm]?)(?:\s*/\s*(?:mo|month))?', card_text)
            if mrr_match:
                revenue_text = mrr_match.group(0).strip()

        # --- Kategori inferansı (site kategorisi yoksa) ---
        final_category = site_category if site_category else infer_category(name + " " + description)

        # --- URL ---
        href = card.get("href", "")
        full_url = href if href.startswith("http") else f"{BASE_URL}{href}"

        apps.append({
            "name":          name,
            "description":   description,
            "mrr":           clean_mrr(revenue_text),
            "mrr_raw":       revenue_text,
            "asking_price":  clean_mrr(asking_price_text),
            "multiple":      multiple_text,
            "growth":        growth_text,
            "category":      final_category,
            "pricing":       "",
            "url":           full_url,
            "source":        "trustmrr",
            "scraped_at":    datetime.now().isoformat(),
        })

    return apps


def scroll_and_collect(page, max_scrolls: int = 80, scroll_pause: float = 2.0) -> str:
    """
    Sayfayı scroll ederek tüm kartları yükle.
    Yeni kart gelmeyi bırakınca dur.
    """
    prev_count = 0
    no_change_count = 0

    for i in range(1, max_scrolls + 1):
        # Mevcut kart sayısı
        count = page.evaluate("document.querySelectorAll('a[href*=\"/startup/\"]').length")

        if count == prev_count:
            no_change_count += 1
            if no_change_count >= 4:
                print(f"  [Scroll] {i}. scroll — kart sayısı değişmedi ({count}), durduruluyor.")
                break
        else:
            no_change_count = 0
            print(f"  [Scroll] {i}. scroll — {count} kart yüklendi")

        prev_count = count

        # Sayfanın en altına scroll et
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(scroll_pause)

    final_count = page.evaluate("document.querySelectorAll('a[href*=\"/startup/\"]').length")
    print(f"  [Scroll] Tamamlandı — toplam {final_count} kart DOM'da")
    return page.content()


def scrape_trustmrr(max_scrolls: int = 80) -> list[dict]:
    print("[TrustMRR] Scraping başlıyor (v4 - Stealth + Scroll)...")
    all_apps = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        page = context.new_page()

        print(f"[TrustMRR] Sayfa açılıyor: {APPS_URL}")
        try:
            page.goto(APPS_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  [ERR] goto hatası: {e}")
            browser.close()
            return []

        # Sayfanın tam yüklenmesini bekle
        time.sleep(5)

        # Kartların yüklenmesini bekle
        try:
            page.wait_for_selector("a[href*='/startup/']", timeout=15000)
            print("[TrustMRR] ✅ Kartlar yüklendi")
        except Exception:
            print("[TrustMRR] ⚠️  Kart selektörü bulunamadı, HTML kaydediliyor...")
            debug_path = os.path.join(os.path.dirname(__file__), "..", "trustmrr_debug.html")
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"  Debug HTML: {debug_path}")
            browser.close()
            return []

        # Pop-up / newsletter kapatma (varsa)
        try:
            close_btn = page.locator("button:has-text('×'), button:has-text('Close'), [aria-label='Close']")
            if close_btn.count() > 0:
                close_btn.first.click()
                time.sleep(1)
        except Exception:
            pass

        # Infinite scroll ile tüm kartları yükle
        html = scroll_and_collect(page, max_scrolls=max_scrolls)

        # HTML'i parse et
        all_apps = parse_html(html)

        browser.close()

    # Duplicate temizle (isim bazlı)
    seen, unique = set(), []
    for a in all_apps:
        key = a["name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    print(f"[TrustMRR] ✅ Toplam {len(unique)} benzersiz startup")
    return unique


def clean_and_save(apps: list[dict]):
    """Eski trustmrr datasını temizle ve yenisiyle güncelle."""
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    existing = []
    if os.path.exists(OUTPUT):
        with open(OUTPUT, "r", encoding="utf-8") as f:
            existing = json.load(f)
        # Eski trustmrr + mock datayı temizle
        before = len(existing)
        existing = [a for a in existing if a.get("source") not in ("trustmrr", "trustmrr_mock")]
        print(f"[Temizle] {before} → {len(existing)} (trustmrr+mock silindi)")

    merged = existing + apps
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"[TrustMRR] 💾 Toplam: {len(merged)} uygulama → {OUTPUT}")


if __name__ == "__main__":
    apps = scrape_trustmrr(max_scrolls=80)
    clean_and_save(apps)

    # Özet göster
    print(f"\n--- İLK 10 STARTUP ÖNİZLEME ---")
    for a in apps[:10]:
        print(f"  {a['name']!r:30} | mrr={a['mrr']!r:12} | price={a['asking_price']!r:12} | mult={a['multiple']!r:6} | growth={a['growth']!r:8} | cat={a['category']!r}")
        print(f"    {a['description'][:80]!r}")
