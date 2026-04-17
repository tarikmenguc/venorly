"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Bell,
  Plus,
  Trash2,
  ArrowLeft,
  Zap,
  Mail,
  Clock,
  AlertTriangle,
} from "lucide-react";

interface NicheAlert {
  id: string;
  keyword: string;
  frequency: "daily" | "weekly" | "realtime";
  email: string;
  created_at: string;
  is_active: boolean;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<NicheAlert[]>([]);
  const [keyword, setKeyword] = useState("");
  const [email, setEmail] = useState("");
  const [frequency, setFrequency] = useState<"daily" | "weekly">("daily");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // Load alerts from DB on mount
  useEffect(() => {
    fetchAlerts();
  }, []);

  async function fetchAlerts() {
    try {
      const res = await fetch("/api/alerts");
      const data = await res.json();
      if (data.alerts) setAlerts(data.alerts);
    } catch (e) {
      console.error("Failed to fetch alerts:", e);
    }
  }

  async function addAlert() {
    if (!keyword || !email) return;
    setLoading(true);
    try {
      const res = await fetch("/api/alerts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword, email, frequency }),
      });
      if (res.ok) {
        setKeyword("");
        fetchAlerts();
      }
    } catch (e) {
      console.error("Failed to add alert:", e);
    } finally {
      setLoading(false);
    }
  }

  async function removeAlert(id: string) {
    try {
      const res = await fetch(`/api/alerts?id=${id}`, { method: "DELETE" });
      if (res.ok) fetchAlerts();
    } catch (e) {
      console.error("Failed to delete alert:", e);
    }
  }

  async function toggleAlert(id: string, currentStatus: boolean) {
    try {
      const res = await fetch("/api/alerts", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, is_active: !currentStatus }),
      });
      if (res.ok) fetchAlerts();
    } catch (e) {
      console.error("Failed to toggle alert:", e);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/5 bg-gradient-to-r from-background via-amber-950/10 to-background">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                Niş Alarm Sistemi
              </h1>
              <p className="text-muted-foreground mt-1">
                Belirli niş alanlardaki fırsatları otomatik takip edin
              </p>
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

      <div className="max-w-3xl mx-auto px-6 py-8 space-y-8">
        {/* Create Alert Form */}
        <div className="rounded-2xl bg-card border border-white/5 p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 rounded-lg bg-gradient-to-br from-amber-500 to-orange-400">
              <Bell className="w-4 h-4 text-white" />
            </div>
            <h2 className="text-lg font-semibold text-white">Yeni Alarm Oluştur</h2>
          </div>

          <p className="text-sm text-muted-foreground">
            Belirli bir anahtar kelime için alarm kurun. Sistem bu nişi periyodik olarak tarar ve yeni fırsatlar bulduğunda size e-posta gönderir.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Niş Anahtar Kelime (Örn: AI invoice)"
              className="px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            />
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="E-posta adresiniz"
              type="email"
              className="px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            />
          </div>

          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              <button
                onClick={() => setFrequency("daily")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  frequency === "daily"
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    : "bg-white/5 text-muted-foreground border border-white/10 hover:bg-white/10"
                }`}
              >
                <Clock className="w-3 h-3 inline mr-1" /> Günlük
              </button>
              <button
                onClick={() => setFrequency("weekly")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  frequency === "weekly"
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    : "bg-white/5 text-muted-foreground border border-white/10 hover:bg-white/10"
                }`}
              >
                <Clock className="w-3 h-3 inline mr-1" /> Haftalık
              </button>
            </div>
            <button
              onClick={addAlert}
              disabled={!keyword || !email}
              className="ml-auto px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-400 text-black text-sm font-semibold hover:opacity-90 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Plus className="w-4 h-4" /> Alarm Kur
            </button>
          </div>
        </div>

        {/* Active Alerts */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" /> Aktif Alarmlar
          </h2>

          {alerts.length === 0 ? (
            <div className="rounded-xl bg-card border border-white/5 p-12 text-center">
              <AlertTriangle className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">Henüz alarm kurulmadı.</p>
              <p className="text-xs text-muted-foreground mt-1">
                Yukarıdaki formu kullanarak ilk alarmınızı oluşturun.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`flex items-center gap-4 rounded-xl border p-4 transition-all ${
                    alert.is_active
                      ? "bg-card border-white/5 hover:border-amber-500/20"
                      : "bg-card/50 border-white/3 opacity-60"
                  }`}
                >
                  <button
                    onClick={() => toggleAlert(alert.id, alert.is_active)}
                    className={`w-10 h-6 rounded-full relative transition-colors ${
                      alert.is_active ? "bg-amber-500" : "bg-white/10"
                    }`}
                  >
                    <div
                      className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                        alert.is_active ? "left-4" : "left-0.5"
                      }`}
                    />
                  </button>

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">{alert.keyword}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-muted-foreground">
                        {alert.frequency === "daily" ? "Günlük" : "Haftalık"}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 mt-0.5">
                      <Mail className="w-3 h-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">{alert.email}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => removeAlert(alert.id)}
                    className="p-2 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-xl bg-amber-500/5 border border-amber-500/10 p-4">
          <p className="text-xs text-amber-400/80">
            💡 <strong>Pro İpucu:</strong> Alarmlar arka planda çalışır ve belirttiğiniz niş alanında yeni fırsatlar tespit edildiğinde e-posta gönderir.
          </p>
        </div>

        {/* Footer */}
        <div className="text-center py-6">
          <p className="text-xs text-muted-foreground">
            Startup Idea Finder V6 — Niş Alarm Sistemi 🔔
          </p>
        </div>
      </div>
    </div>
  );
}
