"""
Scan — Deep Modu
DeepAgent ile derin araştırma + investment memo.
"""

import json


def generate_deep_events(req):
    """Deep modu için SSE olay üreteci."""
    from agent.deep_agent import deep_agent
    from scrapers.automation_intel import collect_automation_intelligence
    from scrapers.producthunt_gaps import find_product_gaps

    automation_signals = []
    try:
        automation_signals = collect_automation_intelligence(req.category)
    except Exception as e:
        print(f"[DeepMode] Otomasyon istihbaratı hatası (devam ediyor): {e}")

    product_gaps = []
    try:
        product_gaps = find_product_gaps(req.category)
    except Exception as e:
        print(f"[DeepMode] Product Hunt gap hatası (devam ediyor): {e}")

    initial_state = {
        "target_category": req.category,
        "trending_models": [],
        "known_apps": [],
        "brainstormed_angles": [],
        "web_research_results": [],
        "competitor_insights": "",
        "selected_angle": "",
        "investment_memo": "",
        "buyer_leads": [],
        "automation_signals": automation_signals,
        "product_gaps": product_gaps,
        "seo_data": {},
        "error": None,
    }
    for event in deep_agent.stream(initial_state):
        node_name = list(event.keys())[0]
        result = event[node_name]
        yield f"data: {json.dumps({'node': node_name, 'state': result})}\n\n"
