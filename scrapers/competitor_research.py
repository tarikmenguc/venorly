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
from lib.tavily_client import get_tavily_client as _lib_get_tavily

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


def _get_client():
    try:
        return _lib_get_tavily()
    except EnvironmentError as e:
        print(f"[CompetitorResearch] ⚠️ {e}")
        return None


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


# ── Reddit Sinyal Frekans Analizi ─────────────────────────────────────────────

def reddit_signal_analysis(category: str, max_results: int = 25) -> list:
    """
    Reddit public JSON API ile problem frekans + intensite analizi yapar.
    Auth gerektirmez. Reddily yaklasimi: upvote + tekrar sayisiyla sinyal gucu olcer.
    Returns: [{"problem", "frequency", "avg_score", "sample_quote", "signal_strength", "url"}]
    """
    import requests
    import time

    headers = {"User-Agent": "Venorly-Research/1.0"}
    queries = [
        category + " problem complaints",
        category + " tool issues frustrating",
        category + " looking for alternative",
    ]

    raw_posts = []
    seen_ids: set = set()

    for query in queries:
        try:
            url = (
                "https://www.reddit.com/search.json"
                "?q=" + requests.utils.quote(query) +
                "&sort=relevance&limit=10&type=link"
            )
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue
            data = resp.json()
            for post in data.get("data", {}).get("children", []):
                p = post.get("data", {})
                pid = p.get("id", "")
                if pid in seen_ids or not p.get("title"):
                    continue
                seen_ids.add(pid)
                raw_posts.append({
                    "id":           pid,
                    "title":        p.get("title", ""),
                    "selftext":     (p.get("selftext") or "")[:300],
                    "score":        int(p.get("score", 0)),
                    "num_comments": int(p.get("num_comments", 0)),
                    "url":          "https://reddit.com" + p.get("permalink", ""),
                    "subreddit":    p.get("subreddit", ""),
                })
            time.sleep(0.5)
        except Exception as e:
            print("[RedditSignal] Sorgu hatasi: " + str(e))

    if not raw_posts:
        return []

    # LLM ile problem temalarini cluster'la
    try:
        from lib.llm import get_llm
        from langchain_core.messages import HumanMessage
        import json

        posts_text = "\n".join(
            "[Score:{score} Comments:{comments}] r/{sub}: {title}".format(
                score=p["score"], comments=p["num_comments"],
                sub=p["subreddit"], title=p["title"]
            )
            for p in raw_posts[:20]
        )

        prompt = (
            'Asagidaki Reddit gonderilerini analiz et. Bunlar "' + category + '" '
            'kategorisindeki kullanici sikayet ve sorunlarini iceriyor.\n\n'
            'Gonderiler:\n' + posts_text + '\n\n'
            'GOREV: En sik tekrar eden 3-5 problem temasini bul. Her tema icin:\n'
            '- problem: Kisa problem tanimi (Turkce, 5-8 kelime)\n'
            '- frequency: Kac gonderide gectigini tahmin et (sayi)\n'
            '- avg_score: Bu temaya ait gonderi ortalama skoru\n'
            '- sample_quote: Bir gonderi basligini aynen alintila\n'
            '- signal_strength: "guclu" (score>50) | "orta" | "zayif"\n\n'
            'SADECE JSON array don:\n'
            '[{"problem": "...", "frequency": 3, "avg_score": 45, '
            '"sample_quote": "...", "signal_strength": "guclu"}]'
        )

        llm = get_llm(temp=0.1)
        raw = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        start, end = raw.find("["), raw.rfind("]") + 1
        if start >= 0 and end > start:
            signals = json.loads(raw[start:end])
            top_url = (
                max(raw_posts, key=lambda x: x["score"])["url"]
                if raw_posts else ""
            )
            for s in signals:
                s["url"] = top_url
                s["source"] = "reddit"
            print("[RedditSignal] " + str(len(signals)) + " sinyal tespit edildi")
            return signals
    except Exception as e:
        print("[RedditSignal] LLM cluster hatasi: " + str(e))

    # Fallback: ham post listesi
    return [
        {
            "problem":         p["title"][:80],
            "frequency":       1,
            "avg_score":       p["score"],
            "sample_quote":    p["title"],
            "signal_strength": "guclu" if p["score"] > 50 else "orta",
            "url":             p["url"],
            "source":          "reddit",
        }
        for p in sorted(raw_posts, key=lambda x: x["score"], reverse=True)[:5]
    ]
