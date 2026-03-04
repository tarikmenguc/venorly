"""
HuggingFace Trending Modeller Scraper
Resmi huggingface_hub SDK kullanır — bot tespiti yok.
Çıktı: data/models_raw.json (fal.py ve replicate.py ile birleştirilir)
"""

import json
import os
from datetime import datetime

from huggingface_hub import list_models

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "models_raw.json")

# Model kategorisi → pazar kategorisi eşleştirmesi
CATEGORY_MAP = {
    "text-to-image":        "image-generation",
    "text-to-video":        "video-generation",
    "image-to-video":       "video-generation",
    "text-to-speech":       "text-to-speech",
    "automatic-speech-recognition": "speech-to-text",
    "text-generation":      "text-generation",
    "text2text-generation": "text-generation",
    "image-to-text":        "image-to-text",
    "text-to-audio":        "music-generation",
    "audio-to-audio":       "audio-processing",
    "image-classification": "image-classification",
    "object-detection":     "computer-vision",
    "depth-estimation":     "computer-vision",
    "video-classification": "video-understanding",
    "feature-extraction":   "embedding",
    "fill-mask":            "text-generation",
    "token-classification": "text-processing",
    "translation":          "translation",
    "summarization":        "text-processing",
    "question-answering":   "text-processing",
    "zero-shot-classification": "classification",
}

INTERESTING_CATEGORIES = {
    "image-generation", "video-generation", "text-to-speech",
    "speech-to-text", "text-generation", "music-generation",
    "audio-processing", "image-to-text", "computer-vision",
}


def scrape_huggingface(limit: int = 200) -> list[dict]:
    print(f"[HuggingFace] Trending modeller çekiliyor (limit={limit})...")
    models = list(list_models(sort="downloads", direction=-1, limit=limit, fetch_config=False))

    result = []
    for m in models:
        raw_category = m.pipeline_tag or "unknown"
        mapped_category = CATEGORY_MAP.get(raw_category, raw_category)

        # Sadece ilgi çekici kategorileri al
        if mapped_category not in INTERESTING_CATEGORIES:
            continue

        result.append({
            "model_id":      m.modelId,
            "name":          m.modelId.split("/")[-1],
            "author":        m.modelId.split("/")[0] if "/" in m.modelId else "unknown",
            "category":      mapped_category,
            "raw_category":  raw_category,
            "downloads":     getattr(m, "downloads", 0) or 0,
            "likes":         getattr(m, "likes", 0) or 0,
            "last_modified": str(m.lastModified) if m.lastModified else "",
            "url":           f"https://huggingface.co/{m.modelId}",
            "source":        "huggingface",
            "scraped_at":    datetime.now().isoformat(),
        })

    print(f"[HuggingFace] ✅ {len(result)} ilgili model bulundu.")
    return result


def save(models: list[dict]):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Varsa mevcut dosyayla birleştir
    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        # HuggingFace kaynaklı olanları temizle, yenilerini ekle
        existing = [m for m in existing if m.get("source") != "huggingface"]

    merged = existing + models
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"[HuggingFace] 💾 {OUTPUT_FILE} güncellendi. Toplam: {len(merged)} model.")


if __name__ == "__main__":
    models = scrape_huggingface(limit=200)
    save(models)
