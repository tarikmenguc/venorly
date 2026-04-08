"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ScanDB } from "@/lib/scan-db";
import { GradientDots } from "@/components/ui/gradient-dots";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  ChevronRight,
  Sparkles,
  TrendingUp,
  Calendar,
  Tag,
  ExternalLink,
  RefreshCw,
  Download,
  Users,
  Flame,
} from "lucide-react";

interface GalleryDetail {
  id: string;
  category: string;
  mode: string;
  status: string;
  created_at: string;
  report_preview?: string;
  full_report?: string;
  leads_count?: number;
  angles_count?: number;
  gallery_title?: string;
  gallery_summary?: string;
  gallery_tags?: string[];
  gallery_score?: number;
  gallery_emoji?: string;
  gallery_week?: string;
}

const SCORE_COLORS = [
  { min: 85, bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30", label: "🔥 Çok Yüksek Potansiyel" },
  { min: 70, bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30", label: "✨ Yüksek Potansiyel" },
  { min: 50, bg: "bg-yellow-500/10", text: "text-yellow-400", border: "border-yellow-500/30", label: "⚡ Orta Potansiyel" },
  { min: 0, bg: "bg-gray-500/10", text: "text-gray-400", border: "border-gray-500/30", label: "💡 Gelişmekte" },
];

function getScoreStyle(score: number) {
  return SCORE_COLORS.find((c) => score >= c.min) || SCORE_COLORS[SCORE_COLORS.length - 1];
}

export default function GalleryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [item, setItem] = useState<GalleryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (id) {
      loadItem(id);
    }
  }, [id]);

  async function loadItem(itemId: string) {
    setLoading(true);
    const data = await ScanDB.getGalleryById(itemId);
    if (!data) {
      setNotFound(true);
    } else {
      setItem(data as unknown as GalleryDetail);
    }
    setLoading(false);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <GradientDots />
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Sparkles size={32} className="animate-pulse text-primary" />
          <p>Yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (notFound || !item) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <GradientDots />
        <p className="text-2xl font-bold">Fikir bulunamadı</p>
        <p className="text-muted-foreground">Bu kayıt mevcut değil veya silinmiş olabilir.</p>
        <Link href="/gallery" className="flex items-center gap-2 text-primary hover:underline">
          <ArrowLeft size={14} /> Galeriye Dön
        </Link>
      </div>
    );
  }

  const score = item.gallery_score ?? 0;
  const scoreStyle = getScoreStyle(score);
  const emoji = item.gallery_emoji || "💡";
  const title = item.gallery_title || item.category;
  const tags = item.gallery_tags || [];
  const weekLabel = item.gallery_week
    ? `${item.gallery_week.split("-W")[0]} · Hafta ${item.gallery_week.split("-W")[1]}`
    : new Date(item.created_at).toLocaleDateString("tr-TR", { month: "long", year: "numeric", day: "numeric" });

  const reportContent = item.full_report || item.report_preview || "";

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      <GradientDots />

      {/* Top nav bar */}
      <div className="fixed top-0 left-0 right-0 z-40 bg-background/80 backdrop-blur-md border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center gap-3">
          <Link
            href="/gallery"
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft size={14} />
            Geri
          </Link>
          <ChevronRight size={12} className="text-muted-foreground/50" />
          <span className="text-sm text-muted-foreground truncate max-w-xs">{title}</span>
          <div className="ml-auto flex items-center gap-2">
            <Link
              href="/"
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-border/60 hover:border-primary/50 transition-colors text-muted-foreground"
            >
              <RefreshCw size={12} />
              Yeni Tarama
            </Link>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-4xl mx-auto px-4 pt-24 pb-16">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-start gap-4 mb-4">
            <span className="text-5xl leading-none mt-1">{emoji}</span>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <Badge variant="outline" className="text-xs">
                  {item.category}
                </Badge>
                <Badge variant="outline" className="text-xs capitalize">
                  {item.mode} modu
                </Badge>
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Calendar size={11} />
                  {weekLabel}
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold leading-tight">{title}</h1>
            </div>
          </div>

          {/* Score badge */}
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl border ${scoreStyle.bg} ${scoreStyle.border} mb-4`}>
            <TrendingUp size={14} className={scoreStyle.text} />
            <span className={`text-sm font-bold ${scoreStyle.text}`}>{score}/100</span>
            <span className={`text-xs ${scoreStyle.text} opacity-80`}>{scoreStyle.label}</span>
          </div>

          {/* Summary */}
          {item.gallery_summary && (
            <p className="text-muted-foreground leading-relaxed mb-4">{item.gallery_summary}</p>
          )}

          {/* Tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="flex items-center gap-1 px-2.5 py-1 bg-muted/40 rounded-lg text-xs text-muted-foreground border border-border/40"
                >
                  <Tag size={10} />
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Meta stats */}
          <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
            {item.leads_count !== undefined && item.leads_count > 0 && (
              <span className="flex items-center gap-1">
                <Users size={11} />
                {item.leads_count} Lead Bulundu
              </span>
            )}
            {item.angles_count !== undefined && item.angles_count > 0 && (
              <span className="flex items-center gap-1">
                <Flame size={11} />
                {item.angles_count} Fırsat Açısı
              </span>
            )}
          </div>
        </div>

        {/* Report */}
        {reportContent ? (
          <div className="bg-card/40 backdrop-blur-sm border border-border/60 rounded-2xl p-6 md:p-8">
            <div className="prose prose-invert prose-sm max-w-none
              prose-headings:font-bold prose-headings:text-foreground
              prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
              prose-p:text-muted-foreground prose-p:leading-relaxed
              prose-strong:text-foreground prose-strong:font-semibold
              prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
              prose-pre:bg-muted prose-pre:border prose-pre:border-border
              prose-blockquote:border-l-primary prose-blockquote:text-muted-foreground
              prose-a:text-primary prose-a:no-underline hover:prose-a:underline
              prose-ul:text-muted-foreground prose-ol:text-muted-foreground
              prose-li:marker:text-primary
              prose-table:text-sm prose-th:text-foreground prose-td:text-muted-foreground
            ">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {reportContent}
              </ReactMarkdown>
            </div>
          </div>
        ) : (
          <div className="text-center py-16 text-muted-foreground">
            <p>Bu tarama için detaylı rapor mevcut değil.</p>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex flex-wrap gap-3 mt-8 pt-6 border-t border-border/40">
          <Link
            href={`/?rescan=${encodeURIComponent(item.category)}`}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:opacity-90 transition-opacity"
          >
            <RefreshCw size={14} />
            Bu Kategoriyi Yeniden Tara
          </Link>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/scans/${item.id}/pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 border border-border rounded-xl text-sm hover:border-primary/50 hover:text-primary transition-colors"
          >
            <Download size={14} />
            PDF İndir
          </a>
          <Link
            href={`/waitlist?category=${encodeURIComponent(item.category)}&title=${encodeURIComponent(title)}`}
            className="flex items-center gap-2 px-4 py-2.5 border border-border rounded-xl text-sm hover:border-primary/50 transition-colors"
          >
            <Users size={14} />
            Waitlist Oluştur
          </Link>
          <Link
            href="/gallery"
            className="flex items-center gap-2 px-4 py-2.5 border border-border rounded-xl text-sm hover:border-primary/50 transition-colors"
          >
            <ArrowLeft size={14} />
            Tüm Fikirlere Dön
          </Link>
        </div>
      </div>
    </div>
  );
}
