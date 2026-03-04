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
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")
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
        # TrustMRR ve ProductHunt daha yavaş, haftada bir yeter
        # ("scrapers/trustmrr.py",   "TrustMRR Scraper"),
        # ("scrapers/producthunt.py","ProductHunt Scraper"),
        ("ingestion/ingest.py",      "ChromaDB Ingestion"),
    ]

    results = {}
    for script, label in steps:
        results[label] = run_step(script, label)

    # Ozet
    log("-" * 50)
    success = sum(1 for v in results.values() if v)
    total = len(results)
    log(f"SONUC: {success}/{total} basarili")
    for label, ok in results.items():
        log(f"  {'[OK]' if ok else '[HATA]'} {label}")
    log("=" * 50)

    return all(results.values())


def run_scheduled(schedule_time: str = "06:00"):
    """Her gün belirlenen saatte pipeline çalıştırır."""
    import schedule as sched  # lazy import

    log(f"Zamanlayici baslatildi -- her gun saat {schedule_time}")
    log(f"   Python: {PYTHON}")
    log(f"   Proje: {BASE_DIR}")

    sched.every().day.at(schedule_time).do(run_pipeline)

    while True:
        sched.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Startup Idea Finder — Scheduler")
    parser.add_argument("--now", action="store_true", help="Hemen bir kere çalıştır")
    parser.add_argument("--time", default="06:00", help="Günlük çalışma saati (default: 06:00)")
    args = parser.parse_args()

    if args.now:
        log("Manuel calistirma (--now)")
        success = run_pipeline()
        sys.exit(0 if success else 1)
    else:
        run_scheduled(args.time)
