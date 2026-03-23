import os
from fpdf import FPDF
import markdown
import re

class ReportPDF(FPDF):
    def header(self):
        # Logo placeholder or Text Logo
        self.set_font("helvetica", "B", 15)
        self.set_text_color(139, 92, 246) # Purple-ish SaaS brand color
        self.cell(0, 10, "STaRTUP iDEA FINDER V6", border=False, align="R", ln=1)
        self.set_font("helvetica", "I", 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "Friction Economy & B2B Intelligence Report", border=False, align="R", ln=1)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Startup Idea Finder (c)", align="C")

def generate_report_pdf(scan_data: dict) -> bytes:
    """
    Supabase'den gelen scan verisini (dict) alır, şık bir PDF'e çevirir 
    ve byte array olarak döner.
    """
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # 1. Başlık ve Kategori
    category = scan_data.get("category", "Bilinmeyen Kategori")
    mode = scan_data.get("mode", "Tarama").upper()
    
    pdf.set_font("helvetica", "B", 24)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 10, f"{category} Pazar Analizi")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f" Tarama Modu: {mode}  |  Bulunan İş Kanıtları (Leads): {scan_data.get('leads_count', 0)}", fill=True, ln=1)
    pdf.ln(10)
    
    # 2. Ana Rapor İçeriği (Markdown Parsing)
    # FPDF2 HTML rendering destekler, Markdown'ı basit HTML'e çevirip PDF'e besleyebiliriz.
    raw_markdown = scan_data.get("report_preview") or ""
    # Full report içerisinde daha detaylı veri varsa onu kullan (Eğer front-end preview'le sınırlandırılmışsa)
    full_report_data = scan_data.get("full_report")
    if isinstance(full_report_data, dict):
        raw_markdown = full_report_data.get("final_report", raw_markdown)

    # Markdown'ı basit bir HTML'e dönüştür (fpdf html parse edebiliyor)
    html_content = markdown.markdown(raw_markdown)
    
    # Emojileri temizle (FPDF standart fontlarla emoji basarken hata verir)
    html_content = re.sub(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u011E\u011F\u0130\u0131\u015E\u015F\u0152\u0153\u0178ÇçÖöÜü]+', '', html_content)
    
    pdf.set_font("helvetica", "", 11)
    
    try:
        pdf.write_html(html_content)
    except Exception as e:
        print(f"HTML Parse Hatası: {e}")
        # B Planı: Düz metin olarak bas
        pdf.multi_cell(0, 6, re.sub('<[^<]+>', '', html_content))
    
    pdf.ln(15)
    
    # 3. Bulunan Müşteri Adayları (Leads) Tablo Halinde
    leads = []
    if isinstance(full_report_data, dict) and full_report_data.get("buyer_leads"):
        leads = full_report_data.get("buyer_leads")
        
    if leads:
        pdf.add_page()
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "Doğrulanmış İş Sinyalleri (Buyer Leads)", ln=1)
        pdf.ln(5)
        
        for idx, lead in enumerate(leads, 1):
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(139, 92, 246)
            pdf.cell(0, 8, f"{idx}. {lead.get('source', 'Unknown')} Sinyali", ln=1)
            
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(30, 30, 30)
            target_title = re.sub(r'[^\x00-\x7F\x80-\xFF\u0100-\u017FüğşiçöÜĞŞİÇÖ]+', '', lead.get('title', ''))
            pdf.multi_cell(0, 6, f"Başlık: {target_title}")
            
            pdf.set_font("helvetica", "I", 10)
            target_desc = re.sub(r'[^\x00-\x7F\x80-\xFF\u0100-\u017FüğşiçöÜĞŞİÇÖ]+', '', lead.get('desc', ''))
            pdf.multi_cell(0, 6, f"Detay: {target_desc}")
            
            sales_pitch = lead.get('sales_pitch')
            if sales_pitch:
                pdf.ln(2)
                pdf.set_font("helvetica", "", 10)
                pdf.set_text_color(100, 100, 100)
                pitch_clean = re.sub(r'[^\x00-\x7F\x80-\xFF\u0100-\u017FüğşiçöÜĞŞİÇÖ]+', '', sales_pitch)
                pdf.multi_cell(0, 5, f"DM Şablonu:\n{pitch_clean}")
                
            pdf.ln(8)
            pdf.set_text_color(0, 0, 0) # Reset color

    # Byte olarak çıktı ver
    return pdf.output()
