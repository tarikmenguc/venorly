from langchain_core.messages import HumanMessage
from typing import TypedDict, Any

def competition_matrix_node(state: Any) -> Any:
    """Rakipleri karşılaştıran bir markdown tablosu oluşturur."""
    print("[Agent] Node 8.5 → competition_matrix")
    from agent.idea_agent import get_llm
    
    apps = state.get("matching_apps", [])
    if not apps:
        return {**state, "competition_matrix": "Rakip uygulama bulunamadı."}
        
    apps_data = []
    for a in apps[:5]:
        name = a.get("name", "Bilinmiyor")
        mrr = a.get("mrr") or "?"
        source = a.get("source", "Bilinmiyor")
        desc = a.get("description", "")[:100]
        apps_data.append(f"- {name} (MRR: {mrr}, Kaynak: {source}) | Özeti: {desc}")
        
    apps_text = "\n".join(apps_data)
    complaints = state.get("complaint_clusters", "")
    
    prompt = f"""Şu rakipler ve bilinen pazar şikayetleri hakkında bir Rekabet Analizi Tablosu (Markdown) oluştur.

    Rakipler:
    {apps_text}
    
    Şikayetler:
    {complaints}
    
    Tablo şu sütunlara sahip olmalı:
    Rakip Adı | Mevcut Model (Vitamin mi?) | Çözülemeyen Acı Noktası | 1 Tıkla Ne Kadar Zaman Kazandırabilir | MRR
    
    Sadece ve sadece Markdown tablosunu üret, başka bir metin yazma."""
    
    try:
        matrix_md = get_llm(temp=0.1).invoke([HumanMessage(content=prompt)]).content.strip()
    except Exception as e:
        print(f"[Agent] Matrix hatası: {e}")
        matrix_md = "Rekabet matrisi oluşturulamadı."

    print("[Agent] ✅ Rekabet matrisi oluşturuldu.")
    return {**state, "competition_matrix": matrix_md}
