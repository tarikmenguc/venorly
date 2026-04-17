"""
LangGraph Agentic RAG — Startup Idea Finder
Faz 3: trending modeller → pazar eşleştirme → rakip şikayetleri → store yorumları → fırsat raporu
Faz 18: ChromaDB kaldırıldı — tüm vektör aramaları Tavily web aramasıyla değiştirildi.
"""

import os
import random
import sys
from typing import TypedDict, List, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Proje kökünü path'e ekle (competitor_research import için)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

load_dotenv()

# ──────────────────────────────────────────────
# MODEL KURULUMU (ChromaDB kaldırıldı — Tavily kullanılıyor)
# ──────────────────────────────────────────────

_llm = None


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
    seo_data: dict                   # google_trends verisi                      [V8]
    error: Optional[str]


# ──────────────────────────────────────────────
# NODE 1: Trend Modelleri Getir
# ──────────────────────────────────────────────

def fetch_trending_models_node(state: AgentState) -> AgentState:
    """Tavily web aramasıyla trend AI modellerini/araçlarını bulur."""
    query = state["user_category"] or "trending AI model"
    print(f"[Agent] Node 1 → fetch_trending_models (Tavily) | query: '{query}'")

    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = tavily.search(
            f"trending AI models tools for {query} 2024 2025",
            max_results=10,
            search_depth="basic"
        )
    except Exception as e:
        print(f"[Agent] ❌ Tavily model arama hatası: {e}")
        return {**state, "trending_models": [], "error": str(e)}

    all_models = []
    for r in results.get("results", []):
        all_models.append({
            "content":   r.get("content", "")[:300],
            "name":      r.get("title", ""),
            "model_id":  "",
            "category":  query,
            "source":    "tavily_web",
            "downloads": "N/A",
            "url":       r.get("url", ""),
        })

    sample_size = min(8, len(all_models))
    models = random.sample(all_models, sample_size) if all_models else []

    print(f"[Agent] ✅ {len(all_models)} model bulundu → {len(models)} rastgele seçildi.")
    return {**state, "trending_models": models, "error": None}


# ──────────────────────────────────────────────
# NODE 2: Pazarla Eşleştir (Tavily ile)
# ──────────────────────────────────────────────

def match_to_market_node(state: AgentState) -> AgentState:
    """
    İngilizce sorgularla pazardaki mevcut SaaS uygulamalarını bulur.
    Domain bazlı dedup, en az 5 sonuç, retry mekanizması.
    """
    print(f"[Agent] Node 2 → match_to_market | kategori: '{state['user_category']}'")

    try:
        from scrapers.competitor_research import find_competitors
        category = state["user_category"]
        competitors = find_competitors(category=category, niche=category, min_results=5)
    except Exception as e:
        print(f"[Agent] ❌ Rakip arama hatası: {e}")
        competitors = []

    # Eski format ile uyumlu hale getir (state'teki diğer node'lar name/url bekliyor)
    all_apps = []
    for c in competitors:
        all_apps.append({
            "name":        c.get("name", ""),
            "url":         c.get("url", ""),
            "domain":      c.get("domain", ""),
            "content":     c.get("snippet", "")[:300],
            "mrr":         c.get("pricing_hint", ""),
            "votes":       "0",
            "category":    state["user_category"],
            "source":      "tavily_web",
            "pricing_hint": c.get("pricing_hint", "bilinmiyor"),
        })

    print(f"[Agent] ✅ {len(all_apps)} rakip/uygulama bulundu.")

    # ── SEO / Google Trends verisi (match_to_market ile birlikte çekiliyor) ──
    seo_data = {}
    try:
        from scrapers.google_trends import get_search_volume, generate_seo_keywords
        keywords = generate_seo_keywords(state["user_category"])
        seo_data = get_search_volume(keywords)
        print(f"[Agent] ✅ SEO verisi alındı: {list(seo_data.keys())}")
    except Exception as e:
        print(f"[Agent] ⚠️  SEO verisi alınamadı (devam ediyor): {e}")

    return {**state, "matching_apps": all_apps, "seo_data": seo_data}


# ──────────────────────────────────────────────
# NODE 3: Rakip Şikayetlerini Çek [FAZ 2]
# ──────────────────────────────────────────────

def scrape_competitor_reviews_node(state: AgentState) -> AgentState:
    """Eşleşen uygulamaların rakip şikayetlerini Tavily ile arar."""
    print("[Agent] Node 3 → scrape_competitor_reviews")

    if not state["matching_apps"]:
        print("[Agent] ⚠️  Eşleşen app yok, şikayet araması atlanıyor.")
        return {**state, "competitor_complaints": []}

    # domain bazlı filtrele — çok genel siteleri (reddit, g2) çıkar
    skip_domains = {"reddit.com", "g2.com", "capterra.com", "trustpilot.com", "producthunt.com"}
    app_names = [
        a["name"] for a in state["matching_apps"]
        if a.get("name") and a.get("domain", "") not in skip_domains
    ]

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

    # Modeller — URL dahil
    if state["trending_models"]:
        models_text = "\n".join([
            f"  • {m['name']} ({m['category']}) | {m['url']}"
            for m in state["trending_models"][:5]
        ])
    else:
        models_text = "  (Model verisi bulunamadı)"

    # Uygulamalar — URL dahil
    if state["matching_apps"]:
        apps_text = "\n".join([
            f"  • {a['name']} | {a.get('url', 'URL yok')}"
            for a in state["matching_apps"][:5]
        ])
    else:
        apps_text = "  (Uygulama verisi bulunamadı)"

    # Atıfta bulunulabilecek kaynaklar — LLM bunları doğrudan kullanacak
    source_pool = []
    for m in state.get("trending_models", [])[:5]:
        if m.get("url") and m["url"].startswith("http"):
            source_pool.append(f"  - {m['name']}: {m['url']}")
    for a in state.get("matching_apps", [])[:5]:
        if a.get("url") and a["url"].startswith("http"):
            source_pool.append(f"  - {a['name']}: {a['url']}")
    for c in state.get("competitor_complaints", [])[:3]:
        if c.get("url") and c["url"].startswith("http"):
            source_pool.append(f"  - {c.get('app','Kaynak')}: {c['url']}")
    cited_sources_block = (
        "Araştırma sırasında bulunan kaynaklar (yalnızca bunları kullan, URL uydurmak yasak):\n"
        + "\n".join(source_pool)
        if source_pool else
        "Araştırma kaynakları: Bu tarama için doğrulanmış URL bulunamadı."
    )

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

    # SEO verisi bölümü
    seo_data = state.get("seo_data", {})
    seo_text = ""
    if seo_data:
        seo_lines = []
        for kw, d in list(seo_data.items())[:3]:
            direction_emoji = "↑" if d.get("trend_direction") == "rising" else ("↓" if d.get("trend_direction") == "declining" else "→")
            seo_lines.append(
                f'  • "{kw}" → İlgi: {d.get("interest_score", "?")} /100 '
                f'({direction_emoji} {d.get("change_pct", "0%")})'
            )
            rising = d.get("related_rising", [])[:3]
            if rising:
                seo_lines.append(f'    Yükselen aramalar: {", ".join(rising)}')
        seo_text = "\nArama Hacmi Verileri:\n" + "\n".join(seo_lines)

    data_context = f"""Kategori: {state['user_category']}
Perspektif: {chosen_perspective}

Trend AI Modelleri ve Kaynakları:
{models_text}

Mevcut Uygulamalar ve Kaynakları:
{apps_text}
{all_complaints}{seo_text}

{cited_sources_block}"""

    # ========================================
    # AŞAMA 1: 3 farklı fikir üret (yaratıcı)
    # ========================================
    print("[Agent]   Aşama 1/3: 3 fikir üretiliyor...")
    prompt1 = f"""Kategori: "{state['user_category']}"

Trend AI Modelleri:
{models_text if models_text.strip() != "(Model verisi bulunamadı)" else "(Kategoriye uygun spesifik AI modellerini düşün.)"}

Mevcut uygulamalar (rakipler):
{apps_text if apps_text.strip() != "(Uygulama verisi bulunamadı)" else "(Bu kategorideki mevcut SaaS ürünlerini göz önünde bulundur.)"}

Görev: Yukarıdaki kategoride, aylık 29-99 dolar ödeyebilecek B2B profesyonellere (ajanslar, freelancer'lar, küçük işletmeler) yönelik 3 farklı Micro-SaaS fikri öner.

Kurallar:
- Tüketici uygulaması değil, iş araçları olsun.
- Her fikir somut bir manuel iş sürecini otomatize etsin — genel "analiz aracı" veya "dashboard" olmasın.
- AI API'leri kullanılarak üretilmiş olsun.
- YALNIZCA TÜRKÇE yaz.

Format:
1. [Başlık] | Hedef: [Spesifik niş] | Sorun: [Manuel süreç] | Çözüm: [Otomasyon]
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
    prompt2 = f"""Aşağıda 3 Micro-SaaS fikri var. Hangisi detaylı analize en değer?

{ideas_raw}

Değerlendirme kriterleri:
- Hedef kitlenin ödeme kapasitesi ve istekliliği
- Çözülen sorunun ciddiyeti (ne kadar zaman/para kaybettiriyor?)
- Rekabet ortamında farklılaşma imkânı

Seçim: [numara] — Gerekçe: [2-3 cümle, nesnel ve kısa]

Sadece seçim numarasını ve gerekçeyi yaz. Abartma."""

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
    # all_complaints'i güvenli şekilde temizle — yabancı dil karakterleri filtrelenir
    complaints_summary = ""
    if all_complaints.strip():
        # Ham metin yerine LLM'e özetle yaptır (dil kirliliği önlenir)
        try:
            clean_prompt = f"""Aşağıdaki kullanıcı şikayeti verilerini analiz et ve mevcut araçların en büyük 3 eksikliğini TÜRKÇE olarak 1-2 cümleyle özetle. Yabancı dil karakterleri veya anlamsız metin varsa yoksay.

Veri:
{all_complaints[:800]}

YALNIZCA TÜRKÇE olarak, sadece 3 maddelik özeti yaz."""
            complaints_summary = get_llm(temp=0.1).invoke([HumanMessage(content=clean_prompt)]).content.strip()
        except Exception:
            complaints_summary = "Rakip şikayet verisi işlenemedi."
    else:
        complaints_summary = "Rakip şikayet verisi bulunamadı — piyasadaki araçların genel boşluklarını analiz et."

    prompt3 = f"""Seçilen B2B/Painkiller fikri:
{selected_idea}

Fikirler:
{ideas_raw}

Veri Kaynakları:
{data_context}

Rakip Eksiklikleri (Özet):
{complaints_summary}

════════════════════════════════════════
ZORUNLU KURALLAR — BUNLARA UYMAZSAN RAPOR GEÇERSİZ SAYILIR:

1. KAYNAK ZORUNLULUĞU
   - Veri kaynakları bölümünde listelenen URL'lerden birini kullandığında parantez içinde yaz: (Kaynak: https://...)
   - Listede olmayan bir URL uydurmak KESİNLİKLE YASAK.
   - Eğer bir iddianın kaynağı yoksa: "(Kaynak: doğrulanamadı)" yaz ve iddiayı tahmin olarak çerçevele.

2. TEKNOLOJİ STACK — SOYUT İFADE YASAK
   - "AI modeli kullanılacak" yazmak yasak.
   - Her teknoloji için spesifik isim + yaklaşık birim maliyet zorunlu.
   - Örnek format: "OpenAI Whisper API (~$0.006/dk) + GPT-4o-mini (~$0.15/1M token)"
   - Eğer kesin fiyat bilinmiyorsa: "yaklaşık $X (Kaynak: doğrulanamadı)" şeklinde yaz.

3. TAM/SAM/SOM — HALÜSİNASYON YASAK
   - Pazar büyüklüğü rakamı veriyorsan hesaplama formülünü göstermek zorundasın.
   - Format: "TAM = [hedef kitle sayısı] kişi × [yıllık fiyat] = [toplam]"
   - Formülün temelindeki varsayımı da belirt: "Dünya genelinde yaklaşık X [meslek] olduğu tahmin edilmektedir (Kaynak: doğrulanamadı)" gibi.
   - Kaynaklı veri yoksa TAM/SAM/SOM rakamı vermek yerine şunu yaz: "Pazar büyüklüğü için güvenilir kaynak bulunamadı, tahmin verilmemiştir."

4. DİL TUTARLILIĞI
   - Yalnızca Türkçe yaz. İngilizce cümle, bölüm başlığı veya paragraf yasak.
   - İngilizce terim kaçınılmazsa ilk kullanımda Türkçe karşılığını ver: "Willingness to Pay (ödeme isteği)"

5. ÜSLUP
   - Fikri onaylama, her iddiayı sorgula.
   - "Bu harika bir fırsat" gibi pazarlama dili yasak.
   - Deneyimli, saygılı, doğrudan — emoji veya ünlem işareti kullanma.
════════════════════════════════════════

Aşağıdaki başlıkları sırayla yaz:

## Fikir

[Tek cümle: kim için, ne yapıyor, hangi teknolojiyle (spesifik model adı zorunlu).]

---

## Gerçekten Bir İhtiyaç Var mı?

[Bu işi bugün manuel yapan insanlar gerçekten var mı? Kaç saat kaybediyorlar? Bu acı, aylık $X ödemeyi haklı kılar mı? Kanıtla ya da kanıtlanamıyorsa "doğrulanamadı" de. Kaynakları parantez içinde göster.]

---

## Hedef Kitle ve Ödeme Kapasitesi

[Spesifik niş, tahmini kitle büyüklüğü (formülle), bu kitlenin bugün benzer araçlara ne ödediği. Ödeme isteksizliği riski varsa belirt.]

---

## Teknoloji Yığını ve Maliyet Yapısı

[Kullanılacak her API/model: isim, birim maliyet, ne için kullanılacağı. Örnek: "OpenAI Whisper API (~$0.006/dk) — ses transkripsiyon için". Maliyet bilinmiyorsa "(Kaynak: doğrulanamadı)" ekle.]

---

## Mevcut Rakiplerin Neden Yetersiz Kaldığı

[Rakip eksiklikleri: {complaints_summary[:200]}

Bu eksiklikler gerçek mi yoksa alışkanlık sorunu mu? Rakipler bu açığı neden kapatmadı? Kaynakları göster.]

---

## Kritik Riskler

[En az 3 somut risk. Her birini 1-2 cümleyle, net yaz.]

---

## Geliştirme Süresi ve Teknik Gerçekçilik

[MVP kaç hafta, hangi API'ler kullanılacak (spesifik), teknik zorluk 1-5 üzerinden ve neden.]

---

## İlk Müşteriye Ulaşma Yolu

[Reklam yok. Hangi topluluk veya kanal, neden orada? İlk 10 müşteri için somut adımlar.]

---

## Fiyatlandırma Mantığı

[Önerilen aylık ücret ve gerekçesi. TAM/SAM/SOM varsa formülle göster, yoksa "güvenilir kaynak bulunamadı" yaz.]

---

## Sonuç

[Nesnel değerlendirme: güçlü yanlar, zayıf yanlar. Hangi varsayımları doğrulamadan bu fikre zaman ayırmak hata olur?]

---

Sadece raporu yaz. Emoji kullanma."""

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
