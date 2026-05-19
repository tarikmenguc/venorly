"""
Multi-Agent Orkestratör (Conductor)
Tek bir monolitik ajan yerine, 3 uzman ajanı koordine eder:

1. 🔍 Araştırma Ajanı (Research Agent)
   - Tüm veri kaynaklarını tarar (ChromaDB, Tavily, n8n, Reddit, GitHub, ProductHunt)
   - Ham veriyi toplar ve yapılandırır

2. 🧠 Analist Ajanı (Analyst Agent)
   - Toplanan veriyi derinlemesine analiz eder
   - Friction Economy filtresini uygular
   - En iyi Micro-SaaS fırsatını seçer
   - Investment Memo yazar

3. 🎯 Satış / GTM Ajanı (GTM Agent)
   - Hazır alıcıları (leads) bulur
   - Kişiselleştirilmiş DM şablonları üretir
   - Waitlist sayfası verisi hazırlar

Bu orchestrator mevcut kodları SARMALAYAN bir üst katmandır —
hiçbir mevcut fonksiyonu bozmaz, geriye uyumludur.
"""

import os
import sys
import json
from typing import TypedDict, List, Optional
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from lib.llm import get_llm
from lib.research_steps import (
    fetch_models_and_apps,
    build_seo_text,
    build_seo_memo_text,
    build_brainstorm_prompt,
    parse_angles,
    run_web_research,
    analyze_competitors,
)
from scrapers.reality_intel import check_upwork_rss, scan_reddit_desperation, scrape_github_gui_requests
from agent.buyer_matcher import BuyerMatcherAgent


# ──────────────────────────────────────────────
# ORCHESTRATOR STATE
# ──────────────────────────────────────────────
class OrchestratorState(TypedDict):
    target_category: str
    # Research Agent çıktıları
    trending_models: List[dict]
    known_apps: List[dict]
    automation_signals: List[dict]
    product_gaps: List[dict]
    research_summary: str
    seo_data: dict
    # Analyst Agent çıktıları
    brainstormed_angles: List[str]
    web_research_results: List[dict]
    competitor_insights: str
    selected_angle: str
    investment_memo: str
    # GTM Agent çıktıları
    buyer_leads: List[dict]
    waitlist_data: dict
    # Orchestrator metadata
    agent_log: List[str]
    error: Optional[str]


# ══════════════════════════════════════════════
# AJAN 1: ARAŞTIRMA AJANI (Research Agent)
# ══════════════════════════════════════════════

def research_agent_node(state: OrchestratorState) -> OrchestratorState:
    """
    Tüm veri kaynaklarını tarar ve ham veriyi toplar.
    ChromaDB + Tavily + n8n İstihbaratı + Product Hunt Gaps
    """
    print("\n" + "═"*50)
    print("🔍 [Research Agent] Aktif — Araştırma başlatıldı...")
    print("═"*50)

    log = state.get("agent_log", [])
    log.append("🔍 Research Agent başlatıldı")
    category = state["target_category"]
    trending_models = []
    known_apps = []

    # 1. Tavily ile AI modelleri + mevcut uygulamaları çek
    try:
        trending_models, known_apps = fetch_models_and_apps(category)
        log.append(f"  ✅ Tavily: {len(trending_models)} model, {len(known_apps)} app")
    except Exception as e:
        log.append(f"  ⚠️ Tavily web arama hatası: {e}")

    # 2. Araştırma Özeti oluştur (LLM ile)
    models_text = ", ".join([m.get("name", "") for m in trending_models[:5]])
    apps_text = ", ".join([a.get("name", "") for a in known_apps[:5]])
    auto_count = len(state.get("automation_signals", []))
    gap_count = len(state.get("product_gaps", []))

    summary_prompt = f"""Sen bir araştırma analistisin. Aşağıdaki verileri 3-4 cümlede özetle:

Kategori: {category}
AI Modelleri: {models_text or "Veri yok"}
Mevcut Uygulamalar: {apps_text or "Veri yok"}
Otomasyon İstihbaratı: {auto_count} sinyal toplandı (n8n/Zapier/Make.com forumlarından)
Product Hunt Boşlukları: {gap_count} eksik özellik tespit edildi

Bu alandaki en büyük fırsatlar ve boşluklar nelerdir?"""

    research_summary = ""
    try:
        research_summary = get_llm(temp=0.2).invoke([HumanMessage(content=summary_prompt)]).content
        log.append("  ✅ Araştırma özeti oluşturuldu")
    except Exception as e:
        research_summary = f"Araştırma verileri toplandı: {len(trending_models)} model, {len(known_apps)} app."
        log.append(f"  ⚠️ Özet LLM hatası, fallback kullanıldı: {e}")

    # SEO / Google Trends verisi
    seo_data = {}
    try:
        from scrapers.google_trends import get_search_volume, generate_seo_keywords
        seo_keywords = generate_seo_keywords(category)
        seo_data = get_search_volume(seo_keywords)
        log.append(f"  ✅ SEO verisi: {len(seo_data)} keyword")
    except Exception as e:
        log.append(f"  ⚠️ SEO verisi hatası: {e}")

    print(f"🔍 [Research Agent] ✅ Tamamlandı — {len(trending_models)} model, {len(known_apps)} app, {auto_count} otomasyon sinyali, {gap_count} PH gap")

    return {
        **state,
        "trending_models": trending_models,
        "known_apps": known_apps,
        "research_summary": research_summary,
        "seo_data": seo_data,
        "agent_log": log,
    }


# ══════════════════════════════════════════════
# AJAN 2: ANALİST AJANI (Analyst Agent)
# ══════════════════════════════════════════════

def analyst_agent_node(state: OrchestratorState) -> OrchestratorState:
    """
    Research Agent'ın topladığı veriyi analiz eder.
    1. 3 Micro-SaaS hipotezi üretir
    2. Web araştırması yapar
    3. Rakip analizi yapar
    4. En iyi fikri seçer
    5. Investment Memo yazar
    """
    if state.get("error"): return state
    print("\n" + "═"*50)
    print("🧠 [Analyst Agent] Aktif — Derinlemesine analiz başlatıldı...")
    print("═"*50)

    log = state.get("agent_log", [])
    log.append("🧠 Analyst Agent başlatıldı")
    category = state["target_category"]

    # ─── Adım 1: Hipotez Üretimi ───
    models_text = ", ".join([m.get("name", "") for m in state["trending_models"][:5]])
    apps_text = ", ".join([a.get("name", "") for a in state["known_apps"][:5]])
    auto_text = "\n".join([
        f"- [{s.get('source')}] {s.get('title', '')[:100]}"
        for s in state.get("automation_signals", [])[:8]
    ])
    gap_text = "\n".join([
        f"- [{g.get('source')}] {g.get('title', '')[:100]}"
        for g in state.get("product_gaps", [])[:6]
    ])
    seo_text = build_seo_text(state.get("seo_data", {}))

    brainstorm_prompt = build_brainstorm_prompt(
        category=category,
        models_text=models_text,
        apps_text=apps_text,
        auto_text=auto_text,
        gap_text=gap_text,
        seo_text=seo_text,
        research_summary=state.get("research_summary", ""),
    )

    angles = []
    try:
        response = get_llm(temp=0.9).invoke([HumanMessage(content=brainstorm_prompt)]).content
        angles = parse_angles(response)
        log.append("  ✅ 3 hipotez üretildi")
    except Exception as e:
        log.append(f"  ❌ Hipotez hatası: {e}")
        return {**state, "error": f"Brainstorm hatası: {e}", "agent_log": log}

    # ─── Adım 2: Web Araştırması ───
    web_results = run_web_research(angles)
    for i in range(len(web_results)):
        log.append(f"  ✅ Açı {i + 1} için web araştırması tamamlandı")

    # ─── Adım 3: Rakip Analizi ───
    competitor_insights = ""
    try:
        competitor_insights = analyze_competitors(web_results)
        log.append("  ✅ Rakip analizi tamamlandı")
    except Exception as e:
        log.append(f"  ⚠️ Rakip analizi hatası: {e}")

    # ─── Adım 4: En İyi Fikir Seçimi ───
    selected_angle = ""
    try:
        angles_text = "\n".join([f"- {a}" for a in angles])
        select_prompt = f"""Sen Y Combinator yatırımcısısın. 3 B2B Micro-SaaS hipotezinden TEK BİRİNİ seç.

Kritik Filtreler:
1. Ödeme İsteği (Willingness to Pay) en yüksek olan hangisi?
2. Zaman Tasarrufu (Time Saved) en çok olan hangisi?
3. Sadece "Ağrı Kesici" olanı seç.

Hipotezler:
{angles_text}

Pazar Analizi:
{competitor_insights}

Seçtiğin açıyı, nedenini ve Go-To-Market stratejini kısaca açıkla."""
        selected_angle = get_llm(temp=0.0).invoke([HumanMessage(content=select_prompt)]).content
        log.append("  ✅ En iyi fikir seçildi")
    except Exception as e:
        log.append(f"  ⚠️ Seçim hatası: {e}")

    # ─── Adım 5: Investment Memo ───
    investment_memo = ""
    try:
        models = "\n".join([m.get("name", "") for m in state["trending_models"][:3]])
        seo_memo_text = build_seo_memo_text(state.get("seo_data", {}))

        memo_prompt = f"""Profesyonel bir "Investment Memo" formatında Markdown raporu oluştur.

Karar: {selected_angle}
AI Modelleri: {models}
{seo_memo_text}

Format:
# 🧠 Deep Research Analizi: {selected_angle[:40]}...

## 1. Executive Summary
## 2. Thesis (Yatırım Tezi)
## 3. Product Vision & AI Stack
## 4. Competitive Dynamics (Rekabet)
## 5. Financial Projections & Pricing
## 6. Go-to-Market Strategy"""
        investment_memo = get_llm(temp=0.4).invoke([HumanMessage(content=memo_prompt)]).content
        log.append("  ✅ Investment Memo hazır")
    except Exception as e:
        log.append(f"  ⚠️ Memo hatası: {e}")

    print(f"🧠 [Analyst Agent] ✅ Tamamlandı — {len(angles)} hipotez, {len(web_results)} web araştırma, 1 seçim, 1 memo")

    return {
        **state,
        "brainstormed_angles": angles[:3],
        "web_research_results": web_results,
        "competitor_insights": competitor_insights,
        "selected_angle": selected_angle,
        "investment_memo": investment_memo,
        "agent_log": log,
    }


# ══════════════════════════════════════════════
# AJAN 3: SATIŞ / GTM AJANI (Go-To-Market Agent)
# ══════════════════════════════════════════════

def gtm_agent_node(state: OrchestratorState) -> OrchestratorState:
    """
    Analyst Agent'ın seçtiği fikir için:
    1. Hazır alıcıları (buyer leads) bulur
    2. Kişiselleştirilmiş DM şablonları üretir
    3. Waitlist sayfası için veri hazırlar
    """
    if state.get("error"): return state
    print("\n" + "═"*50)
    print("🎯 [GTM Agent] Aktif — Müşteri avcılığı başlatıldı...")
    print("═"*50)

    log = state.get("agent_log", [])
    log.append("🎯 GTM Agent başlatıldı")
    category = state.get("target_category", "")
    selected = state.get("selected_angle", "")

    raw_leads = []

    # 1. Upwork/Fiverr RSS
    try:
        jobs = check_upwork_rss(category, limit=3)
        raw_leads.extend(jobs)
        log.append(f"  ✅ Upwork: {len(jobs)} lead")
    except Exception as e:
        log.append(f"  ⚠️ Upwork hatası: {e}")

    # 2. Reddit Çaresizlik Forumları
    subreddits = ["SaaS", "Entrepreneur", "smallbusiness"]
    if "design" in category.lower(): subreddits = ["graphicdesign", "UI_Design"]
    elif "code" in category.lower(): subreddits = ["learnprogramming", "webdev"]
    elif "marketing" in category.lower(): subreddits = ["marketing", "SEO"]
    elif "video" in category.lower(): subreddits = ["VideoEditing", "NewTubers"]
    elif "audio" in category.lower(): subreddits = ["podcasting", "audioengineering"]

    try:
        reddit_leads = scan_reddit_desperation(subreddits, limit=2)
        raw_leads.extend(reddit_leads)
        log.append(f"  ✅ Reddit: {len(reddit_leads)} lead")
    except Exception as e:
        log.append(f"  ⚠️ Reddit hatası: {e}")

    # 3. GitHub GUI Talepleri
    try:
        github_leads = scrape_github_gui_requests("ai")
        for gl in github_leads[:2]:
            raw_leads.append({
                "source": "GitHub",
                "title": gl["opportunity"],
                "url": gl["example_issue_url"],
                "desc": f"Repo: {gl['repo_name']} | Stars: {gl['repo_stars']}"
            })
        log.append(f"  ✅ GitHub: {min(len(github_leads), 2)} lead")
    except Exception as e:
        log.append(f"  ⚠️ GitHub hatası: {e}")

    # 4. BuyerMatcher ile DM şablonları
    buyer_leads = raw_leads
    try:
        matcher = BuyerMatcherAgent()
        buyer_leads = matcher.process_leads(raw_leads[:10], saas_idea=selected)
        log.append(f"  ✅ DM şablonları hazır ({len(buyer_leads)} lead)")
    except Exception as e:
        log.append(f"  ⚠️ Matcher hatası, ham lead'ler kullanılıyor: {e}")

    # 5. Waitlist verisi hazırla
    waitlist_data = {}
    try:
        # Rapordan başlık ve açıklama çıkar
        title = f"{category} için AI Otomasyonu"
        if selected:
            first_line = selected.split('\n')[0][:100]
            title = first_line.replace('#', '').strip()[:80] or title

        waitlist_data = {
            "title": title,
            "description": selected[:200] if selected else "Manuel angaryayı tek tıklamaya indiren AI çözümü.",
            "target_audience": "B2B Profesyoneller",
        }
        log.append("  ✅ Waitlist verisi hazır")
    except Exception as e:
        log.append(f"  ⚠️ Waitlist veri hatası: {e}")

    print(f"🎯 [GTM Agent] ✅ Tamamlandı — {len(buyer_leads)} lead, DM şablonları hazır")

    return {
        **state,
        "buyer_leads": buyer_leads,
        "waitlist_data": waitlist_data,
        "agent_log": log,
    }


# ══════════════════════════════════════════════
# ORKESTRATÖR GRAPH YAPISI
# ══════════════════════════════════════════════

def build_orchestrator_graph():
    """
    3 uzman ajanı sıralı olarak çalıştıran LangGraph StateGraph.
    
    Research Agent → Analyst Agent → GTM Agent
         🔍              🧠              🎯
    """
    graph = StateGraph(OrchestratorState)

    graph.add_node("research_agent", research_agent_node)
    graph.add_node("analyst_agent", analyst_agent_node)
    graph.add_node("gtm_agent", gtm_agent_node)

    graph.set_entry_point("research_agent")
    graph.add_edge("research_agent", "analyst_agent")
    graph.add_edge("analyst_agent", "gtm_agent")
    graph.add_edge("gtm_agent", END)

    return graph.compile()


orchestrator_agent = build_orchestrator_graph()


# ──────────────────────────────────────────────
# TEST
# ──────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    cat = sys.argv[1] if len(sys.argv) > 1 else "data extraction"
    print(f"\n{'='*60}")
    print(f"🚀 MULTI-AGENT ORKESTRATÖR TEST: {cat}")
    print(f"{'='*60}\n")

    for event in orchestrator_agent.stream({
        "target_category": cat,
        "trending_models": [],
        "known_apps": [],
        "automation_signals": [],
        "product_gaps": [],
        "research_summary": "",
        "seo_data": {},
        "brainstormed_angles": [],
        "web_research_results": [],
        "competitor_insights": "",
        "selected_angle": "",
        "investment_memo": "",
        "buyer_leads": [],
        "waitlist_data": {},
        "agent_log": [],
        "error": None,
    }):
        node_name = list(event.keys())[0]
        print(f"\n→ Ajan tamamlandı: {node_name}")

    print("\n" + "="*60)
    final = event[node_name]
    print(f"Agent Log:")
    for entry in final.get("agent_log", []):
        print(f"  {entry}")
    print(f"\nHazır Alıcı Sayısı: {len(final.get('buyer_leads', []))}")
