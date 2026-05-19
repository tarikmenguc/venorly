"""
API Pricing Scraper
AI sağlayıcılarının güncel fiyatlarını Tavily ile arar.
Eksik fiyat durumunda null döner — LLM tahmini kullanılmaz.
Çıktı: data/api_pricing.json
"""

import json
import os
from datetime import datetime, timezone

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "api_pricing.json")

# Aranacak sağlayıcılar ve modeller
PROVIDERS = [
    {"provider": "openai",    "model": "gpt-4o",          "query": "OpenAI GPT-4o API pricing per token USD 2025"},
    {"provider": "openai",    "model": "gpt-4o-mini",      "query": "OpenAI GPT-4o-mini API pricing per token USD 2025"},
    {"provider": "openai",    "model": "whisper",          "query": "OpenAI Whisper API pricing per minute USD 2025"},
    {"provider": "anthropic", "model": "claude-3-5-sonnet","query": "Anthropic Claude 3.5 Sonnet API pricing per token USD 2025"},
    {"provider": "anthropic", "model": "claude-3-haiku",   "query": "Anthropic Claude 3 Haiku API pricing per token USD 2025"},
    {"provider": "replicate", "model": "flux-pro",         "query": "Replicate Flux Pro API pricing per image USD 2025"},
    {"provider": "heygen",    "model": "video-generation", "query": "HeyGen API video generation pricing per credit USD 2025"},
    {"provider": "elevenlabs","model": "tts",              "query": "ElevenLabs TTS API pricing per character USD 2025"},
    {"provider": "fal",       "model": "fast-sdxl",        "query": "fal.ai fast-sdxl API pricing per image USD 2025"},
]


def search_pricing(query: str) -> str | None:
    """Tavily ile fiyat snippet'i çeker. Bulamazsa None döner."""
    try:
        from lib.tavily_client import get_tavily_client
        client = get_tavily_client()
        results = client.search(query, max_results=3, search_depth="basic")
        snippets = [r.get("content", "") for r in results.get("results", []) if r.get("content")]
        return " | ".join(snippets[:2])[:500] if snippets else None
    except Exception as e:
        print(f"[APIPricing] Tavily hatası: {e}")
        return None


def extract_price(snippet: str | None, provider: str, model: str) -> dict:
    """
    Snippet'ten fiyat çıkarır. Yapılandırılmış veri döner.
    Kesin fiyat bulunamazsa price_usd=None — uydurma yapılmaz.
    """
    if not snippet:
        return {"price_usd": None, "unit": None, "note": "veri bulunamadı"}

    # Basit heuristik: "$0.XXX" kalıbını ara
    import re
    matches = re.findall(r"\$[\d,]+\.?\d*\s*(?:per|/)\s*\S+", snippet, re.IGNORECASE)
    price_text = matches[0] if matches else None

    return {
        "price_usd": price_text,
        "unit": None,
        "note": snippet[:200] if not price_text else None,
    }


def run():
    print("[APIPricing] Fiyat taraması başlıyor...")
    scraped_at = datetime.now(timezone.utc).isoformat()
    results = []

    for item in PROVIDERS:
        snippet = search_pricing(item["query"])
        price_data = extract_price(snippet, item["provider"], item["model"])
        entry = {
            "provider":  item["provider"],
            "model":     item["model"],
            "price_usd": price_data["price_usd"],
            "unit":      price_data["unit"],
            "note":      price_data["note"],
            "scraped_at": scraped_at,
        }
        results.append(entry)
        status = entry["price_usd"] or "bulunamadı"
        print(f"  {item['provider']}/{item['model']}: {status}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    found = sum(1 for r in results if r["price_usd"])
    print(f"[APIPricing] Tamamlandı: {found}/{len(results)} fiyat bulundu → {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
