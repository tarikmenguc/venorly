"""
Merkezi retrieval API.
ChromaDB'den önce arar; sonuç yetersizse Tavily fallback'e düşer.
Çağrı: retrieve(query, need, category, k=5)
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from lib.source_routing import SOURCE_DISPATCH, get_confidence
from lib.category_resolver import resolve_category

CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
CHROMA_MIN_RESULTS = 5  # Bu kadar sonuç gelmezse Tavily'ye düş


def retrieve(query: str, need: str, category: str, k: int = 5) -> list[dict]:
    """
    Belirtilen need (trending_models / market_apps / complaints vb.) için
    ilgili kaynaklardan k belge döner. Her belgede _confidence alanı var.

    Returns: [{"content": str, "metadata": dict}, ...]
    """
    resolved = resolve_category(category)
    allowed_sources = SOURCE_DISPATCH.get(resolved, {}).get(need, [])

    # ChromaDB koleksiyonunu need'e göre seç
    collection = _need_to_collection(need)
    docs = []

    if collection:
        docs = _chroma_search(query, collection, allowed_sources, k)

    # Yeterli sonuç yoksa Tavily fallback
    if len(docs) < CHROMA_MIN_RESULTS:
        tavily_docs = _tavily_search(query, k - len(docs))
        docs.extend(tavily_docs)

    # Runtime confidence enjekte et
    for doc in docs:
        source = doc.get("metadata", {}).get("source", "")
        doc["metadata"]["_confidence"] = get_confidence(source)

    return docs[:k]


def _need_to_collection(need: str) -> str | None:
    mapping = {
        "trending_models": "ai_models",
        "market_apps":     "startup_apps",
        "complaints":      "competitor_reviews",
    }
    return mapping.get(need)


def _chroma_search(query: str, collection: str, allowed_sources: list[str], k: int) -> list[dict]:
    """ChromaDB similarity search. Hata durumunda boş liste döner."""
    try:
        from langchain_chroma import Chroma
        from lib.embeddings import get_embeddings

        store = Chroma(
            collection_name=collection,
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_DIR,
        )

        where_filter = {"source": {"$in": allowed_sources}} if allowed_sources else None
        results = store.similarity_search(query, k=k, filter=where_filter)

        return [
            {"content": doc.page_content, "metadata": dict(doc.metadata)}
            for doc in results
        ]
    except Exception as e:
        print(f"[Retrieval] ChromaDB hatası ({collection}): {e}")
        return []


def _tavily_search(query: str, k: int) -> list[dict]:
    """Tavily fallback. Hata durumunda boş liste döner."""
    try:
        from lib.tavily_client import get_tavily_client
        client = get_tavily_client()
        results = client.search(query, max_results=k, search_depth="basic")

        return [
            {
                "content": r.get("content", "")[:400],
                "metadata": {
                    "source": "tavily_generic",
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "scraped_at": "",
                },
            }
            for r in results.get("results", [])
        ]
    except Exception as e:
        print(f"[Retrieval] Tavily hatası: {e}")
        return []
