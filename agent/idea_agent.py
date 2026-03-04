"""
LangGraph Agentic RAG — Startup Idea Finder
Faz 3: trending modeller → pazar eşleştirme → rakip şikayetleri → store yorumları → fırsat raporu
"""

import os
import random
import sys
from typing import TypedDict, List, Optional

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Proje kökünü path'e ekle (competitor_research import için)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

load_dotenv()

# ──────────────────────────────────────────────
# BAĞLANTI & MODEL KURULUMU
# ──────────────────────────────────────────────

CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_embeddings  = None
_models_store = None
_apps_store   = None
_llm          = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def get_models_store():
    global _models_store
    if _models_store is None:
        _models_store = Chroma(
            collection_name="ai_models",
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_DIR,
        )
    return _models_store


def get_apps_store():
    global _apps_store
    if _apps_store is None:
        _apps_store = Chroma(
            collection_name="startup_apps",
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_DIR,
        )
    return _apps_store


def get_llm(provider="groq", temp=0.7):
    """LLM modelini döndürür. Provider: 'groq' veya 'gemini'"""
    if provider == "gemini" and os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=temp,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    # Fallback to default Groq
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=temp,
    )


# ──────────────────────────────────────────────
# STATE (Faz 3 güncellemesi)
# ──────────────────────────────────────────────

class AgentState(TypedDict):
    user_category: str               # "video generation", "image", vs.
    trending_models: List[dict]      # fetch_trending_models_node çıktısı
    matching_apps: List[dict]        # match_to_market_node çıktısı
    competitor_complaints: List[dict] # scrape_competitor_reviews_node çıktısı  [FAZ 2]
    complaint_clusters: str           # cluster_complaints_node çıktısı        [FAZ 2]
    store_app_ids: List[dict]        # find_store_app_node çıktısı              [FAZ 3]
    store_reviews: List[dict]        # scrape_store_reviews_node çıktısı        [FAZ 3]
    store_clusters: str              # cluster_store_problems_node çıktısı      [FAZ 3]
    competition_matrix: str          # competition_matrix_node çıktısı          [FAZ 9]
    final_report: str                # generate_opportunity_node çıktısı
    validation_details: str          # validate_idea_node çıktısı               [FAZ 9]
    error: Optional[str]


# ──────────────────────────────────────────────
# NODE 1: Trend Modelleri Getir
# ──────────────────────────────────────────────

def fetch_trending_models_node(state: AgentState) -> AgentState:
    """ChromaDB 'ai_models' koleksiyonundan trend modelleri çeker.
    Daha fazla sonuç çeker ve rastgele bir subset seçer → her seferinde farklı."""
    query = state["user_category"] or "trending AI model"
    print(f"[Agent] Node 1 → fetch_trending_models | query: '{query}'")

    try:
        results = get_models_store().similarity_search(query, k=25)
    except Exception as e:
        print(f"[Agent] ❌ Model arama hatası: {e}")
        return {**state, "trending_models": [], "error": str(e)}

    all_models = []
    for r in results:
        all_models.append({
            "content":   r.page_content,
            "name":      r.metadata.get("name", ""),
            "model_id":  r.metadata.get("model_id", ""),
            "category":  r.metadata.get("category", ""),
            "source":    r.metadata.get("source", ""),
            "downloads": r.metadata.get("downloads", "0"),
            "url":       r.metadata.get("url", ""),
        })

    sample_size = min(8, len(all_models))
    models = random.sample(all_models, sample_size) if all_models else []

    print(f"[Agent] ✅ {len(all_models)} model bulundu → {len(models)} rastgele seçildi.")
    return {**state, "trending_models": models, "error": None}


# ──────────────────────────────────────────────
# NODE 2: Pazarla Eşleştir
# ──────────────────────────────────────────────

def match_to_market_node(state: AgentState) -> AgentState:
    """Model kategorisiyle uyumlu para kazanan uygulamaları bulur."""
    if not state["trending_models"]:
        print("[Agent] Node 2 → match_to_market | model yok, atlanıyor.")
        return {**state, "matching_apps": []}

    categories = list({m["category"] for m in state["trending_models"] if m["category"]})
    model_names = " ".join([m["name"] for m in state["trending_models"][:3]])
    search_query = f"{state['user_category']} {' '.join(categories[:3])} {model_names}"
    print(f"[Agent] Node 2 → match_to_market | query: '{search_query[:80]}...'")

    try:
        results = get_apps_store().similarity_search(search_query, k=15)
    except Exception as e:
        print(f"[Agent] ❌ App arama hatası: {e}")
        return {**state, "matching_apps": [], "error": str(e)}

    all_apps = []
    for r in results:
        all_apps.append({
            "content":  r.page_content,
            "name":     r.metadata.get("name", ""),
            "mrr":      r.metadata.get("mrr", ""),
            "votes":    r.metadata.get("votes", "0"),
            "category": r.metadata.get("category", ""),
            "source":   r.metadata.get("source", ""),
            "url":      r.metadata.get("url", ""),
        })

    sample_size = min(6, len(all_apps))
    apps = random.sample(all_apps, sample_size) if all_apps else []

    print(f"[Agent] ✅ {len(all_apps)} app bulundu → {len(apps)} rastgele seçildi.")
    return {**state, "matching_apps": apps}


# ──────────────────────────────────────────────
# NODE 3: Rakip Şikayetlerini Çek [FAZ 2]
# ──────────────────────────────────────────────

def scrape_competitor_reviews_node(state: AgentState) -> AgentState:
    """Eşleşen uygulamaların rakip şikayetlerini Tavily ile arar."""
    print("[Agent] Node 3 → scrape_competitor_reviews")

    if not state["matching_apps"]:
        print("[Agent] ⚠️  Eşleşen app yok, şikayet araması atlanıyor.")
        return {**state, "competitor_complaints": []}

    app_names = [a["name"] for a in state["matching_apps"] if a.get("name")]

    try:
        from scrapers.competitor_research import search_competitor_complaints
        complaints = search_competitor_complaints(app_names, max_per_app=3)
    except ImportError:
        print("[Agent] ⚠️  competitor_research modülü bulunamadı.")
        complaints = []
    except Exception as e:
        print(f"[Agent] ❌ Şikayet araması hatası: {e}")
        complaints = []

    print(f"[Agent] ✅ {len(complaints)} şikayet/yorum bulundu.")
    return {**state, "competitor_complaints": complaints}


# ──────────────────────────────────────────────
# NODE 4: Şikayetleri Kümele [FAZ 2]
# ──────────────────────────────────────────────

def cluster_complaints_node(state: AgentState) -> AgentState:
    """Toplanan şikayetleri LLM ile gruplandırır."""
    print("[Agent] Node 4 → cluster_complaints")

    complaints = state.get("competitor_complaints", [])
    if not complaints:
        print("[Agent] ⚠️  Şikayet verisi yok, kümeleme atlanıyor.")
        return {**state, "complaint_clusters": ""}

    # Şikayetleri metin formatına dönüştür
    complaints_text = "\n".join([
        f"[{c['app']}] ({c['source']}): {c['content'][:300]}"
        for c in complaints[:15]  # Max 15 şikayet gönder
    ])

    clustering_prompt = f"""Aşağıda farklı SaaS uygulamaları hakkında kullanıcı yorumları ve şikayetleri var.
Bu şikayetleri analiz et ve en çok tekrarlanan 5 ana sorunu belirle.

Şikayetler:
{complaints_text}

Görevin:
1. Şikayetleri gruplandır
2. Her grup için kaç kez tekrarlandığını belirt
3. Hangi uygulama(lar)da görüldüğünü not et

Çıktı formatı (Türkçe):
1. [Sorun başlığı] — [kaç yorum] — [uygulamalar]
   Örnek yorumlar: "..."
2. ...
(Sadece listeyi yaz, başka açıklama ekleme)"""

    try:
        response = get_llm(temp=0.1).invoke([HumanMessage(content=clustering_prompt)])
        clusters = response.content
    except Exception as e:
        print(f"[Agent] ❌ Kümeleme hatası: {e}")
        clusters = f"(Kümeleme yapılamadı: {e})"

    print("[Agent] ✅ Şikayetler kümelendi.")
    return {**state, "complaint_clusters": clusters}


# ──────────────────────────────────────────────
# NODE 5: Fırsat Raporu Üret (Faz 2 güncellemesi)
# ──────────────────────────────────────────────

def generate_opportunity_node(state: AgentState) -> AgentState:
    """Multi-shot rapor: 3 fikir üret → en iyisini seç → detaylandır."""
    print("[Agent] Node 5 → generate_opportunity (multi-shot)")

    # Modeller
    if state["trending_models"]:
        models_text = "\n".join([
            f"  • {m['name']} ({m['category']}) | İndirme: {m['downloads']} | {m['url']}"
            for m in state["trending_models"][:5]
        ])
    else:
        models_text = "  (Model verisi bulunamadı)"

    # Uygulamalar
    if state["matching_apps"]:
        apps_text = "\n".join([
            f"  • {a['name']} | MRR: {a['mrr'] or '?'} | Oylar: {a['votes']} | {a['source']}"
            for a in state["matching_apps"][:5]
        ])
    else:
        apps_text = "  (Uygulama verisi bulunamadı)"

    # Rakip şikayetleri
    complaint_clusters = state.get("complaint_clusters", "")
    store_clusters = state.get("store_clusters", "")
    all_complaints = ""
    if complaint_clusters:
        all_complaints += f"\nWeb Şikayetleri (G2, Reddit):\n{complaint_clusters}\n"
    if store_clusters:
        all_complaints += f"\nKullanıcı Yorumları:\n{store_clusters}\n"

    # Perspektif
    perspectives = [
        "Sağlık sektörü (klinikler, doktorlar, eczaneler)",
        "Eğitim sektörü (öğretmenler, online kurs yapımcıları)",
        "E-ticaret (küçük mağaza sahipleri, dropshipper'lar)",
        "Hukuk sektörü (avukatlar, hukuk büroları)",
        "İçerik üreticileri (YouTuber'lar, podcast'çiler)",
        "Freelancer'lar (tasarımcılar, yazılımcılar)",
        "Restoran ve yeme-içme sektörü",
        "Fitness ve spor antrenörleri",
        "Küçük ajanslar (reklam, sosyal medya, PR)",
        "Müzisyenler ve ses prodüktörleri",
        "B2B SaaS girişimcileri",
    ]
    chosen_perspective = random.choice(perspectives)

    data_context = f"""Kategori: {state['user_category']}
Perspektif: {chosen_perspective}

Trend AI Modeller:
{models_text}

Para kazanan uygulamalar:
{apps_text}
{all_complaints}"""

    # ========================================
    # AŞAMA 1: 3 farklı fikir üret (yaratıcı)
    # ========================================
    print("[Agent]   Aşama 1/3: 3 fikir üretiliyor...")
    prompt1 = f"""Sen bir Micro-SaaS strateji uzmanısın.
Amacımız milyar dolarlık devleri kopyalamak DEĞİL, dar nişlere odaklanan aylık $1K-$50K kazanan küçük SaaS fikirleri bulmak.

{data_context}

3 FARKLI Micro-SaaS fikri üret. Her biri:
- Farklı bir niş hedef kitleye yönelik olmalı
- Farklı bir AI modeli kullanmalı
- Farklı bir iş modeline sahip olmalı
- 2-3 cümle ile özetlenmiş olmalı

Format:
1. [Fikir başlığı] | Model: [model] | Niş: [kitle] | [kısa açıklama]
2. ...
3. ...

Sadece listeyi yaz."""

    # Çoklu LLM tercihini belirle
    preferred_provider = "gemini" if os.getenv("GOOGLE_API_KEY") else "groq"

    try:
        llm_creative = get_llm(provider=preferred_provider, temp=0.9)
        ideas_response = llm_creative.invoke([HumanMessage(content=prompt1)])
        ideas_raw = ideas_response.content
        print(f"[Agent]   ✅ 3 fikir üretildi.")
    except Exception as e:
        print(f"[Agent]   ❌ Fikir üretme hatası: {e}")
        ideas_raw = "Fikir üretilemedi."

    # ========================================
    # AŞAMA 2: En iyisini seç (analitik)
    # ========================================
    print("[Agent]   Aşama 2/3: En iyi fikir seçiliyor...")
    prompt2 = f"""Aşağıda 3 Micro-SaaS fikri var. Hangisi en gerçekçi ve kârlı?

{ideas_raw}

Deerlendirme kriterleri:
- Pazar büyüklüğü ve para ödeme isteği
- Teknik fizibilite (model uygunluğu)
- Rekabet düzeyi ({"şikayet verileri var" if all_complaints else "genel değerlendirme"})

Seçimin: [numara] — Neden: [2 cümle]

Sadece seçimi ve nedenini yaz."""

    try:
        llm_analytic = get_llm(provider=preferred_provider, temp=0.2)
        selection = llm_analytic.invoke([HumanMessage(content=prompt2)])
        selected_idea = selection.content
        print(f"[Agent]   ✅ En iyi fikir seçildi.")
    except Exception as e:
        print(f"[Agent]   ❌ Seçim hatası: {e}")
        selected_idea = ideas_raw

    # ========================================
    # AŞAMA 3: Detaylı rapor (yapılandırılmış)
    # ========================================
    print("[Agent]   Aşama 3/3: Detaylı rapor üretiliyor...")
    prompt3 = f"""Seçilen fikir:
{selected_idea}

Fikirler:
{ideas_raw}

Veri kaynağı:
{data_context}

Bu fikri aşağıdaki formatta DETAYLI bir rapor olarak yaz (Türkçe, emoji kullan).
Her bölümde SOMUT VERİ kullan, jenerik cümlelerden kaçın.

🔥 NİŞ FIRSAT: [Çok spesifik kısa fikir başlığı]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Kullanılacak Model: [Model adı + neden bu model uygun]
🎯 Odaklanılacak Niş: [Spesifik hedef kitle]

💰 Pazar Mantığı:
   [Yukarıdaki uygulamalardan örneklerle kitlenin para ödeme eğilimini kanıtla]

❌ Rakip Boşlukları:
   [{"Şikayet verilerinden somut boşlukları listele" if all_complaints else "Potansiyel zayıf noktalar"}]

⏱️ Tahmini Geliştirme Süresi:
   MVP: [X hafta] | Full Ürün: [Y ay]
   [Neden bu süre, teknik adımlar neler]

🔧 Teknik Zorluk: [1-5 ⭐]
   [API kullanımı mı, fine-tuning mi, entegrasyon adımları]

🚀 İlk 100 Müşteri Stratejisi:
   [Hangi subreddit, hangi topluluk, nasıl ulaşılır]

💲 Fiyatlandırma Önerisi:
   Free: [ne içerir]
   Pro ($X/ay): [ne içerir]
   Business ($Y/ay): [ne içerir]

💡 Fırsat Özeti:
   [Tam olarak ne yapılacak, 2-3 cümle]

🔗 [Model URL]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sadece raporu yaz."""

    try:
        llm_structured = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.4,
        )
        final = llm_structured.invoke([HumanMessage(content=prompt3)])
        report = final.content
    except Exception as e:
        report = f"❌ LLM hatası: {e}\n\nFikirler:\n{ideas_raw}\n\nSeçim:\n{selected_idea}"

    print("[Agent] ✅ Rapor üretildi (3 aşamalı multi-shot).")
    return {**state, "final_report": report}


# ──────────────────────────────────────────────
# NODE 6: Store App Bul [FAZ 3]
# ──────────────────────────────────────────────

def find_store_app_node(state: AgentState) -> AgentState:
    """Eşleşen startup'ların Play Store paket adlarını LLM ile belirler."""
    print("[Agent] Node 6 → find_store_app")

    if not state.get("matching_apps"):
        return {**state, "store_app_ids": []}

    # Agent'ın bulduğu gerçek startup'ları kullan (büyük devler değil)
    app_names = [a["name"] for a in state["matching_apps"][:6] if a.get("name")]
    if not app_names:
        return {**state, "store_app_ids": []}

    prompt = f"""Below are startup/app names found in the market.
For each, determine if they have a Google Play Store listing.
If yes, return the exact package ID (e.g. com.example.app).
If unsure or the app is web-only, write "none".
Be accurate — wrong package IDs will cause errors.

Apps: {', '.join(app_names)}

Output format (one per line, NO extra text):
AppName|com.example.package

Rules:
- Only return real, verified package IDs you are confident about
- Most small startups are web-only, so "none" is expected for many
- Do NOT guess or make up package IDs"""

    store_ids = []
    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        for line in response.content.strip().split("\n"):
            line = line.strip()
            if "|" not in line:
                continue
            parts = line.split("|")
            if len(parts) == 2:
                name, pkg = parts[0].strip(), parts[1].strip()
                if pkg and pkg.lower() != "none" and "." in pkg and len(pkg) > 5:
                    store_ids.append({"name": name, "play_store_id": pkg})
    except Exception as e:
        print(f"[Agent] ⚠️  LLM ID tahmin hatası: {e}")

    if store_ids:
        print(f"[Agent] ✅ {len(store_ids)} Play Store ID bulundu: {[s['name'] for s in store_ids]}")
    else:
        print("[Agent] ℹ️  Eşleşen startup'ların hiçbirinin Play Store uygulaması yok (web-only).")

    return {**state, "store_app_ids": store_ids}


# ──────────────────────────────────────────────
# NODE 7: Store Yorumlarını Çek [FAZ 3]
# ──────────────────────────────────────────────

def scrape_store_reviews_node(state: AgentState) -> AgentState:
    """Play Store yorumları veya Tavily web yorumları çeker (fallback)."""
    print("[Agent] Node 7 → scrape_store_reviews")

    store_ids = state.get("store_app_ids", [])
    all_reviews = []

    # YOL A: Play Store yorumları (store_ids varsa)
    if store_ids:
        try:
            from scrapers.store_reviews import scrape_play_store_reviews
            for app_info in store_ids[:3]:
                pkg = app_info.get("play_store_id", "")
                if pkg:
                    reviews = scrape_play_store_reviews(pkg, max_reviews=80)
                    all_reviews.extend(reviews[:20])
        except ImportError:
            print("[Agent] ⚠️  store_reviews modülü bulunamadı.")
        except Exception as e:
            print(f"[Agent] ❌ Store yorum hatası: {e}")

    # YOL B: Fallback — Tavily ile web yorumları (store yoksa)
    if not all_reviews and state.get("matching_apps"):
        print("[Agent] ℹ️  Store yorum yok → Tavily web fallback kullanılıyor...")
        try:
            from scrapers.competitor_research import search_app_reviews
            app_names = [a["name"] for a in state["matching_apps"][:3] if a.get("name")]
            for name in app_names:
                web_reviews = search_app_reviews(name, max_results=4)
                all_reviews.extend(web_reviews)
        except Exception as e:
            print(f"[Agent] ❌ Tavily fallback hatası: {e}")

    source = "Play Store" if store_ids else "Tavily web"
    print(f"[Agent] ✅ {len(all_reviews)} yorum toplandı ({source}).")
    return {**state, "store_reviews": all_reviews}


# ──────────────────────────────────────────────
# NODE 8: Store Yorumlarını Kümele [FAZ 3]
# ──────────────────────────────────────────────

def cluster_store_problems_node(state: AgentState) -> AgentState:
    """Store yorumlarındaki kullanıcı acılarını kümeler."""
    print("[Agent] Node 8 → cluster_store_problems")

    store_reviews = state.get("store_reviews", [])
    if not store_reviews:
        print("[Agent] ⚠️  Store yorum yok, kümeleme atlanıyor.")
        return {**state, "store_clusters": ""}

    reviews_text = "\n".join([
        f"[{r['app']}] ({r['score']}*) (thumbs={r.get('thumbs_up', 0)}): {r['text'][:250]}"
        for r in store_reviews[:20]
    ])

    prompt = f"""Aşağıda farklı uygulamaların Play Store/App Store'ıdaki 1-2 yıldız yorumları var.
Bu yorumları analiz et ve gerçek kullanıcıların en çok yaşadığı 5 sorunu belirle.
thumbsUp sayısı yüksek olanlar daha önemli.

Yorumlar:
{reviews_text}

Çıktı formatı (Türkçe):
1. [Sorun] — yaklaşık tekrar sayısı — [uygulama(lar)]
   Örnek: "..."
2. ...
(Sadece listeyi yaz)"""

    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        clusters = response.content
    except Exception as e:
        print(f"[Agent] ❌ Store kümeleme hatası: {e}")
        clusters = ""

    print("[Agent] ✅ Store yorumları kümelendi.")
    return {**state, "store_clusters": clusters}


# ──────────────────────────────────────────────
# GRAPH OLUŞTUR (Faz 3 — 8 node)
# ──────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    # Local imports to avoid circular import
    from agent.competition_matrix import competition_matrix_node
    from agent.validator import validate_idea_node

    # Faz 1 node'ları
    graph.add_node("fetch_trending_models",     fetch_trending_models_node)
    graph.add_node("match_to_market",           match_to_market_node)
    # Faz 2 node'ları
    graph.add_node("scrape_competitor_reviews",  scrape_competitor_reviews_node)
    graph.add_node("cluster_complaints",         cluster_complaints_node)
    # Faz 3 node'ları
    graph.add_node("find_store_app",             find_store_app_node)
    graph.add_node("scrape_store_reviews",       scrape_store_reviews_node)
    graph.add_node("cluster_store_problems",     cluster_store_problems_node)
    # Faz 9 node'ları
    graph.add_node("competition_matrix",         competition_matrix_node)
    graph.add_node("generate_opportunity",       generate_opportunity_node)
    graph.add_node("validate_idea",              validate_idea_node)

    graph.set_entry_point("fetch_trending_models")
    graph.add_edge("fetch_trending_models",     "match_to_market")
    graph.add_edge("match_to_market",           "scrape_competitor_reviews")
    graph.add_edge("scrape_competitor_reviews",  "cluster_complaints")
    graph.add_edge("cluster_complaints",         "find_store_app")
    graph.add_edge("find_store_app",             "scrape_store_reviews")
    graph.add_edge("scrape_store_reviews",       "cluster_store_problems")
    
    # Yeni akış: cluster_store_problems -> competition_matrix -> generate_opportunity -> validate_idea -> END
    graph.add_edge("cluster_store_problems",     "competition_matrix")
    graph.add_edge("competition_matrix",         "generate_opportunity")
    graph.add_edge("generate_opportunity",       "validate_idea")
    graph.add_edge("validate_idea",              END)

    return graph.compile()


# Singleton — Streamlit'te her request'te yeniden build etme
idea_agent = build_graph()


# ──────────────────────────────────────────────
# TERMINAL TEST
# ──────────────────────────────────────────────

if __name__ == "__main__":
    category = sys.argv[1] if len(sys.argv) > 1 else "video generation"
    print(f"\n{'='*55}")
    print(f"  Test calısıyor — kategori: '{category}'")
    print(f"  Graph: 8 node (Faz 3 — Final)")
    print(f"{'='*55}\n")

    result = idea_agent.invoke({
        "user_category": category,
        "trending_models": [],
        "matching_apps": [],
        "competitor_complaints": [],
        "complaint_clusters": "",
        "store_app_ids": [],
        "store_reviews": [],
        "store_clusters": "",
        "competition_matrix": "",
        "final_report": "",
        "validation_details": "",
        "error": None,
    })

    print("\n" + "="*55)
    print(result["final_report"])
    print("="*55)

    # Detayları göster
    if result.get("competitor_complaints"):
        print(f"\n--- {len(result['competitor_complaints'])} RAKİP ŞİKAYETİ ---")
    if result.get("store_reviews"):
        print(f"--- {len(result['store_reviews'])} STORE YORUMU ---")
        for r in result["store_reviews"][:3]:
            print(f"  [{r['app']}] ({r['score']}*): {r['text'][:80]}...")
    if result.get("store_app_ids"):
        print(f"--- STORE ID'LER: {result['store_app_ids']} ---")
