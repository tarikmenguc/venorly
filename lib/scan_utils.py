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

def check_rate_limit(ip: str, mode: str, user_data: dict = None) -> bool:
    """
    Kullanıcının kredisini veya günlük limitini kontrol eder.

    Returns:
        True  → limit aşıldı (isteği reddet)
        False → limit içinde (devam et)
    """
    try:
        if user_data and not user_data.get("dev_mode"):
            # Kullanici giris yapmis — atomic kredi azaltma (TOCTOU race condition onlenir)
            clerk_id = user_data.get("sub") or user_data.get("id")
            if clerk_id:
                cost = 2 if mode in ["deep", "orchestrate"] else 1

                # Supabase RPC ile atomic check-and-decrement
                # SQL: UPDATE users SET credits = credits - cost
                #      WHERE clerk_id = p_clerk_id AND credits >= cost
                # RETURNING credits  (yeni deger)
                try:
                    rpc_res = supabase.rpc("consume_credit", {
                        "p_clerk_id": clerk_id,
                        "p_cost": cost,
                    }).execute()
                    # RPC None veya bos donerse kredi yetersiz demektir
                    if rpc_res.data is None or rpc_res.data is False:
                        return True  # Yetersiz kredi
                except Exception:
                    # RPC henuz tanimlanmamissa (migration eksikse) fallback
                    user_res = supabase.table("users").select("credits").eq("clerk_id", clerk_id).execute()
                    if not user_res.data:
                        return True
                    credits = user_res.data[0].get("credits", 0)
                    if credits < cost:
                        return True
                    supabase.table("users").update({"credits": credits - cost}).eq("clerk_id", clerk_id).execute()

                supabase.table("usage_logs").insert({
                    "ip_address": ip or clerk_id,
                    "action_type": mode,
                }).execute()
                return False  # Isleme izin ver

        # Anonim veya Dev Kullanıcı (IP Bazlı)
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
            if heavy_uses >= 5:  # Anonim limite takılsın
                return True
        else:
            if total_uses >= 10:
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
