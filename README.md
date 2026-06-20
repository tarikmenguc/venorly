# 🔍 Venorly: Model-First Agentic RAG System

**Venorly**, modern AI modellerini (HuggingFace, Replicate, fal.ai) ve pazar verilerini (ProductHunt, TrustMRR) kullanarak kanıtlanmış **Micro-SaaS boşluklarını (White-Space)** tespit eden otonom bir yapay zeka ajanıdır. 

Sistem, basit bir LLM wrapper'ından ziyade; **LangGraph tabanlı State Machine**, **Hybrid Retrieval (ChromaDB + Web)**, **Multi-Shot Generation** ve **Ensemble LLM Evaluation** gibi ileri seviye AI Engineering konseptlerini barındırır.

> "Hangi yeni AI modeli, kullanılmayan bir pazar boşluğunda para kazandırır?"

---

## 🧠 Core AI Architecture (Agentic RAG)

Sistem, LangGraph kullanılarak bir *StateGraph* olarak tasarlanmıştır. Kullanıcıdan gelen "video generation", "voice ai" gibi tek kelimelik ham girdiler, otonom bir araştırma zincirinden geçerek iş modeline dönüşür.

### 1. LangGraph Pipeline (Node Flow)

1. **`expand_query_node`:** Kullanıcının ham girdisini 4 farklı arama vektörüne (Market, Competitor, Pain Point, Tech) dönüştürür.
2. **`fetch_market_data_node`:** *Tavily Advanced Search* ile seçilen nişin TAM/SAM (Toplam Adreslenebilir Pazar) verilerini ve sektörel raporlarını çeker.
3. **`fetch_trending_models_node`:** *Hybrid Retrieval* mekanizmasıyla (önce ChromaDB, fallback olarak Web) seçilen alandaki yükselen açık kaynak veya API tabanlı modelleri getirir.
4. **`match_to_market_node`:** Aynı alanda halihazırda para kazanan SaaS uygulamalarını ve Google Trends (SEO) verilerini toplar.
5. **`scrape_competitor_reviews_node`:** Rakiplerin Reddit, G2 ve Trustpilot üzerindeki 1-2 yıldızlı şikayetlerini ve "acı noktalarını" çeker.
6. **`cluster_complaints_node`:** Dağınık şikayet verisini LLM ile kümeleyerek (Clustering) pazardaki ilk 5 yapısal sorunu çıkarır.
7. **`generate_opportunity_node` (Multi-Shot & Ensemble):** Final karar ve rapor üretimi.

### 2. İleri Seviye LLM Teknikleri

Teknik mülakatlar ve mimari analiz için projedeki kritik AI örüntüleri:

* **Hybrid Retrieval (`lib/retrieval.py`):** Kaynakları tararken önce yerel Vektör Veritabanına (ChromaDB) başvurur. Eğer yeterli Confidence/K-değeri sağlanamazsa, otonom olarak Tavily Web Search'e düşer (Fallback) ve sonuçları birleştirir.
* **Multi-Shot Divergence & Convergence (`generate_opportunity_node`):**
  * *Divergence (Isı=0.9):* Toplanan verilere dayanarak LLM önce 3 farklı, yaratıcı Micro-SaaS fikri üretir.
  * *Convergence (Isı=0.2):* LLM analitik bir persona ile bu 3 fikri LTV, CAC ve pazar çekiciliği açısından puanlar ve tek bir kazanan seçer.
* **Ensemble Decision Making (MoE benzeri):** Seçilen fikir için Groq (LLaMA 3.3) "Go" (Yatırım Yap) kararı verirse, sistem otomatik olarak **Google Gemini** modelini hakem olarak çağırır. İki model de "Go" derse fikir onaylanır. Çelişki varsa karar "Hold"a düşürülür (Hallucination Mitigation).
* **Structured Output Enforcement:** Tüm ajan çıktıları Pydantic şemaları ile doğrulanıp katı bir JSON yapısında (FeasibilityReport) dönmesi sağlanır.

---

## 🏗️ Sistem Mimarisi & Stack

Proje, production-ready bir Microservice mimarisiyle kurgulanmıştır.

```text
┌────────────────────────────────┐         ┌────────────────────────────────┐
│        FRONTEND (Vercel)       │         │     VERİTABANI & AUTH          │
│                                │         │                                │
│ - Next.js 16 (React 19)        │ ◄─────► │ - Supabase (PostgreSQL)        │
│ - Tailwind CSS v4 & Framer M.  │         │ - Clerk (Kimlik Doğrulama)     │
│ - Stripe (Ödeme Altyapısı)     │         │                                │
└───────────────┬────────────────┘         └────────────────┬───────────────┘
                │                                           │
                ▼                                           ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          VPS / SUNUCU (Docker)                            │
│                                                                           │
│  ┌───────────────────────────┐         ┌───────────────────────────────┐  │
│  │       BACKEND API         │         │         SCHEDULER             │  │
│  │ - FastAPI (Python)        │         │ - Data Ingestion (Cron)       │  │
│  │ - LangGraph Agent State   │         │ - Pazar / Model Scraping      │  │
│  │ - PDF/PPTX/HTML Export    │         │ - Email Alert Servisi         │  │
│  └────────────┬──────────────┘         └───────────────────────────────┘  │
│               │                                                           │
│               ▼                                                           │
│  ┌───────────────────────────┐         ┌───────────────────────────────┐  │
│  │    LLM & SEARCH LAYER     │         │        VECTOR DB LAYER        │  │
│  │ - Groq (LLaMA 3.3 70B)    │ ◄─────► │ - ChromaDB                    │  │
│  │ - Gemini (Ensemble Check) │         │ - MiniLM Embedding            │  │
│  │ - Tavily (Web Search)     │         │                               │  │
│  └───────────────────────────┘         └───────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Proje Klasör Yapısı

* `agent/idea_agent.py` : LangGraph StateGraph düğümleri, RAG pipeline ve Ensemble LLM mantığı.
* `lib/retrieval.py` : ChromaDB ve Tavily arasında Hybrid Retrieval fallback katmanı.
* `scrapers/` : HuggingFace, Play Store, TrustMRR, Reddit gibi platformlardan periyodik veri toplayan scriptler.
* `api.py` : FastAPI tabanlı sunucu. Frontend'in ajanı tetiklediği ve Rapor/PDF/Pitch-Deck çıktılarının alındığı API Gateway.
* `scheduler.py` : Veritabanını güncel tutmak için çalışan asenkron arka plan görevleri.
* `web/` : Kullanıcıların araştırmalarını görselleştirdikleri Next.js dashboard arayüzü.

---

## ⚡ Kurulum (Local Development)

Sistemi baştan uca yerel ortamınızda test etmek için:

### 1. Backend (AI Ajanı & API)
Backend, Docker ile izole olarak çalıştırılır.

```bash
git clone https://github.com/tarikmenguc/Startup_Idea_Finder.git
cd Startup_Idea_Finder

# Çevresel değişkenleri ayarlayın (Groq, Tavily, Gemini, Supabase keyleri)
cp .env.example .env

# Docker compose ile API (FastAPI) ve Scheduler'ı başlatın
docker compose up --build -d
```
API dökümantasyonu ve LangGraph uç noktaları `http://localhost:8000/docs` adresinde aktif olacaktır.

### 2. Frontend (Next.js Dashboard)
```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```
Arayüz `http://localhost:3000` adresinde ayağa kalkacaktır.

---

## 🎯 Neden Bu Mimari? (Design Decisions)

1. **Neden Sadece LLM Wrapper Değil de LangGraph?**  
   Micro-SaaS araştırması doğası gereği ardışıktır. "Rakipleri bulmadan, şikayetlerini arayamazsın. Şikayetleri kümelemeden fırsat çıkaramazsın." LangGraph'ın state machine yapısı, LLM'in halüsinasyon görmesini engeller ve her düğümde kontrol mekanizmaları (ör. Reddit sinyal onayı) kurulmasını sağlar.
2. **Neden ChromaDB + Tavily Fallback?**  
   Geleneksel RAG, statik veride harikadır ancak pazar koşulları (yeni çıkan AI modelleri) her gün değişir. Sistem bilindik modelleri ChromaDB'den (Düşük gecikme/maliyet) alırken, LLM yeni/bilinmeyen bir teknoloji gördüğünde anında Tavily ile internete açılır (High freshness).
3. **Neden Multi-Shot Generation?**  
   Tek seferde fikir üretmek, LLM'i "ilk bulduğuna atlamaya" zorlar. Sistem önce sıcaklığı (temperature) yüksek tutarak geniş yelpazede fikirler üretir, ardından sıcaklığı düşürerek analitik bir persona ile en rasyonel olanı seçer. Bu, üretim kalitesini dramatik ölçüde artırır.
