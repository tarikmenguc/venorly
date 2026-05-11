"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Users,
  Mail,
  ExternalLink,
  Copy,
  Check,
  ArrowLeft,
  Filter,
  Inbox,
  MessageSquare,
  CheckCircle2,
  Archive,
  Loader2,
  Search,
  Download,
  X,
  Calendar,
} from "lucide-react";
import { supabase } from "@/lib/supabase";

interface Lead {
  id: string;
  source: string;
  title: string;
  url: string;
  desc: string;
  score: number;
  status: "new" | "contacted" | "converted" | "archived";
  dm_template: string;
  scan_category: string;
  added_at: string;
}

interface LeadStats {
  total: number;
  new_count: number;
  contacted: number;
  converted: number;
  archived: number;
  by_source: Record<string, number>;
}

const STATUS_CONFIG = {
  new: { label: "Yeni", icon: Inbox, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  contacted: { label: "İletişime Geçildi", icon: MessageSquare, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  converted: { label: "Dönüştürüldü", icon: CheckCircle2, color: "text-green-400", bg: "bg-green-500/10 border-green-500/20" },
  archived: { label: "Arşiv", icon: Archive, color: "text-gray-400", bg: "bg-gray-500/10 border-gray-500/20" },
};

function exportToCSV(leads: Lead[]) {
  const headers = ["ID", "Kaynak", "Başlık", "URL", "Açıklama", "Skor", "Durum", "Kategori", "Eklenme Tarihi"];
  const rows = leads.map((l) => [
    l.id,
    l.source,
    `"${(l.title || "").replace(/"/g, '""')}"`,
    l.url || "",
    `"${(l.desc || "").replace(/"/g, '""')}"`,
    l.score,
    l.status,
    l.scan_category || "",
    l.added_at ? new Date(l.added_at).toISOString() : "",
  ]);

  const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `leads_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [allLeads, setAllLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<LeadStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const router = useRouter();
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounce search
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setDebouncedSearch(search), 350);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [search]);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      const params = filter !== "all" ? `?status=${filter}` : "";
      const res = await fetch(`/api/leads${params}`, {
        headers: {
          ...(token && { "Authorization": `Bearer ${token}` })
        }
      });
      const data = await res.json();
      setAllLeads(data.leads || []);
      setStats(data.stats || null);
    } catch (e) {
      console.error("Leads hatası:", e);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  // Client-side filtering: search + date range
  useEffect(() => {
    let filtered = [...allLeads];

    if (debouncedSearch.trim()) {
      const q = debouncedSearch.toLowerCase();
      filtered = filtered.filter(
        (l) =>
          l.title?.toLowerCase().includes(q) ||
          l.desc?.toLowerCase().includes(q) ||
          l.source?.toLowerCase().includes(q) ||
          l.scan_category?.toLowerCase().includes(q)
      );
    }

    if (dateFrom) {
      const from = new Date(dateFrom);
      filtered = filtered.filter((l) => l.added_at && new Date(l.added_at) >= from);
    }
    if (dateTo) {
      const to = new Date(dateTo);
      to.setHours(23, 59, 59, 999);
      filtered = filtered.filter((l) => l.added_at && new Date(l.added_at) <= to);
    }

    setLeads(filtered);
  }, [allLeads, debouncedSearch, dateFrom, dateTo]);

  async function updateStatus(id: string, status: string) {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      await fetch("/api/leads", {
        method: "PATCH",
        headers: { 
          "Content-Type": "application/json",
          ...(token && { "Authorization": `Bearer ${token}` })
        },
        body: JSON.stringify({ id, status }),
      });
      fetchLeads();
    } catch (e) {
      console.error("Status güncelleme hatası:", e);
    }
  }

  function copyDM(id: string, text: string) {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  const hasActiveFilters = debouncedSearch || dateFrom || dateTo;

  function clearFilters() {
    setSearch("");
    setDebouncedSearch("");
    setDateFrom("");
    setDateTo("");
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/5 bg-gradient-to-r from-background via-blue-950/10 to-background">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                Lead Yönetimi
              </h1>
              <p className="text-muted-foreground mt-1">Potansiyel müşterilerinizi takip edin</p>
            </div>
            <div className="flex items-center gap-3">
              {allLeads.length > 0 && (
                <button
                  onClick={() => exportToCSV(leads.length > 0 ? leads : allLeads)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600/15 border border-green-500/20 text-sm text-green-400 hover:bg-green-600/25 transition-all"
                >
                  <Download className="w-4 h-4" />
                  CSV İndir ({leads.length})
                </button>
              )}
              <button
                onClick={() => router.push("/dashboard")}
                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" /> Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Pipeline Stats */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {(Object.entries(STATUS_CONFIG) as [keyof typeof STATUS_CONFIG, typeof STATUS_CONFIG[keyof typeof STATUS_CONFIG]][]).map(([key, cfg]) => {
              const count = key === "new" ? stats.new_count : stats[key as keyof LeadStats] as number;
              return (
                <button
                  key={key}
                  onClick={() => setFilter(filter === key ? "all" : key)}
                  className={`rounded-xl border p-4 text-left transition-all hover:scale-[1.02] ${
                    filter === key ? cfg.bg : "bg-card border-white/5 hover:border-white/10"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <cfg.icon className={`w-5 h-5 ${cfg.color}`} />
                    <span className="text-2xl font-bold text-white">{count || 0}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">{cfg.label}</p>
                </button>
              );
            })}
          </div>
        )}

        {/* Search + Date Filter Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Başlık, kaynak veya kategori ara..."
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:border-purple-500/50 focus:bg-white/8 transition-all"
            />
            {search && (
              <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Date From */}
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="pl-10 pr-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-purple-500/50 transition-all [color-scheme:dark]"
              title="Başlangıç tarihi"
            />
          </div>

          <span className="text-muted-foreground text-sm text-center">—</span>

          {/* Date To */}
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="pl-10 pr-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:border-purple-500/50 transition-all [color-scheme:dark]"
              title="Bitiş tarihi"
            />
          </div>

          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-xs text-muted-foreground hover:text-white hover:bg-white/10 transition-all whitespace-nowrap"
            >
              <X className="w-3.5 h-3.5" /> Temizle
            </button>
          )}
        </div>

        {/* Source Filter Tags */}
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Durum:</span>
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1 rounded-full text-xs transition-all ${
              filter === "all" ? "bg-white/10 text-white" : "text-muted-foreground hover:text-white"
            }`}
          >
            Tümü ({stats?.total || 0})
          </button>
          {stats && Object.entries(stats.by_source).map(([source, count]) => (
            <span key={source} className="px-2 py-1 rounded-full text-xs bg-white/5 text-muted-foreground">
              {source}: {count}
            </span>
          ))}
          {hasActiveFilters && (
            <span className="px-2 py-1 rounded-full text-xs bg-purple-500/15 text-purple-400 border border-purple-500/20">
              {leads.length} sonuç gösteriliyor
            </span>
          )}
        </div>

        {/* Lead List */}
        {leads.length === 0 ? (
          <div className="rounded-xl bg-card border border-white/5 p-16 text-center">
            <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            {hasActiveFilters ? (
              <>
                <p className="text-lg text-muted-foreground">Arama kriterlerine uyan lead bulunamadı.</p>
                <button onClick={clearFilters} className="mt-4 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:text-white transition-all">
                  Filtreleri Temizle
                </button>
              </>
            ) : (
              <>
                <p className="text-lg text-muted-foreground">Henüz lead bulunmuyor.</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Derin Analiz veya Orkestratör modunda tarama yaparak lead toplayabilirsiniz.
                </p>
                <button
                  onClick={() => router.push("/")}
                  className="mt-6 px-6 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-violet-500 text-white text-sm font-medium hover:opacity-90 transition-all"
                >
                  Tarama Başlat →
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {leads.map((lead) => {
              const statusCfg = STATUS_CONFIG[lead.status];
              return (
                <div
                  key={lead.id}
                  className="rounded-xl bg-card border border-white/5 p-5 hover:border-white/10 transition-all group"
                >
                  <div className="flex items-start gap-4">
                    {/* Source Badge */}
                    <div className="shrink-0">
                      <span className="text-[10px] px-2 py-1 rounded-full bg-white/5 text-muted-foreground font-medium">
                        {lead.source}
                      </span>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-white truncate">{lead.title}</p>
                        {lead.url && (
                          <a
                            href={lead.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="shrink-0 text-muted-foreground hover:text-white transition-colors"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                      {lead.desc && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{lead.desc}</p>
                      )}

                      {/* DM Template */}
                      {lead.dm_template && (
                        <div className="mt-3 p-3 rounded-lg bg-white/3 border border-white/5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[10px] text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                              <Mail className="w-3 h-3" /> DM Şablonu
                            </span>
                            <button
                              onClick={() => copyDM(lead.id, lead.dm_template)}
                              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-white transition-colors"
                            >
                              {copiedId === lead.id ? (
                                <><Check className="w-3 h-3 text-green-400" /> Kopyalandı</>
                              ) : (
                                <><Copy className="w-3 h-3" /> Kopyala</>
                              )}
                            </button>
                          </div>
                          <p className="text-xs text-muted-foreground/80 line-clamp-3">{lead.dm_template}</p>
                        </div>
                      )}
                    </div>

                    {/* Status + Actions */}
                    <div className="shrink-0 flex flex-col items-end gap-2">
                      <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${statusCfg.bg}`}>
                        <statusCfg.icon className={`w-3 h-3 ${statusCfg.color}`} />
                        <span className={statusCfg.color}>{statusCfg.label}</span>
                      </div>

                      {/* Status transition buttons */}
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {lead.status === "new" && (
                          <button
                            onClick={() => updateStatus(lead.id, "contacted")}
                            className="px-2 py-1 text-[10px] rounded bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 transition-colors"
                          >
                            İletişime Geç
                          </button>
                        )}
                        {lead.status === "contacted" && (
                          <button
                            onClick={() => updateStatus(lead.id, "converted")}
                            className="px-2 py-1 text-[10px] rounded bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors"
                          >
                            Dönüştür
                          </button>
                        )}
                        {lead.status !== "archived" && (
                          <button
                            onClick={() => updateStatus(lead.id, "archived")}
                            className="px-2 py-1 text-[10px] rounded bg-white/5 text-muted-foreground hover:bg-white/10 transition-colors"
                          >
                            Arşivle
                          </button>
                        )}
                      </div>

                      <span className="text-[10px] text-muted-foreground">
                        {new Date(lead.added_at).toLocaleDateString("tr-TR", { day: "numeric", month: "short" })}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer */}
        <div className="text-center py-6">
          <p className="text-xs text-muted-foreground">
            Startup Idea Finder V6 — Lead Pipeline 🎯
          </p>
        </div>
      </div>
    </div>
  );
}
