"""
Scan — Discover Modu
Tek aşamalı pazar keşfi (idea_agent) endpoint'leri.
"""

import json
import os
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from lib.auth_middleware import verify_user_token
from lib.scan_utils import SSE_HEADERS

router = APIRouter()


def _save_trace(category: str, trace: list) -> None:
    """Scan trace'ini data/traces/ klasörüne JSON olarak yazar."""
    try:
        trace_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "traces")
        os.makedirs(trace_dir, exist_ok=True)
        slug = category[:40].replace(" ", "_").replace("/", "-")
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(trace_dir, f"{ts}_{slug}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"category": category, "timestamp": ts, "nodes": trace},
                      f, ensure_ascii=False, indent=2)
        print(f"[Trace] ✅ {path}")
    except Exception as e:
        print(f"[Trace] ⚠️  Trace yazılamadı: {e}")


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
        "market_data": "",
        "report_json": {},
        "buyer_leads": [],
        "error": None,
        "trace": [],
    }
    final_state = initial_state
    for event in idea_agent.stream(initial_state):
        node_name = list(event.keys())[0]
        result = event[node_name]
        final_state = result
        # Trace'i SSE'ye dahil etme — dosyaya yaz, frontend'i şişirme
        state_clean = {k: v for k, v in result.items() if k != "trace"}
        yield f"data: {json.dumps({'node': node_name, 'state': state_clean})}\n\n"
    # Trace'i dosyaya kaydet
    trace = final_state.get("trace", [])
    if trace:
        _save_trace(req.category, trace)

    # Tamamlanan raporu Supabase'e kaydet
    try:
        import uuid
        from lib.supabase_client import supabase
        from lib.report_actions import compute_actions

        scan_id = str(uuid.uuid4())
        report_json = final_state.get("report_json") or {}
        buyer_leads = final_state.get("buyer_leads") or []
        actions = compute_actions(scan_id, report_json, buyer_leads)

        full_report_payload = {
            "final_report":  final_state.get("final_report", ""),
            "report_json":   report_json,
            "buyer_leads":   buyer_leads,
            "reddit_signals": final_state.get("reddit_signals", []),
            "actions":       actions,
        }
        # user_id: ownership kontrolü için — IDOR fix
        from lib.auth_middleware import _APP_ENV, _DEV_ENVS
        # generate_discover_events req parametresi user bilgisi taşımıyor;
        # user_id scan_id ile birlikte frontend tarafından ayrıca set edilebilir.
        # Şimdilik None — migration sonrası frontend update endpoint'i eklenebilir.
        supabase.table("scans").insert({
            "id":             scan_id,
            "category":       req.category,
            "mode":           req.mode if hasattr(req, "mode") else "discover",
            "report_preview": final_state.get("final_report", "")[:300],
            "leads_count":    len(buyer_leads),
            "full_report":    full_report_payload,
            "user_id":        None,  # /api/scans/{id}/claim ile set edilir
        }).execute()
        print(f"[Discover] ✅ Scan kaydedildi: {scan_id}")
    except Exception as _e:
        print(f"[Discover] Supabase kayit hatasi (devam): {_e}")


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
