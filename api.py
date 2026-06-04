"""
Venorly - FastAPI Entry Point
"""
import logging
import os

from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware

from lib.supabase_client import supabase
from lib.pdf_generator import generate_report_pdf
from lib.landing_page_generator import generate_landing_page
from lib.pitch_deck_generator import generate_pitch_deck
from lib.auth_middleware import verify_user_token

logger = logging.getLogger(__name__)

app = FastAPI(title="Venorly API")

raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]
allow_all = "*" in ALLOWED_ORIGINS
if allow_all:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.scan import router as scan_router
from routers.chat import router as chat_router
from routers.gallery import router as gallery_router
from routers.extension import router as extension_router

app.include_router(scan_router)
app.include_router(chat_router)
app.include_router(gallery_router)
app.include_router(extension_router)


def _get_scan_and_check_owner(scan_id: str, user: dict) -> dict:
    """
    Scan'i cek ve caller'in sahibi oldugunu dogrula.
    Eksik/yanlis sahiplik → 403.
    Bulunamama → 404.
    """
    res = supabase.table("scans").select("*").eq("id", scan_id).single().execute()
    scan_data = res.data
    if not scan_data:
        return None  # 404

    owner_id  = scan_data.get("user_id")
    caller_id = user.get("sub") or user.get("id")

    # Dev modunda veya owner_id henuz yazilmadiysa gecis ver
    if user.get("dev_mode") or not owner_id:
        return scan_data

    if caller_id and owner_id != caller_id:
        return False  # 403

    return scan_data


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running"}


@app.get("/api/scans/{scan_id}/pdf")
async def get_scan_pdf(
    scan_id: str,
    user: dict = Depends(verify_user_token),
):
    try:
        scan_data = _get_scan_and_check_owner(scan_id, user)
        if scan_data is None:
            return Response(content="Not found", status_code=404)
        if scan_data is False:
            return Response(content="Forbidden", status_code=403)

        pdf_bytes = generate_report_pdf(scan_data)
        filename  = "Report_" + scan_data.get("category", "Analysis").replace(" ", "_") + ".pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=" + filename},
        )
    except Exception as e:
        logger.error("PDF generation failed for scan %s: %s", scan_id, e, exc_info=True)
        return Response(
            content='{"error": "Rapor olusturulamadi. Lutfen tekrar deneyin."}',
            media_type="application/json",
            status_code=500,
        )


@app.get("/api/scans/{scan_id}/landing-page")
async def get_landing_page(
    scan_id: str,
    user: dict = Depends(verify_user_token),
):
    try:
        scan_data = _get_scan_and_check_owner(scan_id, user)
        if scan_data is None:
            return Response(content="Not found", status_code=404)
        if scan_data is False:
            return Response(content="Forbidden", status_code=403)

        full = scan_data.get("full_report") or {}
        rj   = (full.get("report_json") if isinstance(full, dict) else None) or {}
        if not rj:
            return Response(content="report_json bulunamadi", status_code=422)

        html     = generate_landing_page(rj)
        category = scan_data.get("category", "landing").replace(" ", "_")
        return Response(
            content=html,
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=" + category + "_landing.html"},
        )
    except Exception as e:
        logger.error("Landing page failed for scan %s: %s", scan_id, e, exc_info=True)
        return Response(
            content='{"error": "Landing page olusturulamadi."}',
            media_type="application/json",
            status_code=500,
        )


@app.get("/api/scans/{scan_id}/pitch-deck")
async def get_pitch_deck(
    scan_id: str,
    user: dict = Depends(verify_user_token),
):
    try:
        scan_data = _get_scan_and_check_owner(scan_id, user)
        if scan_data is None:
            return Response(content="Not found", status_code=404)
        if scan_data is False:
            return Response(content="Forbidden", status_code=403)

        full = scan_data.get("full_report") or {}
        rj   = (full.get("report_json") if isinstance(full, dict) else None) or {}
        if not rj:
            return Response(content="report_json bulunamadi", status_code=422)

        pptx_bytes = generate_pitch_deck(rj)
        category   = scan_data.get("category", "pitch").replace(" ", "_")
        return Response(
            content=pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": "attachment; filename=" + category + "_pitch.pptx"},
        )
    except Exception as e:
        logger.error("Pitch deck failed for scan %s: %s", scan_id, e, exc_info=True)
        return Response(
            content='{"error": "Pitch deck olusturulamadi."}',
            media_type="application/json",
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
