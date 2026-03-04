import os
import sys
import json
from typing import TypedDict, List, Optional
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END

# Proje kökünü path'e ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from agent.idea_agent import get_llm, get_models_store, get_apps_store

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
    error: Optional[str]

tavily = TavilySearchResults(max_results=3)

# ──────────────────────────────────────────────
# NODE 1: Init Research (Veri Hazırlama)
# ──────────────────────────────────────────────
def init_research_node(state: DeepAgentState) -> DeepAgentState:
    print(f"[DeepResearch] Node 1 → init_research ({state['target_category']})")
    try:
        models_store = get_models_store()
        apps_store = get_apps_store()
        
        # Modelleri Çek
        m_docs = models_store.similarity_search(state['target_category'], k=10)
        trending_models = []
        for d in m_docs:
            m = d.metadata.copy()
            m['description'] = d.page_content
            trending_models.append(m)
            
        # App'leri Çek
        a_docs = apps_store.similarity_search(state['target_category'], k=10)
        known_apps = []
        for d in a_docs:
            a = d.metadata.copy()
            a['description'] = d.page_content
            known_apps.append(a)
            
        return {**state, "trending_models": trending_models, "known_apps": known_apps}
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
    
    prompt = f"""Hedef Kategori: {state['target_category']}
Pazardaki AI Modelleri: {models_text}
Mevcut Kazanan Uygulamalar: {apps_text}

Sen bir Micro-SaaS kuluçka merkezi yöneticisisin. Bu verilerden yola çıkarak, pazarın boşluklarına yönelik 3 tamamen farklı ve spesifik 'Saldırı Açısı' (Hypothesis/Angle) oluştur.
Her bir açı, farklı bir dar niş kitleyi ve farklı bir kullanım alanını hedeflemeli.

Format (kesinlikle bu formata uy):
Açı 1: [açıklama]
Açı 2: [açıklama]
Açı 3: [açıklama]"""

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
    for i, angle in enumerate(state["brainstormed_angles"]):
        print(f"  [DeepResearch] 🔍 Açı {i+1} için web taranıyor...")
        try:
            # 1. Rakipler araması
            q1 = f"{angle} SaaS tools software competitors"
            res1 = tavily.invoke(q1)
            # 2. Şikayet araması
            q2 = f"{angle} software reddit complaints issues"
            res2 = tavily.invoke(q2)
            
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
    
    prompt = f"""Sen Y Combinator'dan deneyimli bir yatırımcı ve mühendissin. 
Aşağıdaki 3 Micro-SaaS hipotezini ve rakip pazar analizini oku.
Mantıklı düşün ve sadece EN uygulanabilir, pazar giriş bariyeri düşük ve kârlı olan TEK BİR fikri seç.

Hipotezler:
{angles}

Pazar Analizi (Tavily):
{insights}

Seçtiğin açı, seçme nedenin ve pazara hücum (go-to-market) stratejin nedir? Kısaca açıkla."""

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
    
    prompt = f"""Görevin, aşağıdaki yatırımcı kararını alıp profesyonel bir "Investment Memo" (Yatırım Karar Metni) formatında Mükemmel bir Markdown raporu oluşturmak.

Karar ve Strateji:
{decision}

Kullanılabilecek AI Modelleri:
{models}

Format:
# 🧠 Deep Research Analizi: [Odaklanılan Ürün/Niş]

## 1. Executive Summary
[Hızlı özet]

## 2. Thesis (Yatırım Tezi)
[Neden bu alanda bir boşluk var?]

## 3. Product Vision & AI Stack
[Hangi AI modelleri kullanılacak, ürün tam olarak ne yapacak]

## 4. Competitive Dynamics (Rekabet)
[Mevcut rakipler neden yetersiz kalıyor?]

## 5. Financial Projections & Pricing
[Micro-SaaS fiyatlandırması (örn: Free/$29/$99) ve 12 aylık potansiyel MRR tahmini]

## 6. Go-to-Market Strategy
[İlk 100 kullanıcıya ulaşma taktikleri]
"""

    try:
        memo = get_llm(temp=0.4).invoke([HumanMessage(content=prompt)]).content
        print("[DeepResearch] ✅ Y-Combinator tarzı Memo hazır.")
        return {**state, "investment_memo": memo}
    except Exception as e:
        return {**state, "error": f"Memo hatası: {e}"}

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
    
    graph.set_entry_point("init_research")
    graph.add_edge("init_research", "brainstorm_angles")
    graph.add_edge("brainstorm_angles", "deep_web_research")
    graph.add_edge("deep_web_research", "competitor_deep_dive")
    graph.add_edge("competitor_deep_dive", "reasoning_synthesis")
    graph.add_edge("reasoning_synthesis", "write_investment_memo")
    graph.add_edge("write_investment_memo", END)
    
    return graph.compile()

deep_agent = build_deep_graph()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    cat = sys.argv[1] if len(sys.argv) > 1 else "freelance designers"
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
        "error": None
    }):
        node_name = list(event.keys())[0]
        print(f"--> Tamamlandı: {node_name}")
        
    print("\n\n" + "="*50)
    final_output = event[node_name].get("investment_memo") or event[node_name].get("error")
    print(final_output)
