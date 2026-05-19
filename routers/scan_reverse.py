"""
Scan — Reverse Modu
Rakip girişimi tersine mühendislik ile analiz eder.
"""

import json


def generate_reverse_events(req):
    """Reverse modu için SSE olay üreteci."""
    from agent.reverse_agent import reverse_agent

    initial_state = {
        "target_startup": req.target_startup,
        "startup_analysis": "",
        "competitors": [],
        "competitor_complaints": [],
        "complaint_clusters": "",
        "matching_models": [],
        "final_report": "",
        "error": None,
    }
    for event in reverse_agent.stream(initial_state):
        node_name = list(event.keys())[0]
        result = event[node_name]
        yield f"data: {json.dumps({'node': node_name, 'state': result})}\n\n"
