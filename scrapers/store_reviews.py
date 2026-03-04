"""
Store Reviews Scraper
Play Store ve App Store'dan negatif (1-2 yildiz) yorumları çeker.
google-play-scraper + app-store-scraper kullanır.
"""

import re
from datetime import datetime


def scrape_play_store_reviews(package_name: str, max_reviews: int = 100) -> list[dict]:
    """
    Play Store'dan negatif yorumları çeker.
    
    Args:
        package_name: com.example.app formatında paket adı
        max_reviews: Maksimum yorum sayısı
    
    Returns:
        [{"score": 1, "text": "...", "thumbs_up": 5, "date": "..."}]
    """
    try:
        from google_play_scraper import Sort, reviews
    except ImportError:
        print("[StoreReviews] google-play-scraper kurulu degil!")
        return []

    if not package_name or not re.match(r'^[a-zA-Z][a-zA-Z0-9_.]*$', package_name):
        print(f"[StoreReviews] Gecersiz paket adi: {package_name}")
        return []

    print(f"[StoreReviews] Play Store: {package_name} yorumlari cekiliyor...")

    try:
        result, _ = reviews(
            package_name,
            lang='en',
            country='us',
            sort=Sort.NEWEST,
            count=max_reviews,
            filter_score_with=None,  # Hepsini cek, sonra filtrele
        )
    except Exception as e:
        print(f"[StoreReviews] Play Store hatasi ({package_name}): {e}")
        return []

    # 1-2 yildiz filtrele
    negative = []
    for r in result:
        score = r.get('score', 0)
        if score and score <= 2:
            negative.append({
                "score": score,
                "text": (r.get('content') or '')[:500],
                "thumbs_up": r.get('thumbsUpCount', 0),
                "date": str(r.get('at', '')),
                "source": "play_store",
                "app": package_name,
            })

    # thumbsUpCount'a gore sirala (en cok begenilen sikayetler onde)
    negative.sort(key=lambda x: x['thumbs_up'], reverse=True)

    print(f"[StoreReviews] Play Store: {len(negative)} negatif yorum (toplam {len(result)})")
    return negative[:50]  # Max 50 yorum


def scrape_app_store_reviews(app_name: str, app_id: int = None, max_reviews: int = 50) -> list[dict]:
    """
    App Store'dan negatif yorumlari ceker.
    
    Args:
        app_name: Uygulama adi
        app_id: Apple App ID (opsiyonel)
        max_reviews: Maksimum yorum
    
    Returns:
        [{"score": 1, "text": "...", "date": "..."}]
    """
    try:
        from app_store_scraper import AppStore
    except ImportError:
        print("[StoreReviews] app-store-scraper kurulu degil!")
        return []

    print(f"[StoreReviews] App Store: '{app_name}' yorumlari cekiliyor...")

    try:
        app = AppStore(country='us', app_name=app_name)
        app.review(how_many=max_reviews)
    except Exception as e:
        print(f"[StoreReviews] App Store hatasi ({app_name}): {e}")
        return []

    negative = []
    for r in app.reviews:
        score = r.get('rating', 0)
        if score and score <= 2:
            negative.append({
                "score": score,
                "text": (r.get('review') or r.get('title', ''))[:500],
                "date": str(r.get('date', '')),
                "source": "app_store",
                "app": app_name,
            })

    print(f"[StoreReviews] App Store: {len(negative)} negatif yorum (toplam {len(app.reviews)})")
    return negative[:30]


def scrape_store_reviews(app_name: str, play_store_id: str = None) -> list[dict]:
    """
    Hem Play Store hem App Store'dan negatif yorumları toplar.
    
    Args:
        app_name: Uygulama adı
        play_store_id: Play Store paket adı (varsa)
    
    Returns:
        Birlestirilmis negatif yorum listesi
    """
    all_reviews = []

    if play_store_id:
        all_reviews.extend(scrape_play_store_reviews(play_store_id, max_reviews=100))

    # App Store her zaman dene (isim bazli arama)
    all_reviews.extend(scrape_app_store_reviews(app_name, max_reviews=50))

    return all_reviews


# Test
if __name__ == "__main__":
    print("=== Play Store Test ===")
    ps_reviews = scrape_play_store_reviews("com.lumen5.video", max_reviews=50)
    for r in ps_reviews[:3]:
        print(f"  [{r['score']}*] (thumbs={r['thumbs_up']}): {r['text'][:100]}...")

    print("\n=== App Store Test ===")
    as_reviews = scrape_app_store_reviews("lumen5", max_reviews=30)
    for r in as_reviews[:3]:
        print(f"  [{r['score']}*]: {r['text'][:100]}...")
