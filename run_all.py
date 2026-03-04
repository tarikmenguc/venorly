"""
run_all.py — Tam Pipeline
Tüm scraper'ları sırayla çalıştırır, ardından ChromaDB'ye yükler.

Kullanım:
    python run_all.py            # hepsi
    python run_all.py scrapers   # sadece scraping
    python run_all.py ingest     # sadece ChromaDB
"""

import subprocess
import sys
import time
import os


def run(cmd: list[str], label: str):
    print(f"\n{'='*55}")
    print(f"  ▶ {label}")
    print(f"{'='*55}")
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - t0
    if result.returncode == 0:
        print(f"  ✅ Tamamlandı ({elapsed:.1f}s)")
    else:
        print(f"  ❌ HATA (returncode={result.returncode})")
    return result.returncode == 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    python = sys.executable

    steps_scrapers = [
        ([python, "scrapers/huggingface.py"],  "HuggingFace Trending Modeller"),
        ([python, "scrapers/replicate.py"],    "Replicate Modeller"),
        ([python, "scrapers/fal.py"],          "fal.ai Modeller"),
        ([python, "scrapers/trustmrr.py"],     "TrustMRR Uygulamaları"),
        ([python, "scrapers/producthunt.py"],  "ProductHunt Uygulamaları"),
    ]

    step_ingest = ([python, "ingestion/ingest.py"], "ChromaDB Ingestion")

    print("\n🚀 Startup Idea Finder — Pipeline Başlıyor")
    print(f"   Mod: {mode}")

    success_count = 0
    total = 0

    if mode in ("all", "scrapers"):
        for cmd, label in steps_scrapers:
            total += 1
            if run(cmd, label):
                success_count += 1
            time.sleep(1)

    if mode in ("all", "ingest"):
        total += 1
        if run(*step_ingest):
            success_count += 1

    print(f"\n{'='*55}")
    print(f"  Pipeline tamamlandı: {success_count}/{total} başarılı")
    print(f"{'='*55}")

    if success_count == total:
        print("\n✅ Hazır! UI'ı başlatmak için:")
        print("   streamlit run app.py\n")
    else:
        print("\n⚠️  Bazı adımlar başarısız oldu. Hata mesajlarını incele.\n")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
