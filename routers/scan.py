"""
Scan endpoint — Dispatcher
Her mod kendi dosyasında (scan_discover.py, scan_deep.py, …).
Stage-A / Stage-B endpoint'leri scan_discover.py'de.
"""

import json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from lib.auth_middleware import verify_user_token
from lib.logger import get_logger
from lib.scan_utils import check_rate_limit, SSE_HEADERS

from routers.scan_discover import router as discover_router, generate_discover_events
from routers.scan_deep import generate_deep_events
from routers.scan_reverse import generate_reverse_events
from routers.scan_orchestrate import generate_orchestrate_events
from routers.scan_trends import generate_trends_events

logger = get_logger(__name__)

router = APIRouter()
router.include_router(discover_router)  # /api/scan/stage-a ve /api/scan/stage-b


class ScanRequest(BaseModel):
    mode: str
    category: Optional[str] = ""
    target_startup: Optional[str] = ""


_MODE_HANDLERS = {
    "discover": generate_discover_events,
    "category": generate_discover_events,
    "deep":      generate_deep_events,
    "reverse":   generate_reverse_events,
    "orchestrate": generate_orchestrate_events,
    "trends":    generate_trends_events,
}

_RATE_LIMIT_MSG = (
    "Günlük ücretsiz limitinize ulaştınız. "
    "Derin analizler için günde 1, keşifler için günde 3 hakkınız bulunmaktadır. "
    "Lütfen yarın tekrar deneyin."
)


@router.post("/api/scan")
async def scan_endpoint(
    req: ScanRequest,
    request: Request,
    user: dict = Depends(verify_user_token),
):
    # IP tespiti
    client_ip = request.client.host
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0]

    # Rate limit
    if check_rate_limit(client_ip, req.mode):
        async def err_gen():
            yield f"data: {json.dumps({'error': _RATE_LIMIT_MSG})}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    handler = _MODE_HANDLERS.get(req.mode)
    if not handler:
        async def unknown_mode():
            yield f"data: {json.dumps({'error': f'Bilinmeyen mod: {req.mode}'})}\n\n"
        return StreamingResponse(unknown_mode(), media_type="text/event-stream")

    def event_generator():
        logger.debug(f"event_generator STARTED for mode={req.mode}")
        yield f"data: {json.dumps({'node': 'init', 'state': {'currentNode': 'Modüller yükleniyor...'}})}\n\n"
        try:
            yield from handler(req)
            yield f"data: {json.dumps({'status': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"Scan error (mode={req.mode}): {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=SSE_HEADERS)
