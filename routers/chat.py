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
        import logging
        logging.getLogger(__name__).error("Chat history error: %s", e, exc_info=True)
        return Response(
            content='{"error": "Sohbet gecmisi yuklenemedi."}',
            media_type="application/json",
            status_code=500,
        )


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

        # -- Sistem Promptu temiz ve sabit — kullanici verisi icermez -----
        if is_freeform:
            system_prompt = (
                "Sen deneyimli bir startup danismani ve Y Combinator mentorusun.\n"
                "Kullanicilar sana SaaS fikirleri ve girisimcilik hakkinda sorular soruyor.\n\n"
                "KURALLAR:\n"
                "- Kisa, net ve aksiyon odakli cevaplar ver (max 300 kelime).\n"
                "- Turkce cevap ver.\n"
                "- Friction Economy cercevesi: Sadece B2B, zaman kazandiran fikirler.\n"
                "- Fikir zayifsa nazikce ama donustce soyle ve alternatif oner.\n"
                "- Somut tavsiyeler ver: Fiyat, hedef kitle, teknik stack, MVP suresi."
            )
        else:
            # Rapor icerigi system prompt'a GIRMEZ — prompt injection izolasyonu
            category_safe = (scan_data.get("category", "Bilinmiyor") if scan_data else "Bilinmiyor")[:50]
            system_prompt = (
                "Sen Venorly AI danismanisın. Kullanici bir startup raporu hakkinda soru soruyor.\n"
                "Sadece rapor baglaminda cevap ver. Turkce yaz. Max 300 kelime.\n"
                f"Kategori: {category_safe}"
            )

        messages = [SystemMessage(content=system_prompt)]

        # Rapor icerigi izole Human/AI mesaj cifti olarak eklenir (system seviyesinde degil)
        # Bu yaklasim Stored Prompt Injection'i engeller: sistem talimat bolgesini kirletmez.
        if not is_freeform and report_context:
            safe_context = report_context[:2000]  # Boyut siniri
            messages.append(HumanMessage(content="[RAPOR]\n" + safe_context + "\n[/RAPOR]"))
            messages.append(AIMessage(content="Raporu inceledim. Sorularinizi yanıtlamaya hazirim."))

        for msg in history[-10:]:  # Gecmis sinirla — bellek tasmasini onle
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=req.message))

        from lib.llm import get_llm
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
        import logging
        logging.getLogger(__name__).error("Chat error: %s", e, exc_info=True)
        return Response(
            content=json.dumps({"error": "Chat servisi gecici olarak kullanilamiyor."}),
            status_code=500, media_type="application/json"
        )
