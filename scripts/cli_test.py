import requests
import argparse
import json

def test_api(mode, category):
    url = "http://127.0.0.1:8000/api/scan"
    
    # SSE stream okumak için
    headers = {
        "Accept": "text/event-stream"
    }
    
    payload = {
        "mode": mode,
        "category": category
    }
    
    print(f"Connecting to {url} with mode: {mode}, category: {category}")
    print("-" * 50)
    #a
    try:
        # stream=True ile SSE cevabını satır satır okuruz
        with requests.post(url, json=payload, headers=headers, stream=True) as r:
            if r.status_code != 200:
                print(f"Hata: {r.status_code}")
                print(r.text)
                return
                
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data_str = decoded_line[6:]
                        try:
                            data_json = json.loads(data_str)
                            if 'node' in data_json:
                                print(f"[{data_json['node']}] -> {data_json.get('state', {})}")
                            elif 'error' in data_json:
                                print(f"ERROR: {data_json['error']}")
                            elif 'status' in data_json:
                                print(f"STATUS: {data_json['status']}")
                        except json.JSONDecodeError:
                            print(f"Raw data: {data_str}")
    except requests.exceptions.ConnectionError:
        print("Bağlantı hatası: Sunucu çalışmıyor olabilir. (uvicorn api:app --reload ile başlatın)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the FastAPI backend directly")
    parser.add_argument("--mode", type=str, default="discover", help="Scan modu (discover, deep, vb.)")
    parser.add_argument("--category", type=str, default="video generation", help="Kategori adı")
    
    args = parser.parse_args()
    test_api(args.mode, args.category)
