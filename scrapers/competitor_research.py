"""
Rakip Araştırma Modülü — Tavily Web Arama
Eşleşen uygulamaların rakip şikayetlerini çeker.
G2, Capterra, Reddit, Trustpilot gibi kaynaklardan şikayetleri toplar.
"""

import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


def get_tavily_client():
    if not TAVILY_API_KEY:
        print("[CompetitorResearch] ⚠️  TAVILY_API_KEY bulunamadı!")
        return None
    return TavilyClient(api_key=TAVILY_API_KEY)


def search_competitor_complaints(app_names: list[str], max_per_app: int = 3) -> list[dict]:
    """
    Her app için Tavily ile şikayet araması yapar.
    
    Args:
        app_names: Aranacak uygulama isimleri
        max_per_app: Her app için max sonuç sayısı
    
    Returns:
        [{"app": "Lumen5", "source": "g2.com", "title": "...", "content": "...", "url": "..."}]
    """
    client = get_tavily_client()
    if not client:
        return []

    all_results = []

    for app_name in app_names[:5]:  # Max 5 app ara (API limit koruması)
        # Temizle — fazla spesifik olmayan aramalar daha iyi çalışır
        clean_name = app_name.strip()
        if not clean_name:
            continue

        query = f'"{clean_name}" reviews complaints problems negative feedback'
        print(f"[CompetitorResearch] 🔍 Aranıyor: {clean_name}")

        try:
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=max_per_app,
                include_domains=[
                    "g2.com", "capterra.com", "trustpilot.com",
                    "reddit.com", "producthunt.com", "getapp.com",
                ],
            )

            for result in response.get("results", []):
                all_results.append({
                    "app": clean_name,
                    "title": result.get("title", ""),
                    "content": result.get("content", "")[:500],  # İlk 500 karakter
                    "url": result.get("url", ""),
                    "source": _extract_domain(result.get("url", "")),
                })

        except Exception as e:
            print(f"[CompetitorResearch] ❌ Hata ({clean_name}): {e}")

    print(f"[CompetitorResearch] ✅ Toplam {len(all_results)} sonuç bulundu")
    return all_results


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
    results = search_competitor_complaints(["Lumen5", "Pictory", "InVideo"])
    for r in results:
        print(f"\n[{r['app']}] ({r['source']})")
        print(f"  {r['title']}")
        print(f"  {r['content'][:150]}...")
