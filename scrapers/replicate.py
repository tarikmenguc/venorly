"""
Replicate.com Model Scraper
Explore sayfasından trending/featured modelleri çeker.
API anahtarı gerektirmez — public sayfa parse edilir.
Çıktı: data/models_raw.json'a eklenir
"""

import json
import os
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "models_raw.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# Replicate URL → model kategorisi haritası
CATEGORY_INFERENCE = {
    "image": "image-generation",
    "video": "video-generation",
    "speech": "text-to-speech",
    "tts": "text-to-speech",
    "audio": "audio-processing",
    "music": "music-generation",
    "text": "text-generation",
    "code": "code-generation",
    "vision": "computer-vision",
    "3d": "3d-generation",
    "edit": "image-editing",
    "upscale": "image-processing",
}


def infer_category(name: str, description: str) -> str:
    """Model adı ve açıklamasından kategori çıkar."""
    combined = (name + " " + description).lower()
    for keyword, category in CATEGORY_INFERENCE.items():
        if keyword in combined:
            return category
    return "ai-model"


def parse_run_count(text: str) -> int:
    """'5M runs', '873.4K runs', '30.8K runs' → integer"""
    if not text:
        return 0
    match = re.search(r"([\d,.]+)\s*([KkMmBb]?)\s*runs?", text)
    if not match:
        return 0
    num, suffix = match.groups()
    num = float(num.replace(",", ""))
    multiplier = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}.get(suffix.lower(), 1)
    return int(num * multiplier)


def scrape_replicate_api() -> list[dict]:
    """Replicate API endpoint'inden modelleri çeker."""
    print("[Replicate] API endpoint deneniyor...")

    all_models = []
    url = "https://api.replicate.com/v1/models"
    params = {"sort": "run_count", "limit": 50}

    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for m in data.get("results", []):
                owner = m.get("owner", "")
                name = m.get("name", "")
                description = m.get("description", "")
                run_count = m.get("run_count", 0) or 0

                all_models.append({
                    "model_id": f"{owner}/{name}",
                    "name": name,
                    "author": owner,
                    "description": description[:200],
                    "category": infer_category(name, description),
                    "run_count": run_count,
                    "downloads": run_count,  # uyumluluk için
                    "likes": 0,
                    "url": f"https://replicate.com/{owner}/{name}",
                    "source": "replicate",
                    "scraped_at": datetime.now().isoformat(),
                })

            print(f"[Replicate] API: {len(all_models)} model bulundu")
            return all_models
        else:
            print(f"[Replicate] API yanıt: {resp.status_code}, HTML fallback'e geçiliyor...")
    except Exception as e:
        print(f"[Replicate] API hatası: {e}, HTML fallback'e geçiliyor...")

    return []


def scrape_replicate_html() -> list[dict]:
    """Replicate explore sayfasını HTML olarak parse eder."""
    print("[Replicate] HTML scraping başlıyor...")
    all_models = []

    urls = [
        "https://replicate.com/explore",
    ]

    for url in urls:
        print(f"[Replicate] Sayfa: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Replicate] ❌ HTTP hatası: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # Model kartlarını bul (link + description formatı)
        links = soup.find_all("a", href=re.compile(r"^/[^/]+/[^/]+$"))

        for link in links:
            href = link.get("href", "").strip("/")
            if "/" not in href or href.startswith("docs") or href.startswith("pricing"):
                continue

            parts = href.split("/")
            if len(parts) != 2:
                continue

            owner, name = parts
            text = link.get_text(" ", strip=True)
            description = ""
            run_count = 0

            # Açıklama ve run count'u metin içinden çıkar
            run_match = re.search(r"([\d,.]+[KkMm]?)\s*runs?", text)
            if run_match:
                run_count = parse_run_count(run_match.group(0))
                # Açıklama = run count'tan önceki metin (model adı çıkarılmış)
                desc_part = text[:run_match.start()].strip()
                # Model adını çıkar
                for prefix in [name, owner, f"{owner}/{name}"]:
                    desc_part = desc_part.replace(prefix, "").strip()
                description = desc_part[:200]

            if not run_count:
                continue  # Run count olmayan linkleri atla

            model_id = f"{owner}/{name}"

            # Tekrar kontrolü
            if any(m["model_id"] == model_id for m in all_models):
                continue

            all_models.append({
                "model_id": model_id,
                "name": name,
                "author": owner,
                "description": description,
                "category": infer_category(name, description),
                "run_count": run_count,
                "downloads": run_count,
                "likes": 0,
                "url": f"https://replicate.com/{model_id}",
                "source": "replicate",
                "scraped_at": datetime.now().isoformat(),
            })

        time.sleep(1)

    print(f"[Replicate] HTML: {len(all_models)} model bulundu")
    return all_models


def scrape_replicate() -> list[dict]:
    """Önce API dener, sonra HTML fallback."""
    models = scrape_replicate_api()
    if not models:
        models = scrape_replicate_html()
    if not models:
        print("[Replicate] ⚠️  Hiç model bulunamadı!")
    return models


def save(models: list[dict]):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing = [m for m in existing if m.get("source") != "replicate"]

    merged = existing + models
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"[Replicate] 💾 {OUTPUT_FILE} güncellendi. Toplam: {len(merged)} model.")


if __name__ == "__main__":
    models = scrape_replicate()
    save(models)

    print(f"\n--- İLK 5 MODEL ---")
    for m in models[:5]:
        print(f"  {m['name']:30} | runs={m['run_count']:>10,} | cat={m['category']}")
        print(f"    {m['description'][:80]}")
