# Venorly — Güvenlik Düzeltmeleri Implementasyon Planı

## Mimari Karar: Ne Dokunulur, Ne Dokunulmaz

**Dokunulan dosyalar:**
- `lib/auth_middleware.py` — bypass hardening + timing attack fix
- `api.py` — IDOR fix + exception masking
- `routers/webhooks.py` — imza doğrulama
- `routers/chat.py` — prompt injection izolasyonu
- `routers/gallery.py` — pagination DoS fix + exception masking
- `lib/scan_utils.py` — race condition fix

**Dokunulmayan dosyalar:**
- Tüm agent/ dosyaları
- lib/schemas.py
- Tüm scraper'lar

---

## Fix 1 — auth_middleware.py (CWE-1188 + CWE-208)

### Değişiklikler:
1. `_AUTH_BYPASS` artık `APP_ENV != "production"` ile kontrol edilir
2. `verify_api_key` string karşılaştırması → `hmac.compare_digest`

---

## Fix 2 — api.py (CWE-639 + CWE-209)

### Değişiklikler:
1. PDF, landing-page, pitch-deck endpoint'lerine `Depends(verify_user_token)` eklenir
2. Scan'in `user_id` alanı caller ile karşılaştırılır
3. `str(e)` → generic mesaj, exception sunucu loguna

---

## Fix 3 — webhooks.py (CWE-345)

### Değişiklikler:
1. Stripe: `stripe.Webhook.construct_event` ile imza doğrulama
2. Clerk: `CLERK_WEBHOOK_SECRET` ile HMAC-SHA256 manuel doğrulama (svix opsiyonel)
3. Her iki endpoint başarısız doğrulamada 400 döner

---

## Fix 4 — chat.py (OWASP LLM01)

### Değişiklikler:
1. Rapor içeriği system prompt'tan çıkarılır
2. İlk Human/AI mesaj çifti olarak eklenir (izolasyon)
3. `str(e)` → generic mesaj

---

## Fix 5 — scan_utils.py (CWE-362)

### Değişiklikler:
1. Check-then-debit → Supabase atomic RPC çağrısı
2. Fallback: RPC yoksa optimistic locking

---

## Fix 6 — gallery.py (CWE-770 + CWE-209)

### Değişiklikler:
1. `per_page` max 50 ile sınırlandırılır
2. `str(e)` → generic mesaj

---

## Pipeline Akışı (Güvenlik Katmanı)

```
İstek → auth_middleware (env-aware bypass)
      → verify_user_token (Supabase/Clerk JWT)
      → Ownership check (scan.user_id == caller.sub)
      → Rate limit (atomic decrement)
      → Handler
      → Hata: generic mesaj (detay sadece server log)
```
