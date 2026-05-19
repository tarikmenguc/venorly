"""
n8n / Make.com / Zapier Otomasyon İstihbaratı
Otomasyon forumlarını tarayarak insanların otomatize etmek isteyip de
yapamadığı iş akışlarını bulur — her biri potansiyel Micro-SaaS fırsatıdır.
"""

import os
import sys
import requests
from typing import List, Dict
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from lib.tavily_client import get_tavily_client as _get_tavily
    tavily = _get_tavily()
except Exception:
    tavily = None


# ─────────────────────────────────────────────
# PAIN POINT KALIPLARI (Otomasyon Çaresizliği)
# ─────────────────────────────────────────────
PAIN_PATTERNS = [
    "how to automate",
    "workflow for",
    "can't connect",
    "alternative to",
    "too complex",
    "manually doing",
    "spent hours setting",
    "is there a way to",
    "no-code solution for",
    "looking for integration",
]


# ─────────────────────────────────────────────
# SÜTUN 1: n8n COMMUNITY FORUM TARAMASI
# ─────────────────────────────────────────────

def scrape_n8n_forum(query: str = "automate", limit: int = 15) -> List[Dict]:
    """
    n8n Community Forum'daki (community.n8n.io) konuları Tavily ile tarar.
    'Help Wanted', 'Feature Request' ve 'Questions' başlıklarını bulur.
    """
    print(f"[AutomationIntel] n8n Forum taranıyor: '{query}'...")
    results = []

    if not tavily:
        print("[AutomationIntel] ⚠️ Tavily mevcut değil, n8n forum atlaniyor.")
        return results

    try:
        search_query = f"site:community.n8n.io {query} help OR automate OR workflow"
        raw_results = tavily.search(search_query, max_results=5).get("results", [])

        for r in raw_results[:limit]:
            url = r.get("url", "")
            title = r.get("content", "")[:200] if isinstance(r, dict) else str(r)[:200]

            # Pain pattern kontrolü
            is_pain = any(p in title.lower() for p in PAIN_PATTERNS)

            results.append({
                "source": "n8n Forum",
                "title": title,
                "url": url,
                "is_pain_signal": is_pain,
                "pain_type": "Otomasyon Talebi" if is_pain else "Genel Tartışma",
            })
    except Exception as e:
        print(f"[AutomationIntel] n8n Forum hatası: {e}")

    print(f"[AutomationIntel] ✅ n8n: {len(results)} sonuç bulundu ({sum(1 for r in results if r.get('is_pain_signal'))} pain signal)")
    return results


# ─────────────────────────────────────────────
# SÜTUN 2: ZAPIER / n8n REDDIT ÇARESIZLIĞI
# ─────────────────────────────────────────────

def scrape_automation_reddit(limit: int = 10) -> List[Dict]:
    """
    r/zapier, r/n8n, r/nocode subredditlerini tarayarak
    otomasyon çaresizliği sinyallerini bulur.
    """
    print("[AutomationIntel] Reddit otomasyon forumları taranıyor...")
    leads = []
    headers = {'User-Agent': 'Mozilla/5.0 StartupIdeaFinder/2.0'}

    subreddits = ["zapier", "n8n", "nocode", "automation"]

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                posts = res.json().get("data", {}).get("children", [])
                for p in posts:
                    data = p["data"]
                    title = data.get("title", "").lower()
                    selftext = data.get("selftext", "").lower()
                    combined = f"{title} {selftext}"

                    if any(k in combined for k in PAIN_PATTERNS):
                        leads.append({
                            "source": f"Reddit (r/{sub})",
                            "title": data.get("title"),
                            "url": f"https://reddit.com{data.get('permalink')}",
                            "score": data.get("score"),
                            "desc": data.get("selftext", "")[:300],
                            "is_pain_signal": True,
                            "pain_type": "Otomasyon Çaresizliği"
                        })
        except Exception as e:
            print(f"[AutomationIntel] Reddit hatası (r/{sub}): {e}")

    print(f"[AutomationIntel] ✅ Reddit Otomasyon: {len(leads)} pain signal bulundu")
    return leads


# ─────────────────────────────────────────────
# SÜTUN 3: n8n GITHUB ISSUES (FEATURE REQUESTS)
# ─────────────────────────────────────────────

def scrape_n8n_github_issues(limit: int = 10) -> List[Dict]:
    """
    n8n'in GitHub reposundaki 'feature request' etiketli issue'ları tarar.
    İnsanların n8n'den isteyip de alamadığı özellikler = SaaS fırsatı.
    """
    print("[AutomationIntel] n8n GitHub issues taranıyor...")
    results = []

    url = f"https://api.github.com/search/issues?q=repo:n8n-io/n8n+is:issue+is:open+label:\"feature-request\"&sort=reactions-+1&order=desc&per_page={limit}"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "StartupIdeaFinder"}

    # GitHub token varsa kullan
    gh_token = os.getenv("GITHUB_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            issues = res.json().get("items", [])
            for issue in issues:
                results.append({
                    "source": "n8n GitHub",
                    "title": issue.get("title"),
                    "url": issue.get("html_url"),
                    "reactions": issue.get("reactions", {}).get("+1", 0),
                    "comments": issue.get("comments", 0),
                    "is_pain_signal": True,
                    "pain_type": "Eksik Özellik Talebi"
                })
    except Exception as e:
        print(f"[AutomationIntel] GitHub hatası: {e}")

    print(f"[AutomationIntel] ✅ GitHub: {len(results)} feature request bulundu")
    return results


# ─────────────────────────────────────────────
# SÜTUN 4: GITHUB n8n WORKFLOW REPO'LARI
# (İnsanlar en çok hangi otomasyonları yapıyor?)
# ─────────────────────────────────────────────

# Bilinen popüler n8n workflow koleksiyonları
KNOWN_WORKFLOW_REPOS = [
    "Zie619/n8n-workflows",
    "enescingoz/awesome-n8n-templates",
    "wassupjay/n8n-free-templates",
    "lucaswalter/n8n-ai-automations",
    "Danitilahun/n8n-workflow-templates",
]


def scrape_n8n_workflow_repos(query: str = "n8n workflow", limit: int = 15) -> List[Dict]:
    """
    GitHub'da insanların paylaştığı n8n workflow şablonlarını tarar.
    Her repo, insanların düzenli olarak otomatize etmek istediği bir işi temsil eder.
    Repo'nun star sayısı, o otomasyon ihtiyacının ne kadar yaygın olduğunu gösterir.
    """
    print("[AutomationIntel] GitHub n8n Workflow Repos taranıyor...")
    results = []
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "StartupIdeaFinder"}

    gh_token = os.getenv("GITHUB_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    # 1. Bilinen popüler repo'ların README'lerinden workflow kategorilerini çek
    for repo_full in KNOWN_WORKFLOW_REPOS:
        try:
            url = f"https://api.github.com/repos/{repo_full}"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                results.append({
                    "source": "GitHub Workflows",
                    "title": f"📦 {data.get('full_name')} — {data.get('description', '')[:150]}",
                    "url": data.get("html_url"),
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "topics": data.get("topics", []),
                    "is_pain_signal": True,
                    "pain_type": "Popüler Otomasyon Şablonu"
                })
        except Exception as e:
            print(f"[AutomationIntel] Repo hatası ({repo_full}): {e}")

    # 2. GitHub Search ile query'ye özel n8n workflow repo'larını ara
    try:
        search_url = f"https://api.github.com/search/repositories?q={query}+n8n+automation&sort=stars&order=desc&per_page={limit}"
        res = requests.get(search_url, headers=headers, timeout=15)
        if res.status_code == 200:
            items = res.json().get("items", [])
            existing_urls = {r["url"] for r in results}
            for repo in items:
                html_url = repo.get("html_url")
                if html_url in existing_urls:
                    continue  # Tekrar eden repo'ları atla
                desc = repo.get("description", "") or ""
                results.append({
                    "source": "GitHub Workflows",
                    "title": f"🔍 {repo.get('full_name')} — {desc[:150]}",
                    "url": html_url,
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "topics": repo.get("topics", []),
                    "is_pain_signal": True,
                    "pain_type": "Otomasyon Workflow Şablonu"
                })
    except Exception as e:
        print(f"[AutomationIntel] GitHub Search hatası: {e}")

    print(f"[AutomationIntel] ✅ GitHub Workflows: {len(results)} repo bulundu (Toplam ⭐ {sum(r.get('stars', 0) for r in results)})")
    return results


# ─────────────────────────────────────────────
# ANA FONKSİYON: TÜM KAYNAKLARI BİRLEŞTİR
# ─────────────────────────────────────────────

def collect_automation_intelligence(query: str = "automate") -> List[Dict]:
    """
    Tüm otomasyon istihbarat kaynaklarını tarar ve birleştirir.
    Friction Economy felsefesiyle: 'İnsanlar neyi otomasyona çevirmek istiyor
    ama yapamıyor?' sorusuna cevap arar.
    """
    print(f"\n{'='*50}")
    print(f"[AutomationIntel] Otomasyon İstihbaratı Başlatıldı: '{query}'")
    print(f"{'='*50}\n")

    all_signals = []

    # 1. n8n Forum
    all_signals.extend(scrape_n8n_forum(query))

    # 2. Reddit (Zapier/n8n/Nocode/Automation)
    all_signals.extend(scrape_automation_reddit())

    # 3. n8n GitHub Feature Requests
    all_signals.extend(scrape_n8n_github_issues())

    # 4. GitHub n8n Workflow Repos (İnsanlar en çok neyi otomatize ediyor?)
    all_signals.extend(scrape_n8n_workflow_repos(query))

    # Sadece pain signallerini filtrele
    pain_signals = [s for s in all_signals if s.get("is_pain_signal")]

    print(f"\n[AutomationIntel] 📊 Özet: {len(all_signals)} toplam, {len(pain_signals)} pain signal")
    return pain_signals


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    signals = collect_automation_intelligence("PDF invoice processing")

    print(f"\n{'='*50}")
    print(f"Bulunan Sinyaller ({len(signals)} adet):")
    print(f"{'='*50}")
    for s in signals[:10]:
        emoji = "🔴" if s.get("pain_type") == "Otomasyon Çaresizliği" else "🟡"
        print(f"{emoji} [{s['source']}] {s['title'][:80]}")
        if s.get("url"):
            print(f"  → {s['url']}")
