import uuid
from lib.supabase_client import supabase

def test_insert():
    try:
        scan_id = str(uuid.uuid4())
        
        # Insert test scan
        result = supabase.table("scans").insert({
            "id": scan_id,
            "category": "direct_test",
            "mode": "test",
            "status": "completed",
            "report_preview": "This is a direct test content from Python",
            "leads_count": 0,
            "angles_count": 0
        }).execute()
        
        print("✅ Insert Test Result:", result)
        
        # Verify
        scans = supabase.table("scans").select("*").limit(2).execute()
        print("Data in DB:", scans.data)
        
    except Exception as e:
        print("❌ Insert Error:", e)

if __name__ == "__main__":
    test_insert()
