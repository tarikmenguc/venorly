"""
Scheduler — Günlük Otomatik Veri Güncelleme
Her gün belirlenen saatte scrapers + ingestion pipeline'ını çalıştırır.

Kullanım:
  python scheduler.py              # Foreground — her gün 06:00'da çalışır
  python scheduler.py --now        # Hemen bir kere çalıştır (test)
"""

import os
import sys
import time
import subprocess
import argparse
import json
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

import platform
if platform.system() == "Windows":
    PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")
else:
    PYTHON = os.path.join(BASE_DIR, "venv", "bin", "python")
if not os.path.exists(PYTHON):
    PYTHON = sys.executable

LOG_FILE = os.path.join(BASE_DIR, "data", "scheduler.log")


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_step(script: str, label: str) -> bool:
    """Tek bir script calistirir."""
    log(f">> {label} basliyor...")
    try:
        result = subprocess.run(
            [PYTHON, script],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300,  # 5 dakika timeout
        )
        if result.returncode == 0:
            log(f"[OK] {label} tamamlandi.")
            return True
        else:
            log(f"[HATA] {label} hata! (exit={result.returncode})")
            if result.stderr:
                log(f"   STDERR: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log(f"[TIMEOUT] {label} timeout (5dk)!")
        return False
    except Exception as e:
        log(f"[HATA] {label} exception: {e}")
        return False


def run_pipeline():
    """Tam pipeline: scrapers → ingestion."""
    log("=" * 50)
    log("PIPELINE BAŞLADI")
    log("=" * 50)

    steps = [
        ("scrapers/huggingface.py",  "HuggingFace Scraper"),
        ("scrapers/replicate.py",    "Replicate Scraper"),
        ("scrapers/fal.py",          "fal.ai Scraper"),
        ("scrapers/api_pricing.py",  "API Pricing Scraper"),
        # TrustMRR ve ProductHunt daha yavaş, haftada bir yeter
        # ("scrapers/trustmrr.py",   "TrustMRR Scraper"),
        # ("scrapers/producthunt.py","ProductHunt Scraper"),
        ("ingestion/ingest.py",      "ChromaDB Ingestion"),
    ]

    results = {}
    for script, label in steps:
        results[label] = run_step(script, label)

    # 8.2 Trend Algılama: Snapshot Kaydet ve Trendleri Dön
    history_dir = os.path.join(BASE_DIR, "data", "history")
    os.makedirs(history_dir, exist_ok=True)
    
    current_week = datetime.now().isocalendar()[1]
    current_year = datetime.now().isocalendar()[0]
    snapshot_file = os.path.join(history_dir, f"{current_year}-W{current_week:02d}.json")
    
    # Mevcut veriyi birleştirip snapshot al
    models_file = os.path.join(BASE_DIR, "data", "models_raw.json")
    apps_file = os.path.join(BASE_DIR, "data", "apps_raw.json")
    
    snapshot_data = {"models": [], "apps": []}
    if os.path.exists(models_file):
        with open(models_file, "r", encoding="utf-8") as f:
            snapshot_data["models"] = json.load(f)
    if os.path.exists(apps_file):
        with open(apps_file, "r", encoding="utf-8") as f:
            snapshot_data["apps"] = json.load(f)
            
    with open(snapshot_file, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
    log(f"[Trend] Snapshot kaydedildi: {snapshot_file}")
    
    # Bir önceki haftayı bul
    prev_week = current_week - 1
    prev_year = current_year
    if prev_week == 0:
        prev_week = 52
        prev_year -= 1
        
    prev_snapshot = os.path.join(history_dir, f"{prev_year}-W{prev_week:02d}.json")
    
    if os.path.exists(prev_snapshot):
        # agent.trend_detector'ü import edip çalıştır
        sys.path.insert(0, BASE_DIR)
        from agent.trend_detector import detect_trends
        trends = detect_trends(snapshot_file, prev_snapshot)
        
        trends_file = os.path.join(history_dir, f"{current_year}-W{current_week:02d}_trends.json")
        with open(trends_file, "w", encoding="utf-8") as f:
            json.dump(trends, f, ensure_ascii=False, indent=2)
            
        log(f"[Trend] {len(trends.get('rising_models', []))} model ve {len(trends.get('rising_apps', []))} app artış gösterdi.")
    else:
        log("[Trend] Karşılaştırma için önceki haftanın verisi bulunamadı.")

    # Ozet
    log("-" * 50)
    success = sum(1 for v in results.values() if v)
    total = len(results)
    log(f"SONUC: {success}/{total} basarili")
    for label, ok in results.items():
        log(f"  {'[OK]' if ok else '[HATA]'} {label}")
    log("=" * 50)

    return all(results.values())


def run_gallery_seed():
    """Gallery'yi tüm kategoriler için yeniden seed eder (Pazartesi 03:00)."""
    log("=" * 50)
    log("GALLERY SEED BAŞLADI (Haftalık)")
    log("=" * 50)
    result = run_step("scripts/seed_gallery.py", "Gallery Seed (15 kategori)")
    log(f"Gallery Seed {'[OK]' if result else '[HATA]'}")
    return result


def run_alert_check():
    """Aktif alarmları kontrol edip email gönderir (Her gün 07:00)."""
    log("=" * 50)
    log("ALERT CHECK BAŞLADI")
    log("=" * 50)
    result = run_step("scripts/run_alerts.py", "Alert Check & Email")
    log(f"Alert Check {'[OK]' if result else '[HATA]'}")
    return result


def run_scheduled(schedule_time: str = "06:00"):
    """Her gün belirlenen saatte pipeline, her Pazartesi 03:00'da gallery seed, her gün 07:00'da alert check çalıştırır."""
    import schedule as sched  # lazy import

    log(f"Zamanlayici baslatildi -- her gun saat {schedule_time}")
    log(f"   Gallery Seed  : Her Pazartesi 03:00")
    log(f"   Alert Check   : Her gün 07:00")
    log(f"   Python: {PYTHON}")
    log(f"   Proje: {BASE_DIR}")

    # Günlük scraper + ingestion pipeline
    sched.every().day.at(schedule_time).do(run_pipeline)

    # Haftalık gallery seed — Pazartesi sabah 03:00
    sched.every().monday.at("03:00").do(run_gallery_seed)

    # Günlük alarm check — her gün 07:00
    sched.every().day.at("07:00").do(run_alert_check)

    while True:
        sched.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Startup Idea Finder — Scheduler")
    parser.add_argument("--now", action="store_true", help="Hemen bir kere çalıştır")
    parser.add_argument("--time", default="03:00", help="Günlük çalışma saati (default: 03:00)")
    args = parser.parse_args()

    if args.now:
        log("Manuel calistirma (--now)")
        success = run_pipeline()
        sys.exit(0 if success else 1)
    else:
        run_scheduled(args.time)
