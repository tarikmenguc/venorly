"""
Rapor şemaları — 6 bölümlü standart.
LLM JSON çıktısını bu modelle doğrula; eksik alan null olur.
"""

from typing import Optional
from pydantic import BaseModel


class GoNoGoScore(BaseModel):
    decision: str            # "Go" | "Hold" | "No-Go"
    weighted_score: Optional[float] = None   # 0-100
    market_attractiveness: Optional[float] = None   # % 30
    technical_barrier: Optional[float] = None       # % 30
    unit_economics: Optional[float] = None          # % 20
    gtm_ease: Optional[float] = None                # % 20
    leap_of_faith: Optional[list[str]] = None       # 3 kritik varsayım


class MarketAnalysis(BaseModel):
    tam: Optional[str] = None
    tam_formula: Optional[str] = None
    sam: Optional[str] = None
    som: Optional[str] = None
    cagr: Optional[str] = None
    macro_signals: Optional[str] = None  # Google Trends / Gartner kanıtları


class Competitor(BaseModel):
    name: str
    url: Optional[str] = None
    weakness: Optional[str] = None        # G2/Capterra'dan alıntı
    funding: Optional[str] = None


class CompetitionIntel(BaseModel):
    competitors: list[Competitor] = []
    gap_summary: Optional[str] = None     # Semantik kümeleme özeti
    entry_barriers: Optional[str] = None


class TechFeasibility(BaseModel):
    stack: Optional[str] = None           # model + servis + CDN
    cpu_cost: Optional[str] = None        # 1 işlem toplam maliyet
    ltv: Optional[str] = None
    cac: Optional[str] = None
    pricing_model: Optional[str] = None   # Freemium / Tiered


class GtmAssets(BaseModel):
    icp: Optional[str] = None             # Ideal Customer Profile
    cold_email_sequence: Optional[list[str]] = None
    linkedin_dm: Optional[str] = None
    waitlist_h1: Optional[str] = None
    waitlist_h2: Optional[str] = None
    value_prop: Optional[str] = None


class Source(BaseModel):
    url: str
    title: Optional[str] = None
    scraped_at: Optional[str] = None
    claim_id: Optional[str] = None


class FeasibilityReport(BaseModel):
    idea_title: str
    executive_summary: GoNoGoScore
    market: MarketAnalysis
    competition: CompetitionIntel
    technical: TechFeasibility
    validation: GtmAssets
    sources: list[Source] = []
    confidence_index: Optional[float] = None   # 0.0 - 1.0 (Auditor tarafından doldurulur)


def report_to_markdown(report: FeasibilityReport) -> str:
    """FeasibilityReport → Markdown (mevcut UI ile uyumlu)."""
    lines = [f"# {report.idea_title}", ""]

    # Bölüm 1
    g = report.executive_summary
    lines += [
        "## 1. Yönetici Özeti & Go/No-Go Skoru",
        f"**Karar:** {g.decision}",
        f"**Ağırlıklı Skor:** {g.weighted_score or 'hesaplanmadı'}",
    ]
    if g.leap_of_faith:
        lines += ["**Kritik Varsayımlar:**"]
        lines += [f"- {lof}" for lof in g.leap_of_faith]
    lines.append("")

    # Bölüm 2
    m = report.market
    lines += [
        "## 2. Makro Pazar Analizi",
        f"- TAM: {m.tam or 'kaynak bulunamadı'}" + (f" ({m.tam_formula})" if m.tam_formula else ""),
        f"- SAM: {m.sam or 'kaynak bulunamadı'}",
        f"- SOM: {m.som or 'kaynak bulunamadı'}",
        f"- CAGR: {m.cagr or 'bilinmiyor'}",
    ]
    if m.macro_signals:
        lines.append(m.macro_signals)
    lines.append("")

    # Bölüm 3
    c = report.competition
    lines += ["## 3. Rekabet İstihbaratı ve Boşluk Analizi"]
    for comp in c.competitors:
        lines.append(f"- **{comp.name}** ({comp.url or 'URL yok'}): {comp.weakness or ''}")
    if c.gap_summary:
        lines += ["", c.gap_summary]
    lines.append("")

    # Bölüm 4
    t = report.technical
    lines += [
        "## 4. Teknik & Finansal Fizibilite",
        f"- Stack: {t.stack or 'belirtilmedi'}",
        f"- CPU Maliyeti: {t.cpu_cost or 'bilinmiyor'}",
        f"- LTV: {t.ltv or 'bilinmiyor'} / CAC: {t.cac or 'bilinmiyor'}",
        f"- Fiyatlandırma: {t.pricing_model or 'belirtilmedi'}",
        "",
    ]

    # Bölüm 5
    v = report.validation
    lines += ["## 5. Doğrulama ve GTM"]
    if v.icp:
        lines.append(f"**ICP:** {v.icp}")
    if v.waitlist_h1:
        lines += [f"**Waitlist:** {v.waitlist_h1} — {v.waitlist_h2 or ''}"]
    if v.linkedin_dm:
        lines += ["**LinkedIn DM:**", v.linkedin_dm]
    lines.append("")

    # Bölüm 6
    lines += ["## 6. Kaynakça & Veri Denetleme"]
    if report.confidence_index is not None:
        lines.append(f"**Güven Endeksi:** {report.confidence_index:.0%}")
    for src in report.sources:
        lines.append(f"- [{src.title or src.url}]({src.url})")
    if not report.sources:
        lines.append("(Kaynakça henüz bağlanmadı — Auditor Agent bağlandığında doldurulacak)")

    return "\n".join(lines)
