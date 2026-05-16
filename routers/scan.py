"""
Scan endpoint — Tüm tarama modları (discover, deep, reverse, orchestrate, trends)
"""
import json
import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lib.supabase_client import supabase
from lib.auth_middleware import verify_user_token
from lib.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ScanRequest(BaseModel):
    mode: str  # "discover", "deep", "reverse", "orchestrate", "trends"
    category: str = ""
    target_startup: str = ""


def _check_rate_limit(ip: str, mode: str) -> bool:
    """Kullanıcının günlük limitini kontrol et. True = limit aşıldı."""
    try:
        from datetime import datetime, timezone, timedelta

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        res = supabase.table("usage_logs").select("*").eq("ip_address", ip).gte("created_at", yesterday).execute()
        logs = res.data

        total_uses = len(logs)
        heavy_uses = sum(1 for log in logs if log.get("action_type") in ["deep", "orchestrate"])

        if mode in ["deep", "orchestrate"]:
            if heavy_uses >= 999:  # Geçici olarak limite takılmasın
                return True
        else:
            if total_uses >= 999:  # Geçici olarak limite takılmasın
                return True

        # Kullanımı kaydet
        supabase.table("usage_logs").insert({
            "ip_address": ip,
            "action_type": mode
        }).execute()

        return False

    except Exception as e:
        print(f"Rate Limiting Error: {e}")
        return False


@router.post("/api/scan")
async def scan_endpoint(req: ScanRequest, request: Request, user: dict = Depends(verify_user_token)):
    # IP adresi al
    client_ip = request.client.host
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0]

    # Rate limit kontrolü
    if _check_rate_limit(client_ip, req.mode):
        async def err_gen():
            error_msg = "Günlük ücretsiz limitinize ulaştınız. Derin analizler için günde 1, keşifler için günde 3 hakkınız bulunmaktadır. Lütfen yarın tekrar deneyin."
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    def event_generator():
        logger.debug(f"event_generator STARTED for mode={req.mode}")
        yield f"data: {json.dumps({'node': 'init', 'state': {'currentNode': 'Modüller yükleniyor...'}})}\n\n"

        # Lazy imports
        try:
            logger.debug("Importing agents...")
            from agent.idea_agent import idea_agent
            from agent.deep_agent import deep_agent
            from agent.reverse_agent import reverse_agent
            from agent.orchestrator import orchestrator_agent
            from scrapers.automation_intel import collect_automation_intelligence
            from scrapers.producthunt_gaps import find_product_gaps
            logger.debug("All imports successful!")
        except Exception as e:
            logger.error(f"Import error: {e}")
            yield f"data: {json.dumps({'error': f'Import hatası: {str(e)}' })}\n\n"
            return

        yield f"data: {json.dumps({'node': 'loaded', 'state': {'currentNode': 'Agent hazır, analiz başlıyor...'}})}\n\n"

        try:
            if req.mode == "discover" or req.mode == "category":
                initial_state = {
                    "user_category": req.category,
                    "target_category": req.category,
                    "trending_models": [],
                    "known_apps": [],
                    "matching_apps": [],
                    "competitor_complaints": [],
                    "complaint_clusters": "",
                    "store_app_ids": [],
                    "store_reviews": [],
                    "store_clusters": "",
                    "validation_details": "",
                    "competition_matrix": "",
                    "final_report": "",
                    "seo_data": {},
                    "error": None
                }
                for event in idea_agent.stream(initial_state):
                    node_name = list(event.keys())[0]
                    result = event[node_name]
                    data = {"node": node_name, "state": result}
                    yield f"data: {json.dumps(data)}\n\n"

            elif req.mode == "deep":
                automation_signals = []
                try:
                    automation_signals = collect_automation_intelligence(req.category)
                except Exception as e:
                    print(f"[API] Otomasyon istihbaratı hatası (devam ediyor): {e}")

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

                    # Supabase'e kaydet (sadece son adımda)
                    if node_name == "gtm_agent" and "selected_angle" in result:
                        try:
                            import uuid

                            scan_id = str(uuid.uuid4())
                            leads_count = len(result.get("buyer_leads", []))
                            angles_count = len(result.get("brainstormed_angles", []))

                            supabase.table("scans").insert({
                                "id": scan_id,
                                "category": req.category,
                                "mode": "orchestrate",
                                "status": "completed",
                                "report_preview": result.get("investment_memo", "")[:200],
                                "leads_count": leads_count,
                                "angles_count": angles_count,
                                "full_report": result
                            }).execute()

                            if leads_count > 0:
                                leads_to_insert = []
                                for l in result["buyer_leads"]:
                                    leads_to_insert.append({
                                        "scan_category": req.category,
                                        "source": l.get("source", "Unknown"),
                                        "title": l.get("title", ""),
                                        "url": l.get("url", ""),
                                        "description": l.get("content", l.get("desc", "")),
                                        "score": l.get("score", 0),
                                        "status": "new",
                                        "dm_template": l.get("dm_template", "")
                                    })
                                supabase.table("leads").insert(leads_to_insert).execute()

                        except Exception as e:
                            print(f"[API] Supabase kayıt hatası: {e}")

                    data = {"node": node_name, "state": result}
                    if 'scan_id' in dir() and scan_id:
                        data["scan_id"] = scan_id
                    yield f"data: {json.dumps(data)}\n\n"

            elif req.mode == "trends":
                yield f"data: {json.dumps({'node': 'analyzing_trends', 'state': {'currentNode': 'Trendler aranıyor...'}})}\n\n"

                from agent.idea_agent import get_llm
                from langchain_core.messages import HumanMessage
                from tavily import TavilyClient

                query = req.category if req.category else "Trending AI Models"

                tclient = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                try:
                    results = tclient.search(
                        f"trending top AI models tools for {query} 2024 2025",
                        max_results=10, search_depth="basic"
                    )
                    models_list = []
                    for r in results.get("results", []):
                        models_list.append(f"- {r.get('title', 'Bilinmeyen Model')}: {r.get('content', '')[:150]}")
                    models_text = "\n".join(models_list)
                except Exception as e:
                    models_text = f"Tavily arama hatası: {e}"

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

            # Completion
            yield f"data: {json.dumps({'status': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
