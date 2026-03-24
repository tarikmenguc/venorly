import json
from fastapi import FastAPI, Request, Response
from lib.pdf_generator import generate_report_pdf
from lib.supabase_client import supabase
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Heavy agent/scraper imports are LAZY-LOADED inside endpoints
# to allow uvicorn to bind the port instantly on Render.com
# (importing them here blocks startup for 60+ seconds → port timeout)

app = FastAPI(title="Startup Idea Finder API")

# Allow Next.js frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/scans/{scan_id}/pdf")
async def get_scan_pdf(scan_id: str):
    try:
        # Supabase'den scan verisini çek
        res = supabase.table("scans").select("*").eq("id", scan_id).single().execute()
        scan_data = res.data
        
        if not scan_data:
            return Response(content="Scan not found", status_code=404)
            
        # PDF üret
        pdf_bytes = generate_report_pdf(scan_data)
        
        # Dosya adını temizle
        filename = f"Report_{scan_data.get('category', 'Analysis').replace(' ', '_')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        return Response(content=str(e), status_code=500)

# ============ AI CHAT (Fikir Danışmanı) ============

CHAT_LIMIT_PER_SCAN = 15

class ChatRequest(BaseModel):
    scan_id: str
    message: str

@app.get("/api/chat/{scan_id}")
async def get_chat_history(scan_id: str):
    """Bir taramaya ait sohbet geçmişini döner."""
    try:
        res = supabase.table("chat_messages").select("*").eq("scan_id", scan_id).order("created_at").execute()
        return {"messages": res.data or [], "limit": CHAT_LIMIT_PER_SCAN}
    except Exception as e:
        return Response(content=str(e), status_code=500)

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Rapor bağlamında AI ile sohbet — streaming SSE."""
    try:
        # 1. Mesaj limiti kontrolü
        count_res = supabase.table("chat_messages").select("id", count="exact").eq("scan_id", req.scan_id).eq("role", "user").execute()
        user_msg_count = count_res.count or 0
        if user_msg_count >= CHAT_LIMIT_PER_SCAN:
            return Response(
                content=json.dumps({"error": f"Bu tarama için mesaj limitinize ({CHAT_LIMIT_PER_SCAN}) ulaştınız."}),
                status_code=429,
                media_type="application/json"
            )

        # 2. Rapor bağlamını çek
        scan_res = supabase.table("scans").select("category, mode, full_report, report_preview").eq("id", req.scan_id).single().execute()
        scan_data = scan_res.data

        report_context = ""
        if scan_data:
            fr = scan_data.get("full_report", {})
            if isinstance(fr, dict):
                report_context = fr.get("investment_memo", "") or fr.get("final_report", "") or scan_data.get("report_preview", "")
            elif isinstance(fr, str):
                report_context = fr
            else:
                report_context = scan_data.get("report_preview", "")

        # 3. Geçmiş mesajları al
        history_res = supabase.table("chat_messages").select("role, content").eq("scan_id", req.scan_id).order("created_at").execute()
        history = history_res.data or []

        # 4. Kullanıcı mesajını kaydet
        supabase.table("chat_messages").insert({
            "scan_id": req.scan_id,
            "role": "user",
            "content": req.message
        }).execute()

        # 5. LLM çağrısı (streaming)
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        system_prompt = f"""Sen "Startup Idea Finder" uygulamasının yerleşik AI danışmanısın. 
Kullanıcı bir pazar araştırması yaptı ve aşağıdaki raporu aldı. Şimdi seninle bu rapor hakkında konuşmak istiyor.

KURALLAR:
- SADECE bu rapor bağlamında cevap ver. Genel sohbet yapma.
- Kısa, net ve aksiyon odaklı cevaplar ver (max 300 kelime).
- Türkçe cevap ver.
- Emojileri kullanarak cevapları okunabilir yap.
- Fiyatlandırma, teknik mimari, müşteri bulma, rakip analizi gibi konularda uzman gibi davran.

RAPOR BAĞLAMI:
Kategori: {scan_data.get('category', 'Bilinmiyor') if scan_data else 'Bilinmiyor'}
Mod: {scan_data.get('mode', 'Bilinmiyor') if scan_data else 'Bilinmiyor'}

---
{report_context[:3000]}
---"""

        messages = [SystemMessage(content=system_prompt)]
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=req.message))

        from agent.idea_agent import get_llm
        llm = get_llm(temp=0.6)

        def chat_stream():
            full_response = ""
            try:
                for chunk in llm.stream(messages):
                    token = chunk.content
                    if token:
                        full_response += token
                        yield f"data: {json.dumps({'token': token})}\n\n"

                # Stream bittikten sonra assistant mesajını kaydet
                supabase.table("chat_messages").insert({
                    "scan_id": req.scan_id,
                    "role": "assistant",
                    "content": full_response
                }).execute()

                yield f"data: {json.dumps({'done': True, 'remaining': CHAT_LIMIT_PER_SCAN - user_msg_count - 1})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(chat_stream(), media_type="text/event-stream")

    except Exception as e:
        print(f"Chat Error: {e}")
        return Response(content=json.dumps({"error": str(e)}), status_code=500, media_type="application/json")

# ============ SCAN ENDPOINT ============

class ScanRequest(BaseModel):
    mode: str  # "discover", "deep", "reverse"
    category: str = ""
    target_startup: str = ""

@app.post("/api/scan")
async def scan_endpoint(req: ScanRequest, request: Request):
    # --- RATE LIMITING (Kullanım Limiti) Başlangıcı ---
    # Gerçek IP adresini alıyoruz (Vercel vb. arkasındaysa x-forwarded-for)
    client_ip = request.client.host
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0]

    def is_limit_exceeded(ip: str, mode: str) -> bool:
        try:
            from lib.supabase_client import supabase
            from datetime import datetime, timezone, timedelta
            
            # Son 24 saatin başlangıcı
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            
            # Bu IP'nin son 24 saatteki spesifik kullanım geçmişini çek
            res = supabase.table("usage_logs").select("*").eq("ip_address", ip).gte("created_at", yesterday).execute()
            logs = res.data
            
            # Toplam günlük hak (Discover vb.) -> Max 3
            # Toplam günlük ağır analiz hakkı (Deep/Orchestrate) -> Max 1
            
            total_uses = len(logs)
            heavy_uses = sum(1 for log in logs if log.get("action_type") in ["deep", "orchestrate"])
            
            if mode in ["deep", "orchestrate"]:
                if heavy_uses >= 999: # Geçici olarak limite takılmasın
                    return True # Ağır analiz limiti doldu
            else:
                if total_uses >= 999: # Geçici olarak limite takılmasın
                     return True # Genel limit doldu (Discover vb.)
            
            # Limit aşılmadıysa, kullanımı kaydet (logla)
            supabase.table("usage_logs").insert({
                "ip_address": ip,
                "action_type": mode
            }).execute()
            
            return False
            
        except Exception as e:
            print(f"Rate Limiting Error: {e}")
            # Hata durumunda (Supabase göçerse vb.) blocklamamak için False dön
            return False

    # Limiti kontrol et
    if is_limit_exceeded(client_ip, req.mode):
        async def err_gen():
            error_msg = "Günlük ücretsiz limitinize ulaştınız. Derin analizler için günde 1, keşifler için günde 3 hakkınız bulunmaktadır. Lütfen yarın tekrar deneyin."
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")
    # --- RATE LIMITING Bitişi ---

    def event_generator():
        # Lazy imports — only loaded when a scan request arrives
        from agent.idea_agent import idea_agent
        from agent.deep_agent import deep_agent
        from agent.reverse_agent import reverse_agent
        from agent.orchestrator import orchestrator_agent
        from scrapers.automation_intel import collect_automation_intelligence
        from scrapers.producthunt_gaps import find_product_gaps

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
                    
                    # Supabase'e kaydet (sadece son adımda)
                    if node_name == "gtm_agent" and "selected_angle" in result:
                        try:
                            from lib.supabase_client import supabase
                            import uuid
                            
                            scan_id = str(uuid.uuid4())
                            leads_count = len(result.get("buyer_leads", []))
                            angles_count = len(result.get("brainstormed_angles", []))
                            
                            # 1. Taramayı kaydet
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
                            
                            # 2. Lead'leri kaydet
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
                    # scan_id'yi frontend'e gönder (chat paneli için)
                    if 'scan_id' in dir() and scan_id:
                        data["scan_id"] = scan_id
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
