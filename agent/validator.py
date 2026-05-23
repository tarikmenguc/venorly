import os
import json
import requests
from langchain_core.messages import HumanMessage
from tavily import TavilyClient
from lib.tavily_client import get_tavily_client as _lib_get_tavily
from typing import Any

def _get_tavily_client() -> TavilyClient | None:
    try:
        return _lib_get_tavily()
    except EnvironmentError as e:
        print(f"[Validator] ⚠️ {e}")
        return None


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
    5 boyutlu skor kartı.
    - Her kriter için gerekçe zorunlu
    - 1-10 skalasının tamamı kullanılabilir (orta puana yönelim önlenir)
    - Her kriterde rapordaki somut kanıt veya eksiklik alıntılanır
    Returns: {"scores": {...}, "reasons": {...}, "total": int, "label": str, "markdown": str}
    """
    prompt = f"""Aşağıdaki startup analiz raporunu 5 boyutta değerlendir. Her boyut için 1-10 arası bir puan ver ve gerekçeni 1 cümleyle yaz.

PUANLAMA SKALALARI (Bu skalayı tam olarak uygula — orta değerlere yığılma yapma):

1. willingness_to_pay — Hedef kitlenin ödeme isteği
   1-3: Kitle bu tür araçlara para ödemez veya ücretsiz alternatif çoktur
   4-6: Ödeme olası ama kanıtlanmamış, pazar olgunlaşmamış
   7-9: Benzer araçlara zaten para ödüyor, bu ürün için de öder
   10: Kitle bu olmadan işini sürdüremiyor, fiyata duyarsız

2. time_saved — Çözülen sorunun ağırlığı / zaman tasarrufu
   1-3: Saatte birkaç dakika, kolayca görmezden gelinebilir
   4-6: Haftada 1-2 saat, fark edilir ama kritik değil
   7-9: Haftada 5+ saat, bu iş çözülmeden büyük verimlilik kaybı var
   10: İş hayatta kalmak için bu süreç kritik ve şu an tamamen manüel

3. technical_feasibility — Mevcut teknoloji ile yapılabilirlik
   1-3: Henüz olgunlaşmamış teknoloji, hallüsinasyon riski yüksek
   4-6: Yapılabilir ama önemli teknik zorluklar var
   7-9: Mevcut API/modeller ile makul sürede üretilebilir
   10: Off-the-shelf API'ler birleştirilince çözüm neredeyse hazır

4. competition_level — Rekabetten farklılaşma
   1-3: Kalabalık pazar, büyük oyuncular aynı şeyi yapıyor
   4-6: Rakipler var ama ciddi boşluklar mevcut
   7-9: Bu nişe özel çözüm yok veya mevcut araçlar yetersiz kalıyor
   10: Neredeyse hiç rakip yok ve ihtiyaç net

5. gtm_ease — İlk müşteriye ulaşma kolaylığı
   1-3: Kitleye ulaşmak zor, dağınık veya bilinç düşük
   4-6: Topluluklar mevcut ama güven inşası zaman alır
   7-9: Spesifik, ulaşılabilir bir topluluk var (Reddit, Discord, Slack)
   10: Hedef kitle aktif olarak bu soruna çözüm arıyor

Rapor:
{report[:3000]}

SADECE aşağıdaki JSON formatında yanıt ver. reasons alanına her kriterin gerekçesini yaz (rapordan somut alıntı veya tespit et):
{{
  "willingness_to_pay": 6,
  "wtp_reason": "Kitle benzer araçlara aylık $50-200 ödüyor ancak bu ürünün fiyatlandırması kanıtlanmamış",
  "time_saved": 7,
  "ts_reason": "Manuel süreç haftada ~5 saat alıyor, raporda somut süre verilmiş",
  "technical_feasibility": 5,
  "tf_reason": "GPT-4o entegrasyonu mümkün ancak video rendering gecikme riski var",
  "competition_level": 4,
  "cl_reason": "Lumen5 ve Pictory aynı nişte aktif, farklılaşma belirsiz",
  "gtm_ease": 7,
  "ge_reason": "r/videoediting ve Upwork'te aktif kitle mevcut, DM stratejisi spesifik"
}}"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            raw = json.loads(response[start:end])
        else:
            raise ValueError("JSON bulunamadı")
    except Exception as e:
        print(f"[Validator] Scorecard parse hatası: {e}")
        raw = {
            "willingness_to_pay": 5, "wtp_reason": "Değerlendirilemedi",
            "time_saved": 5, "ts_reason": "Değerlendirilemedi",
            "technical_feasibility": 5, "tf_reason": "Değerlendirilemedi",
            "competition_level": 5, "cl_reason": "Değerlendirilemedi",
            "gtm_ease": 5, "ge_reason": "Değerlendirilemedi",
        }

    scores = {
        "willingness_to_pay":  max(1, min(10, int(raw.get("willingness_to_pay", 5)))),
        "time_saved":          max(1, min(10, int(raw.get("time_saved", 5)))),
        "technical_feasibility": max(1, min(10, int(raw.get("technical_feasibility", 5)))),
        "competition_level":   max(1, min(10, int(raw.get("competition_level", 5)))),
        "gtm_ease":            max(1, min(10, int(raw.get("gtm_ease", 5)))),
    }
    reasons = {
        "wtp": raw.get("wtp_reason", ""),
        "ts":  raw.get("ts_reason", ""),
        "tf":  raw.get("tf_reason", ""),
        "cl":  raw.get("cl_reason", ""),
        "ge":  raw.get("ge_reason", ""),
    }

    total = sum(scores.values())

    if total >= 35:
        label = "Güçlü Fırsat"
        label_indicator = "▲"
    elif total >= 20:
        label = "Araştırmaya Değer"
        label_indicator = "◆"
    else:
        label = "Yüksek Riskli"
        label_indicator = "▼"

    def bar(score):
        filled = "█" * score
        empty = "░" * (10 - score)
        return f"`{filled}{empty}` {score}/10"

    markdown = f"""

---

## Fizibilite Değerlendirmesi

| Kriter | Puan | Gerekçe |
|--------|------|---------|
| Ödeme İsteği | {bar(scores['willingness_to_pay'])} | {reasons['wtp']} |
| Sorunun Ağırlığı | {bar(scores['time_saved'])} | {reasons['ts']} |
| Teknik Fizibilite | {bar(scores['technical_feasibility'])} | {reasons['tf']} |
| Rekabetten Farklılaşma | {bar(scores['competition_level'])} | {reasons['cl']} |
| Pazara Erişim | {bar(scores['gtm_ease'])} | {reasons['ge']} |
| **Toplam** | **{total}/50** | **{label_indicator} {label}** |

_Bu puan kartı üretilen rapora dayalı ön değerlendirmedir. Piyasa doğrulaması yapılmadan yatırım kararı alınmamalıdır._
"""

    return {"scores": scores, "reasons": reasons, "total": total, "label": label, "markdown": markdown}


# ──────────────────────────────────────────────
# C.2: TAM/SAM/SOM Pazar Büyüklüğü
# ──────────────────────────────────────────────

def estimate_market_size(idea_summary: str, target_audience: str, llm, market_data: str = "") -> str:
    """
    Pazar büyüklüğü tahmini yapar.
    Kategori bazlı araştırma destekli TAM aralıkları ile LLM hallüsinasyonu önlenir.
    Markdown tablosu döner.
    """

    market_context = ""
    if market_data and market_data.strip():
        market_context = f"""
Pazar Araştırması Verileri (bu kaynaklardan TAM hesabı yap):
{market_data[:1200]}

"""

    prompt = f"""Aşağıdaki Micro-SaaS fikri için TAM/SAM/SOM tahminlerini yap.

Fikir: {idea_summary}
Hedef Kitle: {target_audience}
{market_context}
ZORUNLU KURALLAR:
1. Her rakam için hesaplama formülünü göster: "X kişi × $Y/yıl = $Z"
2. Formülün temelindeki varsayımı belirt (örn. "Dünya genelinde ~2M serbest fotoğrafçı olduğu tahmin edilmektedir").
3. Yukarıda pazar araştırması verisi varsa onu kullan — gerçek rakamları tercih et.
4. Eğer hiç güvenilir veri yoksa bottom-up hesap yap; tamamen imkânsızsa ilgili alanı null bırak.
5. "Genel SaaS pazarı $X" gibi belirsiz referanslara dayanma — kendi sektöre özgü hesapla.

SADECE aşağıdaki JSON formatında yanıt ver, başka hiçbir şey yazma:
{{"tam": "$2.1B", "tam_formula": "~3M düğün fotoğrafçısı × $700/yıl = $2.1B", "tam_assumption": "Dünya genelinde ~3M düğün fotoğrafçısı olduğu tahmin edilmektedir", "sam": "$340M", "sam_formula": "TAM'ın ~%16'sı: dijital araç kullanan ABD+AB pazarı ~480K kişi × $700/yıl = $336M", "som": "$850K", "som_formula": "İlk yıl 1.500 müşteri × $49/ay × 12 = $882K", "confidence": "düşük"}}

tam/sam/som null olabilir. confidence: "yüksek" (kendi sektörüne özgü kanıtlı veri), "orta" (yaklaşık ama mantıklı), "düşük" (büyük ölçüde varsayım) olabilir."""

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

    confidence = data.get("confidence", "düşük")
    confidence_note = {
        "yüksek": "Tahmin referans veriye dayanmaktadır.",
        "orta": "Tahmin yaklaşık varsayımlara dayanmaktadır, bağımsız doğrulama önerilir.",
        "düşük": "Bu tahmin büyük ölçüde varsayıma dayalıdır. Yatırım kararı öncesi bağımsız pazar araştırması yapılmalıdır.",
    }.get(confidence, "Güven düzeyi bilinmiyor.")

    markdown = f"""

---

## Pazar Büyüklüğü Tahmini

| Metrik | Sonuç | Hesaplama Formülü | Varsayım |
|--------|-------|-------------------|----------|
| TAM (Toplam Adreslenebilir Pazar) | {data.get('tam') or 'veri yok'} | {data.get('tam_formula') or '-'} | {data.get('tam_assumption') or '-'} |
| SAM (Ulaşılabilir Pazar) | {data.get('sam') or 'veri yok'} | {data.get('sam_formula') or '-'} | — |
| SOM (İlk Yıl Gerçekçi Hedef) | {data.get('som') or 'veri yok'} | {data.get('som_formula') or '-'} | — |

Güven düzeyi: **{confidence}** — {confidence_note}
"""
    return markdown


# ──────────────────────────────────────────────
# C.3: Startup Mezarlığı (Failure Check)
# ──────────────────────────────────────────────

def check_startup_graveyard(idea_summary: str, llm, user_category: str = "", target_category: str = "") -> str:
    """
    Benzer başarısız girişimleri arar; her biri için ne denedi / ne kadar ilerledi /
    tam neden kapandı / bu fikre özel uyarı üretir.
    """
    client = _get_tavily_client()
    if not client:
        return ""

    BIG_COMPANIES = {
        "openai", "google", "meta", "microsoft", "apple", "amazon", "netflix",
        "uber", "airbnb", "twitter", "x.com", "adobe", "salesforce", "oracle",
        "sora", "gemini", "claude", "chatgpt", "copilot", "midjourney",
    }

    niche = target_category or user_category or idea_summary
    # Post-mortem ve founder açıklaması odaklı sorgular
    queries = [
        f'"{niche}" startup "post-mortem" OR "why we failed" OR "lessons learned" founder',
        f'{niche} SaaS "we shut down" OR "shutting down" OR "couldn\'t find product market fit" site:indiehackers.com OR site:news.ycombinator.com',
        f'{niche} startup failed 2021 2022 2023 2024 "ran out of runway" OR "not enough customers" OR "low retention" OR "high churn"',
        f'site:producthunt.com {niche} "no longer" OR "discontinued" OR "sunsetting" startup',
        f'{niche} indie hacker "gave up" OR "killed" OR "sunset" product 2022 2023 2024',
    ]

    all_results = []
    seen_urls: set = set()

    for query in queries:
        if len(all_results) >= 8:
            break
        try:
            resp = client.search(query=query, search_depth="advanced", max_results=4)
            for r in resp.get("results", []):
                url = r.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "").lower()
                all_results.append({
                    "title": r.get("title", ""),
                    "content": r.get("content", "")[:500],   # 300 → 500 karakter
                    "url": url,
                    "domain": domain,
                })
        except Exception as e:
            print(f"[Validator] Graveyard sorgu hatası: {e}")

    # Büyük şirket filtresi
    filtered = []
    for r in all_results:
        text = (r.get("title", "") + " " + r.get("content", "")).lower()
        if any(name in text or name in r.get("domain", "") for name in BIG_COMPANIES):
            print(f"[Validator] 🚫 Büyük şirket filtrelendi: {r['title'][:60]}")
        else:
            filtered.append(r)
    all_results = filtered

    if not all_results:
        return """

---

## Benzer Başarısız Girişimler

Erken aşama girişimler arasında bu fikre benzer, kapatılmış bir ürüne dair veri bulunamadı. Bu, denenmemiş alan anlamına gelebilir — önceki hatalardan öğrenmek yerine kendi müşteri keşfinizi yapmanız gerekecek.
"""

    results_text = "\n\n".join([
        f"[{i+1}] Başlık: {r['title']}\n    Kaynak: {r['domain']} | URL: {r['url']}\n    İçerik: {r['content']}"
        for i, r in enumerate(all_results)
    ])

    prompt = f"""Aşağıdaki arama sonuçları "{idea_summary}" fikrine benzer girişimlerin başarısızlık hikayeleri veya post-mortem yazıları içeriyor.

Arama Sonuçları:
{results_text}

GÖREV:
1. Büyük teknoloji şirketlerini (OpenAI, Google, Meta, Microsoft vb.) tamamen yoksay.
2. Kapanma/başarısızlık kanıtı AÇIKÇA belirtilmeyen sonuçları listeye ekleme — uydurma yapma.
3. Gerçekten uygun 2-4 bağımsız girişim bul. Uygun yoksa "YOK" yaz.
4. Her girişim için DÖRT boyutu Türkçe yaz:
   - Ne denedi: Ürünün amacı ve hedef kitlesi (1 cümle)
   - Ne kadar ilerledi: Açıklanan metrikler (müşteri sayısı, MRR, süre — bilgi yoksa "Kamuya açık veri yok")
   - Neden kapandı: Spesifik sebep — dağıtım sorunu / PMF yok / yüksek churn / fiyatlandırma / rakip baskısı / teknik borç (1-2 cümle, arama sonucundaki kanıta dayan)
   - Bu fikre uyarı: "{idea_summary}" geliştirirken bu hatadan nasıl kaçınılır (1 somut cümle)
5. Son olarak tüm örneklerden 1 ortak, pratik ders çıkar.

FORMAT (YALNIZCA TÜRKÇE, emoji yok):
**[Girişim Adı] (~[Yıl])**
- Ne denedi: ...
- Ne kadar ilerledi: ...
- Neden kapandı: ...
- Bu fikre uyarı: ...

**Ortak Ders:** ..."""

    try:
        analysis = llm.invoke([HumanMessage(content=prompt)]).content.strip()

        if analysis.upper().startswith("YOK") and len(analysis) < 80:
            return """

---

## Benzer Başarısız Girişimler

Bağımsız kurucuların yürüttüğü, bu fikre benzer girişimlere dair kamuya açık başarısızlık verisi bulunamadı. Bu, erken pazar doğrulamasının önemini artırır.
"""

        analysis_lower = analysis.lower()
        big_found = any(name in analysis_lower for name in BIG_COMPANIES)
        note = "\n_Not: Büyük şirket örnekleri analiz dışı bırakılmıştır._" if big_found else ""

        return f"""

---

## Benzer Başarısız Girişimler

Bu fikre yakın alanda daha önce denenmiş girişimler tespit edildi. Her birinin neden başarısız olduğunu ve sizin için ne anlama geldiğini aşağıda bulabilirsiniz.

{analysis}{note}
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
    from lib.llm import get_llm

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
    tavily_client = _get_tavily_client()
    try:
        if tavily_client:
            resp = tavily_client.search(
                query=f"{idea_summary} saas software alternative",
                search_depth="basic",
                max_results=5,
            )
            existing_competitors = len(resp.get("results", []))
        else:
            existing_competitors = -1
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

    # 4. TAM/SAM/SOM (C.2) — market_data'yı da geçiriyoruz
    print("[Validator]   📈 Pazar büyüklüğü tahmin ediliyor...")
    market_data_ctx = state.get("market_data", "") or ""
    market_size_md = estimate_market_size(idea_summary, target_audience, llm, market_data=market_data_ctx)

    # 5. Startup Mezarlığı (C.3)
    print("[Validator]   ⚰️ Startup mezarlığı kontrol ediliyor...")
    graveyard_md = check_startup_graveyard(
        idea_summary, llm,
        user_category=state.get("user_category", ""),
        target_category=state.get("target_category", ""),
    )

    # Tüm validation detaylarını birleştir
    competitor_note = f"{existing_competitors} rakip bulundu" if existing_competitors >= 0 else "rakip verisi alınamadı"
    api_note = "erişilebilir" if api_accessible else "erişim sorunu var"

    validation_details = f"""

---

## Bağımsız Doğrulama Notları

Fizibilite Skoru: **{scorecard['total']}/50** — {scorecard['label']}
Rakip taraması: {competitor_note}
Model API durumu: {api_note}

{scorecard['markdown']}
{market_size_md}
{graveyard_md}
"""

    print(f"[Validator] Skor: {scorecard['total']}/50 ({scorecard['label']})")

    # V7: final_report sonuna scorecard bilgilerini ekliyoruz ki ekranda görünsün!
    updated_report = report + "\n" + validation_details.strip()

    return {**state, "validation_details": validation_details.strip(), "final_report": updated_report}
