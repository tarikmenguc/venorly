"""
google_trends.py — Google Trends Arama Hacmi Scraper (V8 SEO)
=============================================================
İki katmanlı fallback sistemi:
  Katman 1 (Birincil): pytrends — ücretsiz, API key gerektirmez
  Katman 2 (Fallback) : Tavily  — pytrends başarısız olursa

Sonuçlar dosya bazlı cache'lenir (TTL: 24 saat).
Kullanım:
    from scrapers.google_trends import get_search_volume
    data = get_search_volume(["ai video editor", "text to video"])
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

CACHE_DIR = os.path.join(BASE_DIR, "data", "seo_cache")
CACHE_TTL_HOURS = 24

# Rate limit: pytrends istekleri arası minimum bekleme
PYTRENDS_SLEEP = 5  # saniye


# ──────────────────────────────────────────────
# CACHE YÖNETİMİ
# ──────────────────────────────────────────────

def _cache_path(keyword: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.md5(keyword.lower().encode()).hexdigest()
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(CACHE_DIR, f"{key}_{date_str}.json")


def _load_cache(keyword: str) -> Optional[dict]:
    path = _cache_path(keyword)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # TTL kontrolü
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
            return None  # Süresi dolmuş
        return data
    except Exception:
        return None


def _save_cache(keyword: str, data: dict) -> None:
    path = _cache_path(keyword)
    data["cached_at"] = datetime.now().isoformat()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Trends] ⚠️  Cache yazma hatası: {e}")


# ──────────────────────────────────────────────
# KATMAN 1: pytrends
# ──────────────────────────────────────────────

def _fetch_via_pytrends(keyword: str) -> Optional[dict]:
    """pytrends ile Google Trends verisini çeker."""
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 30), retries=2, backoff_factor=0.5)
        pytrends.build_payload([keyword], timeframe="today 12-m", geo="")

        # interest_over_time
        df = pytrends.interest_over_time()
        if df is None or df.empty or keyword not in df.columns:
            return None

        values = df[keyword].tolist()
        if not values:
            return None

        avg_interest = round(sum(values) / len(values))

        # Son 3 ay ile ilk 3 ayı karşılaştır → trend yönü
        recent = values[-12:] if len(values) >= 12 else values
        older  = values[:12]  if len(values) >= 12 else []
        if older:
            recent_avg = sum(recent) / len(recent)
            older_avg  = sum(older) / len(older)
            if older_avg > 0:
                change_pct = round(((recent_avg - older_avg) / older_avg) * 100)
            else:
                change_pct = 0
            if change_pct >= 15:
                direction = "rising"
            elif change_pct <= -15:
                direction = "declining"
            else:
                direction = "stable"
        else:
            change_pct = 0
            direction = "stable"

        # Peak ay
        peak_idx  = values.index(max(values))
        peak_date = df.index[peak_idx].strftime("%Y-%m") if peak_idx < len(df.index) else ""

        # Monthly trend listesi (son 12 ay)
        monthly = [
            {"month": df.index[i].strftime("%Y-%m"), "value": int(v)}
            for i, v in enumerate(values[-12:])
        ]

        # Related queries
        try:
            time.sleep(PYTRENDS_SLEEP)
            related = pytrends.related_queries()
            kw_related = related.get(keyword, {})
            rising_df = kw_related.get("rising")
            top_df    = kw_related.get("top")

            rising_queries = rising_df["query"].tolist()[:5] if rising_df is not None and not rising_df.empty else []
            top_queries    = top_df["query"].tolist()[:5]    if top_df    is not None and not top_df.empty    else []
        except Exception:
            rising_queries = []
            top_queries    = []

        return {
            "keyword":         keyword,
            "interest_score":  avg_interest,
            "trend_direction": direction,
            "change_pct":      f"{'+' if change_pct >= 0 else ''}{change_pct}%",
            "peak_month":      peak_date,
            "related_rising":  rising_queries,
            "related_top":     top_queries,
            "monthly":         monthly,
            "source":          "pytrends",
            "cached":          False,
        }

    except ImportError:
        print("[Trends] ⚠️  pytrends kurulu değil. pip install pytrends")
        return None
    except Exception as e:
        print(f"[Trends] ⚠️  pytrends hatası: {e}")
        return None


# ──────────────────────────────────────────────
# KATMAN 2: Tavily Fallback
# ──────────────────────────────────────────────

def _fetch_via_tavily(keyword: str) -> Optional[dict]:
    """Tavily ile Google Trends verisi yaklaşımı (fallback)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from tavily import TavilyClient

        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            return None

        tavily = TavilyClient(api_key=tavily_key)

        # Google Trends sayfasını veya ilgili analiz sitelerini ara
        results = tavily.search(
            f'"{keyword}" search volume trend 2024 2025 google trends',
            max_results=5,
            search_depth="basic"
        )

        snippets = " ".join([
            r.get("content", "") for r in results.get("results", [])
        ])[:2000]

        # LLM ile veriyi yapılandır
        from agent.idea_agent import get_llm
        from langchain_core.messages import HumanMessage

        llm = get_llm(temp=0.0)
        prompt = f"""Web arama sonuçlarından "{keyword}" için Google Trends benzeri veri çıkar.
Eğer veri bulamazsan tahmini değerler ver (50/100, stable, 0%).

Sonuçlar:
{snippets}

SADECE şu JSON formatını döndür (başka metin YOK):
{{
  "interest_score": <0-100 arası sayı>,
  "trend_direction": "<rising|stable|declining>",
  "change_pct": "<+X% veya -X%>",
  "related_rising": ["<sorgu1>", "<sorgu2>"],
  "related_top": ["<sorgu1>", "<sorgu2>"]
}}"""

        response = llm.invoke([HumanMessage(content=prompt)])
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if not match:
            return None

        parsed = json.loads(match.group())

        return {
            "keyword":         keyword,
            "interest_score":  parsed.get("interest_score", 50),
            "trend_direction": parsed.get("trend_direction", "stable"),
            "change_pct":      parsed.get("change_pct", "0%"),
            "peak_month":      "",
            "related_rising":  parsed.get("related_rising", []),
            "related_top":     parsed.get("related_top", []),
            "monthly":         [],    # Tavily'den aylık veri çıkaramıyoruz
            "source":          "tavily_fallback",
            "cached":          False,
        }

    except Exception as e:
        print(f"[Trends] ⚠️  Tavily fallback hatası: {e}")
        return None


# ──────────────────────────────────────────────
# ANA FONKSİYON
# ──────────────────────────────────────────────

def get_search_volume(keywords: list) -> dict:
    """
    Verilen keyword listesi için Google Trends verisi döner.

    Args:
        keywords: Arama yapılacak kelimeler (max 5 önerilir)

    Returns:
        {
            "keyword1": {
                "interest_score": 78,
                "trend_direction": "rising",
                "change_pct": "+34%",
                "peak_month": "2025-03",
                "related_rising": ["sora AI", ...],
                "related_top": ["AI video editor", ...],
                "monthly": [{"month": "2025-01", "value": 65}, ...],
                "source": "pytrends" | "tavily_fallback",
                "cached": True | False,
            },
            ...
        }
    """
    results = {}

    for i, keyword in enumerate(keywords[:5]):  # Max 5 keyword
        keyword = keyword.strip()
        if not keyword:
            continue

        print(f"[Trends] 🔍 '{keyword}' aranıyor...")

        # 1. Cache kontrol
        cached = _load_cache(keyword)
        if cached:
            cached["cached"] = True
            results[keyword] = cached
            print(f"[Trends] ✅ Cache'den geldi: {keyword}")
            continue

        # 2. pytrends dene
        data = _fetch_via_pytrends(keyword)

        # 3. Başarısız → Tavily fallback
        if not data:
            print(f"[Trends] ↩️  Tavily fallback: {keyword}")
            data = _fetch_via_tavily(keyword)

        # 4. Her ikisi de başarısız → safe default
        if not data:
            data = {
                "keyword":         keyword,
                "interest_score":  50,
                "trend_direction": "stable",
                "change_pct":      "0%",
                "peak_month":      "",
                "related_rising":  [],
                "related_top":     [],
                "monthly":         [],
                "source":          "default",
                "cached":          False,
            }
            print(f"[Trends] ⚠️  Default değer kullanıldı: {keyword}")
        else:
            _save_cache(keyword, data)
            print(f"[Trends] ✅ {keyword} → skor={data['interest_score']}, yön={data['trend_direction']}")

        results[keyword] = data

        # Son keyword değilse bekle
        if i < len(keywords) - 1:
            time.sleep(PYTRENDS_SLEEP)

    return results


def generate_seo_keywords(category: str) -> list:
    """
    Kategori adından aranacak keyword listesi üretir.
    Basit heuristic + LLM yok (hız için).
    """
    # Sabit mapping — sık kullanılan kategoriler için
    KEYWORD_MAP = {
        "video generation":  ["ai video generator", "text to video ai", "ai video editor"],
        "image generation":  ["ai image generator", "text to image ai", "ai art generator"],
        "text to speech":    ["ai text to speech", "ai voice generator", "tts ai"],
        "speech to text":    ["ai speech to text", "ai transcription", "voice to text ai"],
        "code generation":   ["ai code generator", "ai coding assistant", "copilot alternative"],
        "music generation":  ["ai music generator", "ai song maker", "ai music composer"],
        "document AI":       ["ai document analysis", "ai pdf reader", "document ai tool"],
        "computer vision":   ["ai image recognition", "computer vision api", "ai visual detection"],
        "chatbot":           ["ai chatbot builder", "custom chatbot ai", "chatbot platform"],
        "automation":        ["ai workflow automation", "ai process automation", "no-code automation ai"],
        "developer tools":   ["ai developer tools", "ai coding tools", "ai devtools"],
        "marketing":         ["ai marketing tools", "ai content generator", "ai marketing automation"],
        "analytics":         ["ai analytics platform", "ai data analysis", "business intelligence ai"],
        "text generation":   ["ai text generator", "ai writing assistant", "ai content writer"],
        "audio processing":  ["ai audio editor", "ai audio processing", "audio ai tools"],
    }

    keywords = KEYWORD_MAP.get(category, [f"ai {category}", f"{category} tools", f"{category} software"])
    return keywords[:3]  # Max 3 (rate limit için)


# ──────────────────────────────────────────────
# TEST
# ──────────────────────────────────────────────

if __name__ == "__main__":
    kws = generate_seo_keywords("video generation")
    print(f"Keywords: {kws}")
    results = get_search_volume(kws)
    print(json.dumps(results, ensure_ascii=False, indent=2))
