"""
Chrome Extension — Reverse Scan Endpoint
"""
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lib.auth_middleware import verify_api_key

router = APIRouter()


class ExtensionScanRequest(BaseModel):
    target_url: str              # Ziyaret edilen sitenin URL'si
    target_domain: str           # Sadece domain (ör: "canva.com")
    page_title: str = ""         # Sayfanın başlığı
    page_description: str = ""   # Meta description
    category_guess: str = ""     # Extension'ın tahmin ettiği kategori


@router.post("/api/extension/scan")
async def extension_scan(req: ExtensionScanRequest, request: Request):
    """
    Chrome Extension için özel Reverse Scan endpoint.
    Ziyaret edilen sitenin domain'ini alıp Reverse Agent çalıştırır.
    SSE streaming ile sonuçları döner.
    """
    verify_api_key(request, required=True)

    def ext_generator():
        yield f"data: {json.dumps({'node': 'init', 'state': {'currentNode': f'{req.target_domain} analiz ediliyor...'}})}\n\n"

        try:
            from agent.reverse_agent import reverse_agent

            target_name = req.page_title or req.target_domain

            initial_state = {
                "target_startup":    target_name,
                "startup_analysis":  "",
                "competitors":       [],
                "complaints":        [],
                "matching_models":   [],
                "disruption_report": "",
                "error":             None,
            }

            for event in reverse_agent.stream(initial_state):
                node_name = list(event.keys())[0]
                result    = event[node_name]
                yield f"data: {json.dumps({'node': node_name, 'state': result})}\n\n"

            yield f"data: {json.dumps({'status': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    headers = {
        "Cache-Control":    "no-cache",
        "Connection":       "keep-alive",
        "X-Accel-Buffering":"no",
    }
    return StreamingResponse(ext_generator(), media_type="text/event-stream", headers=headers)
