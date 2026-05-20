"""
Scan — Discover Modu
Tek aşamalı pazar keşfi (idea_agent) endpoint'leri.
"""

import json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lib.auth_middleware import verify_user_token
from lib.scan_utils import SSE_HEADERS

router = APIRouter()


class StageARequest(BaseModel):
    category: str


class StageBRequest(BaseModel):
    category: str
    sub_niche: str
    phase_a_state: dict


# ──────────────────────────────────────────────
# Discover modu olay üreteci (scan.py tarafından çağrılır)
# ──────────────────────────────────────────────

def generate_discover_events(req):
    """Discover modu için SSE olay üreteci."""
    from agent.idea_agent import idea_agent

    initial_state = {
        "user_category": req.category,
        "target_category": "",
        "search_queries": {},
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
        "error": None,
    }
    for event in idea_agent.stream(initial_state):
        node_name = list(event.keys())[0]
        result = event[node_name]
        yield f"data: {json.dumps({'node': node_name, 'state': result})}\n\n"


# ──────────────────────────────────────────────
# İki Aşamalı Endpoint'ler
# ──────────────────────────────────────────────

@router.post("/api/scan/stage-a")
async def scan_stage_a(
    req: StageARequest,
    request: Request,
    user: dict = Depends(verify_user_token),
):
    """Aşama A: Pazar tarama. Sonunda market_overview + sub_niche seçenekleri döner."""

    def gen():
        yield f"data: {json.dumps({'node': 'init', 'state': {'currentNode': 'Aşama A başlıyor...'}})}\n\n"
        try:
            from agent.phase_agents import phase_a_agent

            init_state = {
                "user_category": req.category,
                "trending_models": [], "matching_apps": [], "competitor_complaints": [],
                "complaint_clusters": "", "store_app_ids": [], "store_reviews": [],
                "store_clusters": "", "competition_matrix": "", "final_report": "",
                "validation_details": "", "seo_data": {}, "market_overview": "",
                "sub_niche": "", "market_sizing": {}, "unit_economics": {}, "gtm_assets": "",
                "error": None,
            }
            for event in phase_a_agent.stream(init_state):
                for node_name, node_state in event.items():
                    yield f"data: {json.dumps({'node': node_name, 'state': {k: v for k, v in node_state.items() if isinstance(v, (str, list, dict, type(None)))}})}\n\n"

            yield f"data: {json.dumps({'status': 'stage_a_done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/api/scan/stage-b")
async def scan_stage_b(
    req: StageBRequest,
    request: Request,
    user: dict = Depends(verify_user_token),
):
    """Aşama B: Derin fizibilite. Aşama A state'i + kullanıcının sub_niche seçimi ile başlar."""

    def gen():
        yield f"data: {json.dumps({'node': 'init', 'state': {'currentNode': 'Aşama B başlıyor...'}})}\n\n"
        try:
            from agent.phase_agents import phase_b_agent

            state = {**req.phase_a_state, "sub_niche": req.sub_niche}
            defaults = {
                "store_app_ids": [], "store_reviews": [], "store_clusters": "",
                "competition_matrix": "", "final_report": "", "validation_details": "",
                "market_sizing": {}, "unit_economics": {}, "gtm_assets": "", "error": None,
            }
            for k, v in defaults.items():
                state.setdefault(k, v)

            for event in phase_b_agent.stream(state):
                for node_name, node_state in event.items():
                    yield f"data: {json.dumps({'node': node_name, 'state': {k: v for k, v in node_state.items() if isinstance(v, (str, list, dict, type(None)))}})}\n\n"

            yield f"data: {json.dumps({'status': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)
