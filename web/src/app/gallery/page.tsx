"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ScanDB } from "@/lib/scan-db";
import { GradientDots } from "@/components/ui/gradient-dots";
import { NavBar } from "@/components/ui/tubelight-navbar";
import {
  Home,
  Sparkles,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  LayoutGrid,
  Flame,
  User,
} from "lucide-react";

const navItems = [
  { name: "Keşfet", url: "/", icon: Home },
  { name: "Galeri", url: "/gallery", icon: Sparkles, href: "/gallery" },
  { name: "Profil",  url: "/profile", icon: User,     href: "/profile" },
];

const SCORE_COLORS = [
  { min: 85, bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30", label: "🔥 Çok Yüksek" },
  { min: 70, bg: "bg-blue-500/20",    text: "text-blue-400",    border: "border-blue-500/30",    label: "✨ Yüksek" },
  { min: 50, bg: "bg-yellow-500/20",  text: "text-yellow-400",  border: "border-yellow-500/30",  label: "⚡ Orta" },
  { min: 0,  bg: "bg-gray-500/20",    text: "text-gray-400",    border: "border-gray-500/30",    label: "💡 Gelişmekte" },
];

function getScoreStyle(score: number) {
  return SCORE_COLORS.find((c) => score >= c.min) || SCORE_COLORS[SCORE_COLORS.length - 1];
}

interface GalleryItem {
  id: string;
  category: string;
  gallery_title?: string;
  gallery_summary?: string;
  gallery_tags?: string[];
  gallery_score?: number;
  gallery_emoji?: string;
  gallery_week?: string;
  created_at: string;
}

interface GalleryStats {
  total_ideas: number;
  avg_score: number;
  top_category: string | null;
}

const PER_PAGE = 12;

export default function GalleryPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Derive state from URL params
  const selectedCategory = searchParams.get("category") ?? "";
  const sort = (searchParams.get("sort") as "score" | "date") ?? "score";
  const page = parseInt(searchParams.get("page") ?? "1", 10);

  const [items, setItems] = useState<GalleryItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [stats, setStats] = useState<GalleryStats>({ total_ideas: 0, avg_score: 0, top_category: null });
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  /** Push new URL params without full reload */
  function updateParams(updates: Record<string, string | null>) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (value === null || value === "") {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    }
    router.push(`/gallery?${params.toString()}`, { scroll: false });
  }

  function setCategory(cat: string) {
    updateParams({ category: cat || null, page: null });
  }

  function setSort(s: "score" | "date") {
    updateParams({ sort: s, page: null });
  }

  function setPage(p: number) {
    updateParams({ page: String(p) });
  }

  const loadCategories = useCallback(async () => {
    const cats = await ScanDB.getGalleryCategories();
    setCategories(
      cats.map((c: { category?: string } | string) =>
        typeof c === "string" ? c : c.category ?? ""
      )
    );
  }, []);

  const loadStats = useCallback(async () => {
    const s = await ScanDB.getGalleryStats();
    setStats(s);
  }, []);

  const loadGallery = useCallback(async () => {
    setLoading(true);
    const result = await ScanDB.getGalleryScans(page, PER_PAGE, selectedCategory, sort);
    setItems((result.items as unknown as GalleryItem[]) || []);
    setTotalPages(result.pages || 1);
    setTotalItems(result.total || 0);
    setLoading(false);
  }, [page, selectedCategory, sort]);

  useEffect(() => {
    loadCategories();
    loadStats();
  }, [loadCategories, loadStats]);

  useEffect(() => {
    loadGallery();
  }, [loadGallery]);

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-x-hidden">
      <GradientDots />
      <NavBar items={navItems} />

      {/* Hero */}
      <div className="pt-24 pb-8 px-4 text-center">
        <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/20 rounded-full px-4 py-1.5 mb-4">
          <Sparkles size={14} className="text-primary" />
          <span className="text-xs text-primary font-medium">Haftalık Otomatik Güncellenir</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-3">
          Discover <span className="text-primary">Gallery</span>
        </h1>
        <p className="text-muted-foreground text-lg max-w-xl mx-auto">
          Yapay zeka tarafından analiz edilen en yüksek potansiyelli Micro-SaaS fırsatları.
          Her hafta otomatik taranır ve puanlanır.
        </p>

        {/* Stats Bar */}
        <div className="flex flex-wrap items-center justify-center gap-6 mt-6">
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <LayoutGrid size={14} />
            <span>
              <strong className="text-foreground">{stats.total_ideas}</strong> Fikir
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <TrendingUp size={14} />
            <span>
              Ort. Puan:{" "}
              <strong className="text-foreground">
                {stats.avg_score?.toFixed(0) ?? "–"}
              </strong>
              /100
            </span>
          </div>
          {stats.top_category && (
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Flame size={14} />
              <span>
                En İyi: <strong className="text-foreground">{stats.top_category}</strong>
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-6xl mx-auto px-4 pb-4">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          {/* Category chips */}
          <button
            onClick={() => setCategory("")}
            className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              selectedCategory === ""
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-muted/40 text-muted-foreground border-border hover:border-primary/50 hover:text-foreground"
            }`}
          >
            Tümü
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                selectedCategory === cat
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-muted/40 text-muted-foreground border-border hover:border-primary/50 hover:text-foreground"
              }`}
            >
              {cat}
            </button>
          ))}

          {/* Sort */}
          <div className="ml-auto flex items-center gap-1.5 bg-muted/40 border border-border rounded-full px-1 py-1">
            <button
              onClick={() => setSort("score")}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                sort === "score"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Puan
            </button>
            <button
              onClick={() => setSort("date")}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                sort === "date"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Tarih
            </button>
          </div>
        </div>

        {/* Total count */}
        {!loading && (
          <p className="text-xs text-muted-foreground mb-4">
            {totalItems} fikir bulundu
            {selectedCategory ? ` "${selectedCategory}" kategorisinde` : ""}
          </p>
        )}

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-52 rounded-2xl bg-muted/30 animate-pulse" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-24 text-muted-foreground">
            <Sparkles size={36} className="mx-auto mb-3 opacity-30" />
            <p className="text-lg font-medium">Henüz galeri içeriği yok</p>
            <p className="text-sm mt-1">
              İlk galeri taramasını başlatmak için seed script&apos;ini çalıştır.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((item) => (
              <GalleryCard key={item.id} item={item} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 mt-8">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="flex items-center gap-1 px-3 py-1.5 rounded-full border border-border text-sm disabled:opacity-40 hover:border-primary/50 transition-colors"
            >
              <ChevronLeft size={14} /> Önceki
            </button>
            <span className="text-sm text-muted-foreground">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="flex items-center gap-1 px-3 py-1.5 rounded-full border border-border text-sm disabled:opacity-40 hover:border-primary/50 transition-colors"
            >
              Sonraki <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function GalleryCard({ item }: { item: GalleryItem }) {
  const score = item.gallery_score ?? 0;
  const style = getScoreStyle(score);
  const emoji = item.gallery_emoji || "💡";
  const title = item.gallery_title || item.category;
  const summary = item.gallery_summary || "";
  const tags = item.gallery_tags || [];
  const weekLabel = item.gallery_week
    ? `Hafta ${item.gallery_week.split("-W")[1] ?? ""} · ${item.gallery_week.split("-W")[0] ?? ""}`
    : new Date(item.created_at).toLocaleDateString("tr-TR", { month: "short", year: "numeric" });

  return (
    <Link
      href={`/gallery/${item.id}`}
      className="group relative bg-card/40 backdrop-blur-sm border border-border/60 rounded-2xl p-5 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5 transition-all duration-200 flex flex-col gap-3"
    >
      {/* Top row: emoji badge + score */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-3xl leading-none">{emoji}</span>
        <div
          className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${style.bg} ${style.text} ${style.border}`}
        >
          {score}
        </div>
      </div>

      {/* Title */}
      <h3 className="font-semibold text-base leading-snug group-hover:text-primary transition-colors line-clamp-2">
        {title}
      </h3>

      {/* Summary */}
      {summary && (
        <p className="text-sm text-muted-foreground line-clamp-3 flex-1">{summary}</p>
      )}

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-auto">
          {tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-muted/60 rounded-md text-xs text-muted-foreground border border-border/40"
            >
              {tag}
            </span>
          ))}
          {tags.length > 3 && (
            <span className="px-2 py-0.5 bg-muted/60 rounded-md text-xs text-muted-foreground border border-border/40">
              +{tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Footer: category + week */}
      <div className="flex items-center justify-between pt-2 border-t border-border/30 mt-1">
        <span className="text-xs text-muted-foreground">{item.category}</span>
        <span className="text-xs text-muted-foreground">{weekLabel}</span>
      </div>
    </Link>
  );
}