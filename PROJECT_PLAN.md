# PROJECT_PLAN.md — Startup Idea Finder (Model-First Yaklaşım)

## Proje Özeti

**Soru:** "Hangi AI modeli kullanılmayan boşlukta para kazandırır?"

Kullanıcı bir AI alanı seçer (video, ses, görsel, kod...) ya da direkt keşif modunda açar.
Sistem şunu yapar:
1. O alanda **trend olan AI modelleri** tespit eder (Replicate, HuggingFace, fal.ai)
2. O model yeteneklerine uygun **para kazanan uygulamaları** bulur (TrustMRR + ProductHunt)
3. O uygulamaların **rakip şikayetlerini** çeker (G2, Play Store, App Store)
4. "Bu modelle bu boşluğu doldur" şeklinde **yapılandırılmış fırsat raporu** üretir

---

## Kullanıcı Akışı

### Mod 1 — Keşfet

```
Uygulama açılır
  → Dashboard: "Bu hafta trend AI modeller"
      [🔥 WAN 2.1 - Video]  [🖼️ Flux Pro - Image]  [🎙️ Dia - TTS]
  → Karta tıklar
  → Agent çalışır → Fırsat raporu çıkar
```

### Mod 2 — Yönlendirilmiş Arama

```
Kullanıcı kategori seçer: [Video] [Ses] [Görsel] [Kod] [Yazı]
  → Agent o kategorideki trend modelleri + para kazanan appları eşleştirir
  → Sıralı fırsat listesi çıkar
```

### Çıktı Formatı

```
🔥 FIRSAT: WAN 2.1 ile Blog-to-Video SaaS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Model: WAN 2.1 (fal.ai / Replicate) — 3.2M çalıştırma
🎯 Kategori: Video Generation

💰 Pazar Kanıtı (TrustMRR):
   • Lumen5    → $40K MRR
   • Pictory   → $12K MRR

❌ Rakip Boşlukları (G2 + Play Store):
   "Kalite çok düşük" × 234 | "2025 model kalitesi yok" × 89

💡 Fikir: Mevcut applar eski modeller kullanıyor.
   WAN 2.1 ile çok daha iyi kalite → $19-49/ay SaaS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Mimari

```
┌──────────────────────────────────────────────────┐
│              MODEL KATMANI  [Faz 1]              │
│  Replicate  → scrapers/replicate.py              │
│  HuggingFace → scrapers/huggingface.py           │
│  fal.ai     → scrapers/fal.py                   │
│  → data/models_raw.json                          │
│  → ChromaDB koleksiyonu: "ai_models"             │
└───────────────────┬──────────────────────────────┘
                    │ model category tags
                    ▼
┌──────────────────────────────────────────────────┐
│             PAZAR KATMANI  [Faz 1]               │
│  TrustMRR   → scrapers/trustmrr.py               │
│  ProductHunt → scrapers/producthunt.py           │
│  → data/apps_raw.json                            │
│  → ChromaDB koleksiyonu: "startup_apps"          │
└───────────────────┬──────────────────────────────┘
                    │ category match
                    ▼
┌──────────────────────────────────────────────────┐
│           RAKİP ANALİZİ  [Faz 2]                │
│  G2/Capterra → scrapers/g2_capterra.py           │
│  Tavily      → web arama                         │
│  → negatif yorumlar → LLM kümeleme               │
└───────────────────┬──────────────────────────────┘
                    │ complaints clusters
                    ▼
┌──────────────────────────────────────────────────┐
│           STORE REVIEWS  [Faz 3]                 │
│  Play Store → google-play-scraper                │
│  App Store  → app-store-scraper                  │
│  → 1-2 yıldız yorumlar → LLM kümeleme           │
└───────────────────┬──────────────────────────────┘
                    │ all insights
                    ▼
┌──────────────────────────────────────────────────┐
│           AGENT KATMANI  [Her Faz]               │
│  LangGraph StateGraph — agent/idea_agent.py      │
│  LLM: Groq llama-3.3-70b-versatile              │
│  Monitoring: LangSmith                           │
└───────────────────┬──────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│                UI  [Faz 1]                       │
│  Streamlit → app.py                              │
└──────────────────────────────────────────────────┘
```

---

## FAZ 1 — Temel Sistem

### Scrapers

| Dosya | Kaynak | Çekilen |
|---|---|---|
| `scrapers/replicate.py` | replicate.com | model adı, kategori, run sayısı, tags |
| `scrapers/huggingface.py` | huggingface.co/models | trending modeller, pipeline tag |
| `scrapers/fal.py` | fal.ai | model listesi, kategori |
| `scrapers/trustmrr.py` | trustmrr.com | app adı, MRR, kategori, açıklama |
| `scrapers/producthunt.py` | GraphQL API | name, tagline, topics, votes |

### ChromaDB — İki Koleksiyon

**Koleksiyon 1: `ai_models`**
```
page_content = "model_name. description. capability tags"
metadata = {
    source, run_count, category,
    url, last_updated, api_available
}
```

**Koleksiyon 2: `startup_apps`**
```
page_content = "app_name. description. category. target_audience"
metadata = {
    mrr, pricing, source, url, category
}
```

### LangGraph Agent — Faz 1 Akışı

```
START
  ↓
fetch_trending_models_node
  (Replicate/HuggingFace'ten bu haftanın trend modelleri)
  ↓
match_to_market_node
  (Model kategorisi → ChromaDB "startup_apps"'de benzer uygulama bul)
  ↓
generate_opportunity_node
  (LLM → fırsat raporu üret)
  ↓
END
```

### API İhtiyaçları — Faz 1

| Key | URL | Plan |
|---|---|---|
| `GROQ_API_KEY` | console.groq.com | Ücretsiz |
| `PRODUCTHUNT_API_KEY` | producthunt.com/v2/oauth | Ücretsiz |
| `LANGSMITH_API_KEY` | smith.langchain.com | Ücretsiz |

---

## FAZ 2 — Rakip Boşluk Analizi

### Yeni Scrapers

| Dosya | Kaynak | Hedef |
|---|---|---|
| `scrapers/g2_capterra.py` | g2.com | Negatif yorumlar, puan |
| (Tavily) | web arama | Rakip haberler, Reddit şikayetleri |

### Agent Güncellemesi — Faz 2

```
match_to_market_node
  ↓
scrape_competitor_reviews_node  ← YENİ
  (G2 + Tavily ile rakip şikayetleri)
  ↓
cluster_complaints_node         ← YENİ
  (LLM: "En çok tekrarlanan 5 şikayet")
  ↓
generate_opportunity_node (genişletildi)
```

### Yeni API — Faz 2

| Key | URL | Plan |
|---|---|---|
| `TAVILY_API_KEY` | tavily.com | Ücretsiz 1K/ay |

---

## FAZ 3 — Uygulama Mağazası Yorumları

### Yeni Scrapers

| Dosya | Kaynak | Hedef |
|---|---|---|
| `scrapers/store_reviews.py` | Play Store + App Store | 1-2 yıldız yorumlar |

### Agent Güncellemesi — Faz 3

```
cluster_complaints_node
  ↓
find_store_app_node    ← YENİ (LLM: Play Store paket adı tahmin et)
  ↓
scrape_store_reviews_node ← YENİ
  ↓
generate_opportunity_node (final versiyon)
```

---

## Klasör Yapısı

```
Startup_Idea_Finder/
├── scrapers/
│   ├── replicate.py          [Faz 1]
│   ├── huggingface.py        [Faz 1]
│   ├── fal.py                [Faz 1]
│   ├── trustmrr.py           [Faz 1]
│   ├── producthunt.py        [Faz 1]
│   ├── g2_capterra.py        [Faz 2]
│   └── store_reviews.py      [Faz 3]
├── ingestion/
│   └── ingest.py             [Faz 1]
├── agent/
│   └── idea_agent.py         [Faz 1→3]
├── data/
│   ├── models_raw.json
│   ├── apps_raw.json
│   └── reviews/
├── chroma_db/                (gitignore!)
├── app.py                    [Faz 1]
├── scheduler.py              [Faz 1]
├── requirements.txt
├── .env.example
├── HOW_TO_BUILD.md
├── deep_report.py
├── README.md
└── PROJECT_PLAN.md
```

---

## Tech Stack

| Araç | Amaç | Faz |
|---|---|---|
| `beautifulsoup4` + `requests` | Replicate, fal.ai, TrustMRR, G2 scraping | 1-2 |
| `huggingface_hub` | HuggingFace trending modeller (resmi SDK) | 1 |
| `google-play-scraper` | Play Store yorumları | 3 |
| `app-store-scraper` | App Store yorumları | 3 |
| `langchain-chroma` | ChromaDB vektör DB | 1 |
| `langchain-huggingface` | MiniLM embedding (yerel, ücretsiz) | 1 |
| `langchain-groq` | Groq LLM | 1 |
| `langgraph` | Agent state machine | 1 |
| `tavily-python` | Web arama | 2 |
| `streamlit` | UI | 1 |
| `schedule` | Günlük otomatik güncelleme | 1 |
| `python-dotenv` | .env yönetimi | 1 |
| `langsmith` | Agent monitoring | 1 |

---

## Durum Takibi

- [x] Proje planı (model-first) hazırlandı
- [ ] Faz 1: Replicate + HuggingFace + fal.ai scrapers
- [ ] Faz 1: TrustMRR + ProductHunt scrapers
- [ ] Faz 1: ChromaDB ingestion (iki koleksiyon)
- [ ] Faz 1: LangGraph agent (temel akış)
- [ ] Faz 1: Streamlit UI
- [ ] Faz 2: G2/Capterra scraper
- [ ] Faz 2: Tavily entegrasyonu
- [ ] Faz 2: Şikayet kümeleme node
- [ ] Faz 3: Play Store scraper
- [ ] Faz 3: App Store scraper
- [ ] Faz 3: Store yorum kümeleme
