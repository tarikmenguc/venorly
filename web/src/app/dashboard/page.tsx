"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart3,
  TrendingUp,
  Users,
  Mail,
  Search,
  Cpu,
  Zap,
  ArrowRight,
  Clock,
  CheckCircle2,
  XCircle,
  Sparkles,
  Loader2,
  Bell,
  CreditCard,
  Target,
} from "lucide-react";

interface DashboardStats {
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
  report_preview: string;
  leads_count: number;
  angles_count: number;
}

const MODE_CONFIG: Record<string, { label: string; color: string; icon: typeof Search }> = {
  discover: { label: "Keşfet", color: "from-blue-500 to-cyan-400", icon: Search },
  deep: { label: "Derin Analiz", color: "from-purple-500 to-violet-400", icon: Cpu },
  orchestrate: { label: "Orkestratör", color: "from-amber-500 to-orange-400", icon: Users },
  reverse: { label: "Rakip Ara", color: "from-red-500 to-rose-400", icon: TrendingUp },
  trends: { label: "Trendler", color: "from-green-500 to-emerald-400", icon: BarChart3 },
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentScans, setRecentScans] = useState<ScanRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchDashboard();
  }, []);

  async function fetchDashboard() {
    try {
      const res = await fetch("/api/dashboard");
      const data = await res.json();
      setStats(data.stats);
      setRecentScans(data.recent_scans || []);
    } catch (e) {
      console.error("Dashboard hatası:", e);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
          <p className="text-muted-foreground animate-pulse">Dashboard yükleniyor...</p>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: "Toplam Tarama",
      value: stats?.total_scans || 0,
      icon: BarChart3,
      gradient: "from-blue-600 to-blue-400",
      desc: `${stats?.completed || 0} tamamlandı`,
    },
    {
      title: "Bulunan Lead'ler",
      value: stats?.total_leads || 0,
      icon: Users,
      gradient: "from-purple-600 to-violet-400",
      desc: "Hazır alıcılar",
    },
    {
      title: "İş Fikirleri",
      value: stats?.total_angles || 0,
      icon: Sparkles,
      gradient: "from-amber-500 to-orange-400",
      desc: "Üretilen hipotezler",
    },
    {
      title: "Waitlist Kayıtları",
      value: stats?.total_emails || 0,
      icon: Mail,
      gradient: "from-green-500 to-emerald-400",
      desc: `${stats?.waitlist_count || 0} aktif waitlist`,
    },
  ];

  const quickActions = [
    { label: "Yeni Keşfet Taraması", mode: "discover", icon: Search, gradient: "from-blue-600 to-cyan-500" },
    { label: "Derin Analiz Başlat", mode: "deep", icon: Cpu, gradient: "from-purple-600 to-violet-500" },
    { label: "Orkestratör Çalıştır", mode: "orchestrate", icon: Zap, gradient: "from-amber-500 to-orange-500" },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/5 bg-gradient-to-r from-background via-purple-950/10 to-background">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                Dashboard
              </h1>
              <p className="text-muted-foreground mt-1">Startup Idea Finder — Genel bakış</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => router.push("/leads")}
                className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-1.5"
              >
                <Target className="w-3.5 h-3.5" /> Lead'ler
              </button>
              <button
                onClick={() => router.push("/alerts")}
                className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-1.5"
              >
                <Bell className="w-3.5 h-3.5" /> Alarmlar
              </button>
              <button
                onClick={() => router.push("/pricing")}
                className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-1.5"
              >
                <CreditCard className="w-3.5 h-3.5" /> Fiyatlandırma
              </button>
              <button
                onClick={() => router.push("/")}
                className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all"
              >
                ← Ana Sayfa
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((card) => (
            <div
              key={card.title}
              className="relative overflow-hidden rounded-xl bg-card border border-white/5 p-5 group hover:border-white/10 transition-all"
            >
              <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${card.gradient} opacity-10 rounded-full blur-2xl group-hover:opacity-20 transition-opacity`} />
              <div className="relative z-10 flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">{card.title}</p>
                  <p className="text-3xl font-bold mt-1 text-white">{card.value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{card.desc}</p>
                </div>
                <div className={`p-2.5 rounded-lg bg-gradient-to-br ${card.gradient} bg-opacity-20`}>
                  <card.icon className="w-5 h-5 text-white" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Hızlı İşlemler</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {quickActions.map((action) => (
              <button
                key={action.mode}
                onClick={() => router.push(`/?mode=${action.mode}`)}
                className={`flex items-center gap-3 p-4 rounded-xl bg-gradient-to-br ${action.gradient} bg-opacity-10 border border-white/5 hover:border-white/20 hover:scale-[1.02] transition-all group`}
                style={{ background: `linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01))` }}
              >
                <div className={`p-2 rounded-lg bg-gradient-to-br ${action.gradient}`}>
                  <action.icon className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm text-white font-medium">{action.label}</span>
                <ArrowRight className="w-4 h-4 text-muted-foreground ml-auto group-hover:text-white group-hover:translate-x-1 transition-all" />
              </button>
            ))}
          </div>
        </div>

        {/* Scan Mode Distribution */}
        {stats && (stats.modes.discover + stats.modes.deep + stats.modes.orchestrate + stats.modes.reverse + stats.modes.trends > 0) && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Mod Dağılımı</h2>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {Object.entries(stats.modes).map(([mode, count]) => {
                const cfg = MODE_CONFIG[mode];
                if (!cfg) return null;
                return (
                  <div key={mode} className="rounded-xl bg-card border border-white/5 p-4 text-center">
                    <div className={`inline-flex p-2 rounded-lg bg-gradient-to-br ${cfg.color} mb-2`}>
                      <cfg.icon className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-2xl font-bold text-white">{count}</p>
                    <p className="text-xs text-muted-foreground">{cfg.label}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Recent Scans */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Son Taramalar</h2>
          {recentScans.length === 0 ? (
            <div className="rounded-xl bg-card border border-white/5 p-12 text-center">
              <Search className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">Henüz tarama yapılmadı.</p>
              <p className="text-xs text-muted-foreground mt-1">Ana sayfadan bir tarama başlatarak burada geçmişinizi görün.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentScans.map((scan) => {
                const cfg = MODE_CONFIG[scan.mode] || MODE_CONFIG.discover;
                return (
                  <div
                    key={scan.id}
                    className="flex items-center gap-4 rounded-xl bg-card border border-white/5 p-4 hover:border-white/10 transition-all group cursor-pointer"
                  >
                    <div className={`p-2.5 rounded-lg bg-gradient-to-br ${cfg.color} shrink-0`}>
                      <cfg.icon className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-white truncate">{scan.category || "Genel Tarama"}</p>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-muted-foreground shrink-0">
                          {cfg.label}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5 truncate">
                        {scan.report_preview || "Rapor bekleniyor..."}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      {scan.leads_count > 0 && (
                        <span className="text-xs text-muted-foreground">
                          {scan.leads_count} lead
                        </span>
                      )}
                      <div className="flex items-center gap-1.5">
                        {scan.status === "completed" && <CheckCircle2 className="w-4 h-4 text-green-400" />}
                        {scan.status === "running" && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
                        {scan.status === "failed" && <XCircle className="w-4 h-4 text-red-400" />}
                      </div>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(scan.created_at).toLocaleDateString("tr-TR", { day: "numeric", month: "short" })}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center py-6">
          <p className="text-xs text-muted-foreground">
            Startup Idea Finder V6 — Friction Economy Engine 🚀
          </p>
        </div>
      </div>
    </div>
  );
}
