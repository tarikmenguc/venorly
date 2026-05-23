# STARTUP IDEA FINDER
**Proje Mimari ve Teknik Raporu**
Versiyon: B2B SaaS Build  |  Mayıs 2026

**6** Scan Modu | **5** LangGraph Agent | **12** Scraper | **60+** Python Dosyası | **9** Supabase Tablosu

---

## 1. Proje Nedir?

Startup Idea Finder, yapay zeka tabanlı bir pazar araştırma ve girişim fikri keşif platformudur. Kullanıcının seçtiği AI kategorisindeki (video generation, code generation vb.) trend modelleri, mevcut rakip uygulamaları ve kullanıcı şikayetlerini analiz ederek henüz karşılanmamış pazar boşluklarını tespit eder ve kanıtlanmış veriye dayalı Micro-SaaS fırsatları önerir.

### 1.1 Temel Hedef
Girişimcilerin aylarca sürebilecek manuel pazar araştırmasını dakikalar içinde tamamlamak. Sistem, 'Friction Economy' felsefesiyle yalnızca B2B/profesyonel segmente yönelik, somut bir acı noktasını çözen ve bir tıklamayla çalışan AI otomasyon fırsatlarını öne çıkarır.

### 1.2 Kullanıcı Arayüzleri
| Arayüz | Teknoloji | Amacı |
|---|---|---|
| **Web (Frontend)** | Next.js 15+ (Vercel) | Son kullanıcı B2B arayüzü — Clerk (Auth) ve Stripe (Ödeme) entegreli. Tailwind CSS + shadcn/ui + Framer Motion ile modern tasarım. |
| **Backend API** | FastAPI + Uvicorn | Üretim REST API — Tüm scan endpoint'leri, webhook'lar, SSE streaming ve yetkilendirme. |
| **Chrome Uzantısı** | Manifest V3 | Tarayıcı uzantısı — Kullanıcıların web'de gezinirken doğrudan platforma veri göndermesini sağlar. |
| **CLI Test** | Python Script | Geliştiriciler için yerel API test aracı (`scripts/cli_test.py`). |

*(Not: Eski sürümlerde yer alan `app.py` Streamlit arayüzü, API güvenlik katmanlarını (auth/rate limit) baypas ettiği ve sunucu (VPS) mimarisiyle uyuşmadığı için projeden tamamen kaldırılmıştır.)*

---

## 2. Nasıl Çalışır?

### 2.1 Veri Toplama Pipeline'ı (Offline)
Sistem çalışmadan önce bir kez çalıştırılan veri toplama katmanı, dış kaynaklardan ham veriyi çeker ve ChromaDB vektör veritabanına yükler.
Bu işlem `lib/pipeline_config.py` isimli merkezi bir konfigürasyondan yönetilir. `run_all.py` (manuel) ve `scheduler.py` (otomatik, APScheduler) bu ortak listeyi okuyarak tutarsızlıkları (drift) önler.

| Scraper | Kaynak | Çıktı |
|---|---|---|
| `scrapers/huggingface.py` | HuggingFace Hub SDK | AI modelleri → `data/models_raw.json` |
| `scrapers/replicate.py` | Replicate.com (public) | AI modelleri → `models_raw.json`'a eklenir |
| `scrapers/fal.py` | fal.ai (public) | AI modelleri → `models_raw.json`'a eklenir |
| `scrapers/api_pricing.py` | API Sağlayıcıları (Tavily) | AI model birim maliyetleri (OpenAI, Anthropic, Replicate, HeyGen, ElevenLabs, fal.ai) → `data/api_pricing.json` + Supabase `api_pricing` tablosu |
| `scrapers/producthunt.py` | ProductHunt GraphQL API | SaaS uygulamaları → `data/apps_raw.json` |
| `scrapers/trustmrr.py` | TrustMRR (Playwright stealth) | MRR/gelir verileri (Cloudflare bypass, infinite scroll) → `apps_raw.json`'a eklenir |
| `scrapers/store_reviews.py` | Play Store / App Store | 1-2 yıldız negatif yorumlar (thumbsUp sıralı) |
| `scrapers/google_trends.py` | Google Trends (PyTrends) | V8: pytrends (birincil) → Tavily+LLM (fallback), 24 saat dosya önbelleği |
| `scrapers/reality_intel.py` | Upwork / HN / Reddit / GitHub | Gerçek dünya talep sinyalleri (freelance arbitraj, Ask HN acıları, Reddit profesyonel forumları, GitHub GUI talepleri) |
| `scrapers/competitor_research.py` | Tavily Web Araması | V4: İngilizce Tavily sorguları, domain dedup, retry mantığı ile rakip bulma + şikayet toplama |
| `scrapers/automation_intel.py` | n8n Forum/GitHub + Reddit | Otomasyon istihbaratı: n8n forum arama, Reddit otomasyon subreddit'leri, n8n GitHub özellik istekleri, iş akışı repo'ları |
| `scrapers/producthunt_gaps.py` | ProductHunt (Tavily) | Boşluk analizi: "missing feature", "wish it had", "deal breaker" kalıplarıyla eksik özellik tespiti |
| `ingestion/ingest.py` | ChromaDB + Gemini Embeddings | JSON → Embedding → 3 koleksiyon |

ChromaDB'de oluşturulan üç koleksiyon:
* `ai_models` — HuggingFace, Replicate, fal.ai'den AI modelleri
* `startup_apps` — ProductHunt ve TrustMRR'dan SaaS uygulamaları
* `competitor_reviews` — Play Store ve App Store negatif yorumları

### 2.2 Retrieval Katmanı (lib/retrieval.py)
Agent'lar veri çekerken doğrudan Tavily'ye gitmez; önce ChromaDB'de arama yapar. Yeterli sonuç gelmezse (varsayılan eşik: 5 belge) Tavily web aramasına fallback eder. Bu iki katmanlı yapı hem hız hem maliyet açısından verimlidir.

**Akış:** İstek → `lib/category_resolver.py` (kategori normalize) → ChromaDB similarity search → Yetersizse Tavily fallback → Belge listesi döner

### 2.3 Scan Modları (Online — Gerçek Zamanlı)
Kullanıcı bir kategori veya girişim adı girerek tarama başlatır. Tüm modlar Server-Sent Events (SSE) ile sonuçları gerçek zamanlı akıtır; her LangGraph node tamamlandığında bir JSON event gönderilir.

| Mod | Agent | Ne Yapar? | Router Dosyası |
|---|---|---|---|
| discover | idea_agent | Otomatik kategori seçimi ile 11 node'luk tam analiz + doğrulama raporu | `routers/scan_discover.py` |
| category | idea_agent | Kullanıcının seçtiği kategoride discover ile aynı akış | `routers/scan_discover.py` |
| deep | deep_agent | Derin web araştırması + investment memo + alıcı lead listesi | `routers/scan_deep.py` |
| reverse | reverse_agent | Belirtilen rakip girişimi tersine mühendislikle analiz eder | `routers/scan_reverse.py` |
| orchestrate | orchestrator | 3 uzman agent (Research → Analyst → GTM), Supabase'e kaydeder | `routers/scan_orchestrate.py` |
| trends | — (Tavily+LLM) | Kategori için 6 aylık AI trend raporu üretir | `routers/scan_trends.py` |

### 2.4 İki Aşamalı Mod (Stage-A / Stage-B)
API üzerinden erişilen özel bir akış. Aşama A pazar taramasını tamamlar ve kullanıcıya 3-5 alt-niş seçeneği sunar. Kullanıcı seçim yaptıktan sonra Aşama B derin fizibilite analizine geçer.
* Stage-A (`POST /api/scan/stage-a`): 5 node — trend analizi, rakip şikayetleri, pazar özeti
* Stage-B (`POST /api/scan/stage-b`): 10 node — pazar büyüklüğü, birim ekonomi, GTM varlıkları, rapor, doğrulama, audit

---

## 3. Mimari

### 3.1 Klasör Yapısı

```
Startup_Idea_Finder/
├── agent/                    # Tüm LangGraph agent'ları ve yardımcı modüller
│   ├── idea_agent.py         # Ana 11-node pipeline (tek aşamalı mod)
│   ├── phase_agents.py       # İki aşamalı agent graph'ları (Stage-A / Stage-B)
│   ├── deep_agent.py         # Derin araştırma + investment memo + buyer leads (7 node)
│   ├── orchestrator.py       # 3 sub-agent koordinatörü (Research→Analyst→GTM)
│   ├── reverse_agent.py      # Rakip tersine mühendislik (4 node)
│   ├── auditor.py            # Rapor doğrulama + Hibrit Güven Endeksi
│   ├── validator.py          # Fikir puanlama (0-50 scorecard) + TAM/SAM/SOM
│   ├── buyer_matcher.py      # Lead listesi + kişiselleştirilmiş DM şablonları
│   ├── competition_matrix.py # LLM ile yapılandırılmış rakip karşılaştırma tablosu
│   └── trend_detector.py     # Tavily+LLM ile trend ve yükselen model tespiti
│
├── lib/                      # Merkezi yardımcı kütüphaneler
│   ├── llm.py                # get_llm() fabrikası — Groq/Gemini dual-provider
│   ├── tavily_client.py      # lru_cache singleton Tavily istemcisi
│   ├── supabase_client.py    # Singleton Supabase istemcisi (env'den otomatik init)
│   ├── retrieval.py          # ChromaDB-first arama (Tavily fallback)
│   ├── category_resolver.py  # 4 aşamalı kategori çözümleme: exact match → partial match → LLM sınıflandırma (Groq) → `generic_tech_saas` fallback. Bilinmeyen kategorileri loglar.
│   ├── source_routing.py     # 3 katmanlı kaynak yönlendirme: (A) Kategori×İhtiyaç→Öncelik kaynakları, (B) Node×İzinli kaynak beyaz listesi, (C) Kaynak güven ağırlıkları (0.20–0.95). 10 kategori profili + genel fallback.
│   ├── research_steps.py     # Ortak araştırma adımları (6 fonksiyon, deep+orchestrator paylaşır)
│   ├── scan_utils.py         # SSE headers + DB entegreli kredi / rate limit kontrolü
│   ├── auth_middleware.py    # Clerk/Supabase JWT doğrulama + Extension API key desteği
│   ├── pipeline_config.py    # Scraper listesi için merkezi konfigürasyon (günlük/haftalık frekans)
│   ├── schemas.py            # Pydantic modelleri (FeasibilityReport) + report_to_markdown()
│   ├── email_service.py      # Resend API ile HTML alert e-posta gönderimi
│   ├── pdf_generator.py      # fpdf2 ile markalı A4 PDF rapor üretimi
│   └── logger.py             # Merkezi logging konfigürasyonu (LOG_LEVEL env desteği)
│
├── routers/                  # FastAPI endpoint'leri
│   ├── scan.py               # Dispatcher (~85 satır) — mod → handler yönlendirme
│   ├── scan_discover.py      # Discover + Stage-A/B endpoint'leri
│   ├── scan_deep.py          # Derin analiz endpoint'i
│   ├── scan_orchestrate.py   # Orkestratör endpoint'i (Supabase kayıt dahil)
│   ├── scan_reverse.py       # Tersine mühendislik endpoint'i
│   ├── scan_trends.py        # Trend raporu endpoint'i
│   ├── chat.py               # AI Fikir Danışmanı serbest sohbet
│   ├── gallery.py            # Galeri listeleme + PDF export
│   ├── extension.py          # Chrome uzantısı API endpoint'leri
│   └── webhooks.py           # Stripe (ödeme) ve Clerk (kullanıcı) webhook dinleyicisi
│
├── scrapers/                 # Veri toplama scriptleri (offline pipeline)
│   ├── huggingface.py        # HuggingFace Hub SDK'dan trending model çekme
│   ├── replicate.py          # Replicate.com'dan model çekme (API + HTML fallback)
│   ├── fal.py                # fal.ai'den model çekme (HTML parse, API key gerekmez)
│   ├── producthunt.py        # ProductHunt GraphQL API'den top-voted app çekme
│   ├── trustmrr.py           # TrustMRR'dan MRR/gelir verisi (Playwright stealth, Cloudflare bypass)
│   ├── store_reviews.py      # Play Store / App Store 1-2 yıldız yorum çekme (thumbsUp sıralı)
│   ├── api_pricing.py        # AI sağlayıcı fiyat tarama (OpenAI, Anthropic, Replicate vb.)
│   ├── google_trends.py      # V8 SEO: pytrends (birincil) → Tavily+LLM (fallback), 24 saat önbellek
│   ├── reality_intel.py      # Upwork RSS + Hacker News + Reddit + GitHub talep sinyalleri
│   ├── competitor_research.py# V4 Tavily ile rakip bulma + şikayet toplama (domain dedup, retry)
│   ├── automation_intel.py   # n8n forum/GitHub + Reddit otomasyon sinyalleri (acı noktaları)
│   └── producthunt_gaps.py   # ProductHunt boşluk analizi ("missing feature", "wish it had" arama)
│
├── scripts/                  # Yardımcı scriptler
│   ├── run_alerts.py         # Niş alarm e-posta gönderici (Resend)
│   ├── seed_gallery.py       # Galeriyi demo verisiyle doldurma
│   └── cli_test.py           # Geliştiriciler için lokal API test istemcisi
│
├── ingestion/                # ChromaDB veri yükleme pipeline'ı
│   └── ingest.py             # JSON → Embedding → 3 koleksiyon
│
├── data/                     # Scraper çıktı verileri
│   ├── models_raw.json       # AI modelleri (HuggingFace/Replicate/fal) ~77KB
│   ├── apps_raw.json         # SaaS uygulamaları (ProductHunt/TrustMRR) ~75KB
│   ├── api_pricing.json      # AI sağlayıcı fiyatları
│   ├── history/              # Haftalık JSON snapshot'ları (trend tespiti için)
│   ├── seo_cache/            # Google Trends önbelleği (24 saat TTL)
│   └── chroma/               # ChromaDB vektör veritabanı dosyaları
│
├── web/                      # Next.js 15+ Frontend (Vercel'de barındırılır)
│   ├── src/app/              # Next.js App Router sayfaları:
│   │   ├── page.tsx          #   Landing page (15KB)
│   │   ├── scan/             #   Tarama arayüzü
│   │   ├── dashboard/        #   Kullanıcı paneli
│   │   ├── gallery/          #   Keşif galerisi
│   │   ├── leads/            #   Lead yönetimi
│   │   ├── alerts/           #   Alarm yönetimi
│   │   ├── pricing/          #   Fiyatlandırma sayfası
│   │   ├── profile/          #   Profil sayfası
│   │   ├── waitlist/         #   Bekleme listesi
│   │   ├── features/         #   Özellikler sayfası
│   │   └── sign-in/sign-up/  #   Clerk auth sayfaları
│   ├── src/components/       # UI bileşenleri:
│   │   ├── ui/               #   shadcn: button, badge, input, chat-panel, navbar vb.
│   │   ├── glsl-hills.tsx    #   WebGL shader animasyonu (9.4KB)
│   │   └── ErrorBoundary.tsx #   Hata yakalama bileşeni
│   ├── src/lib/              # Frontend kütüphaneleri:
│   │   ├── api.ts            #   Backend API istemcisi
│   │   ├── supabase.ts       #   Supabase istemcisi
│   │   ├── scan-db.ts        #   Tarama DB işlemleri
│   │   ├── lead-db.ts        #   Lead DB işlemleri
│   │   ├── alert-db.ts       #   Alarm DB işlemleri
│   │   └── waitlist-db.ts    #   Waitlist DB işlemleri
│   ├── src/context/
│   │   └── AuthContext.tsx   #   Auth context provider
│   ├── vercel.json           # API yönlendirme konfigürasyonu
│   ├── package.json          # Next.js 16+, React 19, Clerk, Stripe, Three.js, Framer Motion, Tailwind 4
│   └── ...
│
├── chrome-extension/         # Chrome Tarayıcı Uzantısı (Manifest V3)
│   ├── manifest.json         # Uzantı tanımı
│   ├── popup.html/js         # Popup arayüzü
│   ├── content.js            # Sayfa içi script
│   ├── background.js         # Service worker
│   └── icons/                # Uzantı ikonları
│
├── api.py                    # FastAPI giriş noktası (tüm router'ları mount eder)
├── run_all.py                # Manuel pipeline çalıştırıcı
├── scheduler.py              # Otomatik günlük pipeline (APScheduler)
├── Dockerfile                # Python 3.11-slim image, uvicorn ile port 8000'de çalışır
├── docker-compose.yml        # 2 servis: api (FastAPI + healthcheck) + scheduler (pipeline + alerts)
├── requirements.txt          # 23 bağımlılık (langchain, langgraph, fastapi, supabase, fpdf2 vb.)
├── supabase_schema.sql       # 8 tablo (tümünde RLS aktif)
├── usage_logs_schema.sql     # usage_logs tablosu (RLS aktif)
└── .env.example              # Ortam değişkeni şablonu
```

### 3.2 idea_agent — Ana Pipeline (11 Node)
`idea_agent.py` içindeki tek aşamalı LangGraph pipeline'ı soldan sağa doğrusal bir akış izler:

**Node Akışı:**
```
fetch_trending_models → match_to_market → scrape_competitor_reviews → cluster_complaints
→ find_store_app → scrape_store_reviews → cluster_store_problems → competition_matrix
→ generate_opportunity → validate_idea → auditor → END
```

| Node | Görev |
|---|---|
| `fetch_trending_models` | ChromaDB'den AI modelleri çeker; yetersizse Tavily fallback |
| `match_to_market` | Kategorideki mevcut SaaS uygulamalarını bulur + SEO/Google Trends verisi çeker |
| `scrape_competitor_reviews` | G2, Reddit üzerinden rakip şikayetlerini toplar |
| `cluster_complaints` | Şikayetleri LLM ile kümeleyerek ana acı noktalarını çıkarır |
| `find_store_app` | Play/App Store'da ilgili uygulamayı bulur (LLM ile paket ID tahmini) |
| `scrape_store_reviews` | 1-2 yıldız yorumları çeker (fallback: Tavily web yorumları) |
| `cluster_store_problems` | Store şikayetlerini kümeleyerek sorun haritası çıkarır |
| `competition_matrix` | Rakip matrisi — fiyat, özellik, boşluk analizi |
| `generate_opportunity` | **Multi-shot rapor:** 3 fikir üret → en iyisini seç → detaylı JSON (Pydantic `FeasibilityReport` ile doğrulanır) |
| `validate_idea` | Fikri 0-50 scorecard ile puanlar (market, pain, competition, tech, monetization) |
| `auditor` | Sayısal iddiaları Tavily ile çapraz doğrular → Güven Endeksi (yeşil/sarı/kırmızı banner) |

### 3.3 deep_agent — Derin Araştırma (7 Node)
`deep_agent`, `lib/research_steps.py`'deki ortak fonksiyonları kullanarak daha odaklı bir araştırma yapar ve sonunda bir investment memo ile alıcı lead listesi üretir.

**Node Akışı:**
```
init_research → brainstorm_angles → deep_web_research → competitor_deep_dive
→ reasoning_synthesis → write_investment_memo → find_buyer_leads → END
```

### 3.4 orchestrator — Multi-Agent (3 Sub-Agent)
Orchestrator, Research → Analyst → GTM sırasıyla çalışan üç uzman agent'ı koordine eder. GTM aşaması tamamlanınca sonuç Supabase'e (scans + leads tablosu) kaydedilir.

| Agent | Görev |
|---|---|
| **Research Agent** | Tavily web araması + otomasyon sinyalleri + product hunt boşlukları → araştırma özeti |
| **Analyst Agent** | Brainstorm → web araştırması → rakip analizi → en iyi fikir seçimi → investment memo |
| **GTM Agent** | Upwork/Reddit/GitHub'dan alıcı lead'leri + kişiselleştirilmiş DM şablonları + waitlist verisi |

### 3.5 reverse_agent — Rakip Tersine Mühendislik (4 Node)
**Node Akışı:**
```
analyze_startup → find_competitors → scrape_all_complaints → generate_reverse_report → END
```

### 3.6 phase_agents — İki Aşamalı Pipeline (Stage-A + Stage-B)
`idea_agent.py`'den paylaşılan node'ları import ederek iki ayrı LangGraph graph oluşturur:
* **Stage-A (5 node):** `fetch_trending_models → match_to_market → scrape_competitor_reviews → cluster_complaints → generate_market_overview → END`
* **Stage-B (10 node):** `compute_market_sizing → find_store_app → scrape_store_reviews → cluster_store_problems → compute_unit_economics → generate_gtm_assets → competition_matrix → generate_opportunity → validate_idea → auditor → END`

### 3.7 Yardımcı Agent Modülleri
| Modül | Görev |
|---|---|
| `agent/auditor.py` | Rapordaki sayısal iddiaları Tavily ile kaynak eşleştirmesiyle doğrular. Hibrit skor: 0.4×Kaynak Kalitesi + 0.6×Çapraz Doğrulama. 3-bant banner: yeşil/sarı/kırmızı. Sonuçları Supabase `audit_trail` tablosuna kaydeder. |
| `agent/validator.py` | 5 boyutlu scorecard (market size, pain severity, competition, tech feasibility, monetization). Her boyut max 10 puan. Ayrıca `estimate_market_size()` fonksiyonu ile Tavily kaynaklı bottom-up TAM/SAM/SOM hesaplaması. |
| `agent/buyer_matcher.py` | Upwork RSS, Reddit, GitHub'dan potansiyel alıcı bulur. Her lead için kişiselleştirilmiş DM şablonu yazar. İki arayüz: `BuyerMatcherAgent` sınıfı ve `generate_buyer_messages()` fonksiyonu. |
| `agent/competition_matrix.py` | Yapılandırılmış rakip verisini tablo formatına dönüştürür, boşluk ve eksiklikleri tespit eder. |
| `agent/trend_detector.py` | Tavily + LLM ile kategori bazlı trend ve yükselen model tespiti. |

---

## 4. Kullanılan Teknolojiler

### 4.1 Temel Framework'ler
| Kütüphane | Kullanım Amacı |
|---|---|
| **LangGraph** | Agent state machine — tüm node graph'ları bu framework üzerinde |
| **LangChain-Groq** | Groq üzerinden Llama 3.3 70B LLM entegrasyonu |
| **LangChain-Google-GenAI** | Gemini 2.5 Flash — alternatif LLM provider (opsiyonel) |
| **Tavily Python SDK** | Web araması — rakip, şikayet, trend verileri için |
| **ChromaDB** | Vektör veritabanı — AI modelleri ve app'lerin embedding'leri |
| **FastAPI + Uvicorn** | REST API, Webhooks ve SSE streaming |
| **Next.js 15+** | Frontend framework (Vercel'de barındırılır) |
| **Supabase** | PostgreSQL veritabanı (9 tablo, tümü RLS korumalı) |
| **Stripe** | B2B SaaS ödeme ve abonelik yönetimi |
| **Clerk** | Kullanıcı kimlik doğrulama ve oturum yönetimi |

### 4.2 Yardımcı Kütüphaneler
| Kütüphane | Kullanım |
|---|---|
| PyTrends | Google Trends arama hacmi ve trend yönü verisi |
| Playwright (stealth) | TrustMRR scraping — Cloudflare bypass + infinite scroll |
| google-play-scraper / app-store-scraper | Mobil app mağaza yorumları |
| feedparser | Upwork RSS — buyer lead tespiti |
| FPDF2 + markdown | PDF rapor üretimi |
| PyJWT + cryptography | JWT tabanlı kullanıcı kimlik doğrulama |
| Resend | E-posta bildirimleri (alert sistemi) |
| APScheduler | Zamanlanmış görevler (günlük pipeline) |
| Framer Motion | Frontend animasyonları |
| Recharts | Frontend grafik ve chart bileşenleri |
| shadcn/ui | Frontend UI bileşen kütüphanesi |
| python-dotenv | Ortam değişkeni yönetimi |

### 4.3 LLM Konfigürasyonu
Tüm LLM çağrıları `lib/llm.py` üzerinden geçer. `get_llm(provider, temp)` fonksiyonu iki provider'ı destekler:

| Provider | Model | Koşul |
|---|---|---|
| **Groq** (varsayılan) | Llama 3.3 70B Versatile | `GROQ_API_KEY` tanımlı olduğunda |
| **Google Gemini** (opsiyonel) | Gemini 2.5 Flash | `GOOGLE_API_KEY` tanımlı olduğunda |

Model adı `GROQ_MODEL` env değişkeni ile değiştirilebilir (örn: `llama-3.1-8b-instant`).

### 4.4 Pydantic Rapor Şeması (lib/schemas.py)
`generate_opportunity_node` tarafından üretilen JSON raporu, `FeasibilityReport` Pydantic modeli ile doğrulanır. Bu model şu alt bölümleri içerir:
* `ExecutiveSummary` — Go/Hold/No-Go kararı, ağırlıklı skor, leap-of-faith varsayımları
* `MarketData` — TAM/SAM/SOM, CAGR, makro sinyaller
* `CompetitionData` — Rakip listesi (isim, URL, zayıflık, fonlama), giriş bariyerleri
* `TechnicalData` — Tech stack, CPU maliyeti, LTV/CAC, fiyatlandırma modeli
* `ValidationData` — ICP tanımı, cold e-posta sekansı, LinkedIn DM, waitlist başlıkları

Doğrulanmış rapor `report_to_markdown()` ile okunabilir Markdown'a dönüştürülür.

---

## 5. Uçtan Uca Veri Akışı

### 5.1 Offline Pipeline (Veri Hazırlama)
1. `lib/pipeline_config.py` dosyasındaki merkezi kurallara göre `run_all.py` (manuel) veya `scheduler.py` (otomatik, günlük) çalıştırılır.
2. Modeller (HuggingFace/Replicate/fal) ve Uygulamalar (ProductHunt/TrustMRR) çekilir.
3. API fiyatları (`api_pricing.py`) scrape edilir → `data/api_pricing.json` + Supabase `api_pricing` tablosu.
4. `ingestion/ingest.py` ile veriler ChromaDB'ye embedding olarak yüklenir (3 koleksiyon).

### 5.2 Online Scan Akışı (Örnek: 'discover' modu)
```
POST /api/scan  {mode: 'discover', category: 'video generation'}
      │
      ▼
scan.py (Dispatcher) → Kullanıcı kredisi veya rate limit kontrolü (lib/scan_utils.py)
      │
      ▼
scan_discover.py → generate_discover_events()
      │
      ▼
idea_agent.stream(initial_state) → Her node tamamlandıkça SSE JSON eventi frontend'e fırlatılır
      │
      ├── Node 1-2: lib/retrieval.py → ChromaDB sorgusu → Tavily fallback → Model + App listesi
      ├── Node 3-4: competitor_research.py → Rakip şikayetleri → LLM kümeleme
      ├── Node 5-7: store_reviews.py → Play/App Store yorumları → Kümeleme
      ├── Node 8:   competition_matrix.py → Rakip tablosu
      ├── Node 9:   generate_opportunity → Multi-shot rapor (3 fikir → seç → JSON → Pydantic doğrulama → Markdown)
      ├── Node 10:  validator.py → 0-50 Scorecard
      └── Node 11:  auditor.py → Güven Endeksi + Banner
      │
      ▼
SSE stream kapanır → Frontend tam raporu gösterir
```

### 5.3 Supabase Veri Modeli (9 Tablo)
Tüm tablolarda **Row-Level Security (RLS) aktiftir**.

| Tablo | İçerik |
|---|---|
| **users** | Clerk ID, Stripe Customer ID, abonelik türü (free/pro), kalan tarama kredileri. |
| **scans** | Her taramanın tam sonucu (category, mode, status, report_preview, leads_count, full_report JSON). Galeri kolonları dahil (is_gallery, gallery_title, gallery_summary, gallery_tags, gallery_score, gallery_emoji, gallery_week). |
| **leads** | Taramadan çıkan alıcı adayları (source, title, URL, description, score, status, dm_template, scan_category). |
| **waitlists** | Bekleme listesi kayıtları (title, description, target_audience, emails dizisi). |
| **chat_messages** | AI Fikir Danışmanı sohbet geçmişi (scan_id, role, content). |
| **alerts** | Niş alarm sistemi (keyword, email, channels, frequency, is_active, last_triggered_at). |
| **api_pricing** | AI sağlayıcılarının güncel fiyat snapshot'ları (provider, model, unit, price_usd). |
| **audit_trail** | Rapordaki iddiaların doğrulama sonuçları (report_id, claim_text, claim_class, source_url, verified, confidence). |
| **usage_logs** | Anonim IP bazlı rate limit takibi (ip_address, action_type). |

---

## 6. Güvenlik ve Diğer Özellikler

### 6.1 Kimlik Doğrulama ve Webhooks
Uygulama tam bir B2B SaaS mantığıyla çalışır. Tüm API endpoint'leri `lib/auth_middleware.py` ile Clerk JWT'lerini doğrular.
Ayrıca `routers/webhooks.py` aracılığıyla:
* Yeni Clerk üyesi geldiğinde `users` tablosuna otomatik eklenir.
* Stripe ödemesi başarılı olduğunda, ilgili kullanıcıya anında kredi (credit) yüklemesi yapılır.

### 6.2 Rate Limiting ve Kredi Tüketimi
`lib/scan_utils.py` içindeki `check_rate_limit()`, iki katmanlı kontrol uygular:

| Kullanıcı Türü | Kontrol Yöntemi | Detay |
|---|---|---|
| **Giriş yapmış** (Authenticated) | Supabase `users` tablosu | Derin analizlerde (deep) 2 kredi, normal analizlerde 1 kredi düşülür |
| **Anonim** (Unauthenticated) | Supabase `usage_logs` tablosu | IP bazlı günlük kota uygulanır |

### 6.3 PDF Export
`GET /api/scans/{scan_id}/pdf` endpoint'i, Supabase'deki scan verisini FPDF2 ile PDF'e dönüştürür ve doğrudan HTTP response olarak döner.

### 6.4 Alert Sistemi
`scripts/run_alerts.py`, Supabase'deki aktif alarmları (`alerts` tablosu) periyodik olarak kontrol eder. Belirli eşiği aşan fırsatlar Resend üzerinden e-posta bildirimi gönderir. Desteklenen frekanslar: günlük veya haftalık.

### 6.5 Galeri (Discover Gallery)
`scans` tablosundaki `is_gallery = true` olan kayıtlar, keşfedilmiş fırsatların kamuya açık bir vitrinini oluşturur. Her galeri öğesinde başlık, özet, etiketler, skor ve emoji bulunur. Aynı kategori + hafta kombinasyonu için duplikasyon önlenmiştir (`idx_gallery_category_week` unique index).

### 6.6 AI Fikir Danışmanı (Chat)
`routers/chat.py` üzerinden sunulan serbest sohbet endpoint'i, kullanıcıların scan sonuçları hakkında LLM ile interaktif tartışma yapmasını sağlar. Sohbet geçmişi Supabase `chat_messages` tablosunda `scan_id` bazlı saklanır.

### 6.7 Chrome Uzantısı
`chrome-extension/` dizininde yer alan Manifest V3 tarayıcı uzantısı, kullanıcıların web'de gezinirken ilgili sayfaları doğrudan platforma göndermesini sağlar. Backend tarafında `routers/extension.py` ile karşılanan özel API endpoint'leri mevcuttur.

### 6.8 Günlükleme
`lib/logger.py` merkezi logging konfigürasyonu sağlar. Tüm agent'lar ve router'lar `get_logger(__name__)` ile modül bazlı logger kullanır.

---

## 7. Dağıtım (Deployment) Mimarisi

### 7.1 Mevcut Durum
| Katman | Nerede | Detay |
|---|---|---|
| **Frontend** | Vercel | Next.js uygulaması, GitHub'a push edildiğinde otomatik deploy |
| **Backend** | Render.com *(geçiş aşamasında)* | FastAPI uygulaması, `vercel.json` ile yönlendiriliyor |
| **Veritabanı** | Supabase | PostgreSQL, 9 tablo (RLS aktif) |

### 7.2 Planlanan Geçiş: OVH VPS
Backend, OVH Cloud'dan kiralanan bir VPS sunucusuna taşınacaktır. Bu sunucuda Docker ile çalıştırılması planlanmaktadır.

| Özellik | Değer |
|---|---|
| **Sunucu** | `vps-c1758eca.vps.ovh.net` |
| **IPv4** | `57.129.6.176` |
| **Lokasyon** | Frankfurt (DE), Almanya |
| **CPU** | 4 vCore |
| **RAM** | 8 GB |
| **Depolama** | 75 GB |

**Geçiş sonrası `web/vercel.json` dosyasındaki Render.com URL'leri VPS IP'si ile değiştirilecektir.**

### 7.3 Docker Konfigürasyonu
Proje kökünde `Dockerfile` ve `docker-compose.yml` dosyaları mevcuttur. VPS'te Docker ile ayağa kaldırılabilir.

**Docker Compose Servisleri:**
| Servis | Görev | Detay |
|---|---|---|
| `api` | FastAPI backend | Port 8000, healthcheck dahil, Caddy reverse proxy ağına bağlı |
| `scheduler` | Günlük pipeline + alerts | `scheduler.py` ile günlük 03:00'te pipeline, her Pazartesi galeri seed, her gün 07:00'de alarm kontrolü |

---

## 8. Ortam Değişkenleri (.env)
| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq LLM API anahtarı |
| `TAVILY_API_KEY` | ✅ | Tavily arama API anahtarı |
| `SUPABASE_URL` | ✅ | Supabase proje URL'i |
| `SUPABASE_KEY` | ✅ | Supabase anon/service anahtarı |
| `GOOGLE_API_KEY` | ❌ | Gemini alternatif LLM (opsiyonel) |
| `GROQ_MODEL` | ❌ | Model override (varsayılan: `llama-3.3-70b-versatile`) |
| `REPLICATE_API_TOKEN` | ❌ | Replicate scraper için API token'ı (yoksa HTML fallback) |
| `CLERK_PUBLIC_KEY` | ✅ | Clerk kimlik doğrulama açık anahtarı |
| `STRIPE_SECRET_KEY` | ✅ | Stripe ödeme gizli anahtarı |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Stripe webhook imzalama anahtarı |
| `RESEND_API_KEY` | ❌ | Resend e-posta servisi anahtarı |
| `PRODUCT_HUNT_TOKEN` | ❌ | ProductHunt API token'ı (GraphQL scraper için) |
| `EXTENSION_API_KEY` | ❌ | Chrome uzantısı API doğrulama anahtarı |
| `ALLOWED_ORIGINS` | ✅ | CORS izinli origin'ler |
| `LANGSMITH_API_KEY` | ❌ | LangSmith agent izleme ve debug (opsiyonel) |
| `NEXT_PUBLIC_*` | ✅ | Frontend ortam değişkenleri (Clerk, Stripe, Supabase public key'leri) |

---

## 9. Mimari Refactoring Özeti

Aşağıdaki tablo, projenin ilk halinden mevcut B2B SaaS mimarisine kadar yapılan tüm önemli değişiklikleri özetlemektedir.

| Metrik | Öncesi | Sonrası |
|---|---|---|
| **UI Tüketimi** | `app.py` Streamlit (Bypass) | Next.js 15+ (Vercel) + Chrome Uzantısı |
| **Backend Barındırma** | Render.com (ücretsiz, uyku sorunu) | OVH VPS'e geçiş planlanıyor (4 vCore, 8GB RAM) |
| **LLM Fabrikası** | 10 farklı dosyada bağımsız init | `lib/llm.py` merkezi fabrika (Groq/Gemini dual-provider) |
| **Tavily İstemcisi** | 10 farklı dosyada bağımsız init | `lib/tavily_client.py` singleton (lru_cache) |
| **Veri Pipeline** | `run_all.py` ve `scheduler.py` uyumsuzdu | `lib/pipeline_config.py` ile ortak ve tek merkez |
| **SaaS Abonelik** | Sadece IP bazlı limit (`usage_logs`) | Clerk + Stripe webhook entegreli kredi sistemi |
| **Rapor Doğrulama** | Yapılandırılmamış metin çıktısı | Pydantic `FeasibilityReport` + `report_to_markdown()` |
| **Güvenlik (RLS)** | `usage_logs` tablosunda RLS eksikti | Tüm 9 tabloda RLS aktif |
| **deep+orchestrator Kopya Kodu** | ~%80 kopya (992 satır) | `lib/research_steps.py` ile paylaşımlı |
| **Test Ortamı** | Karmaşık test dosyaları | `scripts/cli_test.py` ile temiz lokal terminal testi |
| **Ölü Kod** | `diagnose_trustmrr.py`, loglar, git atıkları | Tüm geliştirici atıkları temizlendi |
| **Import Hataları** | `idea_agent.py`'de `random` ve `json` eksikti | Düzeltildi (Mayıs 2026) |

---

## 10. Bilinen Sorunlar ve Yapılacaklar

1. **VPS Geçişi:** `web/vercel.json` dosyasındaki Render.com URL'leri henüz OVH VPS IP'si ile güncellenmedi. Backend hâlâ Render.com'a yönlendiriliyor.
2. **Proje İsmi:** "Startup Idea Finder" ismi geçici olarak kullanılmaktadır; daha profesyonel bir marka ismi planlanmaktadır.
