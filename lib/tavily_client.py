"""
Merkezi Tavily istemcisi.
Tüm agent ve scraper'lar bu modülden get_tavily_client() import eder.

lru_cache sayesinde süreç boyunca tek bir TavilyClient instance'ı oluşur.
API anahtarı eksikse açık bir EnvironmentError fırlatır.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


@lru_cache(maxsize=1)
def get_tavily_client() -> TavilyClient:
    """
    Paylaşılan TavilyClient instance'ını döndürür.

    Env değişkenleri:
        TAVILY_API_KEY – Tavily API anahtarı (zorunlu)

    Raises:
        EnvironmentError: TAVILY_API_KEY bulunamazsa
    """
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "[Tavily] TAVILY_API_KEY bulunamadı. "
            ".env dosyanızı veya ortam değişkenlerinizi kontrol edin."
        )
    return TavilyClient(api_key=api_key)
