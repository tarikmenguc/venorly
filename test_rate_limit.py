import asyncio
import json
import sys
from httpx import AsyncClient

async def test_rate_limit():
    url = "http://localhost:8000/api/scan"
    
    print("\n--- TEST: 'discover' Modu (Limit: 3) ---")
    for i in range(1, 6):
        print(f"[{i}] İstek gönderiliyor...")
        async with AsyncClient() as client:
            try:
                # Normalde streaming response olduğu için ufak bir okuma yapıyoruz.
                async with client.stream("POST", url, json={"mode": "discover", "category": "rate limit test chunk"}) as response:
                    async for chunk in response.aiter_lines():
                        if chunk and chunk.startswith("data: "):
                            data = json.loads(chunk.replace("data: ", ""))
                            if data.get("error"):
                                print(f"  ❌ ENGELLENDI: {data['error']}\n")
                                break
                            elif data.get("node"):
                                print(f"  ✅ BASARILI: {data['node']}")
                                break
            except Exception as e:
                print(f"Hata: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_rate_limit())
