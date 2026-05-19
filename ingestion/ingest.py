"""
ChromaDB Ingestion Pipeline
JSON dosyalarını okur → Document'lara dönüştürür → ChromaDB'ye yükler.
Üç koleksiyon: "ai_models", "startup_apps", "competitor_reviews"
"""

import json
import os
import sys

from langchain_chroma import Chroma
from langchain_core.documents import Document

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
DATA_DIR   = os.path.join(BASE_DIR, "data")

MODELS_FILE   = os.path.join(DATA_DIR, "models_raw.json")
APPS_FILE     = os.path.join(DATA_DIR, "apps_raw.json")
REVIEWS_FILE  = os.path.join(DATA_DIR, "competitor_reviews.json")

# Merkezî embedding modülünü kullan (Gemini Embedding 2)
from lib.embeddings import get_embeddings


def load_json(path: str) -> list[dict]:
    if not os.path.exists(path):
        print(f"[Ingestion] ⚠️  Dosya bulunamadı: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[Ingestion] 📂 {os.path.basename(path)}: {len(data)} kayıt")
    return data


# ──────────────────────────────────────────────
# AI MODELS KOLEKSİYONU
# ──────────────────────────────────────────────

def build_model_documents(models: list[dict]) -> list[Document]:
    docs = []
    for m in models:
        name     = m.get("name") or m.get("model_id", "")
        category = m.get("category", "unknown")
        desc     = m.get("description", "")

        page_content = (
            f"{name}. "
            f"Category: {category}. "
            f"{desc}"
        ).strip()

        metadata = {
            "model_id":    m.get("model_id", name),
            "name":        name,
            "category":    category,
            "source":      m.get("source", ""),
            "downloads":   str(m.get("downloads") or m.get("run_count") or 0),
            "likes":       str(m.get("likes", 0)),
            "url":         m.get("url", ""),
            "scraped_at":  m.get("scraped_at", ""),
        }
        docs.append(Document(page_content=page_content, metadata=metadata))
    return docs


def ingest_models(embeddings) -> int:
    models = load_json(MODELS_FILE)
    if not models:
        print("[Ingestion] ai_models: veri yok, atlanıyor.")
        return 0

    docs = build_model_documents(models)
    store = Chroma(
        collection_name="ai_models",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    # Mevcut koleksiyonu temizle
    existing = store.get()
    if existing["ids"]:
        store.delete(ids=existing["ids"])

    store.add_documents(docs)
    print(f"[Ingestion] ✅ ai_models: {len(docs)} belge eklendi.")
    return len(docs)


# ──────────────────────────────────────────────
# STARTUP APPS KOLEKSİYONU
# ──────────────────────────────────────────────

def build_app_documents(apps: list[dict]) -> list[Document]:
    docs = []
    for a in apps:
        name     = a.get("name", "")
        desc     = a.get("description") or a.get("tagline", "")
        category = a.get("category", "saas")
        topics   = ", ".join(a.get("topics", [])) if a.get("topics") else ""

        page_content = (
            f"{name}. "
            f"{desc}. "
            f"Category: {category}. "
            f"Topics: {topics}"
        ).strip()

        metadata = {
            "name":       name,
            "mrr":        str(a.get("mrr", "")),
            "pricing":    str(a.get("pricing", "")),
            "votes":      str(a.get("votes", 0)),
            "category":   category,
            "source":     a.get("source", ""),
            "url":        a.get("url", ""),
            "scraped_at": a.get("scraped_at", ""),
        }
        docs.append(Document(page_content=page_content, metadata=metadata))
    return docs


def ingest_apps(embeddings) -> int:
    apps = load_json(APPS_FILE)
    if not apps:
        print("[Ingestion] startup_apps: veri yok, atlanıyor.")
        return 0

    docs = build_app_documents(apps)
    store = Chroma(
        collection_name="startup_apps",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    existing = store.get()
    if existing["ids"]:
        store.delete(ids=existing["ids"])

    store.add_documents(docs)
    print(f"[Ingestion] ✅ startup_apps: {len(docs)} belge eklendi.")
    return len(docs)


# ──────────────────────────────────────────────
# COMPETITOR REVIEWS KOLEKSİYONU
# ──────────────────────────────────────────────

def build_review_documents(reviews: list[dict]) -> list[Document]:
    docs = []
    for r in reviews:
        product  = r.get("product", "")
        rating   = r.get("rating", "")
        text     = r.get("text") or r.get("review", "")
        source   = r.get("source", "g2")

        page_content = f"{product}. Rating: {rating}. {text}".strip()

        metadata = {
            "product":     product,
            "rating":      str(rating),
            "source":      source,
            "url":         r.get("url", ""),
            "scraped_at":  r.get("scraped_at", ""),
            "helpful_count": str(r.get("helpful_count", 0)),
        }
        docs.append(Document(page_content=page_content, metadata=metadata))
    return docs


def ingest_reviews(embeddings) -> int:
    reviews = load_json(REVIEWS_FILE)
    if not reviews:
        print("[Ingestion] competitor_reviews: veri yok, atlanıyor.")
        return 0

    docs = build_review_documents(reviews)
    store = Chroma(
        collection_name="competitor_reviews",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    existing = store.get()
    if existing["ids"]:
        store.delete(ids=existing["ids"])

    store.add_documents(docs)
    print(f"[Ingestion] ✅ competitor_reviews: {len(docs)} belge eklendi.")
    return len(docs)


# ──────────────────────────────────────────────
# ANA PIPELINE
# ──────────────────────────────────────────────

def run():
    print("=" * 55)
    print("  ChromaDB Ingestion Pipeline")
    print("=" * 55)

    os.makedirs(CHROMA_DIR, exist_ok=True)
    embeddings = get_embeddings()

    n_models  = ingest_models(embeddings)
    n_apps    = ingest_apps(embeddings)
    n_reviews = ingest_reviews(embeddings)

    print("=" * 55)
    print(f"  Tamamlandı: {n_models} model | {n_apps} uygulama | {n_reviews} yorum")
    print(f"  ChromaDB: {CHROMA_DIR}")
    print("=" * 55)


if __name__ == "__main__":
    run()
