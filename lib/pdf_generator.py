"""
PDF Rapor Uretici - Venorly
FeasibilityReport JSON'unu alir, A4 PDF'e cevirir.
Yapisal veriyi direkt okur; markdown parse veya write_html kullanmaz.
Unicode destegi icin system TTF font kullanir (Liberation Sans / Arial).
"""

import os
import re
from fpdf import FPDF

# -- FONT KURULUMU -------------------------------------------------

_FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    ("C:/Windows/Fonts/arial.ttf",   "C:/Windows/Fonts/arialbd.ttf"),
    ("C:/Windows/Fonts/calibri.ttf", "C:/Windows/Fonts/calibrib.ttf"),
    ("/Library/Fonts/Arial.ttf",     "/Library/Fonts/Arial Bold.ttf"),
]

_FONT_REGULAR = None
_FONT_BOLD = None
for _r, _b in _FONT_CANDIDATES:
    if os.path.exists(_r) and os.path.exists(_b):
        _FONT_REGULAR, _FONT_BOLD = _r, _b
        break

# -- RENK PALETI ---------------------------------------------------

C_BRAND  = (139, 92, 246)
C_DARK   = (30,  30,  30)
C_MEDIUM = (80,  80,  80)
C_LIGHT  = (150, 150, 150)
C_BG     = (245, 245, 250)
C_GREEN  = (34,  197, 94)
C_YELLOW = (234, 179, 8)
C_RED    = (239, 68,  68)
C_BAR_BG = (220, 220, 230)
C_BAR_FG = (139, 92,  246)

# -- YARDIMCI SINIF ------------------------------------------------

class VenorlyPDF(FPDF):

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        if _FONT_REGULAR and _FONT_BOLD:
            self.add_font("Main", "",  _FONT_REGULAR, uni=True)
            self.add_font("Main", "B", _FONT_BOLD,    uni=True)
            self._fn = "Main"
        else:
            self._fn = "Helvetica"

    def _set(self, size=10, bold=False, color=None):
        if color is None:
            color = C_DARK
        self.set_font(self._fn, "B" if bold else "", size)
        self.set_text_color(*color)

    def header(self):
        self._set(9, color=C_LIGHT)
        self.cell(0, 8, "Venorly - Startup Fizibilite Raporu", align="R",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*C_BRAND)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-14)
        self._set(8, color=C_LIGHT)
        self.cell(0, 8, f"Sayfa {self.page_no()}/{{nb}} | venorly.com", align="C")

    def section_title(self, text):
        self.ln(4)
        self._set(12, bold=True, color=C_BRAND)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*C_BRAND)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.l_margin + 60, self.get_y())
        self.ln(3)

    def kv_row(self, label, value, label_w=50):
        self._set(9, bold=True, color=C_MEDIUM)
        self.cell(label_w, 6, label + ":", new_x="RIGHT")
        self._set(9, color=C_DARK)
        self.multi_cell(0, 6, value or "-", new_x="LMARGIN", new_y="NEXT")

    def score_bar(self, label, score, max_score=100.0, width=110):
        ratio = min(1.0, max(0.0, float(score) / float(max_score)))
        bar_h = 5
        text_w = 58
        self._set(9, color=C_DARK)
        self.cell(text_w, bar_h + 1, label, new_x="RIGHT")
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*C_BAR_BG)
        self.rect(x, y, width, bar_h, "F")
        if ratio > 0:
            self.set_fill_color(*C_BAR_FG)
            self.rect(x, y, width * ratio, bar_h, "F")
        self.set_xy(x + width + 2, y)
        self._set(9, bold=True, color=C_DARK)
        self.cell(20, bar_h, f"{float(score):.0f}/100", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def decision_badge(self, decision):
        color = {"Go": C_GREEN, "Hold": C_YELLOW, "No-Go": C_RED}.get(decision, C_MEDIUM)
        self.set_fill_color(*color)
        self._set(13, bold=True, color=(255, 255, 255))
        self.cell(45, 10, f"  {decision}  ", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def confidence_badge(self, ci):
        ci = float(ci)
        if ci >= 0.75:
            color, label = C_GREEN,  "Yuksek Guven"
        elif ci >= 0.50:
            color, label = C_YELLOW, "Orta Guven"
        else:
            color, label = C_RED,    "Dusuk Guven"
        self.set_fill_color(*color)
        self._set(10, bold=True, color=(255, 255, 255))
        self.cell(65, 8, f" Guven Endeksi: {ci:.0%} - {label} ",
                  fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def table_header(self, cols):
        self.set_fill_color(*C_BRAND)
        self._set(9, bold=True, color=(255, 255, 255))
        for title, w in cols:
            self.cell(w, 7, title, border=0, fill=True, new_x="RIGHT")
        self.ln()

    def table_row(self, cells, shade=False):
        if shade:
            self.set_fill_color(*C_BG)
        self._set(9, color=C_DARK)
        for text, w in cells:
            self.cell(w, 6, (text or "-")[:55], border=0, fill=shade, new_x="RIGHT")
        self.ln()

    def bullet(self, text, indent=4):
        self._set(9, color=C_DARK)
        self.set_x(self.l_margin + indent)
        self.multi_cell(0, 6, "- " + text, new_x="LMARGIN", new_y="NEXT")


def _clean(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()


# -- ANA FONKSIYON -------------------------------------------------

def generate_report_pdf(scan_data):
    """scan_data (Supabase'den dict) -> PDF bytes"""
    pdf = VenorlyPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    category = _clean(scan_data.get("category", "Bilinmeyen Kategori"))
    mode     = _clean(scan_data.get("mode", "discover")).upper()
    full     = scan_data.get("full_report") or {}
    rj       = (full.get("report_json") if isinstance(full, dict) else None) or {}

    # Kapak
    title = _clean(rj.get("idea_title") or category)
    pdf._set(20, bold=True, color=C_BRAND)
    pdf.multi_cell(0, 10, title + " Analizi", new_x="LMARGIN", new_y="NEXT")
    pdf._set(10, color=C_MEDIUM)
    pdf.cell(0, 6, f"Mod: {mode}  |  Kategori: {category}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    if not rj:
        _render_fallback(pdf, full, scan_data)
        return bytes(pdf.output())

    # Bolum 1: Yonetici Ozeti
    pdf.section_title("1. Yonetici Ozeti")
    es = rj.get("executive_summary") or {}
    pdf.decision_badge(_clean(es.get("decision", "-")))

    for field, label in [
        ("weighted_score",        "Agirlikli Skor"),
        ("market_attractiveness", "Pazar Cekiciligi"),
        ("technical_barrier",     "Teknik Fizibilite"),
        ("unit_economics",        "Birim Ekonomisi"),
        ("gtm_ease",              "Pazara Erisim"),
    ]:
        val = es.get(field)
        if val is not None:
            pdf.score_bar(label, float(val))

    lof = es.get("leap_of_faith") or []
    if lof:
        pdf.ln(2)
        pdf._set(9, bold=True, color=C_MEDIUM)
        pdf.cell(0, 6, "Kritik Varsayimlar:", new_x="LMARGIN", new_y="NEXT")
        for item in lof[:5]:
            pdf.bullet(_clean(item))

    ci = rj.get("confidence_index")
    if ci is not None:
        pdf.ln(2)
        pdf.confidence_badge(ci)

    # Bolum 2: Pazar Analizi
    pdf.section_title("2. Pazar Analizi")
    m = rj.get("market") or {}
    tam = _clean(m.get("tam"))
    if tam:
        formula = _clean(m.get("tam_formula"))
        pdf._set(9, color=C_DARK)
        pdf.multi_cell(0, 6, "TAM: " + tam + (f"  ({formula})" if formula else ""),
                       new_x="LMARGIN", new_y="NEXT")
    for key, label in [("sam", "SAM"), ("som", "SOM"), ("cagr", "CAGR")]:
        val = _clean(m.get(key))
        if val:
            pdf.kv_row(label, val, label_w=20)
    if m.get("macro_signals"):
        pdf.ln(2)
        pdf._set(9, color=C_MEDIUM)
        pdf.multi_cell(0, 6, _clean(m["macro_signals"]), new_x="LMARGIN", new_y="NEXT")

    # Bolum 3: Rekabet
    pdf.section_title("3. Rekabet Istihbarati")
    c = rj.get("competition") or {}
    competitors = c.get("competitors") or []
    if competitors:
        col_w = [50, 90, 45]
        pdf.table_header([("Rakip", col_w[0]), ("Zayif Nokta", col_w[1]), ("Finansman", col_w[2])])
        for i, comp in enumerate(competitors[:8]):
            pdf.table_row([
                (_clean(comp.get("name")),     col_w[0]),
                (_clean(comp.get("weakness")), col_w[1]),
                (_clean(comp.get("funding")),  col_w[2]),
            ], shade=(i % 2 == 0))
    if c.get("gap_summary"):
        pdf.ln(3)
        pdf._set(9, bold=True, color=C_MEDIUM)
        pdf.cell(0, 6, "Bosluk Analizi:", new_x="LMARGIN", new_y="NEXT")
        pdf._set(9, color=C_DARK)
        pdf.multi_cell(0, 6, _clean(c["gap_summary"]), new_x="LMARGIN", new_y="NEXT")
    if c.get("entry_barriers"):
        pdf.kv_row("Giris Engelleri", _clean(c["entry_barriers"]))

    # Bolum 4: Teknik & Finansal
    pdf.section_title("4. Teknik & Finansal Fizibilite")
    t = rj.get("technical") or {}
    for key, label in [
        ("stack",         "Teknoloji Stack"),
        ("cpu_cost",      "CPU Maliyeti"),
        ("pricing_model", "Fiyatlandirma"),
        ("ltv",           "LTV"),
        ("cac",           "CAC"),
    ]:
        val = _clean(t.get(key))
        if val:
            pdf.kv_row(label, val)

    # Bolum 5: GTM
    pdf.section_title("5. Dogrulama & GTM")
    v = rj.get("validation") or {}
    for key, label in [
        ("value_prop",  "Deger Onermesi"),
        ("icp",         "ICP"),
        ("waitlist_h1", "Waitlist H1"),
        ("waitlist_h2", "Waitlist H2"),
        ("linkedin_dm", "LinkedIn DM"),
    ]:
        val = _clean(v.get(key))
        if val:
            pdf.kv_row(label, val)
    email_seq = v.get("cold_email_sequence") or []
    if email_seq:
        pdf.ln(2)
        pdf._set(9, bold=True, color=C_MEDIUM)
        pdf.cell(0, 6, "Cold Email Sekans:", new_x="LMARGIN", new_y="NEXT")
        for i, step in enumerate(email_seq[:5], 1):
            pdf.bullet(f"Adim {i}: {_clean(step)}")

    # Bolum 6: Kaynakca
    sources = [s for s in (rj.get("sources") or []) if s.get("url")]
    if sources:
        pdf.section_title("6. Kaynakca")
        for src in sources[:15]:
            title_s = _clean(src.get("title") or src.get("url"))
            url_s   = _clean(src.get("url", ""))
            pdf._set(8, color=C_MEDIUM)
            pdf.multi_cell(0, 5, f"- {title_s}  -  {url_s}", new_x="LMARGIN", new_y="NEXT")

    # Buyer Leads
    leads = (full.get("buyer_leads") or []) if isinstance(full, dict) else []
    if leads:
        pdf.add_page()
        pdf.section_title("Dogrulanmis Is Sinyalleri (Buyer Leads)")
        for i, lead in enumerate(leads[:20], 1):
            pdf._set(10, bold=True, color=C_BRAND)
            pdf.cell(0, 7, f"{i}. {_clean(lead.get('source', 'Sinyal'))}",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.kv_row("Baslik",      _clean(lead.get("title")))
            pdf.kv_row("Detay",       _clean(lead.get("desc")))
            if lead.get("sales_pitch"):
                pdf.kv_row("DM Sablonu", _clean(lead.get("sales_pitch")))
            pdf.ln(4)

    return bytes(pdf.output())


def _render_fallback(pdf, full, scan_data):
    """report_json yoksa final_report markdown satirlarini duz metin olarak basar."""
    if isinstance(full, dict):
        raw = full.get("final_report", "") or scan_data.get("report_preview", "")
    elif isinstance(full, str):
        raw = full
    else:
        raw = scan_data.get("report_preview", "")

    if not raw:
        pdf._set(10, color=C_MEDIUM)
        pdf.cell(0, 8, "Rapor verisi bulunamadi.", new_x="LMARGIN", new_y="NEXT")
        return

    for line in raw.split("\n"):
        line = _clean(line)
        if not line:
            pdf.ln(2)
            continue
        if line.startswith("## "):
            pdf.section_title(line[3:])
        elif line.startswith("# "):
            pdf._set(14, bold=True, color=C_BRAND)
            pdf.multi_cell(0, 8, line[2:], new_x="LMARGIN", new_y="NEXT")
        elif line.startswith("- ") or line.startswith("* "):
            pdf.bullet(re.sub(r'\*\*(.+?)\*\*', r'\1', line[2:]))
        else:
            pdf._set(9, color=C_DARK)
            pdf.multi_cell(0, 6, re.sub(r'\*\*(.+?)\*\*', r'\1', line),
                           new_x="LMARGIN", new_y="NEXT")
