"""
Rakip Araştırma Modülü — V4
- Tüm Tavily sorguları İngilizce (daha geniş sonuç, daha iyi kalite)
- Domain bazlı dedup (URL değil domain)
- Her rakip için: isim, URL, tahmini fiyat, ana özellik → yapılandırılmış çıktı
- Sonuç < 5 ise farklı sorgularla retry
- include_domains kısıtlaması YOK
"""

import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

# ── Sorgu şablonları (İngilizce) ──────────────────────────────────────────────

# Birincil: mevcut araçları ve rakipleri bul
PRIMARY_QUERIES = [
    'best {category} software tools for {niche} 2025',
    'top {category} SaaS alternatives comparison pricing',
    '{category} tool reviews site:reddit.com OR site:g2.com OR site:capterra.com',
]

# Retry: daha geniş, farklı açılar
RETRY_QUERIES = [
    '{category} app pricing features review',
    '{category} startup product hunt 2024 2025',
    'alternatives to {category} tools small business',
]

# Şikayet araması (İngilizce)
COMPLAINT_QUERIES = [
    '"{name}" reviews complaints problems users',
    '"{name}" pricing expensive alternative reddit',
    '"{name}" bugs issues negative review 2024 2025',
]

COMPLAINT_RETRY_QUERIES = [
    '"{name}" user feedback pain points',
    '"{name}" SaaS problems limitations',
]


def _get_client() -> TavilyClient | None:
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        print("[CompetitorResearch] ⚠️  TAVILY_API_KEY bulunamadı!")
        return None
    return TavilyClient(api_key=api_key)


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "").lower()
    except Exception:
        return url


def _clean_title(title: str) -> str:
    """Tavily'nin sık verdiği gereksiz ekleri temizle."""
    for suffix in [" - G2", " | Capterra", " | Reddit", " — Wikipedia", " | Product Hunt"]:
        title = title.replace(suffix, "")
    return title.strip()


# ── Ana fonksiyon: Rakip listesi ──────────────────────────────────────────────

def find_competitors(category: str, niche: str = "", min_results: int = 5) -> list[dict]:
    """
    Verilen kategori için rakipleri bulur.
    Her rakip için: name, url, domain, snippet (özellik ipucu), pricing_hint

    Returns:
        [{"name": "...", "url": "...", "domain": "...", "snippet": "...", "pricing_hint": "..."}]
    """
    client = _get_client()
    if not client:
        return []

    niche_str = niche or category
    competitors = []
    seen_domains: set[str] = set()

    def _run_queries(templates: list[str]) -> None:
        for tpl in templates:
            if len(competitors) >= min_results:
                break
            query = tpl.format(category=category, niche=niche_str)
            try:
                resp = client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=8,
                )
                for r in resp.get("results", []):
                    url = r.get("url", "")
                    domain = _extract_domain(url)
                    if not domain or domain in seen_domains:
                        continue
                    # Genel bilgi siteleri filtrele
                    if any(skip in domain for skip in ["wikipedia", "youtube", "linkedin", "twitter", "facebook"]):
                        continue
                    seen_domains.add(domain)
                    title = _clean_title(r.get("title", ""))
                    snippet = r.get("content", "")[:300]
                    pricing_hint = _extract_pricing_hint(snippet)
                    competitors.append({
                        "name": title or domain,
                        "url": url,
                        "domain": domain,
                        "snippet": snippet,
                        "pricing_hint": pricing_hint,
                    })
            except Exception as e:
                print(f"[CompetitorResearch] Sorgu hatası ({query[:50]}): {e}")

    # Birincil sorgular
    print(f"[CompetitorResearch] Rakip aranıyor: '{category}' / '{niche_str}'")
    _run_queries(PRIMARY_QUERIES)

    # Yeterli değilse retry
    if len(competitors) < min_results:
        print(f"[CompetitorResearch] Retry: sadece {len(competitors)} sonuç, geniş sorgularla devam...")
        _run_queries(RETRY_QUERIES)

    print(f"[CompetitorResearch] {len(competitors)} rakip bulundu.")
    return competitors[:10]  # Max 10


def _extract_pricing_hint(text: str) -> str:
    """Snippet içinden fiyat ipucu çıkar ($, /month, free, pricing)."""
    import re
    patterns = [
        r'\$\d+[\d,]*(?:/mo(?:nth)?|/yr(?:ear)?)?',
        r'free(?:\s+plan|\s+tier)?',
        r'freemium',
        r'starts?\s+at\s+\$\d+',
        r'from\s+\$\d+',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return "bilinmiyor"


def competitors_to_markdown_table(competitors: list[dict]) -> str:
    """Rakip listesini Markdown tablosuna dönüştür."""
    if not competitors:
        return "_Rakip verisi bulunamadı._"

    rows = []
    for c in competitors:
        name_link = f"[{c['name']}]({c['url']})" if c.get("url") else c["name"]
        feature = c.get("snippet", "")[:120].replace("|", "/").replace("\n", " ")
        pricing = c.get("pricing_hint", "bilinmiyor")
        rows.append(f"| {name_link} | {feature} | {pricing} |")

    header = "| Rakip | Ana Özellik / Açıklama | Fiyat İpucu |\n|-------|------------------------|-------------|"
    return header + "\n" + "\n".join(rows)


# ── Şikayet araması ───────────────────────────────────────────────────────────

def search_competitor_complaints(app_names: list[str], max_per_app: int = 3) -> list[dict]:
    """
    Her uygulama için İngilizce şikayet araması yapar.
    Domain bazlı dedup.

    Returns:
        [{"app": "...", "source": "...", "title": "...", "content": "...", "url": "..."}]
    """
    client = _get_client()
    if not client:
        return []

    all_results = []
    seen_domains: set[str] = set()

    for app_name in app_names[:5]:
        name = app_name.strip()
        if not name:
            continue

        print(f"[CompetitorResearch] Şikayet aranıyor: {name}")
        app_count = 0

        for tpl in COMPLAINT_QUERIES:
            if app_count >= max_per_app:
                break
            query = tpl.format(name=name)
            try:
                resp = client.search(query=query, search_depth="advanced", max_results=max_per_app)
                for r in resp.get("results", []):
                    url = r.get("url", "")
                    domain = _extract_domain(url)
                    content = r.get("content", "")
                    if domain in seen_domains or len(content) < 50:
                        continue
                    seen_domains.add(domain)
                    entry = {
                        "app": name,
                        "title": _clean_title(r.get("title", "")),
                        "content": content[:500],
                        "url": url,
                        "source": domain,
                    }
                    all_results.append(entry)
                    app_count += 1
            except Exception as e:
                print(f"[CompetitorResearch] Şikayet sorgu hatası ({name}): {e}")

        # Retry
        if app_count < 2:
            print(f"[CompetitorResearch] Retry: {name} için az sonuç ({app_count})")
            for tpl in COMPLAINT_RETRY_QUERIES:
                if app_count >= max_per_app:
                    break
                query = tpl.format(name=name)
                try:
                    resp = client.search(query=query, search_depth="advanced", max_results=3)
                    for r in resp.get("results", []):
                        url = r.get("url", "")
                        domain = _extract_domain(url)
                        content = r.get("content", "")
                        if domain in seen_domains or len(content) < 50:
                            continue
                        seen_domains.add(domain)
                        all_results.append({
                            "app": name,
                            "title": _clean_title(r.get("title", "")),
                            "content": content[:500],
                            "url": url,
                            "source": domain,
                        })
                        app_count += 1
                except Exception as e:
                    print(f"[CompetitorResearch] Retry hatası ({name}): {e}")

        print(f"[CompetitorResearch]   {name}: {app_count} sonuç")

    print(f"[CompetitorResearch] Toplam {len(all_results)} şikayet/yorum bulundu.")
    return all_results


def search_app_reviews(app_name: str, max_results: int = 5) -> list[dict]:
    """
    Tek uygulama için İngilizce web yorumu araması.
    store_reviews fallback olarak kullanır.
    """
    client = _get_client()
    if not client:
        return []

    queries = [
        f'"{app_name}" user reviews negative complaints problems',
        f'"{app_name}" alternative better site:reddit.com',
    ]

    reviews = []
    seen_domains: set[str] = set()

    for query in queries:
        try:
            resp = client.search(query=query, search_depth="advanced", max_results=max_results)
            for r in resp.get("results", []):
                url = r.get("url", "")
                domain = _extract_domain(url)
                content = r.get("content", "")
                if domain in seen_domains or len(content) < 50:
                    continue
                seen_domains.add(domain)
                reviews.append({
                    "score": 1,
                    "text": content[:400],
                    "app": app_name,
                    "source": f"web ({domain})",
                    "thumbs_up": 0,
                    "date": "",
                })
        except Exception as e:
            print(f"[CompetitorResearch] Review hatası ({app_name}): {e}")

    return reviews


# ── Test ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Rakip Arama Testi (V4 — İngilizce sorgu, domain dedup) ===\n")

    comps = find_competitors("AI video generation", niche="marketing agencies")
    print(competitors_to_markdown_table(comps))

    print("\n=== Şikayet Testi ===")
    complaints = search_competitor_complaints(["Lumen5", "Pictory"])
    for c in complaints[:3]:
        print(f"[{c['app']}] {c['source']}: {c['title']}")
        print(f"  {c['content'][:100]}...\n")
