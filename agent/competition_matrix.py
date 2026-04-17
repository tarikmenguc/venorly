"""
Rekabet Matrisi Node — V2
- Yapılandırılmış rakip verisini (name, url, pricing_hint, snippet) kullanır
- LLM boşluk analizi ve eksiklik tespiti yapar
- Türkçe çıktı, emoji yok, nesnel üslup
"""

from langchain_core.messages import HumanMessage
from typing import Any


def competition_matrix_node(state: Any) -> Any:
    """Rakipleri karşılaştıran yapılandırılmış bir Markdown tablosu oluşturur."""
    print("[Agent] Node 8.5 → competition_matrix (V2)")
    from agent.idea_agent import get_llm

    apps = state.get("matching_apps", [])
    if not apps:
        return {**state, "competition_matrix": "_Rakip uygulama verisi bulunamadı._"}

    # Yapılandırılmış rakip satırları
    structured_rows = []
    for a in apps[:6]:
        name = a.get("name", "Bilinmiyor")
        url = a.get("url", "")
        pricing = a.get("pricing_hint") or a.get("mrr") or "bilinmiyor"
        snippet = a.get("content", a.get("snippet", ""))[:200].replace("|", "/").replace("\n", " ")
        structured_rows.append({
            "name": name,
            "url": url,
            "pricing": pricing,
            "snippet": snippet,
        })

    rows_text = "\n".join([
        f"- {r['name']} | Fiyat: {r['pricing']} | URL: {r['url']}\n  Açıklama: {r['snippet']}"
        for r in structured_rows
    ])

    complaints = state.get("complaint_clusters", "")
    complaint_excerpt = complaints[:600] if complaints else "Şikayet verisi bulunamadı."

    prompt = f"""Aşağıdaki rakipler hakkında nesnel bir rekabet analizi tablosu oluştur.

Rakipler:
{rows_text}

Kullanıcı Şikayetleri (özet):
{complaint_excerpt}

GÖREV: Her rakip için şunları doldur:
1. Rakip adı ve URL'si
2. Ana özellik (1 cümle)
3. Fiyatlandırma (bilgi varsa, yoksa "bilinmiyor")
4. Tespit edilen en büyük eksiklik (şikayet verisinden çıkar, yoksa "veri yok")

KURALLAR:
- YALNIZCA Türkçe yaz
- Emoji kullanma
- Bilgi yoksa "bilinmiyor" yaz, uydurma
- Sadece Markdown tablosunu üret, başka metin ekleme

Format:
| Rakip | Ana Özellik | Fiyat | En Büyük Eksiklik |
|-------|------------|-------|-------------------|
| [İsim](URL) | ... | ... | ... |
"""

    try:
        matrix_md = get_llm(temp=0.1).invoke([HumanMessage(content=prompt)]).content.strip()
        # Tablo dışı metin varsa filtrele
        if "|" in matrix_md:
            lines = [l for l in matrix_md.split("\n") if l.strip().startswith("|")]
            if lines:
                matrix_md = "\n".join(lines)
    except Exception as e:
        print(f"[Agent] Matrix hatası: {e}")
        # Fallback: yapılandırılmış veriyi direkt tabloya çevir
        try:
            from scrapers.competitor_research import competitors_to_markdown_table
            matrix_md = competitors_to_markdown_table([
                {"name": r["name"], "url": r["url"], "snippet": r["snippet"], "pricing_hint": r["pricing"]}
                for r in structured_rows
            ])
        except Exception:
            matrix_md = "_Rekabet matrisi oluşturulamadı._"

    print(f"[Agent] Rekabet matrisi oluşturuldu ({len(structured_rows)} rakip).")
    return {**state, "competition_matrix": matrix_md}
