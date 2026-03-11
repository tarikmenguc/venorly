import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.idea_agent import idea_agent
from agent.deep_agent import deep_agent
from agent.reverse_agent import reverse_agent
from agent.orchestrator import orchestrator_agent
from scrapers.automation_intel import collect_automation_intelligence
from scrapers.producthunt_gaps import find_product_gaps

app = FastAPI(title="Startup Idea Finder API")

# Allow Next.js frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    mode: str  # "discover", "deep", "reverse"
    category: str = ""
    target_startup: str = ""

@app.post("/api/scan")
async def scan_endpoint(req: ScanRequest):
    def event_generator():
        try:
            if req.mode == "discover" or req.mode == "category":
                initial_state = {
                    "user_category": req.category,
                    "target_category": req.category,
                    "trending_models": [],
                    "known_apps": [],
                    "matching_apps": [],
                    "competitor_complaints": [],
                    "store_app_ids": [],
                    "store_reviews": [],
                    "validation_details": "",
                    "competition_matrix": "",
                    "final_report": "",
                    "error": None
                }
                for event in idea_agent.stream(initial_state):
                    node_name = list(event.keys())[0]
                    result = event[node_name]
                    # We send progress out in Server-Sent Events (SSE) format
                    data = {"node": node_name, "state": result}
                    yield f"data: {json.dumps(data)}\n\n"

            elif req.mode == "deep":
                # n8n/Make.com otomasyon istihbaratını topla
                automation_signals = []
                try:
                    automation_signals = collect_automation_intelligence(req.category)
                except Exception as e:
                    print(f"[API] Otomasyon istihbaratı hatası (devam ediyor): {e}")

                # Product Hunt boşluk analizi
                product_gaps = []
                try:
                    product_gaps = find_product_gaps(req.category)
                except Exception as e:
                    print(f"[API] Product Hunt gap hatası (devam ediyor): {e}")

                initial_state = {
                    "target_category": req.category,
                    "trending_models": [],
                    "known_apps": [],
                    "brainstormed_angles": [],
                    "web_research_results": [],
                    "competitor_insights": "",
                    "selected_angle": "",
                    "investment_memo": "",
                    "buyer_leads": [],
                    "automation_signals": automation_signals,
                    "product_gaps": product_gaps,
                    "error": None
                }
                for event in deep_agent.stream(initial_state):
                    node_name = list(event.keys())[0]
                    result = event[node_name]
                    data = {"node": node_name, "state": result}
                    yield f"data: {json.dumps(data)}\n\n"

            elif req.mode == "reverse":
                initial_state = {
                    "target_startup": req.target_startup,
                    "startup_analysis": "",
                    "competitors": [],
                    "complaints": [],
                    "matching_models": [],
                    "disruption_report": "",
                    "error": None
                }
                for event in reverse_agent.stream(initial_state):
                    node_name = list(event.keys())[0]
                    result = event[node_name]
                    data = {"node": node_name, "state": result}
                    yield f"data: {json.dumps(data)}\n\n"

            elif req.mode == "orchestrate":
                # Multi-Agent Orkestrasyon modu
                automation_signals = []
                product_gaps = []
                try:
                    automation_signals = collect_automation_intelligence(req.category)
                except Exception as e:
                    print(f"[API] Otomasyon istihbaratı hatası (devam ediyor): {e}")
                try:
                    product_gaps = find_product_gaps(req.category)
                except Exception as e:
                    print(f"[API] Product Hunt gap hatası (devam ediyor): {e}")

                initial_state = {
                    "target_category": req.category,
                    "trending_models": [],
                    "known_apps": [],
                    "automation_signals": automation_signals,
                    "product_gaps": product_gaps,
                    "research_summary": "",
                    "brainstormed_angles": [],
                    "web_research_results": [],
                    "competitor_insights": "",
                    "selected_angle": "",
                    "investment_memo": "",
                    "buyer_leads": [],
                    "waitlist_data": {},
                    "agent_log": [],
                    "error": None,
                }
                for event in orchestrator_agent.stream(initial_state):
                    node_name = list(event.keys())[0]
                    result = event[node_name]
                    data = {"node": node_name, "state": result}
                    yield f"data: {json.dumps(data)}\n\n"

            elif req.mode == "trends":
                yield f"data: {json.dumps({'node': 'analyzing_trends', 'state': {'currentNode': 'Trendler aranıyor...'}})}\n\n"
                
                from agent.idea_agent import get_models_store, get_llm
                from langchain_core.messages import HumanMessage
                
                models_store = get_models_store()
                query = req.category if req.category else "Trending AI Models"
                docs = models_store.similarity_search(query, k=15)
                
                models_text = "\n".join([f"- {d.metadata.get('name', 'Bilinmeyen Model')}: (Kategori: {d.metadata.get('category', 'Genel')}) - {d.page_content[:150]}" for d in docs])
                
                prompt = f"""Sen üst düzey bir Silikon Vadisi AI Trend Analistisin. 
Aşağıdaki HuggingFace modellerine ve verilerine bakarak pazarın NEYE DOĞRU gittiğini, önümüzdeki 6 ay içinde hangi niş alanların patlayacağını anlatan çarpıcı ve vizyoner bir 'Trend Raporu' (Markdown formatında, çok şık) yaz.

Kullanıcı Taraması: {query}
Bulunan Modeller:
{models_text}

Rapor Formatı:
# 📈 AI Trend Analizi: {query.upper() if req.category else 'GENEL PAZAR'}
## 1. Yükselen Dalga (Neler Popüler?)
## 2. Gözden Kaçan Fırsatlar (Sessizce Büyüyenler)
## 3. Önümüzdeki 6 Ayın Tahmini
"""
                report = get_llm(temp=0.5).invoke([HumanMessage(content=prompt)]).content
                yield f"data: {json.dumps({'node': 'generate_opportunity', 'state': {'final_report': report}})}\n\n"
            
            # Indicate completion
            yield f"data: {json.dumps({'status': 'done'})}\n\n"
            
        except Exception as e:
            # Send error if anything fails during streaming
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    # If run directly: python api.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
