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
} from "lucide-react";
import { ScanDB, ScanRecord } from "@/lib/scan-db";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Badge } from "@/components/ui/badge";

export default function ScanDetailPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<ScanRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

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
      window.open(`/api/scans/${id}/pdf`, "_blank");
    } catch (e) {
      console.error("PDF Export Error:", e);
      alert("PDF oluşturulurken bir hata oluştu.");
    } finally {
      setIsExporting(false);
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
            Dashboard'a Dön
          </button>
        </div>
      </div>
    );
  }

  const reportContent = (scan as any).full_report?.final_report || (scan as any).full_report?.investment_memo || scan.report_preview;

  // Validation score banner — validation_details'dan score çıkar
  const validationDetails: string = (scan as any).full_report?.validation_details || "";
  const scoreMatch = validationDetails.match(/Fizibilite Skoru.*?(\d+)\/50/);
  const validationScore = scoreMatch ? parseInt(scoreMatch[1]) : null;
  const scoreBanner = validationScore !== null
    ? validationScore >= 35
      ? { color: "green", label: "🟢 Güçlü Fırsat", bg: "bg-green-500/10 border-green-500/30", text: "text-green-400", desc: "Bu fikir yüksek potansiyel taşıyor." }
      : validationScore >= 20
        ? { color: "yellow", label: "🟡 Araştırmaya Değer", bg: "bg-yellow-500/10 border-yellow-500/30", text: "text-yellow-400", desc: "Ümit verici ancak bazı riskler mevcut." }
        : { color: "red", label: "🔴 Riskli", bg: "bg-red-500/10 border-red-500/30", text: "text-red-400", desc: "Bu fikir önemli riskler içeriyor, dikkatli değerlendirin." }
    : null;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/5 bg-gradient-to-r from-background via-indigo-950/10 to-background shadow-lg">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
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
            <div className="flex items-center gap-3">
              <button
                onClick={handleExportPDF}
                disabled={isExporting}
                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-2 cursor-pointer"
              >
                {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                {isExporting ? "PDF Hazırlanıyor..." : "PDF Olarak İndir"}
              </button>
              <button
                onClick={() => router.push("/dashboard")}
                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" /> Geri Dön
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
                <p className="text-xs text-muted-foreground">Bulunan Lead'ler</p>
                <p className="font-bold text-white">{scan.leads_count || 0}</p>
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

        {/* Footer */}
        <div className="text-center py-6 border-t border-white/5">
           <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground mb-4">
              <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(scan.created_at).toLocaleString("tr-TR")}</span>
              <span className="flex items-center gap-1">
                {scan.status === 'completed' ? <CheckCircle2 className="w-3 h-3 text-green-400" /> : <XCircle className="w-3 h-3 text-red-400" />}
                {scan.status.toUpperCase()}
              </span>
           </div>
           <p className="text-xs text-muted-foreground">
            Startup Idea Finder V6 — Scan Detail View 📄
          </p>
        </div>
      </div>
    </div>
  );
}
