# HOW TO BUILD — Startup Idea Finder (Model-First)

> Agentic RAG öğrenmek için yapıyorsun. Her adımda hem ne yapacağını hem neden yapacağını açıklıyorum.

---

## 🛠️ Ortam Kurulumu (Bir Kez)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # API key'leri doldur
```

### Öncelikli API Key'ler

| Sıra | Key | URL |
|---|---|---|
| 1️⃣ Zorunlu | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| 2️⃣ Zorunlu | `PRODUCTHUNT_API_KEY` | [producthunt.com/v2/oauth](https://www.producthunt.com/v2/oauth/applications) |
| 3️⃣ Önerilen | `LANGSMITH_API_KEY` | [smith.langchain.com](https://smith.langchain.com) |
| 4️⃣ Faz 2'de | `TAVILY_API_KEY` | [tavily.com](https://tavily.com) |

---

---

## FAZ 1 — Model-First MVP (~1 Hafta)

### Mimari Hatırlatma

```
Replicate / HuggingFace / fal.ai  →  ChromaDB "ai_models"
TrustMRR / ProductHunt            →  ChromaDB "startup_apps"
LangGraph agent: model → eşleştir → raporla
```

---

### ✅ 1. Adım: HuggingFace Scraper (Kolay Başlangıç)

**Dosya:** `scrapers/huggingface.py`  
**Neden buradan başlıyoruz?** `huggingface_hub` resmi SDK var → scraping derdi yok → API gibi çalışıyor.  
**Agentic RAG bağlantısı:** Bu veriler `ai_models` ChromaDB koleksiyonuna gidecek.

```python
from huggingface_hub import list_models
import json, os

os.makedirs("data", exist_ok=True)

# Trending modelleri çek
models = list(list_models(
    sort="trending",
    limit=100,
    fetch_config=False
))

result = []
for m in models:
    result.append({
        "model_id": m.modelId,
        "category": m.pipeline_tag or "unknown",   # video-generation, text-to-image...
        "downloads": m.downloads,
        "likes": m.likes,
        "last_modified": str(m.lastModified),
        "url": f"https://huggingface.co/{m.modelId}",
        "source": "huggingface"
    })

with open("data/models_raw.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"✅ {len(result)} model kaydedildi.")
```

> **Test:** `python scrapers/huggingface.py` → `data/models_raw.json` oluştu mu?

---

### ✅ 2. Adım: Replicate Scraper

**Dosya:** `scrapers/replicate.py`  
**Ekstra değer:** `run_count` — bir modelin kaç kez çalıştırıldığı = developer ilgisi sinyali.

```python
import requests, json, time
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE_URL = "https://replicate.com/explore"

def scrape_replicate():
    resp = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    models = []
    # TODO: model kartlarını parse et
    # Her kartta: model adı, kategori tag, run count, açıklama
    return models

result = scrape_replicate()
# data/models_raw.json'a ekle (HuggingFace ile birleştir)
print(f"✅ {len(result)} Replicate modeli eklendi.")
```

**İpucu:** Browser'da `replicate.com/explore` aç → F12 → hangi CSS class'ları var, onları hedefle.

---

### ✅ 3. Adım: TrustMRR Scraper

**Dosya:** `scrapers/trustmrr.py`  
**Amaç:** Para kazanan uygulamaları çek → `startup_apps` koleksiyonuna.

```python
import requests, json, time, os
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://trustmrr.com/apps"

def scrape_page(url):
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    apps = []
    # TODO: uygulama kartlarını bul
    # Her kartta: name, mrr, category, description, pricing, url
    return apps

os.makedirs("data", exist_ok=True)
all_apps = []

for page in range(1, 6):
    apps = scrape_page(f"{BASE_URL}?page={page}")
    all_apps.extend(apps)
    time.sleep(2)   # ← rate limiting! çok önemli

with open("data/apps_raw.json", "w") as f:
    json.dump(all_apps, f, indent=2, ensure_ascii=False)

print(f"✅ {len(all_apps)} uygulama kaydedildi.")
```

---

### ✅ 4. Adım: ProductHunt API

**Dosya:** `scrapers/producthunt.py`  
**Önemli:** ProductHunt REST değil **GraphQL** kullanır → `requests.post()` ile JSON body göndeririz.

```python
import requests, json, os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("PRODUCTHUNT_API_KEY")

QUERY = """
query {
  posts(first: 50, order: VOTES) {
    edges {
      node {
        name
        tagline
        description
        votesCount
        website
        topics { edges { node { name } } }
      }
    }
  }
}
"""

resp = requests.post(
    "https://api.producthunt.com/v2/api/graphql",
    json={"query": QUERY},
    headers={"Authorization": f"Bearer {TOKEN}"}
)

posts = resp.json()["data"]["posts"]["edges"]
apps = []
for edge in posts:
    node = edge["node"]
    apps.append({
        "name": node["name"],
        "tagline": node["tagline"],
        "description": node.get("description", ""),
        "votes": node["votesCount"],
        "url": node.get("website", ""),
        "topics": [t["node"]["name"] for t in node["topics"]["edges"]],
        "source": "producthunt"
    })

# data/apps_raw.json'a ekle (TrustMRR ile birleştir)
print(f"✅ {len(apps)} ProductHunt uygulaması eklendi.")
```

---

### ✅ 5. Adım: ChromaDB Ingestion (İki Koleksiyon)

**Dosya:** `ingestion/ingest.py`  
**Agentic RAG bağlantısı:** İşte burada "Retrieval" kısmı başlıyor.  
Metin → vektör → ChromaDB → ileride similarity_search ile aranacak.

```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import json

# Embedding modeli (yerel çalışır, ücretsiz)
embeddings = HuggingFaceEmbeddings(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

# --- Koleksiyon 1: ai_models ---
models_store = Chroma(
    collection_name="ai_models",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

with open("data/models_raw.json") as f:
    models = json.load(f)

model_docs = []
for m in models:
    doc = Document(
        page_content=f"{m['model_id']}. Category: {m['category']}",
        metadata={
            "model_id": m["model_id"],
            "category": m["category"],
            "downloads": m.get("downloads", 0),
            "source": m["source"],
            "url": m["url"],
        }
    )
    model_docs.append(doc)

models_store.add_documents(model_docs)
print(f"✅ {len(model_docs)} model ChromaDB'ye eklendi (ai_models)")

# --- Koleksiyon 2: startup_apps ---
apps_store = Chroma(
    collection_name="startup_apps",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

with open("data/apps_raw.json") as f:
    apps = json.load(f)

app_docs = []
for a in apps:
    doc = Document(
        page_content=f"{a['name']}. {a.get('description', '')}. "
                     f"Category: {a.get('category', '')}",
        metadata={
            "name": a["name"],
            "mrr": a.get("mrr", ""),
            "pricing": a.get("pricing", ""),
            "source": a["source"],
            "url": a.get("url", ""),
            "category": a.get("category", ""),
        }
    )
    app_docs.append(doc)

apps_store.add_documents(app_docs)
print(f"✅ {len(app_docs)} uygulama ChromaDB'ye eklendi (startup_apps)")
```

---

### ✅ 6. Adım: LangGraph Agent

**Dosya:** `agent/idea_agent.py`  
**Agentic RAG bağlantısı:** İşte "Agentic" kısmı — state machine, adım adım düşünen agent.

```python
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from typing import TypedDict, List
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")

models_store = Chroma(collection_name="ai_models",
                      embedding_function=embeddings, persist_directory="./chroma_db")
apps_store   = Chroma(collection_name="startup_apps",
                      embedding_function=embeddings, persist_directory="./chroma_db")

# STATE — agent'ın hafızası
class AgentState(TypedDict):
    user_category: str        # "video", "image", "audio", "code"
    trending_models: List[dict]   # fetch_trending_models_node üretir
    matching_apps: List[dict]     # match_to_market_node üretir
    final_report: str             # generate_opportunity_node üretir

def fetch_trending_models_node(state: AgentState) -> AgentState:
    """ChromaDB'den kullanıcı kategorisine göre trend modeller bul."""
    category = state["user_category"]
    results = models_store.similarity_search(category, k=5)
    models = [{"content": r.page_content, **r.metadata} for r in results]
    return {**state, "trending_models": models}

def match_to_market_node(state: AgentState) -> AgentState:
    """Model kategorisiyle eşleşen para kazanan appları bul."""
    search_query = state["user_category"] + " " + " ".join(
        [m.get("category", "") for m in state["trending_models"]]
    )
    results = apps_store.similarity_search(search_query, k=5)
    apps = [{"content": r.page_content, **r.metadata} for r in results]
    return {**state, "matching_apps": apps}

def generate_opportunity_node(state: AgentState) -> AgentState:
    """Tüm verileri birleştirip fırsat raporu üret."""
    models_text = "\n".join([m["content"] for m in state["trending_models"]])
    apps_text   = "\n".join([
        f"• {a.get('name', '?')} → {a.get('mrr', '?')} MRR"
        for a in state["matching_apps"]
    ])

    prompt = f"""
Sen bir startup fırsat analistisisin.

Trend AI modeller:
{models_text}

Bu alanda para kazanan uygulamalar:
{apps_text}

Görev:
Bu modeller kullanılarak mevcut appların boşluklarını dolduran somut bir SaaS fikri öner.
Format: Türkçe, yapılandırılmış, emoji kullan, kısa ve net ol.
"""
    report = llm.invoke(prompt).content
    return {**state, "final_report": report}

# GRAPH
graph = StateGraph(AgentState)
graph.add_node("fetch_trending_models", fetch_trending_models_node)
graph.add_node("match_to_market", match_to_market_node)
graph.add_node("generate_opportunity", generate_opportunity_node)

graph.set_entry_point("fetch_trending_models")
graph.add_edge("fetch_trending_models", "match_to_market")
graph.add_edge("match_to_market", "generate_opportunity")
graph.add_edge("generate_opportunity", END)

idea_agent = graph.compile()

# Test
if __name__ == "__main__":
    result = idea_agent.invoke({
        "user_category": "video generation",
        "trending_models": [],
        "matching_apps": [],
        "final_report": ""
    })
    print(result["final_report"])
```

---

### ✅ 7. Adım: Streamlit UI

**Dosya:** `app.py`

```python
import streamlit as st
from agent.idea_agent import idea_agent

st.set_page_config(page_title="Startup Idea Finder", page_icon="🔍")
st.title("🔍 Startup Idea Finder")
st.caption("Trend AI modellerinden kanıtlanmış pazar fırsatları bul")

col1, col2 = st.columns(2)

with col1:
    mode = st.radio("Mod seç", ["🔥 Keşfet", "🎯 Kategori Seç"])

with col2:
    if mode == "🎯 Kategori Seç":
        category = st.selectbox("Alan seç", [
            "video generation", "text to image", "speech to text",
            "text to speech", "code generation", "music generation"
        ])
    else:
        category = "trending"  # Agent kendi bulacak

if st.button("🚀 Fırsat Bul", use_container_width=True):
    with st.spinner("Modeller taranıyor, pazar analiz ediliyor..."):
        result = idea_agent.invoke({
            "user_category": category,
            "trending_models": [],
            "matching_apps": [],
            "final_report": ""
        })
    st.markdown("---")
    st.markdown(result["final_report"])
```

---

## Faz 1 Kontrol Listesi

- [ ] `scrapers/huggingface.py` → `data/models_raw.json` üretiyor
- [ ] `scrapers/replicate.py` → aynı dosyaya ekleniyor
- [ ] `scrapers/trustmrr.py` → `data/apps_raw.json` üretiyor
- [ ] `scrapers/producthunt.py` → aynı dosyaya ekleniyor
- [ ] `ingestion/ingest.py` → İki ChromaDB koleksiyonu doluyor
- [ ] `agent/idea_agent.py` → Terminal testinde rapor üretiyor
- [ ] `app.py` → `streamlit run app.py` çalışıyor

---

---

## FAZ 2 — Rakip Boşluk Analizi (~1 Hafta Sonra)

**Adım 8:** `scrapers/g2_capterra.py` — bulunan appların negatif yorumlarını çek  
**Adım 9:** Agent'a `scrape_competitor_reviews_node` ekle  
**Adım 10:** Agent'a `cluster_complaints_node` ekle (LLM şikayetleri kategorize eder)

---

## FAZ 3 — Store Reviews (~2 Hafta Sonra)

**Adım 11:** `scrapers/store_reviews.py` — Play Store + App Store yorumları  
**Adım 12:** Agent'a `find_store_app_node` ekle (LLM paket adı tahmin eder)  
**Adım 13:** Agent'a `scrape_store_reviews_node` ekle

---

## 🛑 Sık Yapılan Hatalar

| Hata | Çözüm |
|---|---|
| ChromaDB boş | `python ingestion/ingest.py` çalıştırılmadı |
| API key bulunamadı | `.env` dosyası oluşturulmadı |
| Scraper bloklandı | `time.sleep(2)` ekle, User-Agent header ekle |
| LangGraph state key hatası | TypedDict'teki tüm keyler başlangıç state'inde olmalı |
| Embedding çok yavaş | İlk çalıştırmada model indiriliyor — normal |

---

## 📚 Öğrenme Sırası

```
1. ChromaDB + Embedding kavramları
   → "Neden vektör DB kullanıyoruz?"
2. LangChain Retriever
   → "similarity_search nasıl çalışıyor?"
3. LangGraph StateGraph + Node
   → "Agent adım adım nasıl düşünüyor?"
4. Tool use (Tavily, scraper'lar)
   → "Agent dış dünyayla nasıl iletişim kuruyor?"
5. Multi-collection cross-retrieval
   → "İki farklı vektör DB'yi nasıl birleştiriyoruz?"
```

---

*Repo: https://github.com/tarikmenguc/Startup_Idea_Finder*
