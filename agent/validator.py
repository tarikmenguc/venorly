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

def check_startup_graveyard(idea_summary: str, llm) -> str:
    """
    Küçük, erken aşama girişimlere odaklanarak benzer başarısız ürünleri arar.
    ProductHunt, Indie Hackers, HackerNews, BetaList öncelikli.
    Büyük şirket örnekleri (OpenAI, Google, Meta vb.) filtrelenir.
    """
    client = _get_tavily_client()
    if not client:
        return ""

    # Büyük şirket filtresi — LLM analizi için
    BIG_COMPANIES = {
        "openai", "google", "meta", "microsoft", "apple", "amazon", "netflix",
        "uber", "airbnb", "twitter", "x.com", "adobe", "salesforce", "oracle",
        "sora", "gemini", "claude", "chatgpt", "copilot", "midjourney",
    }

    # Çoklu sorgu stratejisi: küçük girişim odaklı, İngilizce
    queries = [
        f'small startup {idea_summary} failed shut down site:indiehackers.com OR site:news.ycombinator.com',
        f'{idea_summary} product "we are shutting down" OR "shutting down" OR "failed to get traction" indie',
        f'{idea_summary} SaaS startup failed "not enough customers" OR "runway" OR "couldn\'t find PMF" 2022 2023 2024',
        f'site:producthunt.com {idea_summary} discontinued OR abandoned OR "no longer available"',
    ]

    all_results = []
    seen_domains: set = set()

    for query in queries:
        if len(all_results) >= 6:
            break
        try:
            resp = client.search(query=query, search_depth="advanced", max_results=4)
            for r in resp.get("results", []):
                url = r.get("url", "")
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "").lower()
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)
                all_results.append({
                    "title": r.get("title", ""),
                    "content": r.get("content", "")[:300],
                    "url": url,
                    "domain": domain,
                })
        except Exception as e:
            print(f"[Validator] Graveyard sorgu hatası: {e}")

    # Büyük şirket içeren sonuçları LLM'ye göndermeden önce filtrele
    filtered_results = []
    for r in all_results:
        text = (r.get('title', '') + ' ' + r.get('content', '')).lower()
        domain_lower = r.get('domain', '').lower()
        if any(name in text or name in domain_lower for name in BIG_COMPANIES):
            print(f"[Validator] 🚫 Büyük şirket filtrelendi: {r['title'][:60]}")
        else:
            filtered_results.append(r)
    all_results = filtered_results

    if not all_results:
        return """

---

## Benzer Başarısız Girişimler

Erken aşama girişimler arasında bu fikre benzer, kapatılmış bir ürüne dair veri bulunamadı. Bu tek başına güvence değildir — denenmemiş alan hem fırsat hem de kanıtsızlık anlamına gelir.
"""

    results_text = "\n".join([
        f"- {r['title']} ({r['domain']}): {r['content'][:200]}\n  URL: {r['url']}"
        for r in all_results
    ])

    prompt = f"""Aşağıda "{idea_summary}" fikrine benzer, daha önce denenmiş ve başarısız olmuş veya kapanmış ürünler/girişimler hakkında web araması sonuçları var.

Sonuçlar:
{results_text}

GÖREV:
1. Büyük teknoloji şirketlerini (OpenAI, Google, Meta, Microsoft, Sora, Gemini, Midjourney vb.) ve onların ürünlerini tamamen yoksay.
2. Yalnızca küçük veya orta ölçekli, bağımsız kurucuların yürüttüğü girişimleri listele.
3. Her biri için: ürün adı, tahmini kapanma yılı, kapanma sebebini 1 cümleyle Türkçe yaz.
4. Bu örneklerden 1 somut, pratik ders çıkar.
5. ÖNEMLI: Eğer arama sonuçlarında bir ürün için kapanma/başarısızlık kanıtı AÇIKÇA belirtilmiyorsa o ürünü listeye ekleme. Uydurma yapma.

Eğer büyük şirketler dışında gerçekten benzer başarısız bir girişim YOKSA, sadece "YOK" yaz.

YALNIZCA TÜRKÇE YAZ. Emoji kullanma. Format:
1. [Ürün/Girişim Adı] (~[Yıl]): [Kapanma sebebi — 1 cümle]
2. ...
Ders: [1 somut, pratik cümle]"""

    try:
        analysis = llm.invoke([HumanMessage(content=prompt)]).content.strip()

        # "YOK" yanıtı veya sadece büyük şirketler varsa
        if analysis.upper().startswith("YOK") and len(analysis) < 80:
            return """

---

## Benzer Başarısız Girişimler

Bağımsız kurucular tarafından yürütülen, bu fikre benzer küçük girişimlere dair başarısızlık verisi bulunamadı. Bu, erken pazar doğrulamasının önemini artırır — önceki deneyimlerden öğrenmek yerine kendi müşteri keşifinizi yapmanız gerekecek.
"""
        else:
            # Büyük şirket adı geçiyor mu kontrol et
            analysis_lower = analysis.lower()
            big_company_found = any(name in analysis_lower for name in BIG_COMPANIES)
            note = ""
            if big_company_found:
                note = "\n_Not: Büyük şirket örnekleri analiz dışı bırakılmıştır; yukarıdaki liste yalnızca bağımsız girişimleri kapsamaktadır._"

            return f"""

---

## Benzer Başarısız Girişimler

Bu fikre yakın alanda daha önce denenmiş, traction bulamadan kapanmış girişimler tespit edildi. Aşağıdaki örnekler, aynı yola çıkmadan önce göz önünde bulundurulmalıdır.

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
    graveyard_md = check_startup_graveyard(idea_summary, llm)

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
