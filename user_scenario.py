"""
================================================================================
  STARTUP IDEA FINDER — KESİNLEŞMİŞ KULLANICI SENARYOSU
  Repo: https://github.com/tarikmenguc/Startup_Idea_Finder
================================================================================

Bu dosya projenin kullanıcı deneyimini (UX flow) ve sistemin tam
davranışını belgelemek için yazılmıştır. Kod değil, referans dokümandır.
================================================================================
"""


# ==============================================================================
# BÖLÜM 1: KULLANICI KİM?
# ==============================================================================

KULLANICI_PROFİLİ = """
Ahmet — AI meraklısı, SaaS yapmak istiyor.

Ahmet'in sorunu:
  - "Hangi AI modeliyle para kazanabileceğim?"
  - Replicate, HuggingFace, fal.ai'de onlarca model var
  - TrustMRR'da saatlerce gezinmesi gerekiyor
  - G2'de rakip şikayetlerini manuel araştırması gerekiyor

Bu proje Ahmet'in tüm bu işi otomatik yapmasını sağlar.
"""


# ==============================================================================
# BÖLÜM 2: KULLANICI AKIŞI (ADIM ADIM)
# ==============================================================================

# --- ADIM 1: Uygulamayı açar ---
ADIM_1 = """
Terminalde çalıştırır:
    streamlit run app.py

Tarayıcıda açılan ekran:

    ┌────────────────────────────────────────────────┐
    │  🔍 Startup Idea Finder                        │
    │  "Trend AI modellerinden pazar fırsatı bul"   │
    │                                                │
    │  [ 🔥 Keşfet ]   [ 🎯 Kategori Seç ]          │
    └────────────────────────────────────────────────┘
"""

# --- ADIM 2: İki seçenek ---
ADIM_2_SECENEKLER = {
    "Keşfet Modu": {
        "açıklama": "Kullanıcı hiçbir şey seçmez, direkt butona basar.",
        "ne_olur":  "Sistem bu haftanın en trend AI modellerini kendisi bulur.",
        "ne_girmez": "Hiçbir şey — kullanıcıdan 0 input",
    },
    "Kategori Modu": {
        "açıklama": "Kullanıcı bir alan seçer.",
        "ne_olur":  "Sistem o alanda trending modeller + para kazanan applar arar.",
        "kategoriler": [
            "Video Generation",
            "Text to Image",
            "Speech to Text",
            "Text to Speech",
            "Code Generation",
            "Music Generation",
            "Document AI",
        ],
    },
}

# --- ADIM 3: Butona basar ---
ADIM_3 = """
Kullanıcı:   🚀 Fırsat Bul  [tıklar]

Ekranda:     ⏳ Modeller taranıyor, pazar analiz ediliyor...

Süre:        ~10-30 saniye
"""

# --- ADIM 4: Arka planda olan ---
ADIM_4_ARKA_PLAN = """
Agent adım adım çalışır (LangGraph StateGraph):

Faz 1:
  1. ChromaDB "ai_models"     → Kategoriye göre trend modeller bul
  2. ChromaDB "startup_apps"  → O modelle uyumlu para kazanan applar bul
  3. LLM                      → Fırsat raporu üret

Faz 2 (eklenir):
  4. G2 / Capterra scraper    → O appların negatif yorumları
  5. Tavily web araması       → Rakip şikayetleri, haberler
  6. LLM kümeleme             → "En çok tekrarlanan 5 şikayet"

Faz 3 (eklenir):
  7. Play Store scraper       → 1-2 yıldız yorumlar (200 adet)
  8. App Store scraper        → 1-2 yıldız yorumlar (100 adet)
  9. LLM kümeleme             → "Kullanıcıların en büyük acısı"
 10. Final rapor üret
"""

# --- ADIM 5: Kullanıcı raporu görür ---
ADIM_5_ORNEK_RAPOR = """
🔥 FIRSAT #1: WAN 2.1 ile Blog-to-Video SaaS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Model: WAN 2.1 (Replicate) — 3.2M çalıştırma
🎯 Kategori: Video Generation

💰 Pazar Kanıtı (TrustMRR + ProductHunt):
   • Lumen5      → $40K MRR   (blog-to-video)
   • Pictory.ai  → $12K MRR   (video summarizer)
   • InVideo     → $15K MRR   (social media video)

❌ Bu Uygulamaların Boşlukları (G2 + Play Store):
   • "Video kalitesi çok düşük" × 234 yorum
   • "2025 model kalitesi yok hâlâ" × 89 yorum
   • "Ses-video senkronizasyonu bozuk" × 67 yorum
   • "Batch export yok" × 45 yorum

💡 Fırsat:
   Mevcut uygulamalar eski modeller kullanıyor.
   WAN 2.1 ile %10x daha iyi kalite sun → $29-49/ay SaaS

🔗 https://replicate.com/wavymulder/wan-2.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 FIRSAT #2: Flux Pro 1.1 ile Product Photography SaaS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
"""

# --- ADIM 6: Kullanıcı bu raporla ne yapar? ---
ADIM_6_SONRASI = """
Kullanıcı favori fikrini seçer:
  → Replicate linkinden modeli inceler
  → Lumen5 / Pictory'ye bakar, eksiklerini bizzat doğrular
  → Kendi SaaS'ını bu model üzerine inşa eder
"""


# ==============================================================================
# BÖLÜM 3: KULLANICIDAN İSTENENLER vs İSTENMEYENLER
# ==============================================================================

KULLANICIDAN_İSTENENLER = [
    "Kategori seçmek (veya hiçbir şey seçmemek — keşfet modu)",
    "Butona basmak",
]

KULLANICIDAN_İSTENMEYENLER = [
    "Beceri girmek ('Python biliyorum' gibi)",
    "Bütçe sınırı girmek",
    "Modelleri manuel araştırmak",
    "TrustMRR'da saat harcamak",
    "G2'de şikayet aramak",
    "Play Store'a manuel bakmak",
    "Pazar analizi yapmak",
]


# ==============================================================================
# BÖLÜM 4: SİSTEMİN KAYNAKLAR HARİTASI
# ==============================================================================

KAYNAKLAR = {
    # MODEL VERİSİ — "Trend hangi modeller?"
    "ai_model_sources": {
        "HuggingFace Hub":  "huggingface_hub SDK — trending modeller",
        "Replicate.com":    "BeautifulSoup — run count (popularite sinyali)",
        "fal.ai":           "BeautifulSoup — yeni yayınlanan modeller",
        "ChromaDB":         "Koleksiyon: 'ai_models'",
    },

    # PAZAR VERİSİ — "Bu kategoride kim para kazanıyor?"
    "market_sources": {
        "TrustMRR":     "BeautifulSoup — MRR + kategori",
        "ProductHunt":  "GraphQL API — oylar + kategori",
        "ChromaDB":     "Koleksiyon: 'startup_apps'",
    },

    # RAKİP ANALİZİ — "Bu uygulamalar neden şikayet alıyor?" [Faz 2]
    "competitor_sources": {
        "G2 / Capterra": "BeautifulSoup — 1-2 yıldız yorumlar",
        "Tavily API":    "Web arama — rakip haberler, Reddit şikayetleri",
    },

    # STORE YORUMLARI — "Gerçek kullanıcılar ne diyor?" [Faz 3]
    "store_sources": {
        "Google Play Store": "google-play-scraper — 1-2 yıldız, 200 yorum",
        "Apple App Store":   "app-store-scraper — 1-2 yıldız, 100 yorum",
    },
}


# ==============================================================================
# BÖLÜM 5: AGENT NODE HARİTASI
# ==============================================================================

LANGGRAPH_NODES = {
    "Faz 1": [
        ("fetch_trending_models_node", "ChromaDB 'ai_models' → trend modeller"),
        ("match_to_market_node",       "ChromaDB 'startup_apps' → para kazanan applar"),
        ("generate_opportunity_node",  "LLM → temel fırsat raporu"),
    ],
    "Faz 2 Eklemeleri": [
        ("scrape_competitor_reviews_node", "G2 + Tavily → negatif yorumlar"),
        ("cluster_complaints_node",        "LLM kümeleme → top 5 şikayet"),
    ],
    "Faz 3 Eklemeleri": [
        ("find_store_app_node",         "LLM → Play Store paket adı tahmin et"),
        ("scrape_store_reviews_node",   "google-play-scraper + app-store-scraper"),
        ("cluster_store_problems_node", "LLM → store kullanıcı acısı kümele"),
    ],
}

FAZ1_GRAPH = """
START
  ↓
fetch_trending_models_node
  ↓
match_to_market_node
  ↓
generate_opportunity_node
  ↓
END
"""

FAZ3_GRAPH = """
START
  ↓
fetch_trending_models_node
  ↓
match_to_market_node
  ↓
scrape_competitor_reviews_node
  ↓
cluster_complaints_node
  ↓
find_store_app_node
  ↓
scrape_store_reviews_node
  ↓
cluster_store_problems_node
  ↓
generate_opportunity_node  (tüm veriler toplandı)
  ↓
END
"""


# ==============================================================================
# BÖLÜM 6: AGENTİC RAG — BU PROJEDE NE ÖĞRENIYORUM?
# ==============================================================================

AGENTIC_RAG_OGRENME_HARITASI = {
    "1. Embedding + Vector Store": {
        "kavram": "Metin → sayı dizisi → ChromaDB'ye kaydedilir",
        "bu_projede": "Model açıklamaları ve app açıklamaları vektöre çevrilir",
        "dosya": "ingestion/ingest.py",
    },
    "2. Retrieval": {
        "kavram": "Sorgu da vektöre çevrilir → en yakın kayıtlar bulunur",
        "bu_projede": "'video generation' → benzer modeller + benzer applar",
        "dosya": "agent/idea_agent.py → similarity_search()",
    },
    "3. LangGraph StateGraph": {
        "kavram": "Agent hafızası (state) + adım adım karar mekanizması",
        "bu_projede": "Her node bir adım — state bir sonraki node'a iletilir",
        "dosya": "agent/idea_agent.py",
    },
    "4. Tool Use": {
        "kavram": "Agent dış dünyaya erişir — scraper, API, web araması",
        "bu_projede": "Tavily, G2 scraper, Play Store → agent'ın araçları",
        "dosya": "scrapers/*.py",
    },
    "5. Cross-Collection Retrieval": {
        "kavram": "İki farklı vektör koleksiyonunu eşleştirme",
        "bu_projede": "'ai_models' koleksiyonu + 'startup_apps' koleksiyonu → cross-match",
        "dosya": "agent/idea_agent.py → match_to_market_node",
        "not": "Bu classic RAG'da olmaz — Agentic RAG'a özgü",
    },
}
