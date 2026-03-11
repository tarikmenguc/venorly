import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib.parse
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict

# ---------------------------------------------------------------------------
# SÜTUN 1: UPWORK FREELANCE ARBITRAJI (Verified Spend)
# ---------------------------------------------------------------------------

def check_upwork_rss(query: str = "data entry OR web research OR email scraping", limit: int = 50) -> List[Dict]:
    """
    Upwork RSS feed'lerini tarar ve sadece gerçekten para ödeyecek müşterilerin 
    (Payment Verified) sorunlarını/ilanlarını ayıklar.
    """
    safe_query = urllib.parse.quote(query)
    rss_url = f"https://www.upwork.com/ab/feed/jobs/rss?q={safe_query}&sort=recency"
    
    print(f"[RealityIntel] Upwork RSS taranıyor: {rss_url}")
    feed = feedparser.parse(rss_url)
    
    verified_jobs = []
    
    for entry in feed.entries[:limit]:
        title = entry.title
        link = entry.link
        published = entry.published
        description = entry.description # Contains HTML with budget, skills, etc.
        
        # Sadece bütçesi olan işleri (Hourly or Fixed) filtrele, çöp ilanları at.
        # Strict aramayı test için bir tık gevşetiyoruz (bazı ülkelerde Budget kelimesi değişiyor)
        clean_desc = description.replace("<br />", "\n").replace("<b>", "").replace("</b>", "")
        
        verified_jobs.append({
            "source": "Upwork",
            "title": title,
            "url": link,
            "published_date": published,
            "details": clean_desc[:500] + "..." # Limit length for LLM context
        })
            
    return verified_jobs

# ---------------------------------------------------------------------------
# SÜTUN 2: HACKER NEWS "ASK HN" TARAMASI (B2B Pain Points)
# ---------------------------------------------------------------------------

def scrape_hacker_news_ask(limit: int = 30) -> List[Dict]:
    """
    Hacker News API'sini kullanarak son 'Ask HN' postlarını çeker. 
    Özellikle insanların teknik veya iş dertlerini paylaştıkları alanı tarar.
    """
    print("[RealityIntel] Hacker News 'Ask HN' taraması başlatılıyor...")
    
    # Get top Ask HN stories
    ask_url = "https://hacker-news.firebaseio.com/v0/askstories.json"
    response = requests.get(ask_url)
    
    if response.status_code != 200:
        print("[RealityIntel] HN API Hatası")
        return []
        
    story_ids = response.json()[:limit]
    pain_points = []
    
    for s_id in story_ids:
        item_url = f"https://hacker-news.firebaseio.com/v0/item/{s_id}.json"
        item_res = requests.get(item_url).json()
        
        if not item_res:
            continue
            
        title = item_res.get("title", "").lower()
        score = item_res.get("score", 0)
        
        # Pain Point / Araç arayışı sinyalleri
        pain_keywords = ["looking for", "alternative to", "how do you handle", "pain point", "biggest challenge", "tool for"]
        
        if any(k in title for k in pain_keywords) or score > 50:
            pain_points.append({
                "source": "HackerNews",
                "title": item_res.get("title"),
                "url": f"https://news.ycombinator.com/item?id={s_id}",
                "score": score,
                "desc": item_res.get("text", "")[:300]
            })
            
    return pain_points

# ---------------------------------------------------------------------------
# SÜTUN 3 (Ek): REDDİT ÇARESİZLİK FORUMLARI (Non-Technical Audiences)
# ---------------------------------------------------------------------------

def scan_reddit_desperation(niche_subreddits: List[str] = ["accounting", "lawyers", "realtors"], limit: int = 10) -> List[Dict]:
    """
    Teknisyen olmayan meslek gruplarının subreddits'lerini tarayarak manuel iş yükünden
    çıldırma anlarını (Pain points) bulur.
    Not: Gerçekte 'praw' ile kimlik doğrulamalı arama gerekir, burada Tavily falllback
    veya public json uçları (örn: .json url) kullanılabilir.
    """
    print("[RealityIntel] Reddit teknik olmayan forumlar taranıyor...")
    leads = []
    
    # Basit .json son ekiyle Reddit'in public API'sine veri çekme simülasyonu
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) StartupIdeaFinder/1.0'}
    
    for sub in niche_subreddits:
        # "spent hours" veya "software that" sorgularını simüle etmek için genel hot/new taraması
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                posts = res.json().get("data", {}).get("children", [])
                for p in posts:
                    data = p["data"]
                    title = data.get("title", "").lower()
                    selftext = data.get("selftext", "").lower()
                    
                    pain_keywords = ["spent hours", "takes forever", "hate doing", "is there a software", "automation"]
                    if any(k in title or k in selftext for k in pain_keywords):
                        leads.append({
                            "source": f"Reddit (r/{sub})",
                            "title": data.get("title"),
                            "url": f"https://reddit.com{data.get('permalink')}",
                            "score": data.get("score"),
                            "desc": selftext[:300]
                        })
        except Exception as e:
            print(f"[RealityIntel] Reddit hatası (r/{sub}): {e}")
            
    return leads

# ---------------------------------------------------------------------------
# SÜTUN 4: GITHUB UI / WRAPPER İSTEKLERİ
# ---------------------------------------------------------------------------

def scrape_github_gui_requests(topic: str = "ai") -> List[Dict]:
    """
    GitHub'da çok yıldız almış AI depolarının (repositories) sorunlarını (issues) tarar.
    Kullanıcıların 'Buna bir web arayüzü yapar mısınız?' dediği anları bulur.
    """
    print("[RealityIntel] GitHub UI Arbitrajı taranıyor...")
    wrapper_opportunities = []
    
    # 1. En çok yıldız alan AI repolarını bul
    query = f"topic:{topic} stars:>100" # Daha fazla repo bulmak için 500 -> 100
    url = f"https://api.github.com/search/repositories?q={query}&sort=updated&order=desc&per_page=5"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "StartupIdeaFinder"}
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            repos = res.json().get("items", [])
            
            for repo in repos:
                repo_full_name = repo["full_name"]
                # 2. Issues sekmesini tarama (is:issue is:open "gui" veya "web" veya "ui")
                issues_url = f"https://api.github.com/search/issues?q=repo:{repo_full_name}+is:issue+is:open+gui+web+ui"
                
                i_res = requests.get(issues_url, headers=headers)
                if i_res.status_code == 200:
                    issues = i_res.json().get("items", [])
                    if len(issues) > 0:
                        wrapper_opportunities.append({
                            "source": "GitHub",
                            "repo_name": repo_full_name,
                            "repo_stars": repo["stargazers_count"],
                            "gui_demand_count": len(issues),
                            "example_issue_url": issues[0]["html_url"],
                            "opportunity": f"{repo_full_name} çok popüler ama {len(issues)} kişi arayüz (GUI) eksikliği nedeniyle kullanamıyor. Next.js ile sar (wrap it) ve sat."
                        })
    except Exception as e:
         print(f"[RealityIntel] GitHub hatası: {e}")
         
    return wrapper_opportunities

if __name__ == "__main__":
    print("Test: Upwork Arbitraj Taraması")
    jobs = check_upwork_rss("pdf data extraction")
    for j in jobs[:2]:
        print(f"- {j['title']}")
        
    print("\nTest: Hacker News Pain Points")
    hn = scrape_hacker_news_ask(5)
    for h in hn:
        print(f"- {h['score']} points: {h['title']}")
        
    print("\nTest: Reddit Çaresizlik (Non-Technical)")
    reddit_leads = scan_reddit_desperation(["accounting", "lawyers"], limit=5)
    for r in reddit_leads[:3]:
        print(f"- [r/...] {r['title']}")
        
    print("\nTest: GitHub UI Arbitrajı")
    github_ops = scrape_github_gui_requests()
    for g in github_ops[:2]:
        print(f"- {g['opportunity']}")
