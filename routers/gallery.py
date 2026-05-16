"""
Gallery endpoints — Discover Gallery API
"""
from fastapi import APIRouter, Response

from lib.supabase_client import supabase

router = APIRouter()


@router.get("/api/gallery")
async def get_gallery(
    page: int = 1,
    per_page: int = 12,
    category: str = "",
    sort: str = "score",   # "score" | "date"
):
    """Galeri listesini sayfalanmış döner."""
    try:
        offset = (page - 1) * per_page

        query = supabase.table("scans") \
            .select("id, category, gallery_title, gallery_summary, gallery_tags, gallery_score, gallery_emoji, gallery_week, created_at") \
            .eq("is_gallery", True) \
            .eq("status", "completed")

        if category:
            query = query.eq("category", category)

        if sort == "score":
            query = query.order("gallery_score", desc=True)
        else:
            query = query.order("created_at", desc=True)

        # Toplam sayı
        count_query = supabase.table("scans") \
            .select("id", count="exact") \
            .eq("is_gallery", True) \
            .eq("status", "completed")
        if category:
            count_query = count_query.eq("category", category)
        count_res = count_query.execute()
        total = count_res.count or 0

        # Sayfalanmış veri
        res = query.range(offset, offset + per_page - 1).execute()
        items = res.data or []

        return {
            "items":    items,
            "total":    total,
            "page":     page,
            "per_page": per_page,
            "pages":    max(1, (total + per_page - 1) // per_page),
        }
    except Exception as e:
        print(f"[Gallery] List Error: {e}")
        return Response(content=str(e), status_code=500)


@router.get("/api/gallery/stats")
async def get_gallery_stats():
    """Galeri özet istatistikleri."""
    try:
        res = supabase.table("scans") \
            .select("category, gallery_score") \
            .eq("is_gallery", True) \
            .eq("status", "completed") \
            .execute()
        items = res.data or []

        if not items:
            return {"total_ideas": 0, "avg_score": 0, "top_category": None}

        avg_score = round(sum(i.get("gallery_score", 0) for i in items) / len(items))
        cat_count: dict = {}
        for i in items:
            c = i.get("category", "")
            cat_count[c] = cat_count.get(c, 0) + 1
        top_category = max(cat_count, key=cat_count.get) if cat_count else None

        return {
            "total_ideas":  len(items),
            "avg_score":    avg_score,
            "top_category": top_category,
        }
    except Exception as e:
        return Response(content=str(e), status_code=500)


@router.get("/api/gallery/categories")
async def get_gallery_categories():
    """Galeriden ayrı kategorileri + sayılarını döner."""
    try:
        res = supabase.table("scans") \
            .select("category, gallery_emoji") \
            .eq("is_gallery", True) \
            .eq("status", "completed") \
            .execute()
        items = res.data or []

        cat_map: dict = {}
        for i in items:
            c = i.get("category", "")
            e = i.get("gallery_emoji", "💡")
            if c not in cat_map:
                cat_map[c] = {"category": c, "emoji": e, "count": 0}
            cat_map[c]["count"] += 1

        return {"categories": sorted(cat_map.values(), key=lambda x: -x["count"])}
    except Exception as e:
        return Response(content=str(e), status_code=500)


@router.get("/api/gallery/{scan_id}")
async def get_gallery_item(scan_id: str):
    """Tek bir galeri fikrini tam rapor dahil döner."""
    try:
        res = supabase.table("scans") \
            .select("*") \
            .eq("id", scan_id) \
            .eq("is_gallery", True) \
            .single() \
            .execute()
        if not res.data:
            return Response(content="Gallery item not found", status_code=404)
        return res.data
    except Exception as e:
        print(f"[Gallery] Item Error: {e}")
        return Response(content=str(e), status_code=404)
