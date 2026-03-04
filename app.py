"""
Startup Idea Finder — Streamlit UI
Faz 2: Keşfet modu + Kategori modu + Rakip Analizi
"""

import sys
import os
import time
import random

import streamlit as st

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ──────────────────────────────────────────────
# SAYFA AYARLARI
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Startup Idea Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# CSS — PREMIUM UI
# ──────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  * { font-family: 'Inter', sans-serif; }

  .stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
  }

  .main-header {
    text-align: center;
    padding: 2.5rem 1rem 1rem;
  }
  .main-header h1 {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
  }
  .main-header p {
    color: #94a3b8;
    font-size: 1.05rem;
  }

  .card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }

  .badge {
    display: inline-block;
    background: rgba(167,139,250,0.2);
    color: #a78bfa;
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 999px;
    padding: 0.2rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 0.2rem;
  }

  .report-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 4px solid #a78bfa;
    border-radius: 12px;
    padding: 1.5rem;
    color: #e2e8f0;
    font-size: 0.95rem;
    line-height: 1.7;
    white-space: pre-wrap;
  }

  div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 2rem;
    font-weight: 600;
    font-size: 1rem;
    width: 100%;
    transition: opacity 0.2s;
  }
  div[data-testid="stButton"] > button:hover {
    opacity: 0.9;
  }

  .stSelectbox > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: white !important;
    border-radius: 10px !important;
  }

  .stRadio > div {
    gap: 0.5rem;
  }

  label, .stRadio label {
    color: #cbd5e1 !important;
  }

  hr { border-color: rgba(255,255,255,0.08); }

  .info-chip {
    background: rgba(52,211,153,0.15);
    border: 1px solid rgba(52,211,153,0.25);
    border-radius: 8px;
    padding: 0.4rem 0.8rem;
    color: #34d399;
    font-size: 0.8rem;
    display: inline-block;
    margin: 0.2rem;
  }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────

st.markdown("""
<div class="main-header">
  <h1>🔍 Startup Idea Finder</h1>
  <p>Trend AI modellerinden kanıtlanmış pazar fırsatları bul</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# KONTROL: ChromaDB var mı?
# ──────────────────────────────────────────────

CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
has_data = os.path.exists(CHROMA_DIR) and len(os.listdir(CHROMA_DIR)) > 0

if not has_data:
    st.warning("""
    ⚠️ **ChromaDB henüz dolu değil!**

    Önce veri çekme pipeline'ını çalıştır:
    ```
    python run_all.py
    ```
    Ya da adım adım:
    ```
    python scrapers/huggingface.py
    python scrapers/replicate.py
    python scrapers/fal.py
    python scrapers/trustmrr.py
    python scrapers/producthunt.py
    python ingestion/ingest.py
    ```
    """)
else:
    # Veri İstatistikleri Dashboard
    import json
    models_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "models_raw.json")
    apps_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "apps_raw.json")

    total_models, total_apps = 0, 0
    source_counts = {}
    try:
        if os.path.exists(models_file):
            with open(models_file, "r", encoding="utf-8") as f:
                models_data = json.load(f)
            total_models = len(models_data)
            for m in models_data:
                src = m.get("source", "unknown")
                source_counts[src] = source_counts.get(src, 0) + 1
        if os.path.exists(apps_file):
            with open(apps_file, "r", encoding="utf-8") as f:
                apps_data = json.load(f)
            total_apps = len(apps_data)
            for a in apps_data:
                src = a.get("source", "unknown")
                source_counts[src] = source_counts.get(src, 0) + 1
    except Exception:
        pass

    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("🤖 AI Modeller", total_models)
    with stat_cols[1]:
        st.metric("💰 Uygulamalar", total_apps)
    with stat_cols[2]:
        st.metric("📡 Veri Kaynağı", len(source_counts))
    with stat_cols[3]:
        st.metric("📂 Toplam Kayıt", total_models + total_apps)

# ──────────────────────────────────────────────
# FORM
# ──────────────────────────────────────────────

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🎯 Arama Modu")

    mode = st.radio(
        "Nasıl arama yapmak istiyorsun?",
        options=["🔥 Keşfet (Otomatik)", "🎯 Kategori Seç"],
        label_visibility="collapsed",
    )

    # Keşfet modunda rastgele kategori seçimi (her butona basışta farklı)
    DISCOVER_CATEGORIES = [
        "video generation", "image generation", "text to speech",
        "speech to text", "code generation", "music generation",
        "document AI", "computer vision", "text generation",
        "audio processing", "chatbot", "automation",
        "developer tools", "marketing", "analytics",
    ]
    category = random.choice(DISCOVER_CATEGORIES)  # butona basınca yenilenir

    if mode == "🎯 Kategori Seç":
        category = st.selectbox(
            "Alan seç",
            options=[
                "video generation",
                "image generation",
                "text to speech",
                "speech to text",
                "code generation",
                "music generation",
                "document AI",
                "computer vision",
            ],
            format_func=lambda x: {
                "video generation":  "🎬 Video Generation",
                "image generation":  "🖼️  Image Generation",
                "text to speech":    "🎙️  Text to Speech",
                "speech to text":    "🎧 Speech to Text",
                "code generation":   "💻 Code Generation",
                "music generation":  "🎵 Music Generation",
                "document AI":       "📄 Document AI",
                "computer vision":   "👁️  Computer Vision",
            }.get(x, x),
        )

    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📡 Veri Kaynakları")
    st.markdown("""
    <span class="badge">🤗 HuggingFace Hub</span>
    <span class="badge">🔁 Replicate</span>
    <span class="badge">⚡ fal.ai</span>
    <br/><br/>
    <span class="badge">💰 TrustMRR</span>
    <span class="badge">🚀 ProductHunt</span>
    <br/><br/>
    <span class="badge">🔍 Tavily (G2, Reddit)</span>
    <br/><br/>
    <span class="info-chip">✅ ChromaDB: ai_models + startup_apps</span>
    <span class="info-chip">✅ LangGraph Agent (8 Node)</span>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# BUTON
# ──────────────────────────────────────────────

st.markdown("<br/>", unsafe_allow_html=True)
run_btn = st.button("🚀 Fırsat Bul", use_container_width=True)

# ──────────────────────────────────────────────
# AGENT ÇALIŞTIR
# ──────────────────────────────────────────────

if run_btn:
    if not has_data:
        st.error("❌ Önce `python run_all.py` çalıştır!")
        st.stop()

    st.markdown("---")

    with st.spinner("🤖 Agent çalışıyor..."):
        # Keşfet modunda hangi kategori seçildiğini göster
        if mode == "🔥 Keşfet (Otomatik)":
            category_labels = {
                "video generation": "🎬 Video Generation",
                "image generation": "🖼️ Image Generation",
                "text to speech": "🎙️ Text to Speech",
                "speech to text": "🎧 Speech to Text",
                "code generation": "💻 Code Generation",
                "music generation": "🎵 Music Generation",
                "document AI": "📄 Document AI",
                "computer vision": "👁️ Computer Vision",
                "text generation": "✍️ Text Generation",
                "audio processing": "🔊 Audio Processing",
                "chatbot": "🤖 Chatbot",
                "automation": "⚡ Automation",
                "developer tools": "🛠️ Developer Tools",
                "marketing": "📣 Marketing",
                "analytics": "📊 Analytics",
            }
            st.info(f"🎲 Rastgele keşif alanı: **{category_labels.get(category, category)}**")

        # Adım göstergesi
        progress = st.progress(0, text="⏳ Başlatılıyor...")
        progress.progress(10, text="🔍 Trend modeller aranıyor...")
        try:
            from agent.idea_agent import idea_agent

            progress.progress(20, text="🤖 Trend modeller ChromaDB'den çekiliyor...")
            t0 = time.time()
            result = idea_agent.invoke({
                "user_category": category,
                "trending_models": [],
                "matching_apps":   [],
                "competitor_complaints": [],
                "complaint_clusters": "",
                "store_app_ids": [],
                "store_reviews": [],
                "store_clusters": "",
                "final_report":    "",
                "error":           None,
            })
            elapsed = time.time() - t0
            progress.progress(100, text="✅ Tamamlandı!")

        except Exception as e:
            st.error(f"❌ Agent hatası: {e}")
            st.stop()

    # ── Sonuçlar ──
    st.success(f"✅ Tamamlandı ({elapsed:.1f}s)")

    # Rapor
    st.markdown("### 💡 Fırsat Raporu")
    st.markdown(
        f'<div class="report-box">{result["final_report"]}</div>',
        unsafe_allow_html=True,
    )

    # Debug bilgileri (expander)
    with st.expander("🔍 Detay: Bulunan Modeller, Uygulamalar ve Şikayetler"):
        col_m, col_a = st.columns(2)
        with col_m:
            st.markdown("**🤖 Trend AI Modeller**")
            for m in result.get("trending_models", []):
                st.markdown(f"- [{m['name']}]({m['url']}) — `{m['category']}`")

        with col_a:
            st.markdown("**💰 Eşleşen Uygulamalar**")
            for a in result.get("matching_apps", []):
                st.markdown(
                    f"- [{a['name']}]({a['url']}) — MRR: `{a['mrr'] or '?'}` ({a['source']})"
                )

        # Rakip Şikayetleri (Faz 2)
        complaints = result.get("competitor_complaints", [])
        if complaints:
            st.markdown("---")
            st.markdown(f"**❌ Rakip Şikayetleri ({len(complaints)} kaynak)**")
            for c in complaints:
                st.markdown(
                    f"- **[{c['app']}]** ({c['source']}): {c['title'][:80]}...\n"
                    f"  _{c['content'][:150]}_"
                )

        clusters = result.get("complaint_clusters", "")
        if clusters:
            st.markdown("---")
            st.markdown("**📊 Kümelenmiş Şikayetler**")
            st.markdown(clusters)

        # Store Yorumları (Faz 3)
        store_reviews = result.get("store_reviews", [])
        if store_reviews:
            st.markdown("---")
            st.markdown(f"**📱 Store Yorumları ({len(store_reviews)} yorum, 1-2 yıldız)**")
            for r in store_reviews[:5]:
                stars = '⭐' * r.get('score', 1)
                thumbs = f" (👍 {r['thumbs_up']})" if r.get('thumbs_up') else ""
                st.markdown(
                    f"- **{r['app']}** {stars}{thumbs}: _{r['text'][:150]}_"
                )

        store_clusters = result.get("store_clusters", "")
        if store_clusters:
            st.markdown("---")
            st.markdown("**📊 Kullanıcı Acıları (Store Yorumlarından)**")
            st.markdown(store_clusters)

# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<center><small style='color:#475569'>Startup Idea Finder · Agentic RAG · "
    "<a href='https://github.com/tarikmenguc/Startup_Idea_Finder' style='color:#7c3aed'>GitHub</a></small></center>",
    unsafe_allow_html=True,
)
