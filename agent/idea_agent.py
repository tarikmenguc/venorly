"""
LangGraph Agentic RAG — Startup Idea Finder
Faz 3: trending modeller → pazar eşleştirme → rakip şikayetleri → store yorumları → fırsat raporu
Faz 18: ChromaDB kaldırıldı — tüm vektör aramaları Tavily web aramasıyla değiştirildi.
"""

import os
import sys
import json
import random
from typing import TypedDict, List, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Proje kökünü path'e ekle (competitor_research import için)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

load_dotenv()

# ──────────────────────────────────────────────
# MODEL KURULUMU — merkezi fabrika lib/llm.py'de
# ──────────────────────────────────────────────
from lib.llm import get_llm  # noqa: E402


# ──────────────────────────────────────────────
# STATE (Faz 3 güncellemesi)
# ──────────────────────────────────────────────

class AgentState(TypedDict):
    user_category: str               # "video generation", "image", vs.
    target_category: str             # expand_query_node çıktısı: rafine kategori
    search_queries: dict             # expand_query_node çıktısı: arama sorguları
    trending_models: List[dict]      # fetch_trending_models_node çıktısı
    matching_apps: List[dict]        # match_to_market_node çıktısı
    competitor_complaints: List[dict] # scrape_competitor_reviews_node çıktısı
    complaint_clusters: str           # cluster_complaints_node çıktısı
    store_app_ids: List[dict]        # find_store_app_node çıktısı
    store_reviews: List[dict]        # scrape_store_reviews_node çıktısı
    store_clusters: str              # cluster_store_problems_node çıktısı
    competition_matrix: str          # competition_matrix_node çıktısı
    final_report: str                # generate_opportunity_node çıktısı
    validation_details: str          # validate_idea_node çıktısı
    seo_data: dict                   # google_trends verisi
    # --- İki aşamalı orkestrasyon (S3) ---
    market_overview: str             # Aşama A çıktısı: pazar özeti + alt-niş önerileri
    sub_niche: str                   # Kullanıcının seçtiği alt-niş (Phase A → B köprüsü)
    market_sizing: dict              # compute_market_sizing_node çıktısı
    unit_economics: dict             # compute_unit_economics_node çıktısı
    gtm_assets: str                  # generate_gtm_assets_node çıktısı
    report_json: dict                # generate_opportunity_node — ham JSON (Auditor için)
    market_data: str                 # fetch_market_data_node çıktısı: TAM/pazar büyüklüğü metinleri
    error: Optional[str]


# ──────────────────────────────────────────────
# NODE 0: Query Expansion — Ham Girdiyi Araştırma Sorgularına Dönüştür
# ──────────────────────────────────────────────

def expand_query_node(state: AgentState) -> AgentState:
    """
    Kullanıcının kısa girdisini (ör. "video") araştırma için
    spesifik sorgulara dönüştürür. Hiçbir yeni bağımlılık gerektirmez —
    zaten mevcut olan Groq kullanılır.
    """
    raw = state["user_category"] or "AI SaaS tool"
    print(f"[Agent] Node 0 → expand_query | ham girdi: '{raw}'")

    prompt = f"""A user wants to research a startup idea in the "{raw}" space.

Expand this into specific research queries. Return ONLY valid JSON:

{{
  "refined_category": "specific niche description in 5-8 words (English)",
  "market_query": "search query to find TAM/market size data and industry reports",
  "competitor_query": "search query to find SaaS tools and competitors in this niche",
  "pain_point_query": "search query for Reddit/forums to find user complaints and pain points",
  "tech_query": "search query for AI models and technology used in this niche"
}}

Rules:
- Queries must be in English (for web search)
- Be very specific — avoid generic terms, focus on the niche
- Return ONLY the JSON object, no explanation"""

    try:
        response = get_llm(temp=0.1).invoke([HumanMessage(content=prompt)])
        raw_content = response.content.strip()
        start = raw_content.find("{")
        end = raw_content.rfind("}") + 1
        parsed = json.loads(raw_content[start:end]) if start >= 0 else {}

        refined = parsed.get("refined_category") or raw
        search_queries = {
            "market":     parsed.get("market_query")     or f"{raw} market size TAM startup 2024",
            "competitor": parsed.get("competitor_query") or f"{raw} SaaS tools competitors alternatives",
            "pain_point": parsed.get("pain_point_query") or f"{raw} problems complaints reddit site:reddit.com",
            "tech":       parsed.get("tech_query")       or f"AI {raw} model API technology",
        }
        print(f"[Agent] ✅ Query expansion tamamlandı: '{raw}' → '{refined}'")
        print(f"[Agent]    Sorgular: {list(search_queries.values())}")
    except Exception as e:
        print(f"[Agent] ⚠️  Query expansion hatası: {e} — fallback sorgular kullanılıyor.")
        refined = raw
        search_queries = {
            "market":     f"{raw} market size TAM startup industry report 2024",
            "competitor": f"best {raw} SaaS tools software competitors",
            "pain_point": f"{raw} tool problems issues reddit complaints",
            "tech":       f"AI {raw} model API open source technology",
        }

    return {**state, "target_category": refined, "search_queries": search_queries}


# ──────────────────────────────────────────────
# NODE 0.5: Pazar Büyüklüğü Verisi Çek
# ──────────────────────────────────────────────

def fetch_market_data_node(state: AgentState) -> AgentState:
    """
    search_queries["market"] sorgusunu kullanarak TAM/pazar büyüklüğü
    verisi çeker. Bulunan metinler generate_opportunity_node'a aktarılır.
    """
    market_query = state.get("search_queries", {}).get("market") or \
                   f"{state['user_category']} market size TAM billion 2024"
    print(f"[Agent] Node 0.5 → fetch_market_data | sorgu: '{market_query}'")

    try:
        from lib.tavily_client import get_tavily_client
        client = get_tavily_client()

        # İki farklı açıdan ara: genel pazar ve rakip gelir verileri
        results_market = client.search(
            market_query,
            max_results=5,
            search_depth="advanced",
            include_domains=["statista.com", "grandviewresearch.com", "mordorintelligence.com",
                             "marketsandmarkets.com", "ibisworld.com", "fortune business insights",
                             "precedenceresearch.com", "businessresearchinsights.com",
                             "globenewswire.com", "prnewswire.com", "bloomberg.com",
                             "techcrunch.com", "crunchbase.com"],
        )
        snippets = [
            f"[{r.get('title', '')}] {r.get('content', '')[:400]} (Kaynak: {r.get('url', '')})"
            for r in results_market.get("results", [])
            if r.get("content")
        ]

        # Yedek: domain kısıtlaması olmadan geniş arama
        if len(snippets) < 2:
            results_broad = client.search(
                f"{state.get('target_category', state['user_category'])} industry market size revenue statistics",
                max_results=5,
                search_depth="advanced",
            )
            snippets += [
                f"[{r.get('title', '')}] {r.get('content', '')[:400]} (Kaynak: {r.get('url', '')})"
                for r in results_broad.get("results", [])
                if r.get("content")
            ]

        market_data = "\n\n".join(snippets[:6]) if snippets else ""
        print(f"[Agent] ✅ {len(snippets)} pazar verisi snippet'i bulundu.")
    except Exception as e:
        print(f"[Agent] ⚠️  Pazar verisi çekme hatası: {e}")
        market_data = ""

    return {**state, "market_data": market_data}


# ──────────────────────────────────────────────
# NODE 1: Trend Modelleri Getir
# ──────────────────────────────────────────────

def fetch_trending_models_node(state: AgentState) -> AgentState:
    """ChromaDB'den önce arar; sonuç yetersizse Tavily'ye düşer."""
    query = state.get("search_queries", {}).get("tech") or state["user_category"] or "trending AI model"
    print(f"[Agent] Node 1 → fetch_trending_models | query: '{query}'")

    from lib.retrieval import retrieve
    docs = retrieve(query, need="trending_models", category=query, k=8)

    models = [
        {
            "content":   d["content"][:300],
            "name":      d["metadata"].get("name") or d["metadata"].get("title", ""),
            "model_id":  d["metadata"].get("model_id", ""),
            "category":  query,
            "source":    d["metadata"].get("source", ""),
            "downloads": d["metadata"].get("downloads", "N/A"),
            "url":       d["metadata"].get("url", ""),
        }
        for d in docs
    ]

    print(f"[Agent] ✅ {len(models)} model döndürüldü.")
    return {**state, "trending_models": models, "error": None}


# ──────────────────────────────────────────────
# NODE 2: Pazarla Eşleştir (Tavily ile)
# ──────────────────────────────────────────────

def match_to_market_node(state: AgentState) -> AgentState:
    """
    Önce ChromaDB startup_apps koleksiyonundan rakip uygulamaları çeker.
    Yetersiz sonuçta competitor_research (Tavily) fallback'e düşer.
    """
    category = state.get("target_category") or state["user_category"]
    competitor_query = state.get("search_queries", {}).get("competitor") or category
    print(f"[Agent] Node 2 → match_to_market | kategori: '{category}'")

    from lib.retrieval import retrieve
    docs = retrieve(competitor_query, need="market_apps", category=category, k=8)

    all_apps = [
        {
            "name":         d["metadata"].get("name", ""),
            "url":          d["metadata"].get("url", ""),
            "domain":       "",
            "content":      d["content"][:300],
            "mrr":          d["metadata"].get("mrr", ""),
            "votes":        d["metadata"].get("votes", "0"),
            "category":     category,
            "source":       d["metadata"].get("source", ""),
            "pricing_hint": d["metadata"].get("pricing", "bilinmiyor"),
        }
        for d in docs
    ]

    # Yeterli sonuç yoksa Tavily tabanlı competitor_research ile tamamla
    if len(all_apps) < 5:
        try:
            from scrapers.competitor_research import find_competitors
            extras = find_competitors(category=competitor_query, niche=category, min_results=5)
            for c in extras:
                all_apps.append({
                    "name":         c.get("name", ""),
                    "url":          c.get("url", ""),
                    "domain":       c.get("domain", ""),
                    "content":      c.get("snippet", "")[:300],
                    "mrr":          c.get("pricing_hint", ""),
                    "votes":        "0",
                    "category":     category,
                    "source":       "tavily_web",
                    "pricing_hint": c.get("pricing_hint", "bilinmiyor"),
                })
        except Exception as e:
            print(f"[Agent] ⚠️  Rakip fallback hatası: {e}")

    print(f"[Agent] ✅ {len(all_apps)} rakip/uygulama bulundu.")

    # ── SEO / Google Trends verisi (match_to_market ile birlikte çekiliyor) ──
    seo_data = {}
    try:
        from scrapers.google_trends import get_search_volume, generate_seo_keywords
        keywords = generate_seo_keywords(state["user_category"])
        seo_data = get_search_volume(keywords)
        print(f"[Agent] ✅ SEO verisi alındı: {list(seo_data.keys())}")
    except Exception as e:
        print(f"[Agent] ⚠️  SEO verisi alınamadı (devam ediyor): {e}")

    return {**state, "matching_apps": all_apps, "seo_data": seo_data}


# ──────────────────────────────────────────────
# NODE 3: Rakip Şikayetlerini Çek [FAZ 2]
# ──────────────────────────────────────────────

def scrape_competitor_reviews_node(state: AgentState) -> AgentState:
    """Eşleşen uygulamaların rakip şikayetlerini Tavily ile arar."""
    print("[Agent] Node 3 → scrape_competitor_reviews")

    if not state["matching_apps"]:
        print("[Agent] ⚠️  Eşleşen app yok, şikayet araması atlanıyor.")
        return {**state, "competitor_complaints": []}

    # domain bazlı filtrele — çok genel siteleri (reddit, g2) çıkar
    skip_domains = {"reddit.com", "g2.com", "capterra.com", "trustpilot.com", "producthunt.com"}
    app_names = [
        a["name"] for a in state["matching_apps"]
        if a.get("name") and a.get("domain", "") not in skip_domains
    ]

    try:
        from scrapers.competitor_research import search_competitor_complaints
        complaints = search_competitor_complaints(app_names, max_per_app=3)
    except ImportError:
        print("[Agent] ⚠️  competitor_research modülü bulunamadı.")
        complaints = []
    except Exception as e:
        print(f"[Agent] ❌ Şikayet araması hatası: {e}")
        complaints = []

    print(f"[Agent] ✅ {len(complaints)} şikayet/yorum bulundu.")
    return {**state, "competitor_complaints": complaints}


# ──────────────────────────────────────────────
# NODE 4: Şikayetleri Kümele [FAZ 2]
# ──────────────────────────────────────────────

def cluster_complaints_node(state: AgentState) -> AgentState:
    """Toplanan şikayetleri LLM ile gruplandırır."""
    print("[Agent] Node 4 → cluster_complaints")

    complaints = state.get("competitor_complaints", [])
    if not complaints:
        print("[Agent] ⚠️  Şikayet verisi yok, kümeleme atlanıyor.")
        return {**state, "complaint_clusters": ""}

    # Şikayetleri metin formatına dönüştür
    complaints_text = "\n".join([
        f"[{c['app']}] ({c['source']}): {c['content'][:300]}"
        for c in complaints[:15]  # Max 15 şikayet gönder
    ])

    clustering_prompt = f"""Aşağıda farklı SaaS uygulamaları hakkında kullanıcı yorumları ve şikayetleri var.
Bu şikayetleri analiz et ve en çok tekrarlanan 5 ana sorunu belirle.

Şikayetler:
{complaints_text}

Görevin:
1. Şikayetleri gruplandır
2. Her grup için kaç kez tekrarlandığını belirt
3. Hangi uygulama(lar)da görüldüğünü not et

Çıktı formatı (Türkçe):
1. [Sorun başlığı] — [kaç yorum] — [uygulamalar]
   Örnek yorumlar: "..."
2. ...
(Sadece listeyi yaz, başka açıklama ekleme)"""

    try:
        response = get_llm(temp=0.1).invoke([HumanMessage(content=clustering_prompt)])
        clusters = response.content
    except Exception as e:
        print(f"[Agent] ❌ Kümeleme hatası: {e}")
        clusters = f"(Kümeleme yapılamadı: {e})"

    print("[Agent] ✅ Şikayetler kümelendi.")
    return {**state, "complaint_clusters": clusters}


# ──────────────────────────────────────────────
# NODE 5: Fırsat Raporu Üret (Faz 2 güncellemesi)
# ──────────────────────────────────────────────

def generate_opportunity_node(state: AgentState) -> AgentState:
    """Multi-shot rapor: 3 fikir üret → en iyisini seç → detaylandır."""
    print("[Agent] Node 5 → generate_opportunity (multi-shot)")

    # Modeller — URL dahil
    if state["trending_models"]:
        models_text = "\n".join([
            f"  • {m['name']} ({m['category']}) | {m['url']}"
            for m in state["trending_models"][:5]
        ])
    else:
        models_text = "  (Model verisi bulunamadı)"

    # Uygulamalar — URL dahil
    if state["matching_apps"]:
        apps_text = "\n".join([
            f"  • {a['name']} | {a.get('url', 'URL yok')}"
            for a in state["matching_apps"][:5]
        ])
    else:
        apps_text = "  (Uygulama verisi bulunamadı)"

    # Atıfta bulunulabilecek kaynaklar — LLM bunları doğrudan kullanacak
    # Akademik / araştırma URL'leri hariç tut
    SKIP_URL_PATTERNS = [
        "arxiv.org", ".pdf", "iiit.ac.in", "cvit.iiit", "lilianweng.github.io",
        "aethir.com/blog-posts", "xenonstack.com/blog", "ecosystem.aethir",
        "cdn.iiit", "researchgate.net", "semanticscholar.org", "dl.acm.org",
        "ieeexplore.ieee.org", "springer.com/article", "nature.com/articles",
    ]

    def is_valid_source_url(url: str) -> bool:
        if not url or not url.startswith("http"):
            return False
        url_lower = url.lower()
        return not any(p in url_lower for p in SKIP_URL_PATTERNS)

    source_pool = []
    for m in state.get("trending_models", [])[:5]:
        url = m.get("url", "")
        if is_valid_source_url(url):
            source_pool.append(f"  - {m['name']}: {url}")
    for a in state.get("matching_apps", [])[:5]:
        url = a.get("url", "")
        if is_valid_source_url(url):
            source_pool.append(f"  - {a['name']}: {url}")
    for c in state.get("competitor_complaints", [])[:3]:
        url = c.get("url", "")
        if is_valid_source_url(url):
            source_pool.append(f"  - {c.get('app','Kaynak')}: {url}")
    cited_sources_block = (
        "Araştırma sırasında bulunan kaynaklar (yalnızca bunları kullan, URL uydurmak yasak):\n"
        + "\n".join(source_pool)
        if source_pool else
        "Araştırma kaynakları: Bu tarama için doğrulanmış URL bulunamadı."
    )

    # Rakip şikayetleri
    complaint_clusters = state.get("complaint_clusters", "")
    store_clusters = state.get("store_clusters", "")
    all_complaints = ""
    if complaint_clusters:
        all_complaints += f"\nWeb Şikayetleri (G2, Reddit):\n{complaint_clusters}\n"
    if store_clusters:
        all_complaints += f"\nKullanıcı Yorumları:\n{store_clusters}\n"

    # Perspektif
    perspectives = [
        "Sağlık sektörü (klinikler, doktorlar, eczaneler)",
        "Eğitim sektörü (öğretmenler, online kurs yapımcıları)",
        "E-ticaret (küçük mağaza sahipleri, dropshipper'lar)",
        "Hukuk sektörü (avukatlar, hukuk büroları)",
        "İçerik üreticileri (YouTuber'lar, podcast'çiler)",
        "Freelancer'lar (tasarımcılar, yazılımcılar)",
        "Restoran ve yeme-içme sektörü",
        "Fitness ve spor antrenörleri",
        "Küçük ajanslar (reklam, sosyal medya, PR)",
        "Müzisyenler ve ses prodüktörleri",
        "B2B SaaS girişimcileri",
    ]
    chosen_perspective = random.choice(perspectives)

    # SEO verisi bölümü
    seo_data = state.get("seo_data", {})
    seo_text = ""
    if seo_data:
        seo_lines = []
        for kw, d in list(seo_data.items())[:3]:
            direction_emoji = "↑" if d.get("trend_direction") == "rising" else ("↓" if d.get("trend_direction") == "declining" else "→")
            seo_lines.append(
                f'  • "{kw}" → İlgi: {d.get("interest_score", "?")} /100 '
                f'({direction_emoji} {d.get("change_pct", "0%")})'
            )
            rising = d.get("related_rising", [])[:3]
            if rising:
                seo_lines.append(f'    Yükselen aramalar: {", ".join(rising)}')
        seo_text = "\nArama Hacmi Verileri:\n" + "\n".join(seo_lines)

    # Pazar büyüklüğü verisi
    market_data = state.get("market_data", "")
    market_data_block = f"\nPazar Büyüklüğü Araştırması (TAM/SAM için kullan):\n{market_data}\n" \
                        if market_data else "\nPazar Büyüklüğü: Doğrulanmış veri bulunamadı.\n"

    data_context = f"""Kategori: {state.get('target_category') or state['user_category']}
Perspektif: {chosen_perspective}

Trend AI Modelleri ve Kaynakları:
{models_text}

Mevcut Uygulamalar ve Kaynakları:
{apps_text}
{all_complaints}{seo_text}
{market_data_block}
{cited_sources_block}"""

    # ========================================
    # AŞAMA 1: 3 farklı fikir üret (yaratıcı)
    # ========================================
    print("[Agent]   Aşama 1/3: 3 fikir üretiliyor...")
    prompt1 = f"""Kategori: "{state['user_category']}"

Trend AI Modelleri:
{models_text if models_text.strip() != "(Model verisi bulunamadı)" else "(Kategoriye uygun spesifik AI modellerini düşün.)"}

Mevcut uygulamalar (rakipler):
{apps_text if apps_text.strip() != "(Uygulama verisi bulunamadı)" else "(Bu kategorideki mevcut SaaS ürünlerini göz önünde bulundur.)"}

Görev: Yukarıdaki kategoride, aylık 29-99 dolar ödeyebilecek B2B profesyonellere (ajanslar, freelancer'lar, küçük işletmeler) yönelik 3 farklı Micro-SaaS fikri öner.

Kurallar:
- Tüketici uygulaması değil, iş araçları olsun.
- Her fikir somut bir manuel iş sürecini otomatize etsin — genel "analiz aracı" veya "dashboard" olmasın.
- AI API'leri kullanılarak üretilmiş olsun.
- YALNIZCA TÜRKÇE yaz.

Format:
1. [Başlık] | Hedef: [Spesifik niş] | Sorun: [Manuel süreç] | Çözüm: [Otomasyon]
2. ...
3. ...

Sadece listeyi yaz."""

    # Çoklu LLM tercihini belirle
    preferred_provider = "gemini" if os.getenv("GOOGLE_API_KEY") else "groq"

    try:
        llm_creative = get_llm(provider=preferred_provider, temp=0.9)
        ideas_response = llm_creative.invoke([HumanMessage(content=prompt1)])
        ideas_raw = ideas_response.content
        print(f"[Agent]   ✅ 3 fikir üretildi.")
    except Exception as e:
        print(f"[Agent]   ❌ Fikir üretme hatası: {e}")
        ideas_raw = "Fikir üretilemedi."

    # ========================================
    # AŞAMA 2: En iyisini seç (analitik)
    # ========================================
    print("[Agent]   Aşama 2/3: En iyi fikir seçiliyor...")
    prompt2 = f"""Aşağıda 3 Micro-SaaS fikri var. Hangisi detaylı analize en değer?

{ideas_raw}

Değerlendirme kriterleri:
- Hedef kitlenin ödeme kapasitesi ve istekliliği
- Çözülen sorunun ciddiyeti (ne kadar zaman/para kaybettiriyor?)
- Rekabet ortamında farklılaşma imkânı

Seçim: [numara] — Gerekçe: [2-3 cümle, nesnel ve kısa]

Sadece seçim numarasını ve gerekçeyi yaz. Abartma."""

    try:
        llm_analytic = get_llm(provider=preferred_provider, temp=0.2)
        selection = llm_analytic.invoke([HumanMessage(content=prompt2)])
        selected_idea = selection.content
        print(f"[Agent]   ✅ En iyi fikir seçildi.")
    except Exception as e:
        print(f"[Agent]   ❌ Seçim hatası: {e}")
        selected_idea = ideas_raw

    # ========================================
    # AŞAMA 3: Detaylı rapor (yapılandırılmış)
    # ========================================
    print("[Agent]   Aşama 3/3: Detaylı rapor üretiliyor...")
    # all_complaints'i güvenli şekilde temizle — yabancı dil karakterleri filtrelenir
    complaints_summary = ""
    if all_complaints.strip():
        # Ham metin yerine LLM'e özetle yaptır (dil kirliliği önlenir)
        try:
            clean_prompt = f"""Aşağıdaki kullanıcı şikayeti verilerini analiz et ve mevcut araçların en büyük 3 eksikliğini TÜRKÇE olarak 1-2 cümleyle özetle. Yabancı dil karakterleri veya anlamsız metin varsa yoksay.

Veri:
{all_complaints[:800]}

YALNIZCA TÜRKÇE olarak, sadece 3 maddelik özeti yaz."""
            complaints_summary = get_llm(temp=0.1).invoke([HumanMessage(content=clean_prompt)]).content.strip()
        except Exception:
            complaints_summary = "Rakip şikayet verisi işlenemedi."
    else:
        complaints_summary = "Rakip şikayet verisi bulunamadı — piyasadaki araçların genel boşluklarını analiz et."

    # Kaynak listesini JSON array olarak hazırla
    sources_json = json.dumps([
        {"url": s.split(": ", 1)[-1].strip(), "title": s.split(":")[0].strip()}
        for s in cited_sources_block.splitlines()
        if "http" in s
    ][:10])

    prompt3 = f"""Seçilen fikir: {selected_idea}
Veri kaynakları: {data_context}
Rakip eksiklikleri: {complaints_summary}

KURALLAR:
- Uydurma yapma. Güvenilir kaynağı olmayan sayısal iddia için null yaz.
- TAM/SAM/SOM: formül + varsayım zorunlu, yoksa null.
- Tech stack: spesifik model adı + birim maliyet zorunlu.
- Dil: Türkçe. Emoji/ünlem yok. Pazarlama dili yok.

SADECE aşağıdaki JSON yapısında yanıt ver (başka hiçbir şey yazma):
{{
  "idea_title": "...",
  "executive_summary": {{
    "decision": "Go|Hold|No-Go",
    "weighted_score": null,
    "market_attractiveness": null,
    "technical_barrier": null,
    "unit_economics": null,
    "gtm_ease": null,
    "leap_of_faith": ["varsayım1", "varsayım2", "varsayım3"]
  }},
  "market": {{
    "tam": null,
    "tam_formula": null,
    "sam": null,
    "som": null,
    "cagr": null,
    "macro_signals": "..."
  }},
  "competition": {{
    "competitors": [{{"name":"...", "url":"...", "weakness":"...", "funding":null}}],
    "gap_summary": "...",
    "entry_barriers": "..."
  }},
  "technical": {{
    "stack": "...",
    "cpu_cost": null,
    "ltv": null,
    "cac": null,
    "pricing_model": "..."
  }},
  "validation": {{
    "icp": "...",
    "cold_email_sequence": ["adım1", "adım2", "adım3"],
    "linkedin_dm": "...",
    "waitlist_h1": "...",
    "waitlist_h2": "...",
    "value_prop": "..."
  }},
  "sources": {sources_json}
}}"""

    try:
        llm_structured = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.3,
        )
        raw = llm_structured.invoke([HumanMessage(content=prompt3)]).content.strip()
        start, end = raw.find("{"), raw.rfind("}") + 1
        report_dict = json.loads(raw[start:end]) if start >= 0 else {}

        # Pydantic ile doğrula
        from lib.schemas import FeasibilityReport, report_to_markdown
        report_obj = FeasibilityReport(**report_dict)
        report = report_to_markdown(report_obj)
        # Ham JSON'u da state'e ekle (UI ve Auditor için)
        report_json = report_obj.model_dump()
    except Exception as e:
        print(f"[Agent] ⚠️  JSON parse/validate hatası: {e} — Markdown fallback.")
        report = raw if "raw" in dir() else f"LLM hatası: {e}"
        report_json = {}

    print("[Agent] ✅ Rapor üretildi (6 bölümlü standart).")
    return {**state, "final_report": report, "report_json": report_json}


# ──────────────────────────────────────────────
# NODE 6: Store App Bul [FAZ 3]
# ──────────────────────────────────────────────

def find_store_app_node(state: AgentState) -> AgentState:
    """Eşleşen startup'ların Play Store paket adlarını LLM ile belirler."""
    print("[Agent] Node 6 → find_store_app")

    if not state.get("matching_apps"):
        return {**state, "store_app_ids": []}

    # Agent'ın bulduğu gerçek startup'ları kullan (büyük devler değil)
    app_names = [a["name"] for a in state["matching_apps"][:6] if a.get("name")]
    if not app_names:
        return {**state, "store_app_ids": []}

    prompt = f"""Below are startup/app names found in the market.
For each, determine if they have a Google Play Store listing.
If yes, return the exact package ID (e.g. com.example.app).
If unsure or the app is web-only, write "none".
Be accurate — wrong package IDs will cause errors.

Apps: {', '.join(app_names)}

Output format (one per line, NO extra text):
AppName|com.example.package

Rules:
- Only return real, verified package IDs you are confident about
- Most small startups are web-only, so "none" is expected for many
- Do NOT guess or make up package IDs"""

    store_ids = []
    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        for line in response.content.strip().split("\n"):
            line = line.strip()
            if "|" not in line:
                continue
            parts = line.split("|")
            if len(parts) == 2:
                name, pkg = parts[0].strip(), parts[1].strip()
                if pkg and pkg.lower() != "none" and "." in pkg and len(pkg) > 5:
                    store_ids.append({"name": name, "play_store_id": pkg})
    except Exception as e:
        print(f"[Agent] ⚠️  LLM ID tahmin hatası: {e}")

    if store_ids:
        print(f"[Agent] ✅ {len(store_ids)} Play Store ID bulundu: {[s['name'] for s in store_ids]}")
    else:
        print("[Agent] ℹ️  Eşleşen startup'ların hiçbirinin Play Store uygulaması yok (web-only).")

    return {**state, "store_app_ids": store_ids}


# ──────────────────────────────────────────────
# NODE 7: Store Yorumlarını Çek [FAZ 3]
# ──────────────────────────────────────────────

def scrape_store_reviews_node(state: AgentState) -> AgentState:
    """Play Store yorumları veya Tavily web yorumları çeker (fallback)."""
    print("[Agent] Node 7 → scrape_store_reviews")

    store_ids = state.get("store_app_ids", [])
    all_reviews = []

    # YOL A: Play Store yorumları (store_ids varsa)
    if store_ids:
        try:
            from scrapers.store_reviews import scrape_play_store_reviews
            for app_info in store_ids[:3]:
                pkg = app_info.get("play_store_id", "")
                if pkg:
                    reviews = scrape_play_store_reviews(pkg, max_reviews=80)
                    all_reviews.extend(reviews[:20])
        except ImportError:
            print("[Agent] ⚠️  store_reviews modülü bulunamadı.")
        except Exception as e:
            print(f"[Agent] ❌ Store yorum hatası: {e}")

    # YOL B: Fallback — Tavily ile web yorumları (store yoksa)
    if not all_reviews and state.get("matching_apps"):
        print("[Agent] ℹ️  Store yorum yok → Tavily web fallback kullanılıyor...")
        try:
            from scrapers.competitor_research import search_app_reviews
            app_names = [a["name"] for a in state["matching_apps"][:3] if a.get("name")]
            for name in app_names:
                web_reviews = search_app_reviews(name, max_results=4)
                all_reviews.extend(web_reviews)
        except Exception as e:
            print(f"[Agent] ❌ Tavily fallback hatası: {e}")

    source = "Play Store" if store_ids else "Tavily web"
    print(f"[Agent] ✅ {len(all_reviews)} yorum toplandı ({source}).")
    return {**state, "store_reviews": all_reviews}


# ──────────────────────────────────────────────
# NODE 8: Store Yorumlarını Kümele [FAZ 3]
# ──────────────────────────────────────────────

def cluster_store_problems_node(state: AgentState) -> AgentState:
    """Store yorumlarındaki kullanıcı acılarını kümeler."""
    print("[Agent] Node 8 → cluster_store_problems")

    store_reviews = state.get("store_reviews", [])
    if not store_reviews:
        print("[Agent] ⚠️  Store yorum yok, kümeleme atlanıyor.")
        return {**state, "store_clusters": ""}

    reviews_text = "\n".join([
        f"[{r['app']}] ({r['score']}*) (thumbs={r.get('thumbs_up', 0)}): {r['text'][:250]}"
        for r in store_reviews[:20]
    ])

    prompt = f"""Aşağıda farklı uygulamaların Play Store/App Store'ıdaki 1-2 yıldız yorumları var.
Bu yorumları analiz et ve gerçek kullanıcıların en çok yaşadığı 5 sorunu belirle.
thumbsUp sayısı yüksek olanlar daha önemli.

Yorumlar:
{reviews_text}

Çıktı formatı (Türkçe):
1. [Sorun] — yaklaşık tekrar sayısı — [uygulama(lar)]
   Örnek: "..."
2. ...
(Sadece listeyi yaz)"""

    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        clusters = response.content
    except Exception as e:
        print(f"[Agent] ❌ Store kümeleme hatası: {e}")
        clusters = ""

    print("[Agent] ✅ Store yorumları kümelendi.")
    return {**state, "store_clusters": clusters}


# ──────────────────────────────────────────────
# S3 NODE — Auditor (Tek aşamalı grafikte de kullanılıyor)
# ──────────────────────────────────────────────

def auditor_node(state: AgentState) -> AgentState:
    """Raporu okur, iddiaları doğrular, Güven Endeksi hesaplar."""
    print("[Agent] Node Auditor → rapor denetleniyor")
    report_json = state.get("report_json") or {}
    if not report_json:
        print("[Agent] ⚠️  report_json boş, auditor atlanıyor.")
        return state

    from agent.auditor import run_audit
    result = run_audit(report_json, report_id=state.get("user_category", "unknown"))

    banner_map = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    banner_emoji = banner_map.get(result["banner"], "⚪")
    banner_line = (
        f"{banner_emoji} **Güven Endeksi: {result['confidence_index']:.0%}** "
        f"(Kaynak Kalitesi: {result['s_score']:.0%} | Çapraz Doğrulama: {result['x_score']:.0%})  \n"
        f"*{result['unverified_count']}/{result['total_claims']} iddia doğrulanamadı.*\n\n---\n\n"
    )
    final_report = banner_line + state.get("final_report", "")

    return {
        **state,
        "report_json": result["report_json"],
        "final_report": final_report,
    }


# ──────────────────────────────────────────────
# GRAPH OLUŞTUR (Faz 3 — Tek Aşamalı)
# ──────────────────────────────────────────────
# Faz A ve B graph'ları → agent/phase_agents.py

def build_graph():
    """Geriye dönük uyum — mevcut tek aşamalı akış."""
    from agent.competition_matrix import competition_matrix_node
    from agent.validator import validate_idea_node

    graph = StateGraph(AgentState)
    graph.add_node("expand_query",             expand_query_node)
    graph.add_node("fetch_market_data",        fetch_market_data_node)
    graph.add_node("fetch_trending_models",    fetch_trending_models_node)
    graph.add_node("match_to_market",          match_to_market_node)
    graph.add_node("scrape_competitor_reviews", scrape_competitor_reviews_node)
    graph.add_node("cluster_complaints",        cluster_complaints_node)
    graph.add_node("find_store_app",            find_store_app_node)
    graph.add_node("scrape_store_reviews",      scrape_store_reviews_node)
    graph.add_node("cluster_store_problems",    cluster_store_problems_node)
    graph.add_node("competition_matrix",        competition_matrix_node)
    graph.add_node("generate_opportunity",      generate_opportunity_node)
    graph.add_node("validate_idea",             validate_idea_node)
    graph.add_node("auditor",                   auditor_node)

    graph.set_entry_point("expand_query")
    graph.add_edge("expand_query",             "fetch_market_data")
    graph.add_edge("fetch_market_data",        "fetch_trending_models")
    graph.add_edge("fetch_trending_models",    "match_to_market")
    graph.add_edge("match_to_market",          "scrape_competitor_reviews")
    graph.add_edge("scrape_competitor_reviews", "cluster_complaints")
    graph.add_edge("cluster_complaints",        "find_store_app")
    graph.add_edge("find_store_app",            "scrape_store_reviews")
    graph.add_edge("scrape_store_reviews",      "cluster_store_problems")
    graph.add_edge("cluster_store_problems",    "competition_matrix")
    graph.add_edge("competition_matrix",        "generate_opportunity")
    graph.add_edge("generate_opportunity",      "validate_idea")
    graph.add_edge("validate_idea",             "auditor")
    graph.add_edge("auditor",                   END)

    return graph.compile()


# Singleton — ana pipeline
# Faz A/B singleton'ları için: agent/phase_agents.py
idea_agent = build_graph()


# ──────────────────────────────────────────────
# TERMINAL TEST
# ──────────────────────────────────────────────

if __name__ == "__main__":
    category = sys.argv[1] if len(sys.argv) > 1 else "video generation"
    print(f"\n{'='*55}")
    print(f"  Test calısıyor — kategori: '{category}'")
    print(f"  Graph: 8 node (Faz 3 — Final)")
    print(f"{'='*55}\n")

    result = idea_agent.invoke({
        "user_category": category,
        "trending_models": [],
        "matching_apps": [],
        "competitor_complaints": [],
        "complaint_clusters": "",
        "store_app_ids": [],
        "store_reviews": [],
        "store_clusters": "",
        "competition_matrix": "",
        "final_report": "",
        "validation_details": "",
        "error": None,
    })

    print("\n" + "="*55)
    print(result["final_report"])
    print("="*55)

    # Detayları göster
    if result.get("competitor_complaints"):
        print(f"\n--- {len(result['competitor_complaints'])} RAKİP ŞİKAYETİ ---")
    if result.get("store_reviews"):
        print(f"--- {len(result['store_reviews'])} STORE YORUMU ---")
        for r in result["store_reviews"][:3]:
            print(f"  [{r['app']}] ({r['score']}*): {r['text'][:80]}...")
    if result.get("store_app_ids"):
        print(f"--- STORE ID'LER: {result['store_app_ids']} ---")
