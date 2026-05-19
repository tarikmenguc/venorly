"""
Merkezi LLM fabrikası.
Tüm agent ve router'lar bu modülden get_llm() import eder.
Model değiştirmek için tek dosya.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_llm(provider: str = "groq", temp: float = 0.7):
    """
    LLM modelini döndürür.

    Args:
        provider: 'groq' (varsayılan) veya 'gemini'
        temp:     Sıcaklık değeri (0.0 – 1.0)

    Env değişkenleri:
        GROQ_API_KEY    – Groq API anahtarı
        GROQ_MODEL      – Kullanılacak Groq modeli (varsayılan: llama-3.3-70b-versatile)
        GOOGLE_API_KEY  – Gemini için (opsiyonel)
    """
    if provider == "gemini" and os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=temp,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

    # Varsayılan: Groq
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=temp,
    )
