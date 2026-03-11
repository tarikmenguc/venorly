"""
Merkezî Embedding Modülü
Tüm projede tek bir yerden embedding modeli yönetilir.
Gemini Embedding 2 kullanır (8192 token, 100+ dil, multimodal).
"""

import os
from dotenv import load_dotenv

load_dotenv()

_embeddings = None


def get_embeddings():
    """
    Google Gemini Embedding 2 modelini döndürür.
    Fallback: GOOGLE_API_KEY yoksa eski HuggingFace MiniLM modeline döner.
    """
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    if os.getenv("GOOGLE_API_KEY"):
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            _embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                task_type="RETRIEVAL_DOCUMENT"
            )
            print("[Embeddings] ✅ Gemini text-embedding-004 yüklendi (Google API)")
            return _embeddings
        except Exception as e:
            print(f"[Embeddings] ⚠️ Gemini Embedding hatası, fallback'e geçiliyor: {e}")

    # Fallback: Yerel HuggingFace modeli
    from langchain_huggingface import HuggingFaceEmbeddings
    _embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    print("[Embeddings] ⚠️ Fallback: HuggingFace MiniLM yüklendi (yerel)")
    return _embeddings
