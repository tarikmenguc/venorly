"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  FileText,
  Users,
  Sparkles,
  Clock,
  Search,
  Download,
  Loader2,
  CheckCircle2,
  XCircle,
  Presentation,
  Globe,
  RefreshCw,
  MessageSquare,
  ExternalLink,
} from "lucide-react";
import { ScanDB, ScanRecord } from "@/lib/scan-db";
import { apiFetch } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Badge } from "@/components/ui/badge";

export default function ScanDetailPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<ScanRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [isDownloadingDeck, setIsDownloadingDeck] = useState(false);
  const [isDownloadingPage, setIsDownloadingPage] = useState(false);

  useEffect(() => {
    fetchScan();
  }, [id]);

  async function fetchScan() {
    try {
      const data = await ScanDB.getById(id);
      setScan(data);
    } catch (e) {
      console.error("Scan fetch error:", e);
    } finally {
      setLoading(false);
    }
  }

  const handleExportPDF = async () => {
    setIsExporting(true);
    try {
      const res = await apiFetch(`/api/scans/${id}/pdf`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rapor_${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("PDF Export Error:", e);
      alert("PDF oluşturulurken bir hata oluştu.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownloadDeck = async () => {
    setIsDownloadingDeck(true);
    try {
      const res = await apiFetch(`/api/scans/${id}/pitch-deck`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pitch_deck_${id.slice(0, 8)}.pptx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Pitch Deck Error:", e);
      alert("Pitch deck oluşturulurken bir hata oluştu.");
    } finally {
      setIsDownloadingDeck(false);
    }
  };

  const handleDownloadLandingPage = async () => {
    setIsDownloadingPage(true);
    try {
      const res = await apiFetch(`/api/scans/${id}/landing-page`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `landing_page_${id.slice(0, 8)}.html`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Landing Page Error:", e);
      alert("Landing page oluşturulurken bir hata oluştu.");
    } finally {
      setIsDownloadingPage(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
          <p className="text-muted-foreground">Rapor yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6 text-center">
        <div className="space-y-4">
          <XCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">Tarama Bulunamadı</h2>
          <p className="text-muted-foreground">Aradığınız tarama kaydı veritabanında mevcut değil.</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="px-6 py-2 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10"
          >
            Dashboard&apos;a Dön
          </button>
        </div>
      </div>
    );
  }

  const fullReport = (scan as any).full_report || {};
  const reportContent = fullReport?.final_report || fullReport?.investment_memo || scan.report_preview;
  const buyerLeads: any[] = fullReport?.buyer_leads || [];
  const pivotSuggestions: string[] = fullReport?.report_json?.pivot_suggestions || [];

  // Validation score banner
  const validationDetails: string = fullReport?.validation_details || "";
  const scoreMatch = validationDetails.match(/Fizibilite Skoru.*?(\d+)\/50/);
  const validationScore = scoreMatch ? parseInt(scoreMatch[1]) : null;
  const scoreBanner = validationScore !== null
    ? validationScore >= 35
      ? { color: "green", label: "🟢 Güçlü Fırsat", bg: "bg-green-500/10 border-green-500/30", text: "text-green-400", desc: "Bu fikir yüksek potansiyel taşıyor." }
      : validationScore >= 20
        ? { color: "yellow", label: "🟡 Araştırmaya Değer", bg: "bg-yellow-500/10 border-yellow-500/30", text: "text-yellow-400", desc: "Ümit verici ancak bazı riskler mevcut." }
        : { color: "red", label: "🔴 Riskli", bg: "bg-red-500/10 border-red-500/30", text: "text-red-400", desc: "Bu fikir önemli riskler içeriyor." }
    : null;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/5 bg-gradient-to-r from-background via-indigo-950/10 to-background shadow-lg">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                  {scan.category}
                </h1>
                <Badge variant="outline" className="text-[10px] uppercase tracking-wider bg-white/5 border-white/10 text-muted-foreground mr-2">
                  {scan.mode}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-1 font-mono opacity-50">ID: {id}</p>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {/* PDF */}
              <button
                onClick={handleExportPDF}
                disabled={isExporting}
                className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-2 cursor-pointer"
              >
                {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                PDF
              </button>
              {/* Pitch Deck */}
              <button
                onClick={handleDownloadDeck}
                disabled={isDownloadingDeck}
                className="px-3 py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-sm text-purple-300 hover:bg-purple-500/20 hover:text-purple-200 transition-all flex items-center gap-2 cursor-pointer"
              >
                {isDownloadingDeck ? <Loader2 className="w-4 h-4 animate-spin" /> : <Presentation className="w-4 h-4" />}
                Pitch Deck
              </button>
              {/* Landing Page */}
              <button
                onClick={handleDownloadLandingPage}
                disabled={isDownloadingPage}
                className="px-3 py-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm text-blue-300 hover:bg-blue-500/20 hover:text-blue-200 transition-all flex items-center gap-2 cursor-pointer"
              >
                {isDownloadingPage ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
                Landing Page
              </button>
              <button
                onClick={() => router.push("/dashboard")}
                className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" /> Geri
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-xl bg-card border border-white/5 p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <Search className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Kategori</p>
              <p className="font-bold text-white truncate max-w-[150px]">{scan.category}</p>
            </div>
          </div>
          <div className="rounded-xl bg-card border border-white/5 p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <Sparkles className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Üretilen Fikirler</p>
              <p className="font-bold text-white">{scan.angles_count || 0}</p>
            </div>
          </div>
          <div className="rounded-xl bg-card border border-white/5 p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
              <Users className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Bulunan Lead&apos;ler</p>
              <p className="font-bold text-white">{buyerLeads.length || scan.leads_count || 0}</p>
            </div>
          </div>
        </div>

        {/* Score Banner */}
        {scoreBanner && (
          <div className={`rounded-xl border p-4 flex items-center gap-4 ${scoreBanner.bg}`}>
            <div className="text-2xl">{scoreBanner.label.split(" ")[0]}</div>
            <div>
              <p className={`font-bold text-sm ${scoreBanner.text}`}>
                {scoreBanner.label} — {validationScore}/50
              </p>
              <p className="text-xs text-muted-foreground">{scoreBanner.desc}</p>
            </div>
            <div className="ml-auto">
              <div className="flex gap-1">
                {Array.from({ length: 10 }).map((_, i) => (
                  <div
                    key={i}
                    className={`h-2 w-4 rounded-full transition-colors ${
                      i < Math.round((validationScore! / 50) * 10)
                        ? scoreBanner.color === "green"
                          ? "bg-green-500"
                          : scoreBanner.color === "yellow"
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        : "bg-white/10"
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Report Content */}
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" /> Tarama Raporu
          </h2>
          <div className="rounded-2xl bg-black/40 border border-white/5 p-8 backdrop-blur-xl prose prose-invert prose-indigo max-w-none shadow-2xl">
            {reportContent ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {reportContent}
              </ReactMarkdown>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground italic">Rapor içeriği henüz yüklenmemiş veya mevcut değil.</p>
              </div>
            )}
          </div>
        </div>

        {/* Pivot Önerileri — sadece düşük skor varsa göster */}
        {pivotSuggestions.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-orange-400" /> Alternatif Pivot Önerileri
            </h2>
            <div className="rounded-xl bg-orange-500/5 border border-orange-500/20 p-6 space-y-3">
              <p className="text-xs text-orange-300/70 mb-4">Bu fikir düşük skor aldı. İşte değerlendirilebilecek 3 alternatif yön:</p>
              {pivotSuggestions.map((pivot, i) => (
                <div key={i} className="flex items-start gap-3 bg-white/5 rounded-lg p-3">
                  <span className="text-orange-400 font-bold text-sm mt-0.5">{i + 1}.</span>
                  <p className="text-sm text-white/80">{pivot}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Buyer Leads */}
        {buyerLeads.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-green-400" /> Potansiyel Müşteriler ({buyerLeads.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {buyerLeads.slice(0, 8).map((lead: any, i: number) => (
                <div key={i} className="rounded-xl bg-card border border-white/5 p-4 space-y-2 hover:border-green-500/20 transition-colors">
                  <div className="flex items-center justify-between gap-2">
                    <Badge variant="outline" className="text-[10px] bg-green-500/10 border-green-500/20 text-green-400">
                      {lead.source || "Web"}
                    </Badge>
                    {lead.url && (
                      <a href={lead.url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-white transition-colors">
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                  <p className="text-sm font-medium text-white line-clamp-2">{lead.title}</p>
                  {lead.desc && (
                    <p className="text-xs text-muted-foreground line-clamp-2">{lead.desc}</p>
                  )}
                  {lead.sales_pitch && (
                    <div className="mt-2 pt-2 border-t border-white/5">
                      <p className="text-[10px] text-purple-400 uppercase tracking-wider mb-1">DM Şablonu</p>
                      <p className="text-xs text-white/60 italic line-clamp-3">{lead.sales_pitch}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center py-6 border-t border-white/5">
          <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground mb-4">
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(scan.created_at).toLocaleString("tr-TR")}</span>
            <span className="flex items-center gap-1">
              {scan.status === "completed" ? <CheckCircle2 className="w-3 h-3 text-green-400" /> : <XCircle className="w-3 h-3 text-red-400" />}
              {scan.status.toUpperCase()}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">Venorly</p>
        </div>
      </div>
    </div>
  );
}
