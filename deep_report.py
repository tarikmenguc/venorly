"""
================================================================================
  STARTUP IDEA FINDER — DERİN TEKNİK RAPOR (Model-First Yaklaşım)
  Repo: https://github.com/tarikmenguc/Startup_Idea_Finder
  Güncelleme: Şubat 2026
================================================================================

PROJE FELSEFESİ:
  Eski yaklaşım: "Kullanıcının becerilerine göre uygulama bul"
  Yeni yaklaşım: "Trend AI modelinden kanıtlanmış pazar fırsatı bul"

  Soru: "Hangi yeni AI modeli kullanılmayan boşlukta para kazandırır?"
================================================================================
"""


# ==============================================================================
# BÖLÜM 1: ÜST DÜZEY AKIŞ
# ==============================================================================

FLOW = """
ADIM 1: MODEL TRENDLERİ
  Replicate.com  → trending modeller + kaç kez çalıştırıldı
  HuggingFace    → bu haftanın trending modelleri
  fal.ai         → yeni yayınlanan modeller
    → Kategori: video-gen, image-gen, speech, code, text...
    → data/models_raw.json

ADIM 2: PAZAR VERİSİ
  TrustMRR       → o kategoride para kazanan applar + MRR
  ProductHunt    → o kategoride oylanan yeni applar
    → data/apps_raw.json

ADIM 3: RAKİP ZAYIF NOKTALARI  [Faz 2]
  G2 / Capterra  → o appların 1-2 yıldız yorumları
  Tavily         → web'den rakip şikayetleri, haberler
    → LLM kümeleme: "En çok tekrarlanan 5 şikayet"

ADIM 4: STORE YORUMLARI  [Faz 3]
  Play Store     → google-play-scraper (1-2 yıldız, 200 yorum)
  App Store      → app-store-scraper
    → LLM kümeleme: "Kullanıcıların en büyük acısı nedir?"

ADIM 5: FIRSAT RAPORU
  LangGraph agent → tüm verileri birleştirir
  Çıktı: Model + Pazar kanıtı + Boşluk + Somut fikir
"""


# ==============================================================================
# BÖLÜM 2: MİMARİ ŞEMA
# ==============================================================================

ARCHITECTURE = """
┌──────────────────────────────────────────────────────────────┐
│                  MODEL KATMANI  [Faz 1]                      │
│  scrapers/replicate.py   → Replicate trending                │
│  scrapers/huggingface.py → HuggingFace Hub trending          │
│  scrapers/fal.py         → fal.ai model listesi              │
└──────────────────────────┬───────────────────────────────────┘
                           │ JSON → ingestion/ingest.py
                           ▼ ChromaDB: "ai_models"
┌──────────────────────────────────────────────────────────────┐
│                  PAZAR KATMANI  [Faz 1]                      │
│  scrapers/trustmrr.py    → BeautifulSoup                     │
│  scrapers/producthunt.py → GraphQL API                       │
└──────────────────────────┬───────────────────────────────────┘
                           │ JSON → ingestion/ingest.py
                           ▼ ChromaDB: "startup_apps"
┌──────────────────────────────────────────────────────────────┐
│              RAKİP ANALİZİ  [Faz 2]                         │
│  scrapers/g2_capterra.py → negatif yorumlar                  │
│  Tavily API              → web arama                         │
└──────────────────────────┬───────────────────────────────────┘
                           │ complaints clusters
                           ▼
┌──────────────────────────────────────────────────────────────┐
│              STORE REVIEWS  [Faz 3]                          │
│  scrapers/store_reviews.py → Play Store + App Store          │
└──────────────────────────┬───────────────────────────────────┘
                           │ all insights
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                AGENT KATMANI  (LangGraph)                    │
│  agent/idea_agent.py                                         │
│  LLM: Groq llama-3.3-70b-versatile                          │
│  Monitoring: LangSmith                                       │
└──────────────────────────┬───────────────────────────────────┘
                           │ structured report
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    UI (Streamlit)                            │
│  app.py — Keşfet modu + Kategorili arama                    │
└──────────────────────────────────────────────────────────────┘
"""


# ==============================================================================
# BÖLÜM 3: İKİ CHROMAdb KOLEKSIYONU
# ==============================================================================

"""
NEDEN İKİ KOLEKSİYON?
  "ai_models" → Hangi model ne yapabiliyor?
  "startup_apps" → Hangi uygulama para kazanıyor?

Agent bu iki koleksiyonu birbirine eşleştirir:
  model.category == "video-generation"
  → startup_apps'de "video creator OR content creation" ara
"""

CHROMADB_MODELS_COLLECTION = {
    "collection_name": "ai_models",
    "page_content": "{model_name}. {description}. Capability: {tags}",
    "metadata_fields": {
        "source": "replicate / huggingface / fal",
        "model_name": "wan-2.1",
        "category": "video-generation",
        "run_count": "3.2M",        # Replicate'ten - popülarite sinyali
        "url": "https://replicate.com/...",
        "last_updated": "2025-12",  # Ne kadar yeni?
        "api_available": True,
    }
}

CHROMADB_APPS_COLLECTION = {
    "collection_name": "startup_apps",
    "page_content": "{name}. {description}. Category: {category}. Audience: {target_audience}",
    "metadata_fields": {
        "source": "trustmrr / producthunt",
        "name": "Lumen5",
        "mrr": "$40,000",
        "pricing": "$29/mo",
        "category": "video-generation",
        "url": "https://...",
        "votes": 1240,   # ProductHunt için
    }
}


# ==============================================================================
# BÖLÜM 4: LANGGRAPH AGENT — FAZ FAZ AKIŞ
# ==============================================================================

FAZ1_AGENT_FLOW = """
START
  ↓
fetch_trending_models_node
  → ChromaDB "ai_models"den bu haftanın trend modellerini çek
  → Kategori etiketlerini al

  ↓
match_to_market_node
  → Model kategorisi → ChromaDB "startup_apps"de similarity search
  → Top-5 para kazanan uygulama bul

  ↓
generate_opportunity_node
  → LLM: "Bu modeli kullanan bu applar var, işte boşluk"
  → Yapılandırılmış Markdown rapor

END
"""

FAZ2_ADDITIONS = """
match_to_market_node
  ↓
scrape_competitor_reviews_node  ← YENİ
  → G2'den negatif yorumlar
  → Tavily'den rakip şikayetleri

  ↓
cluster_complaints_node         ← YENİ
  → LLM: şikayetleri kategorize et, kaç kez tekrarlanmış say

  ↓
generate_opportunity_node (boşluk bilgisi eklendi)
"""

FAZ3_ADDITIONS = """
cluster_complaints_node
  ↓
find_store_app_node    ← YENİ
  → LLM: Play Store paket adı tahmin et (örn: com.lumen5.video)

  ↓
scrape_store_reviews_node ← YENİ
  → google-play-scraper: 1-2 yıldız, 200 yorum
  → app-store-scraper: 1-2 yıldız, 100 yorum

  ↓
generate_opportunity_node (store verileri de eklendi — final versiyon)
"""


# ==============================================================================
# BÖLÜM 5: MODEL KATEGORİ → PAZAR EŞLEŞTİRMESİ
# ==============================================================================

MODEL_CATEGORY_TO_MARKET = {
    "text-to-image":     ["image generator", "AI art", "design tool", "avatar"],
    "video-generation":  ["video creator", "AI video", "content creation", "shorts"],
    "speech-to-text":    ["transcription", "podcast tool", "meeting notes", "subtitle"],
    "text-to-speech":    ["voiceover", "audio content", "podcast", "narration"],
    "code-generation":   ["developer tool", "code assistant", "IDE plugin", "cli"],
    "face-swap":         ["avatar", "entertainment", "video personalization"],
    "image-editing":     ["photo editor", "background removal", "upscaler"],
    "music-generation":  ["music creator", "background music", "jingle maker"],
    "3d-generation":     ["3D model", "game asset", "product visualization"],
    "document-ai":       ["invoice", "OCR", "document parser", "contract analyzer"],
}


# ==============================================================================
# BÖLÜM 6: SCRAPERS — TEKNİK DETAYLAR
# ==============================================================================

SCRAPER_DETAILS = {
    "replicate.py": {
        "base_url": "https://replicate.com/explore",
        "method": "BeautifulSoup",
        "rate_limit": "time.sleep(2)",
        "target_fields": ["model_name", "creator", "category", "run_count", "description", "tags"],
        "pagination": "?cursor=X",
        "anti_bot": "User-Agent header gerekli",
    },
    "huggingface.py": {
        "library": "huggingface_hub",  # Resmi SDK — daha güvenli
        "method": "from huggingface_hub import list_models",
        "filter": "sort='trending', limit=50",
        "target_fields": ["modelId", "pipeline_tag", "downloads", "likes", "lastModified"],
    },
    "fal.py": {
        "base_url": "https://fal.ai/models",
        "method": "BeautifulSoup",
        "rate_limit": "time.sleep(1)",
        "target_fields": ["model_name", "category", "description", "url"],
    },
    "trustmrr.py": {
        "base_url": "https://trustmrr.com/apps",
        "method": "BeautifulSoup",
        "rate_limit": "time.sleep(2)",
        "target_fields": ["name", "mrr", "category", "description", "pricing", "url"],
        "pagination": "?page=N",
    },
    "producthunt.py": {
        "endpoint": "https://api.producthunt.com/v2/api/graphql",
        "method": "GraphQL POST",
        "auth": "Bearer {PRODUCTHUNT_API_KEY}",
        "target_fields": ["name", "tagline", "description", "topics", "votesCount", "website"],
    },
    "g2_capterra.py": {
        "base_url": "https://www.g2.com/search?query={app_name}",
        "method": "BeautifulSoup",
        "rate_limit": "time.sleep(3)  # Agresif bot koruması var!",
        "target_fields": ["rating", "review_count", "negative_reviews"],
        "filter": "1-2 yıldız yorumları filtrele",
    },
    "store_reviews.py": {
        "libraries": ["google-play-scraper", "app-store-scraper"],
        "filter": "score <= 2, count=200",
        "extra": "thumbsUpCount yüksek yorumlar daha önemli",
    },
}


# ==============================================================================
# BÖLÜM 7: API KEY LİSTESİ
# ==============================================================================

API_KEYS = {
    "GROQ_API_KEY": {
        "url": "https://console.groq.com",
        "plan": "Ücretsiz",
        "ne_için": "Groq LLM (llama-3.3-70b-versatile)",
        "faz": 1,
        "zorunlu": True,
    },
    "PRODUCTHUNT_API_KEY": {
        "url": "https://www.producthunt.com/v2/oauth/applications",
        "plan": "Ücretsiz — Developer Token al",
        "ne_için": "ProductHunt GraphQL API",
        "faz": 1,
        "zorunlu": True,
    },
    "TAVILY_API_KEY": {
        "url": "https://tavily.com",
        "plan": "Ücretsiz (1.000 istek/ay)",
        "ne_için": "Rakip web araması",
        "faz": 2,
        "zorunlu": False,
    },
    "LANGSMITH_API_KEY": {
        "url": "https://smith.langchain.com",
        "plan": "Ücretsiz",
        "ne_için": "LangGraph agent trace monitoring",
        "faz": 1,
        "zorunlu": False,
    },
}


# ==============================================================================
# BÖLÜM 8: TECH STACK
# ==============================================================================

TECH_STACK = {
    "beautifulsoup4":       ("Replicate, fal.ai, TrustMRR, G2 scraping", "Faz 1-2"),
    "requests":             ("HTTP istekleri", "Faz 1"),
    "huggingface_hub":      ("HuggingFace trending modeller — resmi SDK", "Faz 1"),
    "google-play-scraper":  ("Play Store yorumları", "Faz 3"),
    "app-store-scraper":    ("App Store yorumları", "Faz 3"),
    "langchain-chroma":     ("ChromaDB — 2 koleksiyon", "Faz 1"),
    "langchain-huggingface": ("MiniLM embedding (yerel, ücretsiz)", "Faz 1"),
    "langchain-groq":       ("Groq LLM entegrasyonu", "Faz 1"),
    "langgraph":            ("Agent state machine", "Faz 1"),
    "tavily-python":        ("Web arama tool", "Faz 2"),
    "streamlit":            ("Kullanıcı arayüzü", "Faz 1"),
    "schedule":             ("Günlük otomatik güncelleme", "Faz 1"),
    "python-dotenv":        ("API key yönetimi", "Faz 1"),
    "langsmith":            ("Agent monitoring ve debugging", "Faz 1"),
}


# ==============================================================================
# BÖLÜM 9: FINAL RAPOR FORMATI
# ==============================================================================

REPORT_EXAMPLE = """
🔥 FIRSAT #1: WAN 2.1 ile Blog-to-Video SaaS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Model: WAN 2.1 (Replicate) — 3.2M çalıştırma — Son güncelleme: Aralık 2025
🎯 Kategori: Video Generation

💰 Pazar Kanıtı (TrustMRR + ProductHunt):
   • Lumen5        → $40K MRR  (blog-to-video)
   • Pictory.ai    → $12K MRR  (video summarizer)
   • InVideo       → $15K MRR  (social media video)
   Ortalama fiyat: $29-49/ay

❌ Bu Appların Boşlukları (G2 + Play Store):
   • "Video kalitesi çok düşük" × 234 yorum
   • "2025 model kalitesini göremiyorum" × 89 yorum
   • "Ses-video senkronizasyonu bozuk" × 67 yorum
   • "Batch export yok" × 45 yorum

💡 Fırsat:
   Mevcut applar eski diffusion modelleri kullanıyor.
   WAN 2.1 ile %10x daha iyi kalite sunulabilir.
   Fiyat: $29-49/ay (rakiplerle rekabetçi)

🔗 Model: https://replicate.com/wavymulder/wan-2.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# ==============================================================================
# BÖLÜM 10: AGENTİC RAG ÖĞRENİM NOTLARI
# ==============================================================================

"""
BU PROJEDEKİ AGENTİC RAG UNSURLARI:

1. RETRIEVAL:
   - "ai_models" koleksiyonundan trend modeller → similarity_search
   - "startup_apps" koleksiyonundan eşleşen applar → similarity_search
   - İki koleksiyon arasında CROSS-RETRIEVAL → bu classic RAG'da olmaz

2. AGENTIC:
   - LangGraph StateGraph: adım adım karar mekanizması
   - Tool use: scraper'lar, G2, Tavily, Play Store → agent araçları
   - Multi-step: Bul → Analiz et → Kümeleme → Raporla
   - Conditional routing (Faz 2'de): "G2'de yeterli yorum var mı?"

3. GENERATION:
   - LLM sadece cevap değil, STRUCTURED rapor üretiyor
   - Prompt engineering: sayısal verileri anlamlı hale getirme

KLASİK RAG vs AGENTİC RAG (Bu Proje):
  Classic: Soru → 1 koleksiyon ara → LLM cevap ver
  Agentic: Model bul → Pazar ara → Rakip analiz et → Kümeleme → Rapor
           (Her adım bir öncekinin çıktısını kullanır — ZINCIRLEME)
"""


# ==============================================================================
# BÖLÜM 11: SÜRE TAHMİNLERİ
# ==============================================================================

TIMELINE = {
    "Faz 1 - Model-First MVP": {
        "Replicate + HuggingFace + fal.ai scrapers": "4-5 saat",
        "TrustMRR + ProductHunt scrapers":            "4-5 saat",
        "ChromaDB ingestion (2 koleksiyon)":          "3 saat",
        "LangGraph agent (temel akış)":               "5-6 saat",
        "Streamlit UI":                               "3-4 saat",
        "TOPLAM":                                     "~1 hafta",
    },
    "Faz 2 - Rakip Analizi": {
        "G2/Capterra scraper":                        "5-6 saat",
        "Tavily entegrasyonu":                        "2 saat",
        "Şikayet kümeleme node":                      "3 saat",
        "Agent güncellemesi":                         "2 saat",
        "TOPLAM":                                     "~1 hafta",
    },
    "Faz 3 - Store Reviews": {
        "Play Store scraper":                         "3 saat",
        "App Store scraper":                          "2 saat",
        "Store yorum kümeleme":                       "3 saat",
        "UI güncellemesi":                            "2 saat",
        "TOPLAM":                                     "~3-4 gün",
    },
}
