# STARTUP IDEA FINDER
**Proje Mimari ve Teknik Raporu**
Versiyon: B2B SaaS Build  |  Mayıs 2026

**6** Scan Modu | **3** LangGraph Agent | **5** Veri Kaynağı | **60+** Python Dosyası

---

## 1. Proje Nedir?

Startup Idea Finder, yapay zeka tabanlı bir pazar araştırma ve girişim fikri keşif platformudur. Kullanıcının seçtiği AI kategorisindeki (video generation, code generation vb.) trend modelleri, mevcut rakip uygulamaları ve kullanıcı şikayetlerini analiz ederek henüz karşılanmamış pazar boşluklarını tespit eder ve kanıtlanmış veriye dayalı Micro-SaaS fırsatları önerir.

### 1.1 Temel Hedef
Girişimcilerin aylarca sürebilecek manuel pazar araştırmasını dakikalar içinde tamamlamak. Sistem, 'Friction Economy' felsefesiyle yalnızca B2B/profesyonel segmente yönelik, somut bir acı noktasını çözen ve bir tıklamayla çalışan AI otomasyon fırsatlarını öne çıkarır.

### 1.2 Kullanıcı Arayüzleri
| Arayüz | Teknoloji | Amacı |
|---|---|---|
| **Web** | Next.js | Son kullanıcı B2B arayüzü — Clerk (Auth) ve Stripe (Ödeme) entegreli. |
| **Backend API** | FastAPI + Uvicorn | Üretim REST API — Tüm scan endpoint'leri, webhook'lar, yetkilendirme ve SSE streaming. |
| **CLI Test** | Python Script | Geliştiriciler için yerel API test aracı (`scripts/cli_test.py`). Streamlit by-pass sorunu giderilerek eklendi. |

*(Not: Eski sürümlerde yer alan `app.py` Streamlit arayüzü, API güvenlik katmanlarını (auth/rate limit) baypas ettiği ve sunucu (VPS) mimarisiyle uyuşmadığı için projeden tamamen kaldırılmıştır.)*

## 2. Nasıl Çalışır?

### 2.1 Veri Toplama Pipeline'ı (Offline)
Sistem çalışmadan önce bir kez çalıştırılan veri toplama katmanı, dış kaynaklardan ham veriyi çeker ve ChromaDB vektör veritabanına yükler. 
**Güncelleme:** Bu işlem artık `lib/pipeline_config.py` isimli merkezi bir konfigürasyondan yönetilir. `run_all.py` ve `scheduler.py` bu ortak listeyi okuyarak tutarsızlıkları (drift) önler.

| Scraper | Kaynak | Çıktı |
|---|---|---|
| `scrapers/huggingface.py` | HuggingFace Hub SDK | AI modelleri → data/models_raw.json |
| `scrapers/replicate.py` | Replicate.com (public) | AI modelleri → models_raw.json'a eklenir |
| `scrapers/fal.py` | fal.ai (public) | AI modelleri → models_raw.json'a eklenir |
| `scrapers/api_pricing.py` | API Sağlayıcıları | AI model birim maliyetleri |
| `scrapers/producthunt.py` | ProductHunt GraphQL API | SaaS uygulamaları → data/apps_raw.json |
| `scrapers/trustmrr.py` | TrustMRR (Playwright) | MRR/gelir verileri → apps_raw.json'a eklenir |
| `scrapers/store_reviews.py` | Play Store / App Store | Negatif yorumlar → competitor_reviews |
| `ingestion/ingest.py` | ChromaDB | JSON → Embedding → 3 koleksiyon |

ChromaDB'de oluşturulan üç koleksiyon:
* `ai_models` — HuggingFace, Replicate, fal.ai'den AI modelleri
* `startup_apps` — ProductHunt ve TrustMRR'dan SaaS uygulamaları
* `competitor_reviews` — Play Store ve App Store negatif yorumları

### 2.2 Retrieval Katmanı (lib/retrieval.py)
Agent'lar veri çekerken doğrudan Tavily'ye gitmez; önce ChromaDB'de arama yapar. Yeterli sonuç gelmezse (varsayılan eşik: 5 belge) Tavily web aramasına fallback eder. Bu iki katmanlı yapı hem hız hem maliyet açısından verimlidir.

**Akış:** İstek → `lib/category_resolver.py` (kategori normalize) → ChromaDB similarity search → Yetersizse Tavily fallback → Belge listesi döner

### 2.3 Scan Modları (Online — Gerçek Zamanlı)
Kullanıcı bir kategori veya girişim adı girerek tarama başlatır. Tüm modlar Server-Sent Events (SSE) ile sonuçları gerçek zamanlı akıtır; her LangGraph node tamamlandığında bir JSON event gönderilir.

| Mod | Agent | Ne Yapar? |
|---|---|---|
| discover | idea_agent | Otomatik kategori seçimi ile 11 node'luk tam analiz + doğrulama raporu |
| category | idea_agent | Kullanıcının seçtiği kategoride discover ile aynı akış |
| deep | deep_agent | Derin web araştırması + investment memo + alıcı lead listesi |
| reverse | reverse_agent | Belirtilen rakip girişimi tersine mühendislikle analiz eder |
| orchestrate | orchestrator | 3 uzman agent (Research → Analyst → GTM), Supabase'e kaydeder |
| trends | — (Tavily+LLM) | Kategori için 6 aylık AI trend raporu üretir |

### 2.4 İki Aşamalı Mod (Stage-A / Stage-B)
API üzerinden erişilen özel bir akış. Aşama A pazar taramasını tamamlar ve kullanıcıya 3-5 alt-niş seçeneği sunar. Kullanıcı seçim yaptıktan sonra Aşama B derin fizibilite analizine geçer.
* Stage-A (`POST /api/scan/stage-a`): 5 node — trend analizi, rakip şikayetleri, pazar özeti
* Stage-B (`POST /api/scan/stage-b`): 10 node — pazar büyüklüğü, birim ekonomi, GTM varlıkları, rapor, doğrulama, audit

## 3. Mimari

### 3.1 Klasör Yapısı
| Dizin / Dosya | Sorumluluk |
|---|---|
| **agent/** | Tüm LangGraph agent'ları ve yardımcı modüller |
| `idea_agent.py` | Ana 11-node pipeline (tek aşamalı mod) |
| `phase_agents.py` | İki aşamalı agent graph'ları (Stage-A / Stage-B) |
| `deep_agent.py` | Derin araştırma + investment memo + buyer leads |
| `orchestrator.py` | 3 sub-agent koordinatörü (Research→Analyst→GTM) |
| **lib/** | Merkezi yardımcı kütüphaneler |
| `llm.py` | get_llm() fabrikası — Groq/Gemini dual-provider |
| `pipeline_config.py`| **[YENİ]** Scraper listesi için merkezi konfigürasyon |
| `scan_utils.py` | SSE headers + DB entegreli kredi / rate limit kontrolü |
| **routers/** | FastAPI endpoint'leri |
| `webhooks.py` | **[YENİ]** Stripe (ödeme) ve Clerk (kullanıcı) dinleyicisi |
| `scan.py` | Dispatcher (~85 satır) — mod → handler yönlendirme |
| **scrapers/** | Veri toplama scriptleri (offline pipeline) |
| **scripts/** | Scheduler, alert runner, gallery seed ve `cli_test.py` (CLI Client) |
| **api.py** | FastAPI giriş noktası |

### 3.2 idea_agent — Ana Pipeline (11 Node)
idea_agent.py içindeki tek aşamalı LangGraph pipeline'ı soldan sağa doğrusal bir akış izler:
**Node Akışı:** fetch_trending_models → match_to_market → scrape_competitor_reviews → cluster_complaints → find_store_app → scrape_store_reviews → cluster_store_problems → competition_matrix → generate_opportunity → validate_idea → auditor → END

### 3.3 deep_agent — Derin Araştırma (7 Node)
deep_agent, lib/research_steps.py'deki ortak fonksiyonları kullanarak daha odaklı bir araştırma yapar ve sonunda bir investment memo ile alıcı lead listesi üretir.
**Node Akışı:** init_research (Tavily: modeller+app'ler+SEO) → brainstorm_angles (3 Micro-SaaS hipotezi) → deep_web_research (her hipotez için rakip+şikayet araması) → competitor_deep_dive → reasoning_synthesis → write_investment_memo → find_buyer_leads → END

### 3.4 orchestrator — Multi-Agent (3 Sub-Agent)
Orchestrator, Research → Analyst → GTM sırasıyla çalışan üç uzman agent'ı koordine eder. GTM aşaması tamamlanınca sonuç Supabase'e (scans + leads tablosu) kaydedilir.

## 4. Kullanılan Teknolojiler

### 4.1 Temel Framework'ler
| Kütüphane | Kullanım Amacı |
|---|---|
| LangGraph | Agent state machine — tüm node graph'ları bu framework üzerinde |
| LangChain-Groq / Gemini | LLM entegrasyonu (Llama 3.3 70B / Gemini 2.5 Flash) |
| Tavily Python SDK | Web araması — rakip, şikayet, trend verileri için |
| ChromaDB | Vektör veritabanı — AI modelleri ve app'lerin embedding'leri |
| FastAPI + Uvicorn | REST API, Webhooks ve SSE streaming |
| Supabase | PostgreSQL veritabanı (users, scans, leads, usage_logs tabloları) |
| Stripe & Clerk | B2B SaaS üyelik, abonelik ve faturalandırma yönetimi |

### 4.2 LLM Konfigürasyonu
Tüm LLM çağrıları `lib/llm.py` üzerinden geçer. Varsayılan provider Groq (Llama 3.3 70B). Env değişkenleri: `GROQ_API_KEY`, `TAVILY_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `ALLOWED_ORIGINS`, `CLERK_PUBLIC_KEY` vb.

## 5. Uçtan Uca Veri Akışı

### 5.1 Offline Pipeline (Veri Hazırlama)
* `lib/pipeline_config.py` dosyasındaki merkezi kurallara göre `run_all.py` (manuel) veya `scheduler.py` (otomatik) çalıştırılır.
* Modeller (HuggingFace/Replicate/fal) ve Uygulamalar (ProductHunt/TrustMRR) çekilir.
* `ingestion/ingest.py` ile veriler ChromaDB'ye yüklenir.

### 5.2 Online Scan Akışı (Örnek: 'discover' modu)
* `POST /api/scan {mode: 'discover', category: 'video generation'}`
* `scan.py` → Kullanıcı kredisi veya rate limit kontrolü (`lib/scan_utils.py`) → `generate_discover_events()`
* `idea_agent.stream(initial_state)` → Her node tamamlandıkça SSE JSON eventi frontend'e fırlatılır.

### 5.3 Supabase Veri Modeli
| Tablo | İçerik |
|---|---|
| **users** | **[YENİ]** Clerk ID, Stripe Customer ID, abonelik türü (free/pro) ve kalan tarama kredileri. |
| **scans** | Her orchestrate modu taramasının tam sonucu (JSON). |
| **leads** | Taramadan çıkan alıcı adayları (URL, metin, DM şablonu). |
| **usage_logs**| Anonim IP bazlı rate limit takibi. |

## 6. Güvenlik ve Diğer Özellikler

### 6.1 Kimlik Doğrulama ve Webhooks
Uygulama tam bir B2B SaaS mantığıyla çalışır. Tüm API endpoint'leri `lib/auth_middleware.py` ile Clerk JWT'lerini doğrular. 
Ayrıca `routers/webhooks.py` aracılığıyla:
* Yeni Clerk üyesi geldiğinde veritabanına eklenir.
* Stripe ödemesi başarılı olduğunda, ilgili `user` tablosuna anında Kredi (Credit) yüklemesi yapılır.

### 6.2 Rate Limiting ve Kredi Tüketimi
`lib/scan_utils.py` içindeki `check_rate_limit()`, giriş yapmış kullanıcılar için Supabase `users` tablosundaki kredilerini kontrol eder. Derin analizlerde (Deep) 2 kredi, normal analizlerde 1 kredi düşülür. Giriş yapmamış (anonim) istekler için IP tabanlı kısıtlı bir günlük kullanım kotası uygulanır.

### 6.3 PDF Export
`GET /api/scans/{scan_id}/pdf` endpoint'i, Supabase'deki scan verisini FPDF2 ile PDF'e dönüştürür ve doğrudan HTTP response olarak döner.

### 6.4 Alert Sistemi
`scripts/run_alerts.py`, Supabase'deki son scan'leri periyodik olarak kontrol eder. Belirli eşiği aşan fırsatlar Resend üzerinden e-posta bildirimi gönderir.

## 7. Mimari Refactoring Özeti

Aşağıdaki tablo projenin ilk haline kıyasla VPS + B2B SaaS geçişi için yapılan en güncel revizyonları karşılaştırmaktadır.

| Metrik | Öncesi | Sonrası |
|---|---|---|
| **UI Tüketimi** | `app.py` Streamlit (Bypass) | `api.py` üzerinden Next.js istemcisi (Güvenli) |
| **Veri Pipeline** | `run_all.py` ve `scheduler.py` uyumsuzdu | `lib/pipeline_config.py` ile ortak ve tek merkez |
| **SaaS Abonelik** | Sadece IP bazlı limit (`usage_logs`) | Clerk + Stripe webhook entegreli Kredi sistemi |
| **Test Ortamı** | Test dosyaları karmaşıktı | `scripts/cli_test.py` ile temiz lokal API terminal testi |
| **Ölü Kod** | `diagnose_trustmrr.py`, loglar, git verileri | Tüm geliştirici atıkları ve geçici dosyalar temizlendi |
