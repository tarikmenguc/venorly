"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { GradientDots } from "@/components/ui/gradient-dots";
import {
  ArrowLeft,
  BarChart3,
  Bell,
  Calendar,
  CheckCircle2,
  Cpu,
  CreditCard,
  Flame,
  Home,
  Layers,
  LayoutGrid,
  Loader2,
  Search,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  XCircle,
  Zap,
} from "lucide-react";

// ─── Types ─────────────────────────────────────────────────────────────────

interface ProfileStats {
  total_scans: number;
  completed: number;
  total_leads: number;
  total_angles: number;
  waitlist_count: number;
  total_emails: number;
  modes: {
    discover: number;
    deep: number;
    orchestrate: number;
    reverse: number;
    trends: number;
  };
}

interface ScanRecord {
  id: string;
  category: string;
  mode: string;
  created_at: string;
  status: "running" | "completed" | "failed";
  leads_count: number;
  angles_count: number;
}

interface ProfileData {
  stats: ProfileStats;
  recent_scans: ScanRecord[];
  member_since: string | null;
  favorite_mode: string | null;
  top_categories: { category: string; count: number }[];
}

// ─── Helpers ────────────────────────────────────────────────────────────────

const MODE_CONFIG: Record<
  string,
  { label: string; color: string; gradient: string; icon: typeof Search }
> = {
  discover:    { label: "Keşfet",       color: "bg-blue-500",   gradient: "from-blue-600 to-cyan-400",    icon: Search },
  deep:        { label: "Derin Analiz", color: "bg-purple-500", gradient: "from-purple-600 to-violet-400", icon: Cpu },
  orchestrate: { label: "Orkestratör", color: "bg-amber-500",   gradient: "from-amber-500 to-orange-400", icon: Zap },
  reverse:     { label: "Rakip Ara",   color: "bg-rose-500",    gradient: "from-red-500 to-rose-400",     icon: TrendingUp },
  trends:      { label: "Trendler",    color: "bg-emerald-500", gradient: "from-green-500 to-emerald-400",icon: BarChart3 },
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function StatusIcon({ status }: { status: ScanRecord["status"] }) {
  if (status === "completed") return <CheckCircle2 size={14} className="text-emerald-400" />;
  if (status === "failed")    return <XCircle      size={14} className="text-rose-400" />;
  return <Loader2 size={14} className="animate-spin text-blue-400" />;
}

// ─── Component ──────────────────────────────────────────────────────────────

export default function ProfilePage() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const [data, setData] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/profile")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: ProfileData) => setData(d))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  // ── Loading ──
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <GradientDots />
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Loader2 size={32} className="animate-spin text-primary" />
          <p>Profil yükleniyor...</p>
        </div>
      </div>
    );
  }

  // ── Error ──
  if (error || !data) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <GradientDots />
        <XCircle size={40} className="text-rose-400" />
        <p className="text-lg font-semibold">Profil yüklenemedi</p>
        <p className="text-sm text-muted-foreground">{error}</p>
        <button
          onClick={() => router.push("/")}
          className="mt-2 flex items-center gap-2 px-4 py-2 rounded-xl border border-border hover:border-primary/50 text-sm transition-colors"
        >
          <Home size={14} /> Ana Sayfaya Dön
        </button>
      </div>
    );
  }

  const { stats, recent_scans, member_since, favorite_mode, top_categories } = data;
  const favModeConfig = favorite_mode ? MODE_CONFIG[favorite_mode] : null;
  const totalModeCount = Object.values(stats.modes).reduce((s, v) => s + v, 0) || 1;

  const statCards = [
    {
      title: "Toplam Tarama",
      value: stats.total_scans,
      sub: `${stats.completed} tamamlandı`,
      gradient: "from-blue-600 to-blue-400",
      icon: LayoutGrid,
    },
    {
      title: "Bulunan Lead",
      value: stats.total_leads,
      sub: "Potansiyel müşteri",
      gradient: "from-purple-600 to-violet-400",
      icon: Users,
    },
    {
      title: "Fırsat Açısı",
      value: stats.total_angles,
      sub: "Üretilen hipotez",
      gradient: "from-amber-500 to-orange-400",
      icon: Sparkles,
    },
    {
      title: "E-posta Kaydı",
      value: stats.total_emails,
      sub: `${stats.waitlist_count} waitlist`,
      gradient: "from-emerald-500 to-green-400",
      icon: Target,
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      <GradientDots />

      {/* ── Top Nav ── */}
      <div className="fixed top-0 left-0 right-0 z-40 bg-background/80 backdrop-blur-md border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft size={14} /> Geri
          </button>
          <span className="text-sm text-muted-foreground/50">/</span>
          <span className="text-sm font-medium">Profil</span>
          <div className="ml-auto flex items-center gap-2">
            <Link href="/dashboard" className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-border/60 hover:border-primary/50 transition-colors text-muted-foreground">
              <BarChart3 size={12} /> Dashboard
            </Link>
            <Link href="/gallery" className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-border/60 hover:border-primary/50 transition-colors text-muted-foreground">
              <Sparkles size={12} /> Galeri
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 pt-24 pb-16 space-y-6">

        {/* ── Identity Card ── */}
        <div className="bg-card/40 backdrop-blur-sm border border-border/60 rounded-2xl p-6">
          <div className="flex items-center gap-5">
            {/* Avatar */}
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-primary/50 border border-primary/30 flex items-center justify-center text-2xl font-bold text-white flex-shrink-0">
              {user?.email?.[0]?.toUpperCase() ?? "🚀"}
            </div>

            <div className="flex-1 min-w-0">
              {user ? (
                <>
                  <h1 className="text-xl font-bold truncate">{user.email}</h1>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Supabase UID: <span className="font-mono">{user.id.slice(0, 8)}…</span>
                  </p>
                </>
              ) : (
                <>
                  <h1 className="text-xl font-bold">Startup Idea Finder</h1>
                  <p className="text-sm text-muted-foreground mt-0.5">Kişisel pazar istihbarat motoru</p>
                </>
              )}
              {member_since && (
                <p className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
                  <Calendar size={11} />
                  İlk tarama: {formatDate(member_since)}
                </p>
              )}
            </div>

            <div className="hidden sm:flex flex-col items-end gap-2 flex-shrink-0">
              {favModeConfig && (
                <div className={`flex items-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-br ${favModeConfig.gradient} bg-opacity-10 border border-white/10`}>
                  <favModeConfig.icon size={14} className="text-white" />
                  <span className="text-xs font-medium text-white whitespace-nowrap">
                    Favori: {favModeConfig.label}
                  </span>
                </div>
              )}
              {user ? (
                <button
                  onClick={async () => { await signOut(); router.push("/"); }}
                  className="text-xs px-3 py-1.5 rounded-full border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  Çıkış Yap
                </button>
              ) : (
                <Link href="/sign-in" className="text-xs px-3 py-1.5 rounded-full border border-primary/40 text-primary hover:bg-primary/10 transition-colors">
                  Giriş Yap
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* ── Stat Cards ── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {statCards.map((card) => (
            <div
              key={card.title}
              className="relative overflow-hidden rounded-xl bg-card border border-white/5 p-4 group hover:border-white/10 transition-all"
            >
              <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${card.gradient} opacity-10 rounded-full blur-2xl group-hover:opacity-20 transition-opacity`} />
              <div className="relative z-10">
                <div className={`inline-flex p-2 rounded-lg bg-gradient-to-br ${card.gradient} bg-opacity-20 mb-2`}>
                  <card.icon size={14} className="text-white" />
                </div>
                <p className="text-2xl font-bold text-white">{card.value}</p>
                <p className="text-[11px] text-muted-foreground uppercase tracking-wide mt-0.5">{card.title}</p>
                <p className="text-[11px] text-muted-foreground/70 mt-0.5">{card.sub}</p>
              </div>
            </div>
          ))}
        </div>

        {/* ── Mode Breakdown + Top Categories ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

          {/* Mode Breakdown */}
          <div className="bg-card/40 backdrop-blur-sm border border-border/60 rounded-2xl p-5">
            <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
              <Layers size={14} className="text-primary" />
              Mod Dağılımı
            </h2>
            <div className="space-y-3">
              {(Object.entries(stats.modes) as [string, number][])
                .sort((a, b) => b[1] - a[1])
                .map(([mode, count]) => {
                  const cfg = MODE_CONFIG[mode];
                  if (!cfg) return null;
                  const pct = Math.round((count / totalModeCount) * 100);
                  return (
                    <div key={mode}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-muted-foreground flex items-center gap-1.5">
                          <cfg.icon size={11} />
                          {cfg.label}
                        </span>
                        <span className="text-xs font-medium text-foreground">{count}</span>
                      </div>
                      <div className="h-1.5 bg-muted/40 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full bg-gradient-to-r ${cfg.gradient} transition-all duration-500`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Top Categories */}
          <div className="bg-card/40 backdrop-blur-sm border border-border/60 rounded-2xl p-5">
            <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
              <Flame size={14} className="text-primary" />
              En Çok Taranan Kategoriler
            </h2>
            {top_categories.length === 0 ? (
              <p className="text-xs text-muted-foreground">Henüz tamamlanan tarama yok.</p>
            ) : (
              <div className="space-y-2">
                {top_categories.map((tc, i) => (
                  <div key={tc.category} className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground/60 w-4 text-right">{i + 1}</span>
                    <span className="flex-1 text-sm text-foreground truncate">{tc.category}</span>
                    <span className="text-xs px-2 py-0.5 bg-muted/40 border border-border/40 rounded-full text-muted-foreground">
                      {tc.count}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Recent Scans ── */}
        <div className="bg-card/40 backdrop-blur-sm border border-border/60 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold flex items-center gap-2">
              <Search size={14} className="text-primary" />
              Son Taramalar
            </h2>
            <Link href="/dashboard" className="text-xs text-primary hover:underline">
              Tümünü Gör →
            </Link>
          </div>

          {recent_scans.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <LayoutGrid size={28} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Henüz tarama yapılmamış.</p>
              <Link href="/" className="text-xs text-primary hover:underline mt-1 inline-block">
                İlk taramanı başlat →
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {recent_scans.map((scan) => {
                const cfg = MODE_CONFIG[scan.mode];
                return (
                  <Link
                    key={scan.id}
                    href={`/scan/${scan.id}`}
                    className="flex items-center gap-3 p-3 rounded-xl border border-border/40 hover:border-primary/30 hover:bg-card/60 transition-all group"
                  >
                    <StatusIcon status={scan.status} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                        {scan.category}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatDate(scan.created_at)}
                      </p>
                    </div>
                    {cfg && (
                      <span className={`text-[11px] px-2 py-0.5 rounded-full border border-white/10 bg-gradient-to-br ${cfg.gradient} text-white font-medium flex-shrink-0`}>
                        {cfg.label}
                      </span>
                    )}
                    {scan.leads_count > 0 && (
                      <span className="text-[11px] text-muted-foreground flex items-center gap-0.5 flex-shrink-0">
                        <Users size={10} /> {scan.leads_count}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Quick Links ── */}
        <div className="bg-card/40 backdrop-blur-sm border border-border/60 rounded-2xl p-5">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Zap size={14} className="text-primary" />
            Hızlı Erişim
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { href: "/",          icon: Home,        label: "Ana Sayfa" },
              { href: "/dashboard", icon: BarChart3,   label: "Dashboard" },
              { href: "/leads",     icon: Target,      label: "Leads" },
              { href: "/gallery",   icon: Sparkles,    label: "Galeri" },
              { href: "/alerts",    icon: Bell,        label: "Alarmlar" },
              { href: "/pricing",   icon: CreditCard,  label: "Fiyatlandırma" },
            ].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-2 px-3 py-2.5 rounded-xl border border-border/40 hover:border-primary/40 hover:bg-card/60 text-sm text-muted-foreground hover:text-foreground transition-all"
              >
                <item.icon size={13} />
                {item.label}
              </Link>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
