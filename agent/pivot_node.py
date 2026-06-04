"""
Pivot Node — Venorly
Fizibilite skoru dusukse (50/100 altinda) 3 alternatif pivot onerisi uretir.
Sadece buyer_leads_node'dan sonra, sadece dusuk skor durumunda calisir.

Bagimliliklar: lib/llm.py, langchain_core (ikisi zaten mevcut)
Dis etki: state["report_json"]["pivot_suggestions"] doldurulur.
"""

from typing import Any


_PIVOT_SCORE_THRESHOLD = 50  # Bu esik altinda pivot onerisi uretilir


def pivot_node(state: Any) -> Any:
    """
    Weighted score < 50 ise LLM'den 3 somut pivot onerisi ister.
    Her pivot: farkli hedef kitle, komsul problem veya yeni is modeli.
    """
    report_json = state.get("report_json") or {}
    es = report_json.get("executive_summary") or {}
    score = es.get("weighted_score")

    # Skor yeterince yuksekse pivot gerekmez
    if score is None or float(score) >= _PIVOT_SCORE_THRESHOLD:
        print(f"[PivotNode] Skor {score}/100 — pivot gerekmiyor.")
        return state

    print(f"[PivotNode] Skor {score}/100 — 3 pivot onerisi uretiliyor...")

    idea_title  = report_json.get("idea_title", "")
    decision    = es.get("decision", "")
    market      = report_json.get("market") or {}
    competition = report_json.get("competition") or {}
    technical   = report_json.get("technical") or {}

    prompt = (
        f'Asagidaki startup fikri fizibilite skorunda basarisiz oldu ({score}/100, karar: {decision}).\n\n'
        f'Fikir: {idea_title}\n'
        f'Pazar: TAM={market.get("tam","")} | CAGR={market.get("cagr","")}\n'
        f'Rekabet durumu: {competition.get("gap_summary","")[:200]}\n'
        f'Teknik stack: {technical.get("stack","")}\n\n'
        'GOREV: Bu fikrin neden dusuk skor aldigini analiz et ve 3 somut, farkli pivot onerisi sun.\n'
        'Her pivot icin:\n'
        '- Yeni hedef kitle VEYA komsul problem VEYA farkli is modeli sec\n'
        '- Mevcut altyapiyi (teknoloji) yeniden kullanabilecek sekilde tasarla\n'
        '- 1 cumlelik net aciklama yap\n\n'
        'FORMAT — sadece 3 satir, baska hicbir sey:\n'
        '1. [Pivot aciklamasi — 1 cumle]\n'
        '2. [Pivot aciklamasi — 1 cumle]\n'
        '3. [Pivot aciklamasi — 1 cumle]'
    )

    pivots = []
    try:
        from lib.llm import get_llm
        from langchain_core.messages import HumanMessage
        response = get_llm(temp=0.7).invoke([HumanMessage(content=prompt)]).content.strip()
        for line in response.split('\n'):
            line = line.strip()
            if line and line[0].isdigit() and '.' in line:
                pivot_text = line.split('.', 1)[-1].strip()
                if pivot_text:
                    pivots.append(pivot_text)
        pivots = pivots[:3]
        print(f"[PivotNode] {len(pivots)} pivot onerisi uretildi ✅")
    except Exception as e:
        print(f"[PivotNode] LLM hatasi (devam): {e}")
        return state

    if not pivots:
        return state

    # report_json'a ekle
    updated_json = {**report_json, "pivot_suggestions": pivots}

    _t = state.get("trace", []) + [{
        "node": "pivot",
        "score": score,
        "pivots_generated": len(pivots),
    }]
    return {**state, "report_json": updated_json, "trace": _t}
