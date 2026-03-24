import os
import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults

# --- 1. State Tanımı ---
class ReverseState(TypedDict):
    target_startup: str
    startup_analysis: str
    competitors: list[str]
    competitor_complaints: list[dict]
    complaint_clusters: str
    matching_models: list[dict]
    final_report: str
    error: str

# --- 2. Araçlar ve LLM ---
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
tavily_search = TavilySearchResults(max_results=3)

# --- 3. Node'lar ---

def analyze_startup_node(state: ReverseState):
    target = state["target_startup"]
    print(f"[Reverse] Node 1 → analyze_startup: {target}")
    
    prompt = f"""'{target}' adlı girişimi/uygulamayı analiz et.
    Tavily search API kullanarak şu soruları yanıtla:
    1. Ne yapıyor? (Hangi problemi çözüyor)
    2. Hedef kitlesi kim?
    3. Hangi sektörde faaliyet gösteriyor?
    Mümkün olduğunca spesifik ol.
    """
    
    try:
        search_results = tavily_search.invoke(f"{target} software saas app what it does pricing")
        analysis_prompt = f"Gelen arama sonuçları: {json.dumps(search_results)}. \n{prompt}"
        analysis = llm.invoke(analysis_prompt).content
        return {"startup_analysis": analysis}
    except Exception as e:
        return {"error": f"Analyze hatası: {e}"}

def find_competitors_node(state: ReverseState):
    if state.get("error"): return state
    print("[Reverse] Node 2 → find_competitors")
    
    analysis = state["startup_analysis"]
    target = state["target_startup"]
    
    prompt = f"""Şu girişimin analizine göre '{target}' isimli girişime rakip olabilecek VEYA aynı pazarı paylaşan 3 adet BAŞKA yazılım/saas uygulaması söyle.
    Sadece uygulama isimlerini virgülle ayrılarak ver (örnek: App1, App2, App3). Ekstra metin yazma.
    
    Analiz: {analysis}
    """
    
    try:
        result = llm.invoke(prompt).content
        competitors = [c.strip() for c in result.split(",") if c.strip()][:3]
        if not competitors:
            competitors = [target] # Fallback
        return {"competitors": competitors}
    except Exception as e:
        return {"error": f"Competitors hatası: {e}"}

def scrape_all_complaints_node(state: ReverseState):
    if state.get("error"): return state
    print("[Reverse] Node 3 → scrape_all_complaints")
    
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scrapers.competitor_research import search_competitor_complaints
    
    competitors = state["competitors"]
    all_complaints = []
    
    for comp in competitors:
        print(f"  [Reverse] '{comp}' şikayetleri çekiliyor...")
        comps = search_competitor_complaints(comp)
        all_complaints.extend(comps)
        
    return {"competitor_complaints": all_complaints}

def find_matching_ai_model_node(state: ReverseState):
    if state.get("error"): return state
    print("[Reverse] Node 4 → find_matching_ai_model")
        
    analysis = state["startup_analysis"]
    complaints = state["competitor_complaints"]
    
    # Şikayetleri kümele
    complaints_text = " ".join([c["title"] + " " + c["content"] for c in complaints[:20]])
    
    prompt = f"""Şu girişim analizi ve rakip şikayetlerine bakarak, bu pazarı 'disrupt' edebilecek (yıkıcı yenilik getirebilecek) bir AI modelinden ne bekleriz? 
    Sadece 5 anahtar kelime ver.
    Analiz: {analysis}
    Şikayetler: {complaints_text[:1000]}
    """
    
    keywords = llm.invoke(prompt).content
    print(f"  [Reverse] Arama kelimeleri: {keywords}")
    
    matching_models = []
    from tavily import TavilyClient
    try:
        tclient = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = tclient.search(
            f"trending AI models APIs tools for {keywords.strip()} 2024 2025",
            max_results=5, search_depth="basic"
        )
        for r in results.get("results", []):
            matching_models.append({
                "name": r.get("title", ""),
                "description": r.get("content", "")[:300],
                "url": r.get("url", ""),
            })
    except Exception as e:
        print(f"  [Reverse] ⚠️ Tavily model arama hatası: {e}")
            
    return {"matching_models": matching_models}

def generate_disruption_report_node(state: ReverseState):
    if state.get("error"): return state
    print("[Reverse] Node 5 → generate_disruption_report")
    
    target = state["target_startup"]
    analysis = state["startup_analysis"]
    complaints = state["competitor_complaints"]
    models = state["matching_models"]
    
    complaints_text = ""
    for c in complaints[:10]:
        complaints_text += f"- {c['app']} ({c['source']}): {c['title']} | {c['content'][:100]}\n"
        
    models_text = ""
    for m in models:
        models_text += f"- {m.get('name')} ({m.get('source')}): {m.get('description', '')[:100]} | Dls: {m.get('downloads', 0)}\n"
        
    prompt = f"""Sen bir yıkıcı B2B SaaS inovasyon (disruptive innovation) uzmanısın.
    Hedefimiz '{target}' adlı girişimin pazarına girip onu alt etmek veya o pazarda B2B müşterilerin saatlerini çalan spesifik bir açığı yakalayıp yeni bir Micro-SaaS yaratmak.
    
    --- VERİLER ---
    Hedef Analizi: {analysis}
    Rakip Pazar Şikayetleri:
    {complaints_text if complaints_text else 'Şikayet bulunamadı.'}
    Kullanabileceğimiz Açık Kaynak/API AI Modelleri:
    {models_text if models_text else 'Model bulunamadı.'}
    
    --- GÖREV ---
    Sadece 'B2B/Painkiller' ve '1-Tıkla Otomasyon' (Friction Economy) kurallarına uyarak aşağıdaki formatta detaylı, somut, sayılarla dolu bir 'Disruption (Yıkım) Raporu' oluştur:
    
    🔥 HEDEF: {target} (Disruption Raporu)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🎯 Hedefin "Vitamin" Kaldığı Zayıf Noktalar: (Şikayetlerden yola çıkarak müşterinin hala manuel yaptığı angaryalar neler?)
    
    🥊 Yıkıcı Fikir (Ağrı Kesici B2B SaaS): (Hangi AI modeliyle, bu angaryayı nasıl 1 tıklamaya indireceğiz?)
    
    💰 Ödeme İsteği (Willingness to Pay): (Müşteriler bu 1 tıklama için neden {target}'a ödedikleri parayı bırakıp bize ödesin? Kaç saat kurtaracaklar?)
    
    ⏱️ Tahmini MVP Geliştirme Süresi: (MVP: X hafta)
    
    🔧 Teknik Zorluk: (1-5 Puan)
    
    🚀 Piyasaya Giriş (GTM) Stratejisi: (Rakiplerin kullanıcılarını nasıl çalacağız? Hangi Reddit/Upwork vb. nişlere gideğiz?)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    report = llm.invoke(prompt).content
    return {"final_report": report}

# --- 4. Graph Oluşturma ---
workflow = StateGraph(ReverseState)

workflow.add_node("analyze_startup", analyze_startup_node)
workflow.add_node("find_competitors", find_competitors_node)
workflow.add_node("scrape_all_complaints", scrape_all_complaints_node)
workflow.add_node("find_matching_ai_model", find_matching_ai_model_node)
workflow.add_node("generate_disruption_report", generate_disruption_report_node)

workflow.set_entry_point("analyze_startup")
workflow.add_edge("analyze_startup", "find_competitors")
workflow.add_edge("find_competitors", "scrape_all_complaints")
workflow.add_edge("scrape_all_complaints", "find_matching_ai_model")
workflow.add_edge("find_matching_ai_model", "generate_disruption_report")
workflow.add_edge("generate_disruption_report", END)

reverse_agent = workflow.compile()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Test: Reverse Agent")
    result = reverse_agent.invoke({
        "target_startup": "Jasper AI",
        "startup_analysis": "",
        "competitors": [],
        "competitor_complaints": [],
        "complaint_clusters": "",
        "matching_models": [],
        "final_report": "",
        "error": ""
    })
    print(result.get("final_report", result.get("error")))
