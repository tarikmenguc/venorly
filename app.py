"""
Startup Idea Finder — Streamlit UI (V2)
Faz 7: Rapor geçmişi, export, grafikler, agent streaming
"""

import sys
import os
import time
import random
from datetime import datetime

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
    initial_sidebar_state="auto",
)

# Session state init
if "report_history" not in st.session_state:
    st.session_state.report_history = []
if "phase_a_state" not in st.session_state:
    st.session_state.phase_a_state = None   # İki aşamalı mod: Aşama A sonucu

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

    # Kaynak dağılımı grafiği
    if source_counts:
        import pandas as pd
        src_df = pd.DataFrame(
            {"Kaynak": list(source_counts.keys()), "Kayıt": list(source_counts.values())}
        ).set_index("Kaynak")
        with st.expander("📊 Kaynak Dağılımı", expanded=False):
            st.bar_chart(src_df)

# ──────────────────────────────────────────────
# FORM
# ──────────────────────────────────────────────

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🎯 Arama Modu")

    mode = st.radio(
        "Nasıl arama yapmak istiyorsun?",
        options=["🔥 Keşfet (Otomatik)", "🎯 Kategori Seç", "🔄 Rakip Analiz", "🧠 Derin Analiz"],
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
    target_startup = ""

    if mode in ["🎯 Kategori Seç", "🧠 Derin Analiz"]:
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
    elif mode == "🔄 Rakip Analiz":
        target_startup = st.text_input("Girişim/Uygulama Adı (örn: Lumen5)", value="Jasper AI")

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

# ── İki Aşamalı Mod: Aşama A bitti, alt-niş seçimi ──
if st.session_state.phase_a_state:
    pa = st.session_state.phase_a_state
    st.markdown("---")
    st.markdown("### 🔍 Pazar Taraması Tamamlandı")
    st.markdown(pa.get("market_overview", ""))
    st.markdown("**Bir alt-niş seçin ve Aşama B'yi başlatın:**")
    options = pa.get("_sub_niche_options") or [pa.get("user_category", "")]
    sub_niche_sel = st.radio("Alt-niş:", options, horizontal=True)
    if st.button("▶️ Derin Analiz Başlat (Aşama B)"):
        st.session_state.phase_a_state = None
        st.session_state["_run_phase_b"] = {"state": pa, "sub_niche": sub_niche_sel}
        st.rerun()

if st.session_state.get("_run_phase_b"):
    pb_args = st.session_state.pop("_run_phase_b")
    st.markdown("---")
    with st.spinner("🤖 Aşama B çalışıyor (derin fizibilite)..."):
        from agent.phase_agents import phase_b_agent
        pb_state = {**pb_args["state"], "sub_niche": pb_args["sub_niche"],
                    "store_app_ids": [], "store_reviews": [], "store_clusters": "",
                    "competition_matrix": "", "final_report": "", "validation_details": "",
                    "market_sizing": {}, "unit_economics": {}, "gtm_assets": "", "report_json": {}}
        pb_result = None
        for event in phase_b_agent.stream(pb_state):
            pb_result = list(event.values())[0]
        if pb_result:
            st.success("✅ Derin analiz tamamlandı!")
            st.markdown("### 💡 Fizibilite Raporu")
            st.markdown(pb_result.get("final_report", ""))

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

        # Adım göstergesi (streaming)
        progress = st.progress(0, text="⏳ Başlatılıyor...")
        status_box = st.empty()

        try:
            t0 = time.time()
            result = None

            if mode in ["🔥 Keşfet (Otomatik)", "🎯 Kategori Seç"]:
                from agent.idea_agent import idea_agent
                NODE_LABELS = {
                    "fetch_trending_models":   (10, "🔍 Trend modeller aranıyor..."),
                    "match_to_market":         (22, "🎯 Pazarla eşleştiriliyor..."),
                    "scrape_competitor_reviews":(36, "❌ Rakip şikayetleri toplanıyor..."),
                    "cluster_complaints":       (48, "📊 Şikayetler kümeleniyor..."),
                    "find_store_app":           (57, "📱 Store uygulamaları aranıyor..."),
                    "scrape_store_reviews":     (65, "⭐ Kullanıcı yorumları çekiliyor..."),
                    "cluster_store_problems":   (72, "🔬 Kullanıcı acıları analiz ediliyor..."),
                    "competition_matrix":       (80, "🥊 Rekabet matrisi hazırlanıyor..."),
                    "generate_opportunity":     (88, "💡 Fırsat raporu üretiliyor..."),
                    "validate_idea":            (93, "✅ Fikir doğrulanıyor ve skorlanıyor..."),
                    "auditor":                  (97, "🔎 Güven Endeksi hesaplanıyor..."),
                }
                _base_state = {
                    "user_category": category,
                    "trending_models": [], "matching_apps": [],
                    "competitor_complaints": [], "complaint_clusters": "",
                    "store_app_ids": [], "store_reviews": [], "store_clusters": "",
                    "competition_matrix": "", "final_report": "",
                    "validation_details": "", "seo_data": {},
                    "market_overview": "", "sub_niche": "",
                    "market_sizing": {}, "unit_economics": {}, "gtm_assets": "",
                    "report_json": {}, "error": None,
                }
                for event in idea_agent.stream(_base_state):
                    node_name = list(event.keys())[0]
                    result = event[node_name]
                    pct, label = NODE_LABELS.get(node_name, (50, f"⚙️ {node_name}..."))
                    progress.progress(pct, text=label)
                    if node_name == "generate_market_overview":
                        st.session_state.phase_a_state = result

            elif mode == "🔄 Rakip Analiz":
                from agent.reverse_agent import reverse_agent
                NODE_LABELS = {
                    "analyze_startup": (20, f"🔍 '{target_startup}' analiz ediliyor..."),
                    "find_competitors": (40, "👥 Rakipler bulunuyor..."),
                    "scrape_all_complaints": (65, "❌ Rakip şikayetleri toplanıyor..."),
                    "find_matching_ai_model": (80, "🤖 Uygun disruptive AI modelleri aranıyor..."),
                    "generate_disruption_report": (95, "🚀 Disruption Raporu yazılıyor..."),
                }
                for event in reverse_agent.stream({
                    "target_startup": target_startup,
                    "startup_analysis": "",
                    "competitors": [],
                    "competitor_complaints": [],
                    "complaint_clusters": "",
                    "matching_models": [],
                    "final_report": "",
                    "error": None,
                }):
                    node_name = list(event.keys())[0]
                    result = event[node_name]
                    pct, label = NODE_LABELS.get(node_name, (50, f"⚙️ {node_name}..."))
                    progress.progress(pct, text=label)

            elif mode == "🧠 Derin Analiz":
                st.info("🕒 Bu mod çoklu (paralel) web araması ve detaylı akıl yürütme içerdiği için 1-2 dakika sürebilir.")
                from agent.deep_agent import deep_agent
                NODE_LABELS = {
                    "init_research": (10, "📚 Pazar verileri (Model & App) toplanıyor..."),
                    "brainstorm_angles": (25, "🌀 3 farklı niş Micro-SaaS açısı türetiliyor..."),
                    "deep_web_research": (50, "🌐 Her açı için Tavily paralel web araştırması yapılıyor..."),
                    "competitor_deep_dive": (70, "🥊 Rakiplerin zayıf yönlerine derin dalış yapılıyor..."),
                    "reasoning_synthesis": (85, "🧠 Veriler sentezleniyor, en kârlı açı seçiliyor..."),
                    "write_investment_memo": (95, "📝 Investment Memo (Yatırım Raporu) yazılıyor..."),
                }
                for event in deep_agent.stream({
                    "target_category": category,
                    "trending_models": [],
                    "known_apps": [],
                    "brainstormed_angles": [],
                    "web_research_results": [],
                    "competitor_insights": "",
                    "selected_angle": "",
                    "investment_memo": "",
                    "error": None,
                }):
                    node_name = list(event.keys())[0]
                    result = event[node_name]
                    pct, label = NODE_LABELS.get(node_name, (50, f"⚙️ {node_name}..."))
                    progress.progress(pct, text=label)
                    
            elapsed = time.time() - t0
            progress.progress(100, text="✅ Tamamlandı!")

            if result is None or result.get("error"):
                st.error(f"❌ Agent hatası: {result.get('error', 'Sonuç dönmedi.')}")
                st.stop()

        except Exception as e:
            st.error(f"❌ Beklenmeyen hata: {e}")
            st.stop()

    # ── Sonuçlar ──
    st.success(f"✅ Tamamlandı ({elapsed:.1f}s)")

    # Rapor geçmişine ekle
    st.session_state.report_history.append({
        "category": category,
        "report": result.get("final_report", ""),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "elapsed": f"{elapsed:.1f}s",
    })

    # Validation Details
    if result.get("validation_details"):
        st.markdown(result["validation_details"])

    # Rapor
    if mode == "🧠 Derin Analiz":
        st.markdown("### 🧠 Investment Memo (Derin Analiz)")
        st.markdown(
            f'<div class="report-box" style="border-left: 4px solid #8b5cf6;">{result.get("investment_memo", "")}</div>',
            unsafe_allow_html=True,
        )
        export_text = result.get("investment_memo", "")
    else:
        st.markdown("### 💡 Fırsat Raporu")
        st.markdown(
            f'<div class="report-box">{result.get("final_report", "")}</div>',
            unsafe_allow_html=True,
        )
        export_text = result.get("final_report", "")
        
        if result.get("competition_matrix"):
            st.markdown("### 🥊 Rekabet Matrisi")
            st.markdown(result["competition_matrix"])
            export_text += "\n\n### 🥊 Rekabet Matrisi\n" + result["competition_matrix"]

    # ── Güven Endeksi Rozeti ──
    report_json = result.get("report_json") or {}
    if report_json.get("confidence_index") is not None:
        ci = report_json["confidence_index"]
        s_score = report_json.get("s_score", 0)
        x_score = report_json.get("x_score", 0)
        banner = report_json.get("banner", "red")
        color_map = {"green": "#22c55e", "yellow": "#f59e0b", "red": "#ef4444"}
        color = color_map.get(banner, "#94a3b8")
        st.markdown(
            f'<div style="border:1px solid {color};border-radius:8px;padding:12px 16px;margin:12px 0;">'
            f'<span style="color:{color};font-weight:700;font-size:1.1rem;">Güven Endeksi: {ci:.0%}</span>'
            f'&nbsp;&nbsp;<span style="color:#94a3b8;font-size:0.85rem;">'
            f'Kaynak Kalitesi: {s_score:.0%} | Çapraz Doğrulama: {x_score:.0%}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Kaynakça Paneli ──
    sources = (report_json.get("sources") or []) + [
        {"url": m.get("url",""), "title": m.get("name","Kaynak")}
        for m in result.get("trending_models",[])[:3] if m.get("url","").startswith("http")
    ]
    if sources:
        with st.expander("📚 Kaynakça"):
            for src in sources:
                url   = src.get("url") or src.get("link","")
                title = src.get("title") or url
                if url:
                    st.markdown(f"- [{title}]({url})")

    # Markdown export butonu
    if result.get("validation_details") and mode != "🧠 Derin Analiz":
        export_text += "\n\n" + result["validation_details"]
        
    st.download_button(
        label="📥 Raporu İndir (.md)",
        data=export_text,
        file_name=f"{'deep_memo' if mode == '🧠 Derin Analiz' else 'firsat'}_{category.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
    )

    # Debug bilgileri (expander)
    with st.expander("🔍 Detay: Bulunan Modeller, Uygulamalar ve Şikayetler"):
        if mode == "🧠 Derin Analiz":
            st.markdown("**🧠 Üretilen 3 Alternatif Hipotez**")
            for a in result.get("brainstormed_angles", []):
                st.markdown(f"- {a}")
            st.markdown("---")
            st.markdown("**🌐 Tavily Deep Dive Çıkarımları**")
            st.markdown(result.get("competitor_insights", ""))
            
        elif mode in ["🔥 Keşfet (Otomatik)", "🎯 Kategori Seç", "🔄 Rakip Analiz"]:
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

        elif mode == "🔄 Rakip Analiz":
            st.markdown(f"**🎯 Hedef Analizi:** {result.get('startup_analysis', '')}")
            st.markdown("---")
            st.markdown(f"**👥 Rakipler:** {', '.join(result.get('competitors', []))}")
            st.markdown("---")
            st.markdown("**🤖 Eşleşen Yıkıcı AI Modelleri**")
            for m in result.get("matching_models", []):
                st.markdown(f"- **{m.get('name')}**: {m.get('description', '')[:150]}...")
            st.markdown("---")
            complaints = result.get("competitor_complaints", [])
            st.markdown(f"**❌ Toplanan Şikayetler ({len(complaints)} adet)**")
            for c in complaints[:10]:
                st.markdown(f"- **[{c['app']}]**: {c['content'][:150]}...")

# ──────────────────────────────────────────────
# SIDEBAR: Rapor Geçmişi
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📜 Rapor Geçmişi")
    if st.session_state.report_history:
        for i, h in enumerate(reversed(st.session_state.report_history)):
            with st.expander(f"{h['category']} — {h['timestamp']} ({h['elapsed']})"):
                st.markdown(h["report"][:500] + "..." if len(h["report"]) > 500 else h["report"])
    else:
        st.caption("Henüz rapor yok. Yukarıdan arama yapın.")

# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<center><small style='color:#475569'>Startup Idea Finder V2 · Agentic RAG · "
    "<a href='https://github.com/tarikmenguc/Startup_Idea_Finder' style='color:#7c3aed'>GitHub</a></small></center>",
    unsafe_allow_html=True,
)
