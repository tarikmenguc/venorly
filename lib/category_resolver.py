"""
Kategori çözümleyici.
Kullanıcının kategorisini SOURCE_DISPATCH anahtarlarına eşler.
4 aşama: tam eşleşme → semantik → LLM → genel fallback
"""

import os
from lib.source_routing import SOURCE_DISPATCH

# Sözlükte olmayan kategoriler için LLM üst-kova sınıflandırması
SUPER_BUCKETS = [
    "b2b_saas", "consumer_app", "developer_tools",
    "vertical_ai", "marketplace", "infrastructure",
    "ai_video", "ai_image", "ai_audio",
]

FALLBACK_CATEGORY = "generic_tech_saas"


def resolve_category(user_category: str) -> str:
    """
    Kullanıcının kategorisini SOURCE_DISPATCH anahtarına çevirir.
    Bulamazsa 'generic_tech_saas' döner.
    """
    normalized = user_category.lower().strip().replace(" ", "_")

    # Aşama 1: Tam eşleşme
    if normalized in SOURCE_DISPATCH:
        return normalized

    # Aşama 2: Kısmi eşleşme (anahtar içeriyor mu?)
    for key in SOURCE_DISPATCH:
        if key in normalized or normalized in key:
            return key

    # Aşama 3: LLM sınıflandırma
    try:
        result = _llm_classify(user_category)
        if result and result in SOURCE_DISPATCH:
            return result
    except Exception:
        pass

    # Aşama 4: Genel fallback
    _log_unknown_category(user_category)
    return FALLBACK_CATEGORY


def _llm_classify(user_category: str) -> str | None:
    """Groq ile hızlı kategori sınıflandırması."""
    try:
        from langchain_core.messages import HumanMessage
        from lib.llm import get_llm

        buckets_str = ", ".join(SUPER_BUCKETS)
        prompt = (
            f"Classify this startup category into exactly one of these buckets: {buckets_str}\n"
            f"Category: {user_category}\n"
            f"Reply with only the bucket name, nothing else."
        )
        result = get_llm(temp=0).invoke([HumanMessage(content=prompt)]).content.strip().lower()
        return result if result in SUPER_BUCKETS else None
    except Exception:
        return None


def _log_unknown_category(category: str) -> None:
    """Bilinmeyen kategoriyi log dosyasına yazar (haftalık gözden geçirme için)."""
    try:
        import os
        from datetime import datetime
        log_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "unknown_categories.log"
        )
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()} | {category}\n")
    except Exception:
        pass
