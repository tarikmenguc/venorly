import os
import requests
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Any

tavily = TavilySearchResults(max_results=3)

def check_url_accessibility(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    try:
        res = requests.get(url, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

def validate_idea_node(state: Any) -> Any:
    """Üretilen fikrin validasyonunu yapar."""
    print("[Validator] Node 9 → validate_idea")
    from agent.idea_agent import get_llm
    
    report = state.get("final_report", "")
    if not report:
        return {**state, "validation_score": 0, "validation_details": "Rapor yok."}
        
    # Fikrin özünü LLM ile çıkar
    extract_prompt = f"Şu rapordan fikrin ne olduğunu sadece 3-5 kelime ile özetle (örn: AI destekli dişçi CRM): {report[:500]}"
    try:
        idea_summary = get_llm(temp=0.1).invoke([HumanMessage(content=extract_prompt)]).content.strip()
    except Exception:
        idea_summary = "AI SaaS tool"
        
    # 1. Tavily ile bu fikre benzer kaç sonuç var bak
    try:
        search_results = tavily.invoke(f"{idea_summary} saas software alternative")
        existing_competitors = len(search_results) if search_results else 0
    except Exception as e:
        print(f"[Validator] Tavily hatası: {e}")
        existing_competitors = -1
        
    # 2. Model URL erişilebilirlik
    models = state.get("trending_models", [])
    api_accessible = True # Default
    if models and len(models) > 0:
        url = models[0].get("url", "")
        if url:
            api_accessible = check_url_accessibility(url)

    # 3. LLM Skorlama
    score_prompt = f"""Bir yatırımcı olarak aşağıdaki Micro-SaaS startup raporunu 1-10 arası puanla.
    Friction Economy Kriterleri:
    - B2B ve "Ağrı Kesici" Odaklılık (B2C ise direkt 1 puan ver)
    - Ödeme İsteği (Willingness to Pay - İnsanlar saatlerce uğraşmamak için buna para öder mi?)
    - Teknik Fizibilite
    
    Rapor: {report[:1500]}
    
    Çıktı Formatı:
    Sadece ve sadece bir sayı ver (örn: 7). Başka hiçbir kelime veya noktalama işareti ekleme."""
    
    try:
        score_str = get_llm(temp=0.1).invoke([HumanMessage(content=score_prompt)]).content.strip()
        score = int(''.join(filter(str.isdigit, score_str)) or "5")
        if score > 10: score = 10
    except Exception as e:
        print(f"[Validator] LLM score hatası: {e}")
        score = 5

    validation_details = f"""
    ✅ **Doğrulama Özeti**
    - **Fizibilite Skoru:** {score}/10
    - **Benzer Rakipler (Web):** {existing_competitors if existing_competitors >= 0 else 'Bilinmiyor'} bulunan sonuç
    - **Model API Durumu:** {'Çalışıyor/Erişilebilir' if api_accessible else 'Erişim Sorunu Olabilir'}
    """
    
    print(f"[Validator] ✅ Skor: {score}/10, Rakipler: {existing_competitors}")
    
    # State'e eklemek için yeni bir field gerekiyor: validation_details
    return {**state, "validation_details": validation_details.strip()}
