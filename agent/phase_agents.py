"""
İki Fazlı Agent Modülü
Aşama A (pazar tarama) ve Aşama B (derin fizibilite) için
LangGraph graph'larını ve singleton agent'larını barındırır.

idea_agent.py'den bağımsız olarak geliştirilip test edilebilir.
"""

import os
import json
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from lib.llm import get_llm

# Proje kökü (api_pricing.json için)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paylaşılan node'lar ve State — idea_agent.py'den import
from agent.idea_agent import (
    AgentState,
    auditor_node,
    fetch_trending_models_node,
    match_to_market_node,
    scrape_competitor_reviews_node,
    cluster_complaints_node,
    find_store_app_node,
    scrape_store_reviews_node,
    cluster_store_problems_node,
    generate_opportunity_node,
)


# ──────────────────────────────────────────────
# AŞAMA A — Son Node: Pazar Özeti + Alt-Niş Önerileri
# ──────────────────────────────────────────────

def generate_market_overview_node(state: AgentState) -> AgentState:
    """Aşama A sonu: pazar özeti + 3-5 alt-niş önerisi üretir."""
    print("[Agent] Node A-final → generate_market_overview")
    llm = get_llm(temp=0.3)
    category = state["user_category"]
    apps_text = "\n".join(
        f"  • {a['name']}: {a.get('content','')[:100]}" for a in state["matching_apps"][:5]
    ) or "  (veri yok)"
    complaints_text = state.get("complaint_clusters", "") or "(veri yok)"

    prompt = f"""Kategori: {category}

Mevcut uygulamalar:
{apps_text}

Kullanıcı şikayetleri:
{complaints_text[:600]}

Görev:
1. Bu pazarın 2-3 cümlelik özetini yaz.
2. Kullanıcıya seçtir: bu kategoride en fazla acı hisseden 3-5 spesifik alt-niş listesi ver.
   Format: JSON array, örn: ["AI avatar oluşturucu", "blog-to-video çevirici", "podcast klipper"]

SADECE JSON döndür: {{"summary": "...", "sub_niches": [...]}}"""

    try:
        raw = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        start, end = raw.find("{"), raw.rfind("}") + 1
        data = json.loads(raw[start:end]) if start >= 0 else {"summary": raw, "sub_niches": []}
    except Exception as e:
        data = {"summary": f"Pazar özeti üretilemedi: {e}", "sub_niches": []}

    overview = f"## Pazar Özeti\n{data.get('summary','')}\n\n**Alt-niş seçenekleri:** {data.get('sub_niches',[])}"
    return {**state, "market_overview": overview, "_sub_niche_options": data.get("sub_niches", [])}


# ──────────────────────────────────────────────
# AŞAMA B — Node'lar
# ──────────────────────────────────────────────

def compute_market_sizing_node(state: AgentState) -> AgentState:
    """Aşama B başı: bottom-up TAM/SAM/SOM (kaynaksız ise null)."""
    print("[Agent] Node B-1 → compute_market_sizing")
    from agent.validator import estimate_market_size
    llm = get_llm(temp=0.2)
    sub_niche = state.get("sub_niche") or state["user_category"]
    result_md = estimate_market_size(sub_niche, sub_niche, llm)
    sizing = {"markdown": result_md, "sub_niche": sub_niche}
    return {**state, "market_sizing": sizing}


def compute_unit_economics_node(state: AgentState) -> AgentState:
    """api_pricing.json'dan CPU maliyetini çeker, LTV/CAC tahmini yapar."""
    print("[Agent] Node B-2 → compute_unit_economics")
    import json as _json

    pricing_file = os.path.join(BASE_DIR, "data", "api_pricing.json")
    pricing_data = []
    if os.path.exists(pricing_file):
        try:
            with open(pricing_file, "r", encoding="utf-8") as f:
                pricing_data = _json.load(f)
        except Exception:
            pass

    pricing_text = "\n".join(
        f"  {p['provider']}/{p['model']}: {p['price_usd'] or 'bilinmiyor'}"
        for p in pricing_data[:10]
    ) or "  (fiyat verisi yok)"

    sub_niche = state.get("sub_niche") or state["user_category"]
    llm = get_llm(temp=0.2)
    prompt = f"""Ürün: {sub_niche}

Mevcut API fiyatları (güncel snapshot):
{pricing_text}

Görev: Bu ürün için birim ekonomi tahmini yap.
- 1 işlem için toplam API maliyeti (CPU)
- Önerilen fiyatlandırma (Freemium/Tiered)
- LTV ve CAC kaba tahmini

Kaynak yoksa null yaz. SADECE JSON döndür:
{{"cpu_cost": "...", "pricing_model": "...", "ltv_estimate": "...", "cac_estimate": "...", "payback_months": null}}"""

    try:
        raw = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        start, end = raw.find("{"), raw.rfind("}") + 1
        economics = _json.loads(raw[start:end]) if start >= 0 else {}
    except Exception:
        economics = {}

    return {**state, "unit_economics": economics}


def generate_gtm_assets_node(state: AgentState) -> AgentState:
    """buyer_matcher'ı çağırır, cold e-posta + LinkedIn DM + Waitlist CTA üretir."""
    print("[Agent] Node B-3 → generate_gtm_assets")
    sub_niche = state.get("sub_niche") or state["user_category"]
    complaints_text = state.get("complaint_clusters", "")[:400] or "(şikayet yok)"

    try:
        from agent.buyer_matcher import generate_buyer_messages
        dm_output = generate_buyer_messages(
            idea=sub_niche,
            pain_points=complaints_text,
        )
    except Exception as e:
        dm_output = f"(buyer_matcher hatası: {e})"

    llm = get_llm(temp=0.5)
    prompt = f"""Ürün: {sub_niche}
Kullanıcı acıları: {complaints_text}

Üret (Türkçe, emoji/ünlem yok):
1. Waitlist landing page başlık (H1) ve alt başlık (H2) + tek cümle value proposition
2. 3 adımlı cold e-posta sekansı (konu satırı + gövde, her biri max 5 cümle)
3. LinkedIn DM (max 3 cümle, rakip zayıflığına değin)

JSON döndür: {{"waitlist": {{"h1":"...","h2":"...","value_prop":"..."}}, "cold_emails": [...], "linkedin_dm": "..."}}"""

    try:
        raw = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        import json as _j
        start, end = raw.find("{"), raw.rfind("}") + 1
        assets = _j.loads(raw[start:end]) if start >= 0 else {}
    except Exception:
        assets = {}

    gtm_text = f"### GTM Varlıkları\n{dm_output}\n\n```json\n{assets}\n```"
    return {**state, "gtm_assets": gtm_text}


# ──────────────────────────────────────────────
# GRAPH BUILDER'LAR
# ──────────────────────────────────────────────

def build_phase_a_graph():
    """
    Aşama A: Pazar tarama + rakip analizi + pazar özeti.
    Kullanıcı alt-niş seçtikten sonra Aşama B tetiklenir.
    """
    graph = StateGraph(AgentState)

    graph.add_node("fetch_trending_models",     fetch_trending_models_node)
    graph.add_node("match_to_market",           match_to_market_node)
    graph.add_node("scrape_competitor_reviews", scrape_competitor_reviews_node)
    graph.add_node("cluster_complaints",        cluster_complaints_node)
    graph.add_node("generate_market_overview",  generate_market_overview_node)

    graph.set_entry_point("fetch_trending_models")
    graph.add_edge("fetch_trending_models",     "match_to_market")
    graph.add_edge("match_to_market",           "scrape_competitor_reviews")
    graph.add_edge("scrape_competitor_reviews", "cluster_complaints")
    graph.add_edge("cluster_complaints",        "generate_market_overview")
    graph.add_edge("generate_market_overview",  END)

    return graph.compile()


def build_phase_b_graph():
    """
    Aşama B: Derin fizibilite (pazar büyüklüğü + birim ekonomi + GTM + rapor).
    Aşama A state'i + kullanıcının sub_niche seçimi ile başlar.
    """
    from agent.competition_matrix import competition_matrix_node
    from agent.validator import validate_idea_node

    graph = StateGraph(AgentState)

    graph.add_node("compute_market_sizing",   compute_market_sizing_node)
    graph.add_node("find_store_app",          find_store_app_node)
    graph.add_node("scrape_store_reviews",    scrape_store_reviews_node)
    graph.add_node("cluster_store_problems",  cluster_store_problems_node)
    graph.add_node("compute_unit_economics",  compute_unit_economics_node)
    graph.add_node("generate_gtm_assets",     generate_gtm_assets_node)
    graph.add_node("competition_matrix",      competition_matrix_node)
    graph.add_node("generate_opportunity",    generate_opportunity_node)
    graph.add_node("validate_idea",           validate_idea_node)
    graph.add_node("auditor",                 auditor_node)

    graph.set_entry_point("compute_market_sizing")
    graph.add_edge("compute_market_sizing",  "find_store_app")
    graph.add_edge("find_store_app",         "scrape_store_reviews")
    graph.add_edge("scrape_store_reviews",   "cluster_store_problems")
    graph.add_edge("cluster_store_problems", "compute_unit_economics")
    graph.add_edge("compute_unit_economics", "generate_gtm_assets")
    graph.add_edge("generate_gtm_assets",    "competition_matrix")
    graph.add_edge("competition_matrix",     "generate_opportunity")
    graph.add_edge("generate_opportunity",   "validate_idea")
    graph.add_edge("validate_idea",          "auditor")
    graph.add_edge("auditor",                END)

    return graph.compile()


# ──────────────────────────────────────────────
# SINGLETON'LAR
# ──────────────────────────────────────────────
phase_a_agent = build_phase_a_graph()
phase_b_agent = build_phase_b_graph()
