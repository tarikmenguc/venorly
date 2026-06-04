"""
Report Actions — Venorly
Rapor tamamlandiktan sonra frontend'in render edecegi CTA (call-to-action) listesini uretir.
Frontend bu array'i alir ve "Simdi ne yaparsam?" sorusunu gorsel olarak cevaplar.

Bagimlilik yok — sadece saf Python, state dict'lerini okur.
"""

from typing import Any


def compute_actions(scan_id: str, report_json: dict, buyer_leads: list) -> list:
    """
    Rapor durumuna gore kullaniciya sunulacak aksiyon listesi uretir.

    Returns:
        [
          {"type": str, "url": str, "label": str, "count": int|None, "priority": int},
          ...
        ]
        priority: 1=en onemli, kucuk sayi = on siraya gelir.
    """
    actions = []

    if not scan_id or not report_json:
        return actions

    es = report_json.get("executive_summary") or {}
    decision = es.get("decision", "")
    score = es.get("weighted_score") or 0
    has_pivot = bool(report_json.get("pivot_suggestions"))
    lead_count = len(buyer_leads) if buyer_leads else 0

    # 1. Buyer leads (en degerli aksiyon — gercek insanlar)
    if lead_count > 0:
        actions.append({
            "type":     "buyer_leads",
            "url":      None,          # frontend kendi modal'ini acar
            "label":    f"{lead_count} Potansiyel Musteri",
            "sublabel": "Hazir DM sablonu ile ulasabilirsiniz",
            "count":    lead_count,
            "priority": 1,
        })

    # 2. Landing page (validation oncesi deploy edilebilir)
    if report_json.get("validation", {}).get("waitlist_h1"):
        actions.append({
            "type":     "landing_page",
            "url":      f"/api/scans/{scan_id}/landing-page",
            "label":    "Landing Page Indir",
            "sublabel": "Deploy-ready tek dosya HTML",
            "count":    None,
            "priority": 2,
        })

    # 3. Pitch deck (yatirimci gorusmesi icin)
    if decision in ("Go", "Hold") and float(score) >= 30:
        actions.append({
            "type":     "pitch_deck",
            "url":      f"/api/scans/{scan_id}/pitch-deck",
            "label":    "Pitch Deck Olustur",
            "sublabel": "10 slide yatirimci sunumu",
            "count":    None,
            "priority": 3,
        })

    # 4. PDF raporu
    actions.append({
        "type":     "pdf",
        "url":      f"/api/scans/{scan_id}/pdf",
        "label":    "PDF Rapor Indir",
        "sublabel": "Tam fizibilite analizi",
        "count":    None,
        "priority": 4,
    })

    # 5. Pivot onerisi (dusuk skor durumunda)
    if has_pivot:
        actions.append({
            "type":     "pivot_suggestions",
            "url":      None,          # frontend rapor icinde gosterir
            "label":    "3 Pivot Onerisi Goster",
            "sublabel": "Farkli hedef kitle veya is modeli",
            "count":    3,
            "priority": 5,
        })

    # Prioritye gore sirala
    actions.sort(key=lambda x: x["priority"])
    return actions
