import os
import requests
import json

def test_api():
    url = "http://127.0.0.1:8000/api/scan"
    payload = {
        "category": "n8n automation for SEO",
        "mode": "orchestrate"
    }
    
    # We will just print the streaming response
    try:
        print(f"Testing {url} with {payload}")
        with requests.post(url, json=payload, stream=True) as r:
            if r.status_code != 200:
                print(f"Error: HTTP {r.status_code}")
                print(r.text)
                return
            
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data_str = decoded_line[6:]
                        try:
                            # Parse JSON if it's JSON
                            data = json.loads(data_str)
                            if "node" in data:
                                print(f"[NODE]: {data['node']}")
                            if "content" in data:
                                print(f"[CONTENT]: {data['content']}")
                            if "error" in data:
                                print(f"[ERROR]: {data['error']}")
                            if "done" in data and data["done"]:
                                print("[DONE] Response completed successfully.")
                        except json.JSONDecodeError:
                            print(f"Non-JSON block: {data_str[:100]}...")
                            
    except Exception as e:
        print(f"Failed to connect or stream: {e}")

if __name__ == "__main__":
    test_api()
