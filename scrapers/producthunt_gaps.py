"""
Product Hunt "Boşluk" Analizi (Gap Analysis)
Belirli bir kategoride Product Hunt'taki popüler ürünlerin yorumlarını tarayarak
"Great product BUT..." / "Missing feature" / "I wish..." kalıplarını bulur.
Her eksik özellik = potansiyel Micro-SaaS fırsatı.
"""

import os
import sys
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from langchain_community.tools.tavily_search import TavilySearchResults
    tavily = TavilySearchResults(max_results=5)
except Exception:
    tavily = None


# ─────────────────────────────────────────────
# EKSİK ÖZELLİK KALIPLARI (Gap Patterns)
# ─────────────────────────────────────────────
GAP_PATTERNS = [
    "missing feature",
    "doesn't support",
    "wish it had",
    "but it lacks",
    "can't do",
    "not possible to",
    "would love",
    "needs improvement",
    "deal breaker",
    "switched away",
    "limited to",
    "still no",
    "frustrating",
    "no api",
    "no integration",
    "workaround",
    "too expensive",
    "pricing is",
    "affordable alternative",
]


def find_product_gaps(category: str, limit: int = 10) -> List[Dict]:
    """
    Product Hunt'taki popüler ürünlerin yorumlarını Tavily ile tarar.
    Hedef: "Missing feature", "doesn't support", "wish it had" kalıpları.
    Çıktı: Kategorideki eksik özellikler listesi.
    """
    print(f"[ProductHuntGaps] '{category}' kategorisi için boşluk analizi başlatıldı...")
    results = []

    if not tavily:
        print("[ProductHuntGaps] ⚠️ Tavily mevcut değil, atlaniyor.")
        return results

    # Farklı arama sorguları ile eksik özellikleri bul
    search_queries = [
        f"site:producthunt.com {category} tool review missing feature",
        f"site:producthunt.com {category} app cons limitations",
        f"{category} SaaS review 'wish it had' OR 'doesn't support' OR 'deal breaker'",
        f"{category} tool alternative 'switched away' OR 'too expensive' OR 'frustrating'",
    ]

    for sq in search_queries:
        try:
            raw = tavily.invoke(sq)
            for r in raw[:limit]:
                if not isinstance(r, dict):
                    continue

                url = r.get("url", "")
                content = r.get("content", "")[:400]

                # Gap pattern kontrolü
                content_lower = content.lower()
                matched_gaps = [p for p in GAP_PATTERNS if p in content_lower]
                is_gap = len(matched_gaps) > 0

                if is_gap or "producthunt.com" in url:
                    results.append({
                        "source": "Product Hunt Gap",
                        "title": content[:150],
                        "url": url,
                        "matched_patterns": matched_gaps,
                        "is_pain_signal": is_gap,
                        "pain_type": "Eksik Özellik / Boşluk" if is_gap else "Ürün İncelemesi",
                    })
        except Exception as e:
            print(f"[ProductHuntGaps] Sorgu hatası: {e}")

    # Tekrar eden URL'leri temizle
    seen_urls = set()
    unique_results = []
    for r in results:
        url = r.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    pain_count = sum(1 for r in unique_results if r.get("is_pain_signal"))
    print(f"[ProductHuntGaps] ✅ {len(unique_results)} sonuç bulundu ({pain_count} boşluk sinyali)")
    return unique_results


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    gaps = find_product_gaps("AI video editing")

    print(f"\n{'='*50}")
    print(f"Product Hunt Boşluk Analizi ({len(gaps)} sonuç):")
    print(f"{'='*50}")
    for g in gaps[:10]:
        emoji = "🔴" if g.get("is_pain_signal") else "🟡"
        patterns = ", ".join(g.get("matched_patterns", []))
        print(f"{emoji} [{g['source']}] {g['title'][:80]}")
        if patterns:
            print(f"   📌 Eşleşen kalıplar: {patterns}")
        if g.get("url"):
            print(f"   → {g['url']}")
