# 🔍 Startup Idea Finder

**Model-First Agentic RAG** — Trend AI modellerinden kanıtlanmış Micro-SaaS fırsatları bulan akıllı agent.

> "Hangi yeni AI modeli, kullanılmayan bir boşlukta para kazandırır?"

---

## 🎯 Ne Yapıyor?

```
📡 Veri Toplama
   Replicate / HuggingFace / fal.ai → Trend AI modeller
   TrustMRR + ProductHunt → Para kazanan startup'lar
        ↓
🔍 Rakip Analizi
   Tavily (G2, Reddit) → Rakip şikayetleri
   Play Store → Gerçek kullanıcı yorumları (1-2 ⭐)
        ↓
🤖 LangGraph Agent (8 Node)
   Modelleri bul → Pazarı eşle → Şikayetleri kümeleme → Fırsat raporu üret
        ↓
💡 Çıktı: Somut Micro-SaaS fikri + pazar kanıtı + boşluk analizi
```

### Örnek Çıktı
```
🔥 NİŞ FIRSAT: Restoran Sesli Menü Oluşturma
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Model: Kokoro-82M (text-to-speech) — 9.8M indirme
🎯 Niş: Restoran ve yeme-içme sektörü

💰 Pazar Mantığı:
   Origami.chat ve Straion gibi uygulamalar aylık abonelik alıyor.

❌ Rakip Boşlukları:
   - Uygulama hataları ve sorunları
   - Kullanıcı dostu olmayan arayüz
   - Şeffaflık eksikliği

💡 Fırsat: Kokoro-82M ile restoranlar için sesli menü SaaS — $29-49/ay
🔗 https://huggingface.co/hexgrad/Kokoro-82M
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────┐
│                  MODEL KATMANI (Faz 1)                   │
│  scrapers/huggingface.py  → HuggingFace Hub SDK          │
│  scrapers/replicate.py    → Replicate API + HTML          │
│  scrapers/fal.py          → fal.ai HTML parse             │
└──────────────────────────┬──────────────────────────────┘
                           │ JSON → ingestion/ingest.py
                           ▼ ChromaDB: "ai_models" (166 model)
┌─────────────────────────────────────────────────────────┐
│                  PAZAR KATMANI (Faz 1)                    │
│  scrapers/trustmrr.py     → BeautifulSoup scraping        │
│  scrapers/producthunt.py  → GraphQL API                   │
└──────────────────────────┬──────────────────────────────┘
                           │ JSON → ingestion/ingest.py
                           ▼ ChromaDB: "startup_apps" (96 app)
┌─────────────────────────────────────────────────────────┐
│              RAKİP ANALİZİ (Faz 2)                       │
│  scrapers/competitor_research.py → Tavily web arama       │
│  LLM kümeleme → şikayet kategorileri                      │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│              STORE YORUMLARI (Faz 3)                      │
│  scrapers/store_reviews.py → Play Store 1-2 ⭐ yorumlar   │
│  LLM kümeleme → kullanıcı acıları                         │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│             AGENT (LangGraph — 8 Node)                    │
│  agent/idea_agent.py                                      │
│  LLM: Groq llama-3.3-70b-versatile                        │
│  Monitoring: LangSmith                                    │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  UI (Streamlit)                            │
│  app.py — Keşfet modu + Kategorili arama + Dashboard      │
└─────────────────────────────────────────────────────────┘
```

### 8-Node Agent Akışı

```
fetch_trending_models → match_to_market → scrape_competitor_reviews → cluster_complaints
    → find_store_app → scrape_store_reviews → cluster_store_problems → generate_opportunity
```

---

## ⚡ Hızlı Başlangıç

```bash
# 1. Repo'yu klonla
git clone https://github.com/tarikmenguc/Startup_Idea_Finder.git
cd Startup_Idea_Finder

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Bağımlılıkları kur
pip install -r requirements.txt

# 4. API key'leri ayarla
copy .env.example .env
# .env dosyasını aç ve key'leri doldur

# 5. Veri çek + ChromaDB yükle (tek komut)
python run_all.py

# 6. UI başlat
streamlit run app.py
```

### Gerekli API Key'ler

| Key | Nereden? | Ücretsiz? |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | ✅ Evet |
| `PRODUCTHUNT_API_KEY` | [producthunt.com/v2/oauth](https://www.producthunt.com/v2/oauth/applications) | ✅ Evet |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | ✅ 1.000 istek/ay |
| `LANGSMITH_API_KEY` | [smith.langchain.com](https://smith.langchain.com) | ✅ Opsiyonel |

---

## 📁 Proje Yapısı

```
Startup_Idea_Finder/
├── agent/
│   └── idea_agent.py         # LangGraph 8-node agent
├── scrapers/
│   ├── huggingface.py        # HuggingFace Hub SDK
│   ├── replicate.py          # Replicate API + HTML scraping
│   ├── fal.py                # fal.ai HTML parse
│   ├── trustmrr.py           # TrustMRR BeautifulSoup
│   ├── producthunt.py        # ProductHunt GraphQL
│   ├── competitor_research.py # Tavily web araması
│   └── store_reviews.py      # Play Store yorumları
├── ingestion/
│   └── ingest.py             # JSON → ChromaDB pipeline
├── app.py                    # Streamlit UI
├── run_all.py                # Tam pipeline runner
├── scheduler.py              # Günlük otomatik güncelleme
├── deep_report.py            # Teknik dokümantasyon
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠️ Teknoloji Stack

| Kategori | Araç |
|---|---|
| **Model Scraping** | HuggingFace Hub SDK, Replicate API, fal.ai |
| **Pazar Verisi** | TrustMRR (BeautifulSoup), ProductHunt (GraphQL) |
| **Rakip Analizi** | Tavily API (G2, Reddit, Capterra) |
| **Store Reviews** | google-play-scraper |
| **Vektör DB** | ChromaDB (2 koleksiyon) |
| **Embedding** | paraphrase-multilingual-MiniLM-L12-v2 (yerel) |
| **LLM** | Groq — llama-3.3-70b-versatile |
| **Agent** | LangGraph StateGraph |
| **UI** | Streamlit |
| **Monitoring** | LangSmith |

---

## 📊 Faz Planı

| Faz | Kapsam | Durum |
|---|---|---|
| **Faz 1** | 5 Scraper + ChromaDB + LangGraph Agent + Streamlit UI | ✅ Tamamlandı |
| **Faz 2** | Tavily rakip araması + LLM şikayet kümeleme | ✅ Tamamlandı |
| **Faz 3** | Play Store yorum çekme + LLM kullanıcı acısı analizi | ✅ Tamamlandı |

---

## 🧠 Agentic RAG Öğrenme Projesi

Bu proje Agentic RAG kavramlarını pratikte uygulamak için tasarlanmıştır:

| Kavram | Bu Projede |
|---|---|
| **Retrieval** | 2 ChromaDB koleksiyonundan cross-retrieval |
| **Agentic** | LangGraph StateGraph ile 8 adımlı karar mekanizması |
| **Tool Use** | Scraper, Tavily, Play Store → agent araçları |
| **Multi-step** | Bul → Analiz et → Kümeleme → Raporla |
| **Structured Output** | LLM, Markdown formatında yapılandırılmış rapor üretir |

**Klasik RAG:** Soru → 1 koleksiyon ara → LLM cevap ver  
**Agentic RAG (Bu Proje):** Model bul → Pazar ara → Rakip analiz → Store yorumları → Kümeleme → Rapor

---

Detaylı teknik plan: [PROJECT_PLAN.md](./PROJECT_PLAN.md)  
Adım adım inşa rehberi: [HOW_TO_BUILD.md](./HOW_TO_BUILD.md)  
Teknik dokümantasyon: [deep_report.py](./deep_report.py)
