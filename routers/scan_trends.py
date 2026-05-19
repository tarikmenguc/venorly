"""
Scan — Trends Modu
Tavily + LLM ile AI trend raporu üretir.
"""

import json


def generate_trends_events(req):
    """Trends modu için SSE olay üreteci."""
    from lib.llm import get_llm
    from lib.tavily_client import get_tavily_client
    from langchain_core.messages import HumanMessage

    yield f"data: {json.dumps({'node': 'analyzing_trends', 'state': {'currentNode': 'Trendler aranıyor...'}})}\n\n"

    query = req.category if req.category else "Trending AI Models"

    try:
        tclient = get_tavily_client()
        results = tclient.search(
            f"trending top AI models tools for {query} 2024 2025",
            max_results=10,
            search_depth="basic",
        )
        models_list = [
            f"- {r.get('title', 'Bilinmeyen Model')}: {r.get('content', '')[:150]}"
            for r in results.get("results", [])
        ]
        models_text = "\n".join(models_list)
    except Exception as e:
        models_text = f"Tavily arama hatası: {e}"

    prompt = f"""Sen üst düzey bir Silikon Vadisi AI Trend Analistisin.
Aşağıdaki modellere ve verilere bakarak pazarın NEYE DOĞRU gittiğini, önümüzdeki 6 ay içinde hangi niş alanların patlayacağını anlatan çarpıcı ve vizyoner bir 'Trend Raporu' (Markdown formatında, çok şık) yaz.

Kullanıcı Taraması: {query}
Bulunan Modeller:
{models_text}

Rapor Formatı:
# 📈 AI Trend Analizi: {query.upper()}
## 1. Yükselen Dalga (Neler Popüler?)
## 2. Gözden Kaçan Fırsatlar (Sessizce Büyüyenler)
## 3. Önümüzdeki 6 Ayın Tahmini
"""
    report = get_llm(temp=0.5).invoke([HumanMessage(content=prompt)]).content
    yield f"data: {json.dumps({'node': 'generate_opportunity', 'state': {'final_report': report}})}\n\n"
