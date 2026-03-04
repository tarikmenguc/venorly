import os
import json
from datetime import datetime

def load_snapshot(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def detect_trends(current_week_file: str, previous_week_file: str) -> dict:
    """İki haftalık snapshot'u karşılaştırır ve trendleri bulur."""
    print(f"[TrendDetector] Karşılaştırılıyor: {previous_week_file} -> {current_week_file}")
    
    current_data = load_snapshot(current_week_file)
    prev_data = load_snapshot(previous_week_file)

    if not current_data or not prev_data:
        return {"error": "Karşılaştırma için yeterli veri yok (en az 2 hafta gerekli)."}

    # Modelleri ID'ye göre sözlüğe al
    curr_models = {m["model_id"]: m for m in current_data.get("models", []) if "model_id" in m}
    prev_models = {m["model_id"]: m for m in prev_data.get("models", []) if "model_id" in m}

    # Appleri isme göre sözlüğe al
    curr_apps = {a["name"]: a for a in current_data.get("apps", []) if "name" in a}
    prev_apps = {a["name"]: a for a in prev_data.get("apps", []) if "name" in a}

    rising_models = []
    new_entries = []

    # Model Trendleri (İndirme/Beğeni artışı)
    for m_id, curr_m in curr_models.items():
        if m_id not in prev_models:
            new_entries.append(curr_m)
        else:
            prev_m = prev_models[m_id]
            curr_dl = curr_m.get("downloads") or curr_m.get("run_count") or 0
            prev_dl = prev_m.get("downloads") or prev_m.get("run_count") or 0
            
            # %50'den fazla artış varsa (ve en az 100 artış)
            if prev_dl > 0 and (curr_dl - prev_dl) > 100:
                growth_pct = ((curr_dl - prev_dl) / prev_dl) * 100
                if growth_pct >= 50:
                    curr_m["growth_pct"] = round(growth_pct, 1)
                    curr_m["growth_abs"] = curr_dl - prev_dl
                    rising_models.append(curr_m)

    # En çok artanları sırala
    rising_models.sort(key=lambda x: x.get("growth_abs", 0), reverse=True)
    new_entries.sort(key=lambda x: x.get("downloads", 0) or x.get("run_count", 0), reverse=True)

    # App Trendleri (Sadece MRR büyümesi varsa yakala)
    rising_apps = []
    for a_name, curr_a in curr_apps.items():
        if a_name in prev_apps:
            prev_a = prev_apps[a_name]
            curr_str = str(curr_a.get("mrr", "")).replace("$", "").replace(",", "")
            prev_str = str(prev_a.get("mrr", "")).replace("$", "").replace(",", "")
            
            try:
                # K cinsinden (örn 5.2k -> 5200)
                def parse_mrr(s):
                    if not s: return 0
                    s = s.lower().replace("/mo", "").strip()
                    if "k" in s: return float(s.replace("k", "")) * 1000
                    if "m" in s: return float(s.replace("m", "")) * 1000000
                    return float(s)
                    
                curr_mrr_val = parse_mrr(curr_str)
                prev_mrr_val = parse_mrr(prev_str)
                
                if prev_mrr_val > 0 and curr_mrr_val > prev_mrr_val:
                    growth_pct = ((curr_mrr_val - prev_mrr_val) / prev_mrr_val) * 100
                    if growth_pct >= 10:  # %10 MRR artışı
                        curr_a["growth_pct"] = round(growth_pct, 1)
                        rising_apps.append(curr_a)
            except Exception:
                pass
                
    rising_apps.sort(key=lambda x: x.get("growth_pct", 0), reverse=True)

    return {
        "rising_models": rising_models[:10],
        "new_entries": new_entries[:10],
        "rising_apps": rising_apps[:10],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Sadece print ile gösterim (manuel test için)
    import sys
    if len(sys.argv) == 3:
        trends = detect_trends(sys.argv[1], sys.argv[2])
        print(json.dumps(trends, indent=2, ensure_ascii=False))
    else:
        print("Kullanım: python trend_detector.py <current_week.json> <previous_week.json>")
