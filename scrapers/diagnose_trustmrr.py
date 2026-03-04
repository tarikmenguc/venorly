"""
TrustMRR kart yapısını Playwright locator ile incele.
İlk 2 kartın HTML'ini yazdırır → doğru selector'ı bulabiliriz.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

URL = "https://trustmrr.com/acquire"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    print(f"Sayfa açılıyor: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)

    try:
        page.wait_for_selector("a[href*='/startup/']", timeout=10000)
        print("Selector bulundu!")
    except Exception:
        print("Selector timeout - devam ediyorum")

    cards = page.locator("a[href*='/startup/']").all()
    print(f"\nToplam kart: {len(cards)}")

    for i, card in enumerate(cards[:3]):
        print(f"\n{'='*60}")
        print(f"KART {i+1} — href: {card.get_attribute('href')}")
        print(f"{'='*60}")
        print(card.inner_html()[:1500])

    # Tam sayfayı kaydet
    with open("data/trustmrr_snapshot.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("\n[Snapshot kaydedildi: data/trustmrr_snapshot.html]")
    browser.close()
