"""
Scan — Orchestrate Modu
Multi-agent orkestratör: Research → Analyst → GTM.
Supabase'e scan ve lead kaydeder.
"""

import json
import uuid

from lib.supabase_client import supabase


def generate_orchestrate_events(req):
    """Orchestrate modu için SSE olay üreteci."""
    from agent.orchestrator import orchestrator_agent
    from scrapers.automation_intel import collect_automation_intelligence
    from scrapers.producthunt_gaps import find_product_gaps

    automation_signals = []
    try:
        automation_signals = collect_automation_intelligence(req.category)
    except Exception as e:
        print(f"[OrchestrateMode] Otomasyon istihbaratı hatası (devam ediyor): {e}")

    product_gaps = []
    try:
        product_gaps = find_product_gaps(req.category)
    except Exception as e:
        print(f"[OrchestrateMode] Product Hunt gap hatası (devam ediyor): {e}")

    initial_state = {
        "target_category": req.category,
        "trending_models": [],
        "known_apps": [],
        "automation_signals": automation_signals,
        "product_gaps": product_gaps,
        "research_summary": "",
        "brainstormed_angles": [],
        "web_research_results": [],
        "competitor_insights": "",
        "selected_angle": "",
        "investment_memo": "",
        "buyer_leads": [],
        "waitlist_data": {},
        "agent_log": [],
        "error": None,
    }

    scan_id = None
    for event in orchestrator_agent.stream(initial_state):
        node_name = list(event.keys())[0]
        result = event[node_name]

        # Supabase'e kaydet (sadece gtm_agent tamamlandığında)
        if node_name == "gtm_agent" and "selected_angle" in result:
            try:
                scan_id = str(uuid.uuid4())
                leads_count = len(result.get("buyer_leads", []))
                angles_count = len(result.get("brainstormed_angles", []))

                supabase.table("scans").insert({
                    "id": scan_id,
                    "category": req.category,
                    "mode": "orchestrate",
                    "status": "completed",
                    "report_preview": result.get("investment_memo", "")[:200],
                    "leads_count": leads_count,
                    "angles_count": angles_count,
                    "full_report": result,
                }).execute()

                if leads_count > 0:
                    leads_to_insert = [
                        {
                            "scan_category": req.category,
                            "source": l.get("source", "Unknown"),
                            "title": l.get("title", ""),
                            "url": l.get("url", ""),
                            "description": l.get("content", l.get("desc", "")),
                            "score": l.get("score", 0),
                            "status": "new",
                            "dm_template": l.get("dm_template", ""),
                        }
                        for l in result["buyer_leads"]
                    ]
                    supabase.table("leads").insert(leads_to_insert).execute()

            except Exception as e:
                print(f"[OrchestrateMode] Supabase kayıt hatası: {e}")

        data: dict = {"node": node_name, "state": result}
        if scan_id:
            data["scan_id"] = scan_id
        yield f"data: {json.dumps(data)}\n\n"
