import os
import json
import requests
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Any

tavily = TavilySearchResults(max_results=3)


def check_url_accessibility(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    try:
        res = requests.get(url, timeout=5)
        return res.status_code == 200
    except Exception:
        return False


# ──────────────────────────────────────────────
# C.1: Idea Scorecard (5 Boyutlu Puan Kartı)
# ──────────────────────────────────────────────

def generate_idea_scorecard(report: str, llm) -> dict:
    """
    5 boyutlu skor kartı üretir.
    Returns: {"scores": {...}, "total": int, "label": str, "markdown": str}
    """
    prompt = f"""Aşağıdaki Micro-SaaS startup raporunu 5 boyutta 1-10 arası puanla.

PUANLAMA KRİTERLERİ:
1. willingness_to_pay: Hedef kitlenin ödeme isteği (bu acıyı çözmek için para öderler mi?)
2. time_saved: Zaman tasarrufu (manuel süreç yerine ne kadar zaman kazandırıyor?)
3. technical_feasibility: Teknik fizibilite (mevcut API/AI ile yapılabilir mi?)
4. competition_level: Rekabet avantajı (10=çok az rakip, 1=kırmızı okyanus)
5. gtm_ease: Go-to-market kolaylığı (hedef kitleye ulaşmak ne kadar kolay?)

Rapor:
{report[:2000]}

SADECE aşağıdaki JSON formatında yanıt ver, başka hiçbir şey yazma:
{{"willingness_to_pay": 7, "time_saved": 8, "technical_feasibility": 6, "competition_level": 5, "gtm_ease": 7}}"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        # JSON'u bul ve parse et
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            scores = json.loads(response[start:end])
        else:
            scores = {"willingness_to_pay": 5, "time_saved": 5, "technical_feasibility": 5, "competition_level": 5, "gtm_ease": 5}
    except Exception as e:
        print(f"[Validator] Scorecard parse hatası: {e}")
        scores = {"willingness_to_pay": 5, "time_saved": 5, "technical_feasibility": 5, "competition_level": 5, "gtm_ease": 5}

    # Puanları sınırla
    for k in scores:
        scores[k] = max(1, min(10, int(scores.get(k, 5))))

    total = sum(scores.values())

    if total >= 35:
        label = "🟢 Güçlü Fırsat"
    elif total >= 20:
        label = "🟡 Araştırmaya Değer"
    else:
        label = "🔴 Riskli"

    # Emoji bar oluştur
    def bar(score):
        filled = "█" * score
        empty = "░" * (10 - score)
        return f"`{filled}{empty}` **{score}/10**"

    markdown = f"""
---

## 📊 Idea Scorecard — {label}

| Kriter | Puan |
|--------|------|
| 🎯 Ödeme İsteği (WTP) | {bar(scores['willingness_to_pay'])} |
| ⏱️ Zaman Tasarrufu | {bar(scores['time_saved'])} |
| 🏗️ Teknik Fizibilite | {bar(scores['technical_feasibility'])} |
| 🗡️ Rekabet Avantajı | {bar(scores['competition_level'])} |
| 🚀 GTM Kolaylığı | {bar(scores['gtm_ease'])} |
| **📊 TOPLAM** | **{total}/50 — {label}** |
"""

    return {"scores": scores, "total": total, "label": label, "markdown": markdown}


# ──────────────────────────────────────────────
# C.2: TAM/SAM/SOM Pazar Büyüklüğü
# ──────────────────────────────────────────────

def estimate_market_size(idea_summary: str, target_audience: str, llm) -> str:
    """Pazar büyüklüğü tahmini yapar. Markdown tablosu döner."""

    prompt = f"""Sen bir pazar araştırma analistisin. Aşağıdaki Micro-SaaS fikri için TAM/SAM/SOM tahminlerini yap.

Fikir: {idea_summary}
Hedef Kitle: {target_audience}

Hesaplama yöntemi:
- TAM (Total Addressable Market): Dünya genelinde bu problemi yaşayan potansiyel kullanıcı sayısı × yıllık fiyat
- SAM (Serviceable Addressable Market): Dijital araç kullanıcıları, ulaşılabilir pazar dilimi
- SOM (Serviceable Obtainable Market): İlk 12 ayda gerçekçi hedef (aylık müşteri × aylık fiyat × 12)

SADECE aşağıdaki JSON formatında yanıt ver:
{{"tam": "$2.1B", "tam_explanation": "Dünyada 3M düğün fotoğrafçısı × $700/yıl", "sam": "$340M", "sam_explanation": "ABD+AB dijital araç kullananlar ~480K", "som": "$850K", "som_explanation": "İlk yıl 1.500 müşteri × $49/ay"}}"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(response[start:end])
        else:
            return ""
    except Exception as e:
        print(f"[Validator] Market size hatası: {e}")
        return ""

    markdown = f"""
## 📈 Pazar Büyüklüğü Tahmini

| Metrik | Büyüklük | Açıklama |
|--------|----------|----------|
| **TAM** (Toplam Pazar) | **{data.get('tam', '?')}** | {data.get('tam_explanation', '')} |
| **SAM** (Ulaşılabilir) | **{data.get('sam', '?')}** | {data.get('sam_explanation', '')} |
| **SOM** (İlk Yıl Hedef) | **{data.get('som', '?')}** | {data.get('som_explanation', '')} |

> 💡 *Bu tahminler yapay zeka tarafından üretilmiştir. Kesin rakamlar için derinlemesine pazar araştırması yapılmalıdır.*
"""
    return markdown


# ──────────────────────────────────────────────
# C.3: Startup Mezarlığı (Failure Check)
# ──────────────────────────────────────────────

def check_startup_graveyard(idea_summary: str, llm) -> str:
    """Benzer başarısız girişimleri arar. Markdown uyarısı döner."""

    # Tavily ile başarısız girişim araması
    try:
        search_results = tavily.invoke(f'"{idea_summary}" startup failed OR shutdown OR pivoted OR "shut down" OR acquired')
        if not search_results:
            return ""
    except Exception as e:
        print(f"[Validator] Graveyard arama hatası: {e}")
        return ""

    # Sonuçları metin olarak hazırla
    results_text = ""
    for r in search_results[:5]:
        if isinstance(r, dict):
            results_text += f"- {r.get('content', '')[:200]}\n"

    if not results_text.strip():
        return ""

    # LLM ile analiz
    prompt = f"""Aşağıda "{idea_summary}" fikrine benzer başarısız veya kapanmış girişimler hakkında web araması sonuçları var.

Sonuçlar:
{results_text}

Görevin:
1. Bu sonuçlardan gerçekten kapanmış/başarısız olmuş girişimleri tespit et
2. Her biri için kapanma sebebini 1 cümlede özetle
3. Kullanıcının bu hatalardan nasıl kaçınabileceğine dair 1 tavsiye ver

Eğer gerçekten benzer başarısız bir girişim YOKSA, sadece "YOK" yaz.

Format:
1. **[Girişim Adı]** (Yıl): Kapanma sebebi — ...
2. ...
💡 Farklılaşma Fırsatın: ..."""

    try:
        analysis = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        if "YOK" in analysis.upper() and len(analysis) < 50:
            return """
## ✅ Startup Mezarlığı Kontrolü

Bu fikre benzer başarısız bir girişim bulunamadı — **temiz geçmiş!** Bu, ya henüz denenmemiş bir alan olduğu ya da başarılı girişimlerin hâlâ ayakta olduğu anlamına gelir.
"""
        else:
            return f"""
## ⚰️ Startup Mezarlığı Kontrolü

> ⚠️ Bu fikre benzer daha önce başarısız olmuş girişimler tespit edildi. Aşağıdaki dersleri dikkate al:

{analysis}
"""
    except Exception as e:
        print(f"[Validator] Graveyard analiz hatası: {e}")
        return ""


# ──────────────────────────────────────────────
# ANA VALIDASYON NODE'U (Genişletilmiş)
# ──────────────────────────────────────────────

def validate_idea_node(state: Any) -> Any:
    """Üretilen fikrin kapsamlı validasyonunu yapar — Scorecard + Market Size + Graveyard."""
    print("[Validator] Node 9 → validate_idea (V7 Enhanced)")
    from agent.idea_agent import get_llm

    report = state.get("final_report", "")
    if not report:
        return {**state, "validation_score": 0, "validation_details": "Rapor yok."}

    llm = get_llm(temp=0.1)

    # Fikrin özünü LLM ile çıkar
    extract_prompt = f"Şu rapordan fikrin ne olduğunu sadece 3-5 kelime ile özetle (örn: AI destekli dişçi CRM): {report[:500]}"
    try:
        idea_summary = llm.invoke([HumanMessage(content=extract_prompt)]).content.strip()
    except Exception:
        idea_summary = "AI SaaS tool"

    # Hedef kitle çıkar
    audience_prompt = f"Şu rapordan hedef kitleyi sadece 3-5 kelime ile özetle (örn: Düğün Fotoğrafçıları): {report[:500]}"
    try:
        target_audience = llm.invoke([HumanMessage(content=audience_prompt)]).content.strip()
    except Exception:
        target_audience = "B2B Professionals"

    print(f"[Validator] Fikir: {idea_summary} | Hedef: {target_audience}")

    # 1. Tavily ile rakip kontrolü
    try:
        search_results = tavily.invoke(f"{idea_summary} saas software alternative")
        existing_competitors = len(search_results) if search_results else 0
    except Exception as e:
        print(f"[Validator] Tavily hatası: {e}")
        existing_competitors = -1

    # 2. Model URL erişilebilirlik
    models = state.get("trending_models", [])
    api_accessible = True
    if models and len(models) > 0:
        url = models[0].get("url", "")
        if url:
            api_accessible = check_url_accessibility(url)

    # 3. Idea Scorecard (C.1)
    print("[Validator]   📊 Scorecard hesaplanıyor...")
    scorecard = generate_idea_scorecard(report, llm)

    # 4. TAM/SAM/SOM (C.2)
    print("[Validator]   📈 Pazar büyüklüğü tahmin ediliyor...")
    market_size_md = estimate_market_size(idea_summary, target_audience, llm)

    # 5. Startup Mezarlığı (C.3)
    print("[Validator]   ⚰️ Startup mezarlığı kontrol ediliyor...")
    graveyard_md = check_startup_graveyard(idea_summary, llm)

    # Tüm validation detaylarını birleştir
    validation_details = f"""
✅ **Doğrulama Özeti**
- **Fizibilite Skoru:** {scorecard['total']}/50 — {scorecard['label']}
- **Benzer Rakipler (Web):** {existing_competitors if existing_competitors >= 0 else 'Bilinmiyor'} sonuç
- **Model API Durumu:** {'Çalışıyor ✅' if api_accessible else 'Erişim Sorunu ⚠️'}

{scorecard['markdown']}
{market_size_md}
{graveyard_md}
"""

    print(f"[Validator] ✅ Skor: {scorecard['total']}/50 ({scorecard['label']})")

    # V7: final_report sonuna scorecard bilgilerini ekliyoruz ki ekranda görünsün!
    updated_report = report + "\n" + validation_details.strip()

    return {**state, "validation_details": validation_details.strip(), "final_report": updated_report}
