"""
Chat endpoints — AI Fikir Danışmanı
"""
import json
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lib.supabase_client import supabase
from lib.auth_middleware import verify_user_token

router = APIRouter()

CHAT_LIMIT_PER_SCAN = 15
FREEFORM_LIMIT = 10


class ChatRequest(BaseModel):
    scan_id: str = ""       # Boş olursa "freeform" (bağımsız) mod
    message: str
    session_id: str = ""    # Freeform modda oturum takibi


@router.get("/api/chat/{scan_id}")
async def get_chat_history(scan_id: str):
    """Bir taramaya ait sohbet geçmişini döner."""
    try:
        res = supabase.table("chat_messages").select("*").eq("scan_id", scan_id).order("created_at").execute()
        return {"messages": res.data or [], "limit": CHAT_LIMIT_PER_SCAN}
    except Exception as e:
        return Response(content=str(e), status_code=500)


@router.post("/api/chat")
async def chat_endpoint(req: ChatRequest, user: dict = Depends(verify_user_token)):
    """Rapor bağlamında veya bağımsız (freeform) AI sohbet — streaming SSE."""
    try:
        # Freeform vs report-bound mod belirleme
        is_freeform = not req.scan_id or req.scan_id.strip() == ""
        chat_id = req.scan_id if not is_freeform else (req.session_id or "freeform_default")
        limit = FREEFORM_LIMIT if is_freeform else CHAT_LIMIT_PER_SCAN

        # 1. Mesaj limiti kontrolü
        count_res = supabase.table("chat_messages").select("id", count="exact").eq("scan_id", chat_id).eq("role", "user").execute()
        user_msg_count = count_res.count or 0
        if user_msg_count >= limit:
            return Response(
                content=json.dumps({"error": f"Mesaj limitinize ({limit}) ulaştınız."}),
                status_code=429,
                media_type="application/json"
            )

        # 2. Rapor bağlamını çek (varsa)
        report_context = ""
        scan_data = None
        if not is_freeform:
            scan_res = supabase.table("scans").select("category, mode, full_report, report_preview").eq("id", req.scan_id).single().execute()
            scan_data = scan_res.data
            if scan_data:
                fr = scan_data.get("full_report", {})
                if isinstance(fr, dict):
                    report_context = fr.get("investment_memo", "") or fr.get("final_report", "") or scan_data.get("report_preview", "")
                elif isinstance(fr, str):
                    report_context = fr
                else:
                    report_context = scan_data.get("report_preview", "")

        # 3. Geçmiş mesajları al
        history_res = supabase.table("chat_messages").select("role, content").eq("scan_id", chat_id).order("created_at").execute()
        history = history_res.data or []

        # 4. Kullanıcı mesajını kaydet
        supabase.table("chat_messages").insert({
            "scan_id": chat_id,
            "role": "user",
            "content": req.message
        }).execute()

        # 5. System prompt seçimi
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        if is_freeform:
            system_prompt = """Sen deneyimli bir startup danışmanı ve Y Combinator mentörüsün.
Kullanıcılar sana SaaS fikirleri, pazar fırsatları ve girişimcilik hakkında sorular soruyor.

KURALLAR:
- Kısa, net ve aksiyon odaklı cevaplar ver (max 300 kelime).
- Türkçe cevap ver.
- "Friction Economy" çerçevesini kullan: Sadece ağrı kesici fikirler (B2B, zaman kazandıran).
- Fikir zayıfsa nazikçe ama dürüstçe söyle ve alternatif öner.
- Emojileri kullanarak cevapları okunabilir yap.
- Somut tavsiyeler ver: Fiyat, hedef kitle, teknik stack, MVP süresi gibi."""
        else:
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
                    "scan_id": chat_id,
                    "role": "assistant",
                    "content": full_response
                }).execute()

                yield f"data: {json.dumps({'done': True, 'remaining': limit - user_msg_count - 1})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(chat_stream(), media_type="text/event-stream")

    except Exception as e:
        print(f"Chat Error: {e}")
        return Response(content=json.dumps({"error": str(e)}), status_code=500, media_type="application/json")
