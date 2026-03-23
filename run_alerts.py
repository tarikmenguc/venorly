import os
import time
import schedule
from datetime import datetime, timezone
from lib.supabase_client import supabase
from agent.orchestrator import orchestrator_agent
from scrapers.automation_intel import collect_automation_intelligence
from scrapers.producthunt_gaps import find_product_gaps

def process_single_alert(alert):
    keyword = alert.get("keyword")
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚨 Alarm tetiklendi: {keyword}")
    
    # Run the orchestrator silently
    automation_signals = []
    product_gaps = []
    try:
        automation_signals = collect_automation_intelligence(keyword)
        product_gaps = find_product_gaps(keyword)
    except Exception as e:
        print(f"Error in scraping: {e}")

    initial_state = {
        "target_category": keyword,
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
    
    print(f"Orkestrasyon başlatılıyor...")
    final_state = None
    for event in orchestrator_agent.stream(initial_state):
        node_name = list(event.keys())[0]
        final_state = event[node_name]
        print(f"  -> {node_name} tamamlandı")
        
    # Simulate Email Send 
    # (Gerçek dünyada Resend, Sendgrid vb. API kullanılır, şu an sadece terminale ve DB'ye işliyoruz)
    print(f"✅ Rapor hazırlandı. {len(final_state.get('buyer_leads', []))} lead bulundu.")
    print(f"📧 Gerçekte {keyword} için e-posta gönderilecekti.")

def run_daily_alerts():
    print("Günlük alarmlar kontrol ediliyor...")
    try:
        response = supabase.table("alerts").select("*").eq("is_active", True).eq("frequency", "daily").execute()
        alerts = response.data
        if not alerts:
            print("Çalıştırılacak günlük alarm bulunamadı.")
            return

        for alert in alerts:
            process_single_alert(alert)

    except Exception as e:
        print(f"Alarm okuma hatası: {e}")

def run_weekly_alerts():
    print("Haftalık alarmlar kontrol ediliyor...")
    try:
        response = supabase.table("alerts").select("*").eq("is_active", True).eq("frequency", "weekly").execute()
        alerts = response.data
        if not alerts:
            return

        for alert in alerts:
            process_single_alert(alert)
    except Exception as e:
        print(f"Alarm okuma hatası: {e}")

if __name__ == "__main__":
    print(f"Startup Idea Finder - Niş Alarm Servisi Başlatıldı 🔔")
    print("Periyodik kontroller bekleniyor...")
    
    # Her gün sabah 09:00'da günlük alarmları çalıştır
    schedule.every().day.at("09:00").do(run_daily_alerts)
    
    # Her Pazartesi sabah 09:30'da haftalık alarmları çalıştır
    schedule.every().monday.at("09:30").do(run_weekly_alerts)

    # test amaçlı hemen bir kere hepsini çalıştır (görmek için):
    # run_daily_alerts()

    while True:
        schedule.run_pending()
        time.sleep(60)
