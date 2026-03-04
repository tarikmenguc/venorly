"""
fal.ai Model Scraper
fal.ai model listesi sayfasından AI modelleri çeker.
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

# fal.ai URL path → kategori haritası
PATH_CATEGORY_MAP = {
    "text-to-video": "video-generation",
    "image-to-video": "video-generation",
    "text-to-image": "image-generation",
    "image-to-image": "image-editing",
    "text-to-speech": "text-to-speech",
    "text-to-audio": "audio-processing",
    "training": "model-training",
}

# Keyword → kategori
KEYWORD_CATEGORY_MAP = {
    "video": "video-generation",
    "image gen": "image-generation",
    "image-to-video": "video-generation",
    "text-to-video": "video-generation",
    "text-to-image": "image-generation",
    "speech": "text-to-speech",
    "tts": "text-to-speech",
    "voice": "text-to-speech",
    "audio": "audio-processing",
    "music": "music-generation",
    "upscale": "image-processing",
    "edit": "image-editing",
    "avatar": "avatar-generation",
    "3d": "3d-generation",
    "lora": "model-training",
    "train": "model-training",
}


def infer_category_from_text(name: str, description: str, tags: list[str] = None) -> str:
    """Model adı, açıklama ve tag'lerden kategori çıkar."""
    combined = (name + " " + description + " " + " ".join(tags or [])).lower()

    # Önce path tabanlı eşleştirme
    for key, cat in PATH_CATEGORY_MAP.items():
        if key in combined:
            return cat

    # Sonra keyword tabanlı
    for keyword, category in KEYWORD_CATEGORY_MAP.items():
        if keyword in combined:
            return category

    return "ai-model"


def scrape_fal_models() -> list[dict]:
    """fal.ai model sayfasını parse eder."""
    print("[fal.ai] Model listesi çekiliyor...")
    all_models = []

    # Ana sayfa + kategorilere göre sayfalar
    urls = [
        ("https://fal.ai/models", "all"),
        ("https://fal.ai/explore/recently-added", "recent"),
    ]

    seen_ids = set()

    for url, label in urls:
        print(f"[fal.ai] Sayfa: {url} ({label})")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[fal.ai] ❌ HTTP hatası: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # Model linklerini bul: /models/fal-ai/... veya /models/username/...
        model_links = soup.find_all("a", href=re.compile(r"/models/[^/]+/[^/]+"))

        for link in model_links:
            href = link.get("href", "")

            # Model ID çıkar: fal-ai/nano-banana-2 gibi
            match = re.search(r"/models/([^/]+/[^/?#]+)", href)
            if not match:
                continue

            model_path = match.group(1)

            # Duplicate kontrolü
            if model_path in seen_ids:
                continue
            seen_ids.add(model_path)

            # İsim ve açıklama çıkar
            text_parts = link.get_text(" ", strip=True).split("\n")
            text = link.get_text(" ", strip=True)

            # Model adını belirle
            name = model_path.split("/")[-1]
            author = model_path.split("/")[0]

            # İçerdeki h1/h2/h3 veya strong tag'den isim bul
            title_tag = link.find(["h1", "h2", "h3", "strong"])
            if title_tag:
                name = title_tag.get_text(strip=True)

            # Açıklama — link içindeki p tag veya başlıktan sonraki metin
            desc_tag = link.find("p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            if not description:
                # Fallback: tüm metin (bazen model adı)
                description = text[:200] if text else ""

            # Tag'leri çıkar (varsa span elementleri)
            tags = []
            for span in link.find_all("span"):
                tag_text = span.get_text(strip=True).lower()
                if tag_text and len(tag_text) < 30:
                    tags.append(tag_text)

            # Kategori inferansı
            category = infer_category_from_text(name, description, tags)

            # "api" sayfalarını ve docs linklerini atla
            if "/api" in href or "/docs" in href:
                continue

            all_models.append({
                "model_id": model_path,
                "name": name,
                "author": author,
                "description": description[:200],
                "category": category,
                "tags": tags[:5],
                "downloads": 0,  # fal.ai run count göstermiyor public'te
                "likes": 0,
                "url": f"https://fal.ai/models/{model_path}",
                "source": "fal",
                "scraped_at": datetime.now().isoformat(),
            })

        time.sleep(1)

    print(f"[fal.ai] ✅ {len(all_models)} model bulundu")
    return all_models


def save(models: list[dict]):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing = [m for m in existing if m.get("source") != "fal"]

    merged = existing + models
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"[fal.ai] 💾 {OUTPUT_FILE} güncellendi. Toplam: {len(merged)} model.")


if __name__ == "__main__":
    models = scrape_fal_models()
    save(models)

    print(f"\n--- İLK 10 MODEL ---")
    for m in models[:10]:
        print(f"  {m['name']:35} | cat={m['category']:20} | {m['author']}")
        print(f"    {m['description'][:80]}")
