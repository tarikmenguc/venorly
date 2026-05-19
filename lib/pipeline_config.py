import os
import sys

# Merkezi pipeline adımları tanımı
# Bu yapı run_all.py ve scheduler.py arasındaki tutarsızlığı gidermek içindir.

PIPELINE_SCRAPERS = [
    {"script": "scrapers/huggingface.py",  "label": "HuggingFace Trending Modeller", "frequency": "daily"},
    {"script": "scrapers/replicate.py",    "label": "Replicate Modeller", "frequency": "daily"},
    {"script": "scrapers/fal.py",          "label": "fal.ai Modeller", "frequency": "daily"},
    {"script": "scrapers/api_pricing.py",  "label": "API Pricing", "frequency": "daily"},
    # Daha yavaş olanlar haftalık olarak işaretlenebilir (isteğe bağlı)
    {"script": "scrapers/trustmrr.py",     "label": "TrustMRR Uygulamaları", "frequency": "weekly"},
    {"script": "scrapers/producthunt.py",  "label": "ProductHunt Uygulamaları", "frequency": "weekly"},
]

PIPELINE_INGEST = {"script": "ingestion/ingest.py", "label": "ChromaDB Ingestion", "frequency": "daily"}

def get_python_executable():
    """Çalışılan ortama göre doğru python yolunu döner."""
    return sys.executable
