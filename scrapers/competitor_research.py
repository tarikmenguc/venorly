"""
Rakip Araştırma Modülü — Tavily Web Arama (V2)
Çoklu sorgu stratejisi ile daha zengin şikayet verisi toplar.
G2, Capterra, Reddit, Trustpilot + AlternativeTo kaynaklarından.
"""

import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

REVIEW_DOMAINS = [
    "g2.com", "capterra.com", "trustpilot.com",
    "reddit.com", "producthunt.com", "getapp.com",
    "alternativeto.net",
]

# Her app için birden fazla sorgu şablonu
QUERY_TEMPLATES = [
    '"{name}" reviews complaints problems',
    '"{name}" pricing expensive alternative',
    '"{name}" bugs issues site:reddit.com',
]


def get_tavily_client():
    if not TAVILY_API_KEY:
        print("[CompetitorResearch] ⚠️  TAVILY_API_KEY bulunamadı!")
        return None
    return TavilyClient(api_key=TAVILY_API_KEY)


def search_competitor_complaints(app_names: list[str], max_per_app: int = 3) -> list[dict]:
    """
    Her app için çoklu Tavily sorgusu ile şikayet araması yapar.

    Returns:
        [{"app": "...", "source": "...", "title": "...", "content": "...", "url": "..."}]
    """
    client = get_tavily_client()
    if not client:
        return []

    all_results = []
    seen_urls = set()

    for app_name in app_names[:5]:
        clean_name = app_name.strip()
        if not clean_name:
            continue

        print(f"[CompetitorResearch] 🔍 Aranıyor: {clean_name}")

        for template in QUERY_TEMPLATES:
            query = template.format(name=clean_name)

            try:
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_per_app,
                    include_domains=REVIEW_DOMAINS,
                )

                for result in response.get("results", []):
                    url = result.get("url", "")
                    content = result.get("content", "")

                    # Duplicate ve düşük kalite filtrele
                    if url in seen_urls:
                        continue
                    if len(content) < 50:
                        continue

                    seen_urls.add(url)
                    all_results.append({
                        "app": clean_name,
                        "title": result.get("title", ""),
                        "content": content[:500],
                        "url": url,
                        "source": _extract_domain(url),
                    })

            except Exception as e:
                print(f"[CompetitorResearch] ❌ Hata ({clean_name}, {template[:30]}): {e}")

    print(f"[CompetitorResearch] ✅ Toplam {len(all_results)} sonuç bulundu")
    return all_results


def search_app_reviews(app_name: str, max_results: int = 5) -> list[dict]:
    """
    Tek bir app için Tavily ile kullanıcı yorumlarını arar.
    Store review node'u fallback olarak kullanır.

    Returns:
        [{"score": 1, "text": "...", "app": "...", "source": "tavily_web", "thumbs_up": 0}]
    """
    client = get_tavily_client()
    if not client:
        return []

    queries = [
        f'"{app_name}" user reviews complaints problems negative',
        f'"{app_name}" alternative better than site:reddit.com',
    ]

    reviews = []
    seen_urls = set()

    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
            )

            for result in response.get("results", []):
                url = result.get("url", "")
                content = result.get("content", "")

                if url in seen_urls or len(content) < 50:
                    continue
                seen_urls.add(url)

                reviews.append({
                    "score": 1,  # Web şikayetleri = negatif varsayılır
                    "text": content[:400],
                    "app": app_name,
                    "source": f"tavily_web ({_extract_domain(url)})",
                    "thumbs_up": 0,
                    "date": "",
                })

        except Exception as e:
            print(f"[CompetitorResearch] ❌ Review arama hatası ({app_name}): {e}")

    return reviews


def _extract_domain(url: str) -> str:
    """URL'den alan adını çıkar."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return url


# Test
if __name__ == "__main__":
    print("=== Çoklu Sorgu Testi ===")
    results = search_competitor_complaints(["Lumen5", "Pictory"])
    for r in results:
        print(f"\n[{r['app']}] ({r['source']})")
        print(f"  {r['title']}")
        print(f"  {r['content'][:120]}...")

    print("\n=== App Review Testi ===")
    reviews = search_app_reviews("Lumen5")
    for r in reviews:
        print(f"  [{r['app']}] ({r['source']}): {r['text'][:100]}...")
