"""
Scan router'ları için paylaşılan yardımcı araçlar.
Rate limit kontrolü ve SSE başlıkları burada merkezi olarak tanımlıdır.
"""

from lib.supabase_client import supabase

# ──────────────────────────────────────────────
# SSE Başlıkları (tüm scan router'ları kullanır)
# ──────────────────────────────────────────────

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


# ──────────────────────────────────────────────
# Rate Limit Kontrolü
# ──────────────────────────────────────────────

def check_rate_limit(ip: str, mode: str) -> bool:
    """
    Kullanıcının günlük limitini kontrol eder.

    Returns:
        True  → limit aşıldı (isteği reddet)
        False → limit içinde (devam et)
    """
    try:
        from datetime import datetime, timezone, timedelta

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        res = (
            supabase.table("usage_logs")
            .select("*")
            .eq("ip_address", ip)
            .gte("created_at", yesterday)
            .execute()
        )
        logs = res.data

        total_uses = len(logs)
        heavy_uses = sum(1 for log in logs if log.get("action_type") in ["deep", "orchestrate"])

        if mode in ["deep", "orchestrate"]:
            if heavy_uses >= 999:  # Geçici olarak limite takılmasın
                return True
        else:
            if total_uses >= 999:
                return True

        # Kullanımı kaydet
        supabase.table("usage_logs").insert({
            "ip_address": ip,
            "action_type": mode,
        }).execute()

        return False

    except Exception as e:
        print(f"[ScanUtils] Rate limit hatası: {e}")
        return False
