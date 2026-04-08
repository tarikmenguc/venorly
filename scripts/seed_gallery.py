"""
seed_gallery.py — Discover Gallery Otomatik Doldurma
=====================================================
Tüm kategoriler için idea_agent çalıştırır ve sonuçları
Supabase scans tablosuna gallery=true olarak kaydeder.

Kullanım:
    python scripts/seed_gallery.py              # Tüm kategoriler
    python scripts/seed_gallery.py --category "video generation"  # Tek kategori
    python scripts/seed_gallery.py --dry-run    # Supabase'e yazmadan test

Not: Groq free tier (30 req/min) nedeniyle kategoriler arası 45sn bekleme var.
     Toplam süre: ~15 kategori × 60sn ≈ 15 dakika
"""

import os
import sys
import time
import json
import argparse
import hashlib
from datetime import datetime

# Proje kökünü path'e ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv()

# ──────────────────────────────────────────────
# KATEGORİ TANIMLARI
# ──────────────────────────────────────────────

GALLERY_CATEGORIES = [
    "video generation",
    "image generation",
    "text to speech",
    "speech to text",
    "code generation",
    "music generation",
    "document AI",
    "computer vision",
    "text generation",
    "audio processing",
    "chatbot",
    "automation",
    "developer tools",
    "marketing",
    "analytics",
]

CATEGORY_EMOJIS = {
    "video generation":  "🎬",
    "image generation":  "🖼️",
    "text to speech":    "🎙️",
    "speech to text":    "🎧",
    "code generation":   "💻",
    "music generation":  "🎵",
    "document AI":       "📄",
    "computer vision":   "👁️",
    "text generation":   "✍️",
    "audio processing":  "🔊",
    "chatbot":           "🤖",
    "automation":        "⚡",
    "developer tools":   "🛠️",
    "marketing":         "📣",
    "analytics":         "📊",
}

RATE_LIMIT_SLEEP = 45  # saniye — Groq free tier için


# ──────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ──────────────────────────────────────────────

def get_current_week() -> str:
    """ISO hafta formatı döner: "2025-W15" """
    now = datetime.now()
    iso = now.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def extract_gallery_title(report: str, category: str) -> str:
    """Rapordan kısa, dikkat çekici başlık çıkarır."""
    import re
    # "🔥 NİŞ FIRSAT: ..." satırını bul
    match = re.search(r'NİŞ FIRSAT[:\s]+(.+)', report)
    if match:
        title = match.group(1).strip()
        # Uzun başlıkları kısalt
        if len(title) > 80:
            title = title[:77] + "..."
        return title
    # Fallback: kategori bazlı başlık
    return f"{CATEGORY_EMOJIS.get(category, '💡')} {category.title()} için AI Micro-SaaS Fırsatı"


def extract_gallery_score(validation_details: str) -> int:
    """Validation detaylarından skoru çıkarır (0-100)."""
    import re
    if not validation_details:
        return 60  # default
    # "Skor: 85" veya "85/100" veya "**85**" gibi pattern'ları ara
    patterns = [
        r'[Ss]kor[:\s]+(\d{1,3})',
        r'(\d{1,3})\s*/\s*100',
        r'\*\*(\d{1,3})\*\*',
    ]
    for p in patterns:
        m = re.search(p, validation_details)
        if m:
            score = int(m.group(1))
            if 0 <= score <= 100:
                return score
    return 65  # default


def extract_gallery_tags(category: str, models: list) -> list:
    """Kategori ve modellerden tag listesi üretir."""
    tags = [category]
    # Modellerin kategori bilgisini de ekle
    for m in models[:3]:
        cat = m.get("category", "")
        if cat and cat != category and len(cat) < 30:
            tags.append(cat)
    # Standart B2B tag'i
    tags.append("B2B")
    tags.append("Micro-SaaS")
    return list(dict.fromkeys(tags))[:6]  # max 6, dedup


def generate_gallery_summary(report: str, llm) -> str:
    """LLM ile 2-3 cümlelik galeri özeti üretir."""
    from langchain_core.messages import HumanMessage

    truncated = report[:1500]
    prompt = f"""Aşağıdaki Micro-SaaS fırsat raporunu 2-3 kısa, dikkat çekici cümleyle özetle.
Türkçe yaz. Emojisiz. Hangi sorunu çözdüğünü ve kim için olduğunu belirt.
Maksimum 150 karakter.

Rapor:
{truncated}

Özet (SADECE 2-3 cümle, başka şey yazma):"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
        # Çok uzunsa kırp
        if len(summary) > 300:
            summary = summary[:297] + "..."
        return summary
    except Exception as e:
        print(f"[Seed] ⚠️  Summary üretme hatası: {e}")
        # Raporden ilk anlamlı satırları al
        lines = [l.strip() for l in report.split("\n") if len(l.strip()) > 20]
        return " ".join(lines[:2])[:200] if lines else "AI destekli Micro-SaaS fırsatı."


# ──────────────────────────────────────────────
# ANA SEED FONKSİYONU
# ──────────────────────────────────────────────

def seed_category(category: str, supabase_client, llm, dry_run: bool = False) -> bool:
    """Tek bir kategori için agent çalıştırır ve Supabase'e yazar."""
    print(f"\n{'─'*55}")
    print(f"[Seed] 🔄 Kategori: '{category}'")
    print(f"{'─'*55}")

    current_week = get_current_week()

    # ── Mevcut kaydı kontrol et (dedup) ──
    if not dry_run and supabase_client:
        try:
            existing = supabase_client.table("scans") \
                .select("id, created_at") \
                .eq("category", category) \
                .eq("gallery_week", current_week) \
                .eq("is_gallery", True) \
                .execute()
            if existing.data:
                print(f"[Seed] ⏭️  Bu hafta '{category}' zaten mevcut (id={existing.data[0]['id']}). Atlanıyor.")
                return True
        except Exception as e:
            print(f"[Seed] ⚠️  Dedup kontrol hatası: {e} — devam ediliyor.")

    # ── Agent çalıştır ──
    print(f"[Seed] 🤖 idea_agent çalıştırılıyor...")
    t0 = time.time()

    try:
        from agent.idea_agent import idea_agent
        result = idea_agent.invoke({
            "user_category": category,
            "trending_models": [],
            "matching_apps": [],
            "competitor_complaints": [],
            "complaint_clusters": "",
            "store_app_ids": [],
            "store_reviews": [],
            "store_clusters": "",
            "competition_matrix": "",
            "final_report": "",
            "validation_details": "",
            "seo_data": {},
            "error": None,
        })
    except Exception as e:
        print(f"[Seed] ❌ Agent hatası: {e}")
        return False

    elapsed = time.time() - t0
    print(f"[Seed] ✅ Agent tamamlandı ({elapsed:.1f}s)")

    final_report = result.get("final_report", "")
    validation_details = result.get("validation_details", "")

    if not final_report:
        print(f"[Seed] ⚠️  Boş rapor, atlanıyor.")
        return False

    # ── Metadata çıkar ──
    gallery_title   = extract_gallery_title(final_report, category)
    gallery_score   = extract_gallery_score(validation_details)
    gallery_tags    = extract_gallery_tags(category, result.get("trending_models", []))
    gallery_emoji   = CATEGORY_EMOJIS.get(category, "💡")
    gallery_summary = generate_gallery_summary(final_report, llm)

    print(f"[Seed] 📝 Başlık  : {gallery_title}")
    print(f"[Seed] ⭐ Skor    : {gallery_score}/100")
    print(f"[Seed] 🏷️  Tag'ler : {gallery_tags}")
    print(f"[Seed] 📄 Özet    : {gallery_summary[:80]}...")

    if dry_run:
        print(f"[Seed] 🔍 DRY RUN — Supabase'e yazılmadı.")
        return True

    # ── Supabase'e UPSERT ──
    scan_record = {
        "category":        category,
        "mode":            "gallery",
        "status":          "completed",
        "is_gallery":      True,
        "gallery_title":   gallery_title,
        "gallery_summary": gallery_summary,
        "gallery_tags":    gallery_tags,
        "gallery_score":   gallery_score,
        "gallery_emoji":   gallery_emoji,
        "gallery_week":    current_week,
        "report_preview":  final_report[:200],
        "leads_count":     0,
        "angles_count":    0,
        "full_report":     result,
    }

    try:
        # Mevcut kayıt varsa güncelle (ON CONFLICT), yoksa ekle
        existing_check = supabase_client.table("scans") \
            .select("id") \
            .eq("category", category) \
            .eq("gallery_week", current_week) \
            .eq("is_gallery", True) \
            .execute()

        if existing_check.data:
            # UPDATE
            scan_id = existing_check.data[0]["id"]
            supabase_client.table("scans") \
                .update(scan_record) \
                .eq("id", scan_id) \
                .execute()
            print(f"[Seed] 🔄 Güncellendi — id={scan_id}")
        else:
            # INSERT
            res = supabase_client.table("scans").insert(scan_record).execute()
            scan_id = res.data[0]["id"] if res.data else "?"
            print(f"[Seed] ✅ Eklendi — id={scan_id}")

        return True

    except Exception as e:
        print(f"[Seed] ❌ Supabase yazma hatası: {e}")
        return False


def run_seed(categories: list, dry_run: bool = False):
    """Tüm kategorileri sırayla seed eder."""
    print("\n" + "═"*55)
    print("🌱 GALLERY SEED BAŞLATILDI")
    print(f"   Kategoriler : {len(categories)}")
    print(f"   Dry-Run     : {dry_run}")
    print(f"   Rate Limit  : {RATE_LIMIT_SLEEP}sn aralık")
    print("═"*55)

    # Supabase bağlantısı
    supabase_client = None
    if not dry_run:
        try:
            from lib.supabase_client import supabase as sb
            supabase_client = sb
            print("[Seed] ✅ Supabase bağlantısı kuruldu.")
        except Exception as e:
            print(f"[Seed] ❌ Supabase bağlantı hatası: {e}")
            print("[Seed] ⚠️  Dry-run moduna geçiliyor.")
            dry_run = True

    # LLM
    from agent.idea_agent import get_llm
    llm = get_llm(temp=0.3)

    results = {}
    for i, category in enumerate(categories):
        success = seed_category(category, supabase_client, llm, dry_run)
        results[category] = success

        # Son kategori değilse bekle (rate limit)
        if i < len(categories) - 1:
            print(f"\n[Seed] ⏳ Rate limit bekleme: {RATE_LIMIT_SLEEP}sn...")
            time.sleep(RATE_LIMIT_SLEEP)

    # Özet
    print("\n" + "═"*55)
    print("📊 SEED SONUÇLARI")
    print("═"*55)
    ok = sum(1 for v in results.values() if v)
    fail = len(results) - ok
    print(f"✅ Başarılı : {ok}/{len(results)}")
    print(f"❌ Başarısız: {fail}/{len(results)}")
    for cat, success in results.items():
        emoji = "✅" if success else "❌"
        print(f"  {emoji} {cat}")
    print("═"*55)


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gallery Seed — Discover Gallery otomatik doldurma")
    parser.add_argument("--category", type=str, help="Sadece bu kategoriyi seed et")
    parser.add_argument("--dry-run", action="store_true", help="Supabase'e yazmadan test et")
    args = parser.parse_args()

    if args.category:
        cats = [args.category]
    else:
        cats = GALLERY_CATEGORIES

    run_seed(cats, dry_run=args.dry_run)
