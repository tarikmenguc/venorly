"""
run_alerts.py — Niş Alarm Tarayıcısı & E-posta Göndericisi

Akış:
  1. Supabase'den aktif alarmları çeker (is_active=true)
  2. Frekansı geçmiş olanları filtreler (daily → 24h, weekly → 7g)
  3. Her alarm için idea_agent ile mini tarama yapar
  4. Fırsat bulunursa Resend ile e-posta gönderir
  5. last_triggered_at güncellenir

Kullanım:
  python scripts/run_alerts.py                # Tüm aktif alarmları kontrol et
  python scripts/run_alerts.py --dry-run      # DB/email olmadan test et
  python scripts/run_alerts.py --alert-id X   # Tek alarm test et
"""

import os
import sys
import argparse
import time
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from lib.logger import get_logger
from lib.supabase_client import supabase
from lib.email_service import send_alert_email

logger = get_logger("run_alerts")

# Her tarama arasındaki bekleme (Groq rate limiting)
SLEEP_BETWEEN_ALERTS = int(os.getenv("ALERT_SLEEP_SECS", "30"))


def is_due(alert: dict) -> bool:
    """Alarmın tetikleme zamanının gelip gelmediğini kontrol eder."""
    last = alert.get("last_triggered_at")
    freq = alert.get("frequency", "daily")

    if not last:
        return True  # Hiç tetiklenmemişse, hemen tetikle

    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return True

    now = datetime.now(tz=timezone.utc)
    delta = timedelta(hours=24) if freq == "daily" else timedelta(days=7)
    return (now - last_dt) >= delta


def scan_for_keyword(keyword: str) -> list[dict]:
    """
    idea_agent ile keyword taraması yapar.
    Returns: [{"title": str, "summary": str, "score": int}]
    """
    try:
        from agent.idea_agent import idea_agent

        initial_state = {
            "user_category": keyword,
            "complaint_clusters": [],
            "store_clusters": [],
            "trending_models": [],
            "known_apps": [],
            "final_report": "",
            "validation_details": "",
            "seo_data": {},
        }

        final = None
        for event in idea_agent.stream(initial_state):
            node_name = list(event.keys())[0]
            final = event[node_name]

        if not final or not final.get("final_report"):
            return []

        report = final["final_report"]

        # Rapordan başlık ve özet çıkar
        title_match = __import__("re").search(r"NİŞ FIRSAT[:\s]+(.+)", report)
        title = title_match.group(1).strip()[:80] if title_match else f"{keyword} fırsatı"

        # Skor çıkar
        score_match = __import__("re").search(r"Doğrulama Skoru[:\s]+(\d+)", report)
        score = int(score_match.group(1)) if score_match else 70

        # Özet: ilk 200 karakter
        summary_match = __import__("re").search(r"Fırsat Özeti[:\s]*([\s\S]{50,200})", report)
        summary = summary_match.group(1).strip()[:200] if summary_match else report[:200]

        return [{"title": title, "summary": summary, "score": score}]

    except Exception as e:
        logger.error(f"scan_for_keyword hatası ({keyword}): {e}")
        return []


def update_last_triggered(alert_id: str, dry_run: bool = False) -> None:
    if dry_run:
        logger.info(f"[DRY-RUN] last_triggered_at güncellenmedi: {alert_id}")
        return
    try:
        supabase.table("alerts").update({
            "last_triggered_at": datetime.now(tz=timezone.utc).isoformat()
        }).eq("id", alert_id).execute()
    except Exception as e:
        logger.error(f"last_triggered_at güncelleme hatası: {e}")


def process_alert(alert: dict, dry_run: bool = False) -> bool:
    """Tek bir alarmı işler. True → email gönderildi, False → atlandı/hata."""
    keyword = alert.get("keyword", "")
    email = alert.get("email", "")
    alert_id = alert.get("id", "")

    logger.info(f"→ Alarm işleniyor: '{keyword}' → {email}")

    if not is_due(alert):
        logger.info(f"  ⏭ Henüz zamanı gelmedi ({alert.get('frequency')}), atlanıyor.")
        return False

    opportunities = scan_for_keyword(keyword)

    if not opportunities:
        logger.warning(f"  ⚠ '{keyword}' için fırsat bulunamadı.")
        update_last_triggered(alert_id, dry_run)
        return False

    logger.info(f"  ✅ {len(opportunities)} fırsat bulundu, e-posta gönderiliyor...")

    if dry_run:
        logger.info(f"  [DRY-RUN] E-posta atlanıyor → {email}")
        logger.info(f"  [DRY-RUN] İlk fırsat: {opportunities[0]}")
        update_last_triggered(alert_id, dry_run)
        return True

    sent = send_alert_email(to=email, keyword=keyword, opportunities=opportunities)
    update_last_triggered(alert_id, dry_run)
    return sent


def main():
    parser = argparse.ArgumentParser(description="Niş Alarm Tarayıcısı")
    parser.add_argument("--dry-run", action="store_true", help="DB/email yazmadan test")
    parser.add_argument("--alert-id", type=str, help="Tek bir alarm ID'si ile test")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("ALERT CHECK BAŞLADI" + (" [DRY-RUN]" if args.dry_run else ""))
    logger.info("=" * 50)

    # Alarmları çek
    try:
        if args.alert_id:
            res = supabase.table("alerts").select("*").eq("id", args.alert_id).single().execute()
            alerts = [res.data] if res.data else []
        else:
            res = supabase.table("alerts").select("*").eq("is_active", True).execute()
            alerts = res.data or []
    except Exception as e:
        logger.error(f"Alarmlar çekilemedi: {e}")
        sys.exit(1)

    logger.info(f"Toplam aktif alarm: {len(alerts)}")

    sent_count = 0
    for i, alert in enumerate(alerts):
        if i > 0:
            logger.info(f"Rate limit için {SLEEP_BETWEEN_ALERTS}s bekleniyor...")
            time.sleep(SLEEP_BETWEEN_ALERTS)

        ok = process_alert(alert, dry_run=args.dry_run)
        if ok:
            sent_count += 1

    logger.info("-" * 50)
    logger.info(f"TAMAMLANDI: {sent_count}/{len(alerts)} alarm e-posta gönderdi.")
    logger.info("=" * 50)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
