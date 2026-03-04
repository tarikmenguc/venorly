"""
ProductHunt GraphQL API Scraper
Resmi GraphQL API kullanır — Bearer token ile kimlik doğrulama.
Çıktı: data/apps_raw.json (trustmrr.py ile birleştirilir)
"""

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "apps_raw.json")

GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"
TOKEN = os.getenv("PRODUCTHUNT_API_KEY")

# Konu → kategori eşleştirmesi
TOPIC_CATEGORY_MAP = {
    "Artificial Intelligence": "ai-tools",
    "Machine Learning":        "ai-tools",
    "Video":                   "video-generation",
    "Image Generation":        "image-generation",
    "Audio":                   "audio-processing",
    "Music":                   "music-generation",
    "Developer Tools":         "developer-tools",
    "No-Code":                 "no-code",
    "SaaS":                    "saas",
    "Productivity":            "productivity",
    "Design Tools":            "design",
    "Marketing":               "marketing",
    "E-Commerce":              "e-commerce",
    "Education":               "education",
    "Finance":                 "finance",
    "Analytics":               "analytics",
}

QUERY = """
query GetPosts($cursor: String) {
  posts(first: 50, after: $cursor, order: VOTES) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        name
        tagline
        description
        votesCount
        website
        createdAt
        topics {
          edges {
            node {
              name
            }
          }
        }
      }
    }
  }
}
"""


def map_category(topics: list[str]) -> str:
    for topic in topics:
        if topic in TOPIC_CATEGORY_MAP:
            return TOPIC_CATEGORY_MAP[topic]
    return "saas"


def fetch_page(cursor: str = None) -> dict:
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }
    variables = {}
    if cursor:
        variables["cursor"] = cursor

    resp = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY, "variables": variables},
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def scrape_producthunt(max_pages: int = 4) -> list[dict]:
    if not TOKEN:
        print("[ProductHunt] ❌ PRODUCTHUNT_API_KEY bulunamadı.")
        return []

    print(f"[ProductHunt] API çekimi başlıyor (max {max_pages} sayfa)...")

    all_apps = []
    cursor = None

    for page in range(1, max_pages + 1):
        print(f"[ProductHunt] Sayfa {page}...")
        try:
            data = fetch_page(cursor)
        except requests.RequestException as e:
            print(f"[ProductHunt] ❌ Hata: {e}")
            break

        if "errors" in data:
            print(f"[ProductHunt] ❌ GraphQL hatası: {data['errors']}")
            break

        posts = data.get("data", {}).get("posts", {})
        edges = posts.get("edges", [])
        page_info = posts.get("pageInfo", {})

        for edge in edges:
            node = edge["node"]
            topics = [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])]
            category = map_category(topics)

            all_apps.append({
                "name":        node.get("name", ""),
                "description": (node.get("description") or node.get("tagline") or ""),
                "tagline":     node.get("tagline", ""),
                "mrr":         "",  # ProductHunt MRR vermez
                "votes":       node.get("votesCount", 0),
                "category":    category,
                "topics":      topics,
                "pricing":     "",
                "url":         node.get("website") or f"https://www.producthunt.com/posts/{node.get('id')}",
                "source":      "producthunt",
                "scraped_at":  datetime.now().isoformat(),
            })

        print(f"[ProductHunt] Sayfa {page}: {len(edges)} uygulama")

        if not page_info.get("hasNextPage"):
            print("[ProductHunt] Son sayfaya ulaşıldı.")
            break
        cursor = page_info.get("endCursor")

    print(f"[ProductHunt] ✅ Toplam {len(all_apps)} uygulama.")
    return all_apps


def save(apps: list[dict]):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing = [a for a in existing if a.get("source") != "producthunt"]

    merged = existing + apps
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"[ProductHunt] 💾 {OUTPUT_FILE} güncellendi. Toplam: {len(merged)} uygulama.")


if __name__ == "__main__":
    apps = scrape_producthunt(max_pages=4)
    save(apps)
