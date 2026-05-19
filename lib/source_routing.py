"""
Merkezi kaynak yönlendirme sözlüğü.
Kategori × ihtiyaç → öncelikli kaynak listesi
Node × izin verilen kaynaklar (whitelist)
Kaynak güven ağırlıkları
"""

# ──────────────────────────────────────────────
# Katman A — Kategori × İhtiyaç → Kaynak Önceliği
# ──────────────────────────────────────────────

SOURCE_DISPATCH: dict[str, dict[str, list[str]]] = {
    "ai_video": {
        "trending_models": ["replicate", "huggingface", "fal"],
        "market_apps":     ["producthunt", "trustmrr"],
        "complaints":      ["g2", "capterra", "reddit"],
        "store_reviews":   ["google_play", "app_store"],
        "buyer_intent":    ["upwork", "reddit"],
    },
    "ai_image": {
        "trending_models": ["replicate", "huggingface", "fal"],
        "market_apps":     ["producthunt", "trustmrr"],
        "complaints":      ["g2", "capterra", "reddit"],
        "buyer_intent":    ["upwork", "reddit"],
    },
    "ai_audio": {
        "trending_models": ["huggingface", "replicate"],
        "market_apps":     ["producthunt", "trustmrr"],
        "complaints":      ["g2", "capterra", "reddit"],
        "buyer_intent":    ["upwork", "reddit"],
    },
    "developer_tools": {
        "trending_models": ["huggingface", "replicate"],
        "market_apps":     ["producthunt", "trustmrr"],
        "complaints":      ["github_issues", "reddit", "stackoverflow"],
        "buyer_intent":    ["upwork", "reddit"],
    },
    "b2b_saas": {
        "trending_models": ["huggingface", "replicate"],
        "market_apps":     ["producthunt", "trustmrr"],
        "complaints":      ["g2", "capterra", "reddit"],
        "buyer_intent":    ["upwork", "reddit"],
    },
    "consumer_app": {
        "trending_models": ["huggingface", "replicate", "fal"],
        "market_apps":     ["producthunt", "google_play", "app_store"],
        "complaints":      ["google_play", "app_store", "reddit"],
        "buyer_intent":    ["reddit", "upwork"],
    },
    "vertical_ai": {
        "trending_models": ["huggingface", "replicate"],
        "market_apps":     ["producthunt", "trustmrr"],
        "complaints":      ["g2", "capterra", "reddit"],
        "buyer_intent":    ["upwork", "reddit"],
    },
    "marketplace": {
        "trending_models": ["huggingface", "replicate"],
        "market_apps":     ["producthunt", "trustmrr"],
        "complaints":      ["g2", "capterra", "reddit"],
        "buyer_intent":    ["upwork", "reddit"],
    },
    "infrastructure": {
        "trending_models": ["huggingface", "replicate"],
        "market_apps":     ["producthunt", "trustmrr"],
        "complaints":      ["github_issues", "reddit"],
        "buyer_intent":    ["upwork", "reddit"],
    },
    # Güvenli genel profil — sözlükte olmayan kategoriler için fallback
    "generic_tech_saas": {
        "trending_models": ["huggingface", "replicate", "tavily_generic"],
        "market_apps":     ["producthunt", "tavily_generic"],
        "complaints":      ["g2", "reddit", "tavily_generic"],
        "buyer_intent":    ["upwork", "reddit", "tavily_generic"],
    },
}

# ──────────────────────────────────────────────
# Katman B — Node × İzin Verilen Kaynak (Whitelist)
# ──────────────────────────────────────────────

NODE_SOURCE_WHITELIST: dict[str, list[str]] = {
    "compute_market_sizing":  ["statista", "gartner", "crunchbase", "linkedin_sales_nav"],
    "cluster_complaints":     ["g2", "capterra", "reddit", "trustpilot", "google_play", "app_store"],
    "generate_gtm_assets":    ["reddit", "upwork"],
    "fetch_trending_models":  ["replicate", "huggingface", "fal", "tavily_generic"],
    "match_to_market":        ["producthunt", "trustmrr", "tavily_generic"],
}

# ──────────────────────────────────────────────
# Katman C — Kaynak × Güven Ağırlığı
# ──────────────────────────────────────────────

SOURCE_CONFIDENCE: dict[str, float] = {
    "crunchbase":      0.95,
    "g2":              0.90,
    "capterra":        0.90,
    "statista":        0.90,
    "gartner":         0.90,
    "producthunt":     0.80,
    "trustmrr":        0.80,
    "github_issues":   0.75,
    "stackoverflow":   0.75,
    "google_play":     0.70,
    "app_store":       0.70,
    "reddit":          0.60,
    "upwork":          0.60,
    "trustpilot":      0.65,
    "tavily_generic":  0.30,
}


def get_confidence(source_id: str) -> float:
    """Kaynak için güven ağırlığını döner. Bilinmeyende 0.20."""
    return SOURCE_CONFIDENCE.get(source_id, 0.20)
