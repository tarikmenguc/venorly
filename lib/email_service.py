"""
Email Service — Resend API ile e-posta gönderimi
Niş alarm bildirimleri için kullanılır.

Kurulum:
  pip install resend
  .env → RESEND_API_KEY=re_xxxx
         EMAIL_FROM=alerts@yourdomain.com   (opsiyonel, default: onboarding@resend.dev)
"""

import os
from lib.logger import get_logger

logger = get_logger(__name__)

# Lazy import — RESEND_API_KEY yoksa import hatası vermemesi için
def _get_resend():
    try:
        import resend
        resend.api_key = os.getenv("RESEND_API_KEY", "")
        return resend
    except ImportError:
        logger.warning("resend paketi yüklü değil. `pip install resend` ile yükleyin.")
        return None


FROM_EMAIL = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
APP_URL = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")


def send_alert_email(to: str, keyword: str, opportunities: list[dict]) -> bool:
    """
    Niş alarm e-postası gönderir.

    Args:
        to:            Alıcı e-posta adresi
        keyword:       Alarm anahtar kelimesi (örn: "AI invoice")
        opportunities: [{"title": str, "summary": str, "score": int}]

    Returns:
        True → başarılı, False → hata
    """
    resend = _get_resend()
    if not resend:
        logger.error("Resend import edilemedi, e-posta gönderilemedi.")
        return False

    if not resend.api_key:
        logger.warning("RESEND_API_KEY tanımlı değil, e-posta atlanıyor.")
        return False

    # HTML şablon
    cards_html = ""
    for opp in opportunities[:5]:  # max 5 fırsat göster
        score = opp.get("score", 0)
        score_color = "#10b981" if score >= 80 else ("#3b82f6" if score >= 60 else "#f59e0b")
        cards_html += f"""
        <div style="background:#1a1a2e;border:1px solid #2d2d4e;border-radius:12px;padding:16px;margin-bottom:12px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <span style="font-size:14px;font-weight:700;color:#e5e5f0;">{opp.get('title', '')}</span>
            <span style="font-size:12px;font-weight:700;color:{score_color};background:rgba(255,255,255,0.05);padding:3px 10px;border-radius:20px;">{score}/100</span>
          </div>
          <p style="font-size:13px;color:#9ca3af;margin:0;line-height:1.5;">{opp.get('summary', '')}</p>
        </div>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#0a0a0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
      <div style="max-width:600px;margin:0 auto;padding:32px 16px;">

        <!-- Header -->
        <div style="text-align:center;margin-bottom:32px;">
          <div style="font-size:32px;margin-bottom:8px;">🔔</div>
          <h1 style="color:#fff;font-size:22px;font-weight:800;margin:0 0 6px;">Yeni Fırsatlar Bulundu!</h1>
          <p style="color:#9ca3af;font-size:14px;margin:0;">
            <strong style="color:#a78bfa;">{keyword}</strong> nişinde {len(opportunities)} yeni fırsat tespit edildi.
          </p>
        </div>

        <!-- Cards -->
        {cards_html}

        <!-- CTA -->
        <div style="text-align:center;margin-top:28px;">
          <a href="{APP_URL}/gallery"
             style="background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff;text-decoration:none;
                    padding:12px 28px;border-radius:10px;font-size:14px;font-weight:600;display:inline-block;">
            Tüm Fırsatları Gör →
          </a>
        </div>

        <!-- Footer -->
        <div style="text-align:center;margin-top:32px;padding-top:20px;border-top:1px solid #1f1f3a;">
          <p style="color:#4b5563;font-size:11px;margin:0;">
            Bu e-postayı almak istemiyorsanız
            <a href="{APP_URL}/alerts" style="color:#7c3aed;">alarm ayarlarınızı</a> güncelleyebilirsiniz.
          </p>
          <p style="color:#374151;font-size:10px;margin:6px 0 0;">Venorly — Niş Alarm Sistemi</p>
        </div>

      </div>
    </body>
    </html>
    """

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to],
            "subject": f"🔔 {keyword} — {len(opportunities)} Yeni Micro-SaaS Fırsatı",
            "html": html_body,
        })
        logger.info(f"E-posta gönderildi → {to} (id: {result.get('id', '?')})")
        return True
    except Exception as e:
        logger.error(f"E-posta gönderilemedi → {to}: {e}")
        return False
