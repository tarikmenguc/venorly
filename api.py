"""
Venorly — FastAPI Entry Point
Tüm endpoint mantığı routers/ altında. Bu dosya sadece:
  1. FastAPI app oluşturur
  2. CORS middleware ekler
  3. Router'ları mount eder
  4. Basit utility endpoint'leri barındırır (health, PDF)
"""
import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from lib.supabase_client import supabase
from lib.pdf_generator import generate_report_pdf

# ── App ──────────────────────────────────────────────

app = FastAPI(title="Venorly API")

# ── CORS ─────────────────────────────────────────────

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

# ── Routers ──────────────────────────────────────────

from routers.scan import router as scan_router
from routers.chat import router as chat_router
from routers.gallery import router as gallery_router
from routers.extension import router as extension_router
from routers.webhooks import router as webhooks_router

app.include_router(scan_router)
app.include_router(chat_router)
app.include_router(gallery_router)
app.include_router(extension_router)
app.include_router(webhooks_router)

# ── Utility Endpoints ────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running"}


@app.get("/api/scans/{scan_id}/pdf")
async def get_scan_pdf(scan_id: str):
    try:
        res = supabase.table("scans").select("*").eq("id", scan_id).single().execute()
        scan_data = res.data

        if not scan_data:
            return Response(content="Scan not found", status_code=404)

        pdf_bytes = generate_report_pdf(scan_data)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)