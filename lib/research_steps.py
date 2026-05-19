"""
Ortak Araştırma Adımları
deep_agent.py ve orchestrator.py'nin ~%80 aynı olan fonksiyonlarını barındırır.
Bu modülü düzenlemek, her iki agent'ı aynı anda günceller.
"""

from __future__ import annotations

import json
from typing import Optional
from langchain_core.messages import HumanMessage

from lib.llm import get_llm
from lib.tavily_client import get_tavily_client


# ──────────────────────────────────────────────
# 1. Tavily: Trending Modeller + Mevcut App'ler
# ──────────────────────────────────────────────

def fetch_models_and_apps(category: str) -> tuple[list[dict], list[dict]]:
    """
    Tavily ile kategori için trending AI modelleri ve SaaS uygulamaları çeker.

    Returns:
        (trending_models, known_apps) — her biri dict listesi:
          {"name", "description", "category", "source", "url"}
    """
    trending_models: list[dict] = []
    known_apps: list[dict] = []

    try:
        tavily = get_tavily_client()

        model_results = tavily.search(
            f"trending AI models tools for {category} 2024 2025",
            max_results=8,
            search_depth="basic",
        )
        for r in model_results.get("results", []):
            trending_models.append({
                "name": r.get("title", ""),
                "description": r.get("content", "")[:300],
                "category": category,
                "source": "tavily_web",
                "url": r.get("url", ""),
            })

        app_results = tavily.search(
            f"SaaS startups apps using {category} AI",
            max_results=8,
            search_depth="basic",
        )
        for r in app_results.get("results", []):
            known_apps.append({
                "name": r.get("title", ""),
                "description": r.get("content", "")[:300],
                "category": category,
                "source": "tavily_web",
                "url": r.get("url", ""),
            })
    except Exception as e:
        print(f"[ResearchSteps] Tavily fetch hatası: {e}")

    return trending_models, known_apps


# ──────────────────────────────────────────────
# 2. SEO Verisi → Prompt Metni
# ──────────────────────────────────────────────

def build_seo_text(seo_data: dict) -> str:
    """
    Google Trends / SEO sözlüğünü prompt'a hazır Türkçe metne dönüştürür.
    Boş dict gelirse boş string döner.
    """
    if not seo_data:
        return ""

    seo_lines: list[str] = []
    for kw, d in list(seo_data.items())[:3]:
        direction = d.get("trend_direction", "stable")
        direction_emoji = "↑" if direction == "rising" else ("↓" if direction == "declining" else "→")
        seo_lines.append(
            f'  • "{kw}" → İlgi: {d.get("interest_score", "?")} /100 '
            f'({direction_emoji} {d.get("change_pct", "0%")})'
        )
        rising = d.get("related_rising", [])[:3]
        if rising:
            seo_lines.append(f'    Yükselen aramalar: {", ".join(rising)}')

    return "\n📈 Google Trends / Arama Hacmi:\n" + "\n".join(seo_lines)


def build_seo_memo_text(seo_data: dict) -> str:
    """Memo (rapor) bölümü için daha kısa SEO özeti."""
    if not seo_data:
        return ""

    seo_lines: list[str] = []
    for kw, d in list(seo_data.items())[:3]:
        direction = d.get("trend_direction", "stable")
        direction_emoji = "↑" if direction == "rising" else ("↓" if direction == "declining" else "→")
        seo_lines.append(
            f'- "{kw}": İlgi {d.get("interest_score", "?")} /100, '
            f'{direction_emoji} {d.get("change_pct", "0%")}'
        )

    return "\nGoogle Trends Verileri:\n" + "\n".join(seo_lines)


# ──────────────────────────────────────────────
# 3. Brainstorm Prompt Oluşturma
# ──────────────────────────────────────────────

def build_brainstorm_prompt(
    category: str,
    models_text: str,
    apps_text: str,
    auto_text: str,
    gap_text: str,
    seo_text: str,
    research_summary: str = "",
) -> str:
    """
    YC yatırımcısı rolünde 3 Micro-SaaS hipotezi üretecek prompt oluşturur.
    Hem deep_agent hem orchestrator için aynı şablon kullanılır.
    """
    auto_block = (
        f"\nOTOMASYON İSTİHBARATI (n8n/Zapier/Make.com Forumlarından):\n{auto_text}\n"
        "ÖNEMLİ: Yukarıdaki otomasyon talepleri, GERÇEK İNSANLARIN gerçekten otomasyona "
        "çevirmek isteyip de yapamadığı işlerdir."
    ) if auto_text else ""

    gap_block = (
        f"\nPRODUCT HUNT BOŞLUK ANALİZİ (Mevcut Ürünlerin Zayıf Noktaları):\n{gap_text}\n"
        "ÖNEMLİ: Bu boşluklar, kullanıcıların mevcut ürünlerden memnun olmadığı noktaları "
        "gösterir. Burası altın madeni."
    ) if gap_text else ""

    research_block = f"\nARAŞTIRMA ÖZETİ: {research_summary}\n" if research_summary else ""

    return f"""KULLANICININ SEÇTİĞİ ANA KATEGORİ: {category}
{research_block}
Pazardaki İlgili AI Modelleri: {models_text or "Bu nişte kullanılabilecek top-tier AI modellerini düşün."}
Mevcut Kazanan Uygulamalar: {apps_text or "Bu piyasadaki mevcut yazılımların yetersizliğini (boşluğu) hayal et."}
{auto_block}
{gap_block}
{seo_text}

Sen Y Combinator'dan acımasız bir yatırımcısın. Görevin {category} odağında 3 farklı Micro-SaaS 'Saldırı Açısı' (Hypothesis) yazmak.

KATI KURALLAR (Friction Economy):
1. B2C (Tüketici/İzleyici) fikirleri KESİNLİKLE YASAKTIR. Sadece para ödeme gücü olan Profesyoneller, C-Level, Freelancer'lar, Ajanslar veya geliri olan İçerik Üreticileri hedeflenmeli.
2. "Vitamin" Reddedilecek: Pazardaki "Kanal analizi", "Dashboard" gibi jenerik fikirleri ÇÖPE AT. Sadece insanların manuel olarak 5-10 saatini çalan belirli bir angarya işi (Painkiller) çözen, tek tıklamalık AI otomasyonları üret.

Format (kesinlikle bu formata uy):
Açı 1: [Niş Hedef Kitle] - [Manuel Acı Noktası] - [AI Otomasyon Çözümü]
Açı 2: [Niş Hedef Kitle] - [Manuel Acı Noktası] - [AI Otomasyon Çözümü]
Açı 3: [Niş Hedef Kitle] - [Manuel Acı Noktası] - [AI Otomasyon Çözümü]"""


# ──────────────────────────────────────────────
# 4. Angle Parsing
# ──────────────────────────────────────────────

def parse_angles(response: str) -> list[str]:
    """
    LLM çıktısından 'Açı 1/2/3:' satırlarını ayıklar.
    Format bozuksa response'u 3 parçaya böler (fallback).
    """
    angles: list[str] = []
    for line in response.split("\n"):
        stripped = line.strip()
        if stripped.startswith("Açı "):
            part = stripped.split(":", 1)[1].strip() if ":" in stripped else stripped
            angles.append(part)

    if len(angles) < 3:
        # Fallback: ilk 3 × 100 karakter
        angles = [response[:100], response[100:200], response[200:300]]

    return angles[:3]


# ──────────────────────────────────────────────
# 5. Web Araştırması (Rakip + Şikayet)
# ──────────────────────────────────────────────

def run_web_research(angles: list[str], max_results_per_query: int = 3) -> list[dict]:
    """
    Her açı için Tavily ile rakip ve şikayet araması yapar.

    Returns:
        [{"angle", "competitor_data", "complaint_data"}, ...]
    """
    results: list[dict] = []
    try:
        tavily = get_tavily_client()
    except EnvironmentError as e:
        print(f"[ResearchSteps] Tavily bağlantısı yok: {e}")
        return results

    for i, angle in enumerate(angles[:3]):
        try:
            q1 = f"{angle[:60]} SaaS tools software competitors"
            q2 = f"{angle[:60]} software reddit complaints issues"
            res1 = tavily.search(q1, max_results=max_results_per_query, search_depth="basic").get("results", [])
            res2 = tavily.search(q2, max_results=max_results_per_query, search_depth="basic").get("results", [])
            results.append({
                "angle": angle,
                "competitor_data": res1,
                "complaint_data": res2,
            })
            print(f"  [ResearchSteps] ✅ Açı {i + 1} web araştırması tamamlandı")
        except Exception as e:
            print(f"  [ResearchSteps] ⚠️ Açı {i + 1} web araştırma hatası: {e}")

    return results


# ──────────────────────────────────────────────
# 6. Rakip Analizi (LLM)
# ──────────────────────────────────────────────

def analyze_competitors(web_results: list[dict]) -> str:
    """Web araştırması sonuçlarını LLM ile özetler."""
    if not web_results:
        return "Yeterli rakip verisi bulunamadı."

    raw_data = json.dumps(web_results)[:4000]
    prompt = f"""Aşağıdaki ham web arama sonuçlarını analiz et. Pazardaki mevcut rakipleri, fiyat aralıklarını ve kullanıcıların en çok şikayet ettiği zayıf yönleri özetle.

Ham Veri: {raw_data}

Net ve anlaşılır bir rapor formatında ver."""

    try:
        return get_llm(temp=0.1).invoke([HumanMessage(content=prompt)]).content
    except Exception as e:
        print(f"[ResearchSteps] Rakip analiz hatası: {e}")
        return "Rakip analizi tamamlanamadı."
