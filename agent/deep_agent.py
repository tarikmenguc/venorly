import os
import sys
import json
from typing import TypedDict, List, Optional
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from tavily import TavilyClient

# Proje kökünü path'e ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from agent.idea_agent import get_llm
from scrapers.reality_intel import check_upwork_rss, scan_reddit_desperation, scrape_github_gui_requests
from agent.buyer_matcher import BuyerMatcherAgent

# ──────────────────────────────────────────────
# STATE DEFINITION
# ──────────────────────────────────────────────
class DeepAgentState(TypedDict):
    target_category: str
    trending_models: List[dict]
    known_apps: List[dict]
    brainstormed_angles: List[str]
    web_research_results: List[dict]
    competitor_insights: str
    selected_angle: str
    investment_memo: str
    buyer_leads: List[dict]
    automation_signals: List[dict]
    product_gaps: List[dict]
    seo_data: dict
    error: Optional[str]

def _get_tavily() -> TavilyClient | None:
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        print("[DeepResearch] ⚠️ TAVILY_API_KEY bulunamadı!")
        return None
    return TavilyClient(api_key=api_key)

# ──────────────────────────────────────────────
# NODE 1: Init Research (Tavily Web Araması)
# ──────────────────────────────────────────────
def init_research_node(state: DeepAgentState) -> DeepAgentState:
    print(f"[DeepResearch] Node 1 → init_research ({state['target_category']})")
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Trending modelleri Tavily ile bul
        model_results = tavily.search(
            f"trending AI models tools for {state['target_category']} 2024 2025",
            max_results=8, search_depth="basic"
        )
        trending_models = []
        for r in model_results.get("results", []):
            trending_models.append({
                "name": r.get("title", ""),
                "description": r.get("content", "")[:300],
                "category": state["target_category"],
                "source": "tavily_web",
                "url": r.get("url", ""),
            })
            
        # App'leri Tavily ile bul
        app_results = tavily.search(
            f"SaaS startups apps using {state['target_category']} AI",
            max_results=8, search_depth="basic"
        )
        known_apps = []
        for r in app_results.get("results", []):
            known_apps.append({
                "name": r.get("title", ""),
                "description": r.get("content", "")[:300],
                "category": state["target_category"],
                "source": "tavily_web",
                "url": r.get("url", ""),
            })
            
        # SEO / Google Trends verisi
        from scrapers.google_trends import get_search_volume, generate_seo_keywords
        seo_keywords = generate_seo_keywords(state["target_category"])
        seo_data = get_search_volume(seo_keywords)

        return {**state, "trending_models": trending_models, "known_apps": known_apps, "seo_data": seo_data}
    except Exception as e:
        print(f"[DeepResearch] ❌ Init Hatası: {e}")
        return {**state, "error": str(e)}

# ──────────────────────────────────────────────
# NODE 2: Brainstorm Angles (Hipotez Üretimi)
# ──────────────────────────────────────────────
def brainstorm_angles_node(state: DeepAgentState) -> DeepAgentState:
    if state.get("error"): return state
    print("[DeepResearch] Node 2 → brainstorm_angles")
    
    models_text = ", ".join([m.get("name", "") for m in state["trending_models"][:5]])
    apps_text = ", ".join([a.get("name", "") for a in state["known_apps"][:5]])
    
    # n8n/Make.com otomasyon istihbaratını prompt'a ekle
    auto_signals = state.get("automation_signals", [])
    auto_text = ""
    if auto_signals:
        auto_lines = []
        for s in auto_signals[:10]:
            auto_lines.append(f"- [{s.get('source')}] {s.get('title', '')[:100]}")
        auto_text = "\n".join(auto_lines)

    # Product Hunt gap verilerini prompt'a ekle
    gap_signals = state.get("product_gaps", [])
    gap_text = ""
    if gap_signals:
        gap_lines = []
        for g in gap_signals[:8]:
            gap_lines.append(f"- [{g.get('source')}] {g.get('title', '')[:120]}")
        gap_text = "\n".join(gap_lines)

    # SEO / Google Trends verisi prompt'a ekle
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
        seo_text = "\n📈 Google Trends / Arama Hacmi:\n" + "\n".join(seo_lines)

    prompt = f"""KULLANICININ SEÇTİĞİ ANA KATEGORİ: {state['target_category']}
    
Pazardaki İlgili AI Modelleri: {models_text if models_text else "Bu nişte kullanılabilecek top-tier AI modellerini düşün."}
Mevcut Kazanan Uygulamalar: {apps_text if apps_text else "Bu piyasadaki mevcut yazılımların yetersizliğini (boşluğu) hayal et."}
{f'''
OTOMASYON İSTİHBARATI (n8n/Zapier/Make.com Forumlarından):
{auto_text}
ÖNEMLİ: Yukarıdaki otomasyon talepleri, GERÇEK İNSANLARIN gerçekten otomasyona çevirmek istediği ama yapamadığı işlerdir.''' if auto_text else ''}
{f'''
PRODUCT HUNT BOŞLUK ANALİZİ (Mevcut Ürünlerin Zayıf Noktaları):
{gap_text}
ÖNEMLİ: Bu boşluklar, kullanıcıların mevcut ürünlerden memnun olmadığı noktaları gösterir. Burası altın madeni.''' if gap_text else ''}
{seo_text if seo_text else ''}

Sen Y Combinator'dan acımasız bir yatırımcısın. Görevin KULLANICININ SEÇTİĞİ ANA KATEGORİ ({state['target_category']}) odağında 3 farklı Micro-SaaS 'Saldırı Açısı' (Hypothesis) yazmak.

KATI KURALLAR (Friction Economy):
1. B2C (Tüketici/İzleyici) fikirleri KESİNLİKLE YASAKTIR. Sadece para ödeme gücü olan Profesyoneller, C-Level, Freelancer'lar, Ajanslar veya geliri olan İçerik Üreticileri hedeflenmeli.
2. "Vitamin" Reddedilecek: Pazardaki "Kanal analizi", "Dashboard" gibi jenerik fikirleri ÇÖPE AT. Sadece insanların manuel olarak 5-10 saatini çalan belirli bir angarya işi (Painkiller) çözen, tek tıklamalık AI otomasyonları üret.

Format (kesinlikle bu formata uy):
Açı 1: [Niş Hedef Kitle] - [Manuel Acı Noktası] - [AI Otomasyon Çözümü]
Açı 2: [Niş Hedef Kitle] - [Manuel Acı Noktası] - [AI Otomasyon Çözümü]
Açı 3: [Niş Hedef Kitle] - [Manuel Acı Noktası] - [AI Otomasyon Çözümü]"""

    try:
        response = get_llm(temp=0.9).invoke([HumanMessage(content=prompt)]).content
        angles = []
        for line in response.split('\n'):
            if line.strip().startswith('Açı '):
                angles.append(line.split(':', 1)[1].strip())
        
        # Eğer formatı bozarsa, tüm response'u tek açı yapıp bölelim
        if len(angles) < 3:
            angles = [response[:100], response[100:200], response[200:300]]
            
        print(f"[DeepResearch] ✅ 3 Hipotez üretildi.")
        return {**state, "brainstormed_angles": angles[:3]}
    except Exception as e:
        return {**state, "error": f"Brainstorm hatası: {e}"}

# ──────────────────────────────────────────────
# NODE 3: Deep Web Research (Tavily Çoklu Arama)
# ──────────────────────────────────────────────
def deep_web_research_node(state: DeepAgentState) -> DeepAgentState:
    if state.get("error"): return state
    print("[DeepResearch] Node 3 → deep_web_research (Paralel Arama Simülasyonu)")
    
    results = []
    tavily = _get_tavily()
    for i, angle in enumerate(state["brainstormed_angles"]):
        print(f"  [DeepResearch] 🔍 Açı {i+1} için web taranıyor...")
        try:
            if not tavily:
                continue
            # 1. Rakipler araması
            q1 = f"{angle} SaaS tools software competitors"
            res1 = tavily.search(q1, max_results=3, search_depth="basic").get("results", [])
            # 2. Şikayet araması
            q2 = f"{angle} software reddit complaints issues"
            res2 = tavily.search(q2, max_results=3, search_depth="basic").get("results", [])

            results.append({
                "angle": angle,
                "competitor_data": res1,
                "complaint_data": res2
            })
        except Exception as e:
            print(f"  [DeepResearch] ⚠️ Arama hatası: {e}")
            
    return {**state, "web_research_results": results}

# ──────────────────────────────────────────────
# NODE 4: Competitor Deep Dive (Rakip İncelemesi)
# ──────────────────────────────────────────────
def competitor_deep_dive_node(state: DeepAgentState) -> DeepAgentState:
    if state.get("error"): return state
    print("[DeepResearch] Node 4 → competitor_deep_dive")
    
    raw_data = json.dumps(state["web_research_results"])[:4000] # LLM limitleri
    
    prompt = f"""Aşağıdaki ham web arama sonuçlarını analiz et ve bu 3 araştırma açısı için pazardaki mevcut rakipleri, fiyat aralıklarını ve kullanıcıların en çok şikayet ettiği zayıf yönleri özetle.
    
    Ham Veri:
    {raw_data}
    
    Özetini çok net ve anlaşılır bir rapor formatında ver."""
    
    try:
        insights = get_llm(temp=0.1).invoke([HumanMessage(content=prompt)]).content
        return {**state, "competitor_insights": insights}
    except Exception as e:
        return {**state, "error": f"Deep Dive hatası: {e}"}

# ──────────────────────────────────────────────
# NODE 5: Reasoning Synthesis (Akıl Yürütme)
# ──────────────────────────────────────────────
def reasoning_synthesis_node(state: DeepAgentState) -> DeepAgentState:
    if state.get("error"): return state
    print("[DeepResearch] Node 5 → reasoning_synthesis (Karar Verme)")
    
    angles = "\n".join([f"- {a}" for a in state["brainstormed_angles"]])
    insights = state["competitor_insights"]
    
    prompt = f"""Sen Y Combinator'dan acımasız bir yatırımcısın. 
Aşağıdaki 3 B2B/B2Creator Micro-SaaS hipotezini ve rakip pazar analizini dikkatle oku.

Kritik Değerlendirme Filtresi:
1. Pazar büyüklüğü umrumda değil, "Ödeme İsteği (Willingness to Pay)" umrumda. Hangi kitle bu araca en çok para öder?
2. "Zaman Tasarrufu (Time Saved)": Hangisi manuel bir işi en fazla süreden en kısa süreye indiriyor?
3. Sadece "Ağrı Kesici" olanı (kanayan bir iş yarasını çözen) TEK BİR Fikri seç. "Vitamin" (alsam iyi olur) araçlarını reddet.

Hipotezler:
{angles}

Pazar Analizi (Tavily):
{insights}

Sadece en kârlı TEK açıyı seç. Seçtiğin açı, seçme nedenin (ödeme isteği kanıtı) ve ilk 10 müşteriye ulaşma (Go-To-Market) stratejin nedir? Kısaca açıkla."""

    try:
        # Burada özellikle temp=0 kullanıyoruz ki reasoning en yüksek seviyede olsun
        selected = get_llm(temp=0.0).invoke([HumanMessage(content=prompt)]).content
        print("[DeepResearch] ✅ En iyi fikir sentelendi.")
        return {**state, "selected_angle": selected}
    except Exception as e:
        return {**state, "error": f"Synthesis hatası: {e}"}

# ──────────────────────────────────────────────
# NODE 6: Write Investment Memo (Final Rapor)
# ──────────────────────────────────────────────
def write_investment_memo_node(state: DeepAgentState) -> DeepAgentState:
    if state.get("error"): return state
    print("[DeepResearch] Node 6 → write_investment_memo (Memo Oluşturuluyor)")

    models = "\n".join([m.get("name", "") for m in state["trending_models"][:3]])
    decision = state["selected_angle"]

    # SEO verisi memo'ya ekle
    seo_data = state.get("seo_data", {})
    seo_memo_text = ""
    if seo_data:
        seo_lines = []
        for kw, d in list(seo_data.items())[:3]:
            direction_emoji = "↑" if d.get("trend_direction") == "rising" else ("↓" if d.get("trend_direction") == "declining" else "→")
            seo_lines.append(
                f'- "{kw}": İlgi {d.get("interest_score", "?")} /100, '
                f'{direction_emoji} {d.get("change_pct", "0%")}'
            )
        seo_memo_text = "\nGoogle Trends Verileri:\n" + "\n".join(seo_lines)

    prompt = f"""Görevin, aşağıdaki araştırma bulgusunu esas alarak nesnel ve sorgulamalı bir iş analizi raporu yazmak. Bu bir satış metni değil — güçlü ve zayıf yanları eşit ağırlıkla ele alan, saygılı ama doğrudan bir değerlendirme belgesi olmalı.

YALNIZCA TÜRKÇE YAZ. Emoji kullanma. Abartı ve süslü dil kullanma.

Araştırma Bulgusu:
{decision}

Kullanılabilecek AI Modelleri:
{models}
{seo_memo_text}

Aşağıdaki başlıkları sırayla, düz ve ciddi bir dille yaz:

# Derin Araştırma Raporu: {state['target_category']}

## Fikir ve Kapsam

[Bu fikir ne öneriyor? Kim için, ne yapıyor, hangi teknolojiyle? 2-3 cümle, sade.]

---

## Neden Bu Boşluk Var?

[Rakipler bu problemi neden çözmedi? Teknik engel mi, pazar büyüklüğü mü, yoksa gerçekten talep yok mu? Nesnel değerlendir.]

---

## Ürün ve Teknoloji

[Hangi AI modelleri kullanılacak? Ürün ne yapıyor, ne yapmıyor? Teknik gerçekçiliği sorgula.]

---

## Rekabet Gerçekliği

[Mevcut rakipler neden yetersiz kalıyor? Ama rakipler bu açığı fark etmedi mi? Onlar da aynı şeyi yapabilir mi?]

---

## Finansal Gerçekçilik

[Fiyatlandırma önerisi ve dayandığı mantık. 12 aylık MRR tahmini — gerçekçi, abartısız.]

---

## İlk Müşteriye Ulaşma Yolu

[Reklam yok. Hangi topluluk, kanal veya niş? Neden orada? İlk 10 müşteri için somut plan.]

---

## Sonuç: Bu Fikrin Önüne Geçebilecek Riskler

[En az 3 somut risk. Bunları görmezden gelmek hata olur. Nesnel ve kısa.]

---

Sadece raporu yaz.
"""

    try:
        memo = get_llm(temp=0.4).invoke([HumanMessage(content=prompt)]).content
        print("[DeepResearch] ✅ Y-Combinator tarzı Memo hazır.")
        return {**state, "investment_memo": memo}
    except Exception as e:
        return {**state, "error": f"Memo hatası: {e}"}

# ──────────────────────────────────────────────
# NODE 7: Find Buyer Leads (Sütunlar & Matchev)
# ──────────────────────────────────────────────
def find_buyer_leads_node(state: DeepAgentState) -> DeepAgentState:
    if state.get("error"): return state
    print("[DeepResearch] Node 7 → find_buyer_leads (Müşteriler Bulunuyor...)")
    
    ideas = state.get("selected_angle", "")
    target = state.get("target_category", "")
    
    raw_leads = []
    
    # 1. Upwork/Fiverr RSS (Kısılmış aramalar ile)
    print("  [DeepResearch] Upwork taranıyor...")
    try:
        jobs = check_upwork_rss(target, limit=3)
        raw_leads.extend(jobs)
    except Exception as e:
         print(f"  [DeepResearch] ⚠️ Upwork Hatası: {e}")
         
    # 2. Reddit Çaresizlik Forumları
    print("  [DeepResearch] Reddit taranıyor...")
    # Basit bir kelime eşleştirme yapalım
    subreddits = ["accounting", "lawyers", "realtors"] 
    if "design" in target.lower(): subreddits = ["graphicdesign", "UI_Design"]
    elif "code" in target.lower(): subreddits = ["learnprogramming", "webdev"]
    elif "marketing" in target.lower(): subreddits = ["marketing", "SEO"]
    
    try:
        reddit_leads = scan_reddit_desperation(subreddits, limit=2)
        raw_leads.extend(reddit_leads)
    except Exception as e:
        print(f"  [DeepResearch] ⚠️ Reddit Hatası: {e}")
        
    # 3. GitHub UI
    print("  [DeepResearch] GitHub taranıyor...")
    try:
        github_leads = scrape_github_gui_requests("ai")
        # Listeyi dönüştürelim
        for gl in github_leads[:2]:
            raw_leads.append({
                "source": "GitHub",
                "title": gl["opportunity"],
                "url": gl["example_issue_url"],
                "desc": f"Repo: {gl['repo_name']} | Stars: {gl['repo_stars']} | GUI Demands: {gl['gui_demand_count']}"
            })
    except Exception as e:
        print(f"  [DeepResearch] ⚠️ GitHub Hatası: {e}")
        
    # 4. Alıcı Eşleştirme (DM Pitch)
    print("  [DeepResearch] LLM ile Soğuk Satış Şablonları (DM) yazılıyor...")
    try:
        matcher = BuyerMatcherAgent()
        matched_leads = matcher.process_leads(raw_leads[:10], saas_idea=ideas)
        return {**state, "buyer_leads": matched_leads}
    except Exception as e:
        print(f"  [DeepResearch] ⚠️ Matcher Hatası: {e}")
        return {**state, "buyer_leads": raw_leads}

# ──────────────────────────────────────────────
# GRAPH CONFIGURATION
# ──────────────────────────────────────────────
def build_deep_graph():
    graph = StateGraph(DeepAgentState)
    
    graph.add_node("init_research", init_research_node)
    graph.add_node("brainstorm_angles", brainstorm_angles_node)
    graph.add_node("deep_web_research", deep_web_research_node)
    graph.add_node("competitor_deep_dive", competitor_deep_dive_node)
    graph.add_node("reasoning_synthesis", reasoning_synthesis_node)
    graph.add_node("write_investment_memo", write_investment_memo_node)
    graph.add_node("find_buyer_leads", find_buyer_leads_node)
    
    graph.set_entry_point("init_research")
    graph.add_edge("init_research", "brainstorm_angles")
    graph.add_edge("brainstorm_angles", "deep_web_research")
    graph.add_edge("deep_web_research", "competitor_deep_dive")
    graph.add_edge("competitor_deep_dive", "reasoning_synthesis")
    graph.add_edge("reasoning_synthesis", "write_investment_memo")
    graph.add_edge("write_investment_memo", "find_buyer_leads")
    graph.add_edge("find_buyer_leads", END)
    
    return graph.compile()

deep_agent = build_deep_graph()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    cat = sys.argv[1] if len(sys.argv) > 1 else "data extraction"
    print(f"=== DEEP RESEARCH TEST: {cat} ===")
    
    for event in deep_agent.stream({
        "target_category": cat,
        "trending_models": [],
        "known_apps": [],
        "brainstormed_angles": [],
        "web_research_results": [],
        "competitor_insights": "",
        "selected_angle": "",
        "investment_memo": "",
        "buyer_leads": [],
        "automation_signals": [],
        "product_gaps": [],
        "seo_data": {},
        "error": None
    }):
        node_name = list(event.keys())[0]
        print(f"--> Tamamlandı: {node_name}")
        
    print("\n\n" + "="*50)
    final_output = event[node_name].get("buyer_leads")
    print(f"Bulunan Hazır Alıcı Sayısı: {len(final_output) if final_output else 0}")
