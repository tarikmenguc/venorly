"use client";

import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  FileText,
  Users,
  Sparkles,
  Clock,
  Search,
} from "lucide-react";

export default function ScanDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/5 bg-gradient-to-r from-background via-indigo-950/10 to-background">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                Tarama Detayı
              </h1>
              <p className="text-sm text-muted-foreground mt-1 font-mono">ID: {params.id}</p>
            </div>
            <button
              onClick={() => router.push("/dashboard")}
              className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> Dashboard
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* Placeholder Info */}
        <div className="rounded-2xl bg-card border border-white/5 p-8 text-center space-y-4">
          <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-400 mb-2">
            <FileText className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-xl font-bold text-white">Tarama Raporu</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Bu sayfa, seçilen taramanın detaylı raporunu, bulunan lead&apos;leri ve üretilen
            Investment Memo&apos;yu gösterir. Şu anda tarama geçmişi Supabase entegrasyonu
            (Faz 15) ile aktif hale gelecektir.
          </p>

          <div className="grid grid-cols-3 gap-4 max-w-sm mx-auto mt-6">
            <div className="rounded-xl bg-white/5 border border-white/5 p-4 text-center">
              <Search className="w-5 h-5 text-blue-400 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Tarama</p>
              <p className="text-xl font-bold text-white">—</p>
            </div>
            <div className="rounded-xl bg-white/5 border border-white/5 p-4 text-center">
              <Sparkles className="w-5 h-5 text-purple-400 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Hipotezler</p>
              <p className="text-xl font-bold text-white">—</p>
            </div>
            <div className="rounded-xl bg-white/5 border border-white/5 p-4 text-center">
              <Users className="w-5 h-5 text-green-400 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Lead&apos;ler</p>
              <p className="text-xl font-bold text-white">—</p>
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 pt-4 text-xs text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            <span>Faz 15&apos;te Supabase ile tam rapor saklama aktif edilecek</span>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => router.push("/")}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-violet-500 text-white text-sm font-medium hover:opacity-90 transition-all"
          >
            Yeni Tarama Başlat
          </button>
          <button
            onClick={() => router.push("/leads")}
            className="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all"
          >
            Lead&apos;leri Görüntüle
          </button>
        </div>

        {/* Footer */}
        <div className="text-center py-6">
          <p className="text-xs text-muted-foreground">
            Startup Idea Finder V6 — Scan Detail 📄
          </p>
        </div>
      </div>
    </div>
  );
}
