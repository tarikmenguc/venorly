"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatPanel } from "@/components/ui/chat-panel";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ReportDisplay, FeasibilityReport } from "@/components/ReportDisplay";

const WORDS = ["Micro-SaaS", "AI App", "Deep Tech", "Unicorn"];

const NODES = [
  "expand_query", "fetch_market_data", "fetch_trending_models",
  "match_to_market", "scrape_competitor_reviews", "cluster_complaints",
  "find_store_app", "scrape_store_reviews", "cluster_store_problems",
  "competition_matrix", "generate_opportunity", "validate_idea", "auditor",
];

const MODES = {
  disc: { label: "KEŞFET",       btn: "Hızlı Tarama",          color: "var(--c-disc)", bg: "var(--info-bg)",      border: "var(--info-bd)",      apiMode: "discover" },
  deep: { label: "DERİN ANALİZ", btn: "Derin Analiz Başlat",   color: "var(--p300)",   bg: "oklch(11% .185 268)", border: "oklch(25% .26 268)", apiMode: "deep" },
  orch: { label: "ORKESTRATÖR",  btn: "Orkestratörü Çalıştır", color: "var(--c-orch)", bg: "var(--warning-bg)",   border: "var(--warning-bd)",   apiMode: "orchestrate" },
  comp: { label: "RAKİP ARA",    btn: "Rakip Tara",             color: "var(--c-comp)", bg: "var(--error-bg)",     border: "var(--error-bd)",     apiMode: "reverse" },
  trnd: { label: "TRENDLER",     btn: "Trend Analizi",          color: "var(--c-trnd)", bg: "var(--success-bg)",   border: "var(--success-bd)",   apiMode: "trends" },
} as const;

type ModeKey = keyof typeof MODES;
type AppState = "empty" | "loading" | "done";

export default function HomePage() {
  const router      = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();

  const [appState, setAppState]       = useState<AppState>("empty");
  const [mode, setModeKey]            = useState<ModeKey>("disc");
  const [category, setCategory]       = useState("");
  const [wordIdx, setWordIdx]         = useState(0);
  const [currentNode, setCurrentNode] = useState("");
  const [pipelineStep, setPipelineStep] = useState(0);
  const [report, setReport]           = useState("");
  const [leads, setLeads]             = useState<any[]>([]);
  const [scanId, setScanId]           = useState<string | null>(null);
  const [isCreatingWaitlist, setIsCreatingWaitlist] = useState(false);
  const [reportJson, setReportJson] = useState<FeasibilityReport | null>(null);

  const pTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Sync mode from ?mode= query param on mount
  useEffect(() => {
    const modeMap: Record<string, ModeKey> = {
      discover: "disc", deep: "deep", orchestrate: "orch", reverse: "comp", trends: "trnd",
    };
    const m = searchParams.get("mode");
    if (m && modeMap[m]) setModeKey(modeMap[m]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Word rotation
  useEffect(() => {
    const t = setInterval(() => setWordIdx(i => (i + 1) % WORDS.length), 2700);
    return () => clearInterval(t);
  }, []);

  const goEmpty = useCallback(() => {
    if (pTimerRef.current) clearInterval(pTimerRef.current);
    setAppState("empty");
    setCategory("");
    setReport("");
    setLeads([]);
    setCurrentNode("");
    setPipelineStep(0);
    setScanId(null);
    setReportJson(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const handleScan = async () => {
    const q = category.trim();
    if (!q) { alert("Lütfen bir kategori veya niş girin"); return; }

    setAppState("loading");
    setCurrentNode("Agent başlatılıyor...");
    setReport("");
    setLeads([]);
    setPipelineStep(0);

    try {
      const response = await apiFetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: MODES[mode].apiMode, category: q }),
      });

      if (!response.ok) {
        const errText = await response.text();
        let msg = `HTTP ${response.status}`;
        try { msg = JSON.parse(errText)?.detail || msg; } catch {}
        if (response.status === 401) msg = "Oturumunuz yok veya süresi dolmuş. Lütfen giriş yapın.";
        setCurrentNode(`Hata: ${msg}`);
        setAppState("done");
        return;
      }

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buffer.indexOf("\n\n")) >= 0) {
          const ev = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          if (!ev.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(ev.slice(6));
            if (data.scan_id) setScanId(data.scan_id);
            if (data.status === "done") {
              if (pTimerRef.current) clearInterval(pTimerRef.current);
              setPipelineStep(NODES.length);
              setCurrentNode("Tüm nodlar tamamlandı · 13/13");
              setAppState("done");
            } else if (data.error) {
              if (pTimerRef.current) clearInterval(pTimerRef.current);
              setCurrentNode(data.error);
              setReport(`> **Hata:** ${data.error}`);
              setAppState("done");
            } else if (data.node) {
              const ni = NODES.indexOf(data.node);
              if (ni >= 0) setPipelineStep(ni);
              setCurrentNode(`İşlem: ${data.node}...`);
              if (data.state) {
                const out = data.state.investment_memo || data.state.final_report;
                if (out) setReport(out);
                if (data.state.buyer_leads?.length > 0) setLeads(data.state.buyer_leads);
                if (data.state.report_json) setReportJson(data.state.report_json as FeasibilityReport);
              }
            }
          } catch {}
        }
      }
    } catch {
      if (pTimerRef.current) clearInterval(pTimerRef.current);
      setCurrentNode("Bağlantı hatası — Backend çalışıyor mu?");
      setAppState("done");
    }
  };

  const handleCreateWaitlist = async () => {
    if (!report) return;
    setIsCreatingWaitlist(true);
    try {
      const titleMatch = report.match(/🔥 NİŞ FIRSAT: (.+)/);
      const title = titleMatch ? titleMatch[1].replace(/━+/g, "").trim() : `${category} için AI Otomasyonu`;
      const audienceMatch = report.match(/🎯 Odaklanılacak B2B Niş: (.+)/);
      const audience = audienceMatch ? audienceMatch[1].trim() : "B2B Profesyoneller";
      const summaryMatch = report.match(/💡 Fırsat Özeti:([\s\S]*?)(🔗|━|$)/);
      const description = summaryMatch?.[1]?.replace(/\[|\]/g, "").trim() ||
        "Manuel saatler alan angaryayı tek tıklamaya indiren yapay zeka çözümü.";
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, target_audience: audience }),
      });
      const data = await res.json();
      if (data.id) window.open(`/waitlist/${data.id}`, "_blank");
      else alert("Waitlist oluşturulamadı.");
    } catch { alert("Hata oluştu."); }
    finally { setIsCreatingWaitlist(false); }
  };

  const m = MODES[mode];
  const modePill = (
    <span className="vn-mode-pill" style={{ color: m.color, background: m.bg, borderColor: m.border }}>
      {m.label}
    </span>
  );

  return (
    <main className="vn-root">
      {/* Background */}
      <div className="vn-aurora" />
      <div className="vn-orb vn-orb1" />
      <div className="vn-orb vn-orb2" />
      <div className="vn-orb vn-orb3" />

      {/* Navbar */}
      <nav className="vn-nav">
        <button className="vn-brand" onClick={goEmpty}>
          <div className="vn-mark">V</div>
          <span className="vn-name">Venorly</span>
        </button>
        <div className="vn-tabs">
          {(Object.keys(MODES) as ModeKey[]).map(k => (
            <button
              key={k}
              className={`vn-tab${mode === k ? " on" : ""}`}
              onClick={() => { setModeKey(k); setReport(""); setLeads([]); setCategory(""); setCurrentNode(""); }}
            >
              <span className="vn-dot" style={{ background: MODES[k].color }} />
              {{ disc: "Keşfet", deep: "Derin Analiz", orch: "Orkestratör", comp: "Rakip Ara", trnd: "Trendler" }[k]}
            </button>
          ))}
          <Link href="/gallery" className="vn-tab">
            <span className="vn-dot" style={{ background: "var(--t4)" }} />
            Galeri
          </Link>
        </div>
        <div className="vn-nav-right">
          {user ? (
            <div className="vn-avatar" onClick={() => router.push("/profile")} title={user.email ?? ""}>
              {user.email?.[0]?.toUpperCase() ?? "U"}
            </div>
          ) : (
            <Link href="/sign-in" className="vn-avatar" style={{ fontSize: 10 }}>Giriş</Link>
          )}
        </div>
      </nav>

      <div className="vn-main">

        {/* ── STATE 1: EMPTY ── */}
        {appState === "empty" && (
          <div className="vn-s-empty">
            <div className="vn-hero-badge">
              <div className="vn-badge-pulse" />
              AI Pipeline — 13 Ajan Aktif
            </div>
            <h1 className="vn-hero-h1">
              <span className="vn-hero-first">Find your next</span>
              <span key={wordIdx} className="vn-hero-word">{WORDS[wordIdx]}</span>
            </h1>
            <p className="vn-hero-sub">
              Yapay zeka destekli pazar istihbarat motoru.<br />
              Kârlı nişleri herkes bulmadan önce keşfet.
            </p>
            <div className="vn-search-pill">
              <input
                className="vn-search-input"
                value={category}
                onChange={e => setCategory(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleScan()}
                placeholder={mode === "comp" ? "Örn: Lumen5..." : "Örn: Video Generation..."}
                autoComplete="off"
              />
              <button className="vn-search-go" onClick={handleScan}>
                <span>{m.btn}</span>
              </button>
            </div>
            <div className="vn-hero-links">
              <Link href="/features" className="vn-hero-link">Nasıl Çalışır?</Link>
              <span className="vn-sep">·</span>
              <Link href="/dashboard" className="vn-hero-link">Dashboard</Link>
              <span className="vn-sep">·</span>
              <Link href="/pricing" className="vn-hero-link">Fiyatlandırma</Link>
            </div>
          </div>
        )}

        {/* ── STATE 2: LOADING ── */}
        {appState === "loading" && (
          <div className="vn-s-load">
            <div className="vn-content-shell">
              <div className="vn-status-card">
                <div className="vn-sc-top">
                  <div className="vn-spinner" />
                  <div className="vn-sc-info">
                    <div className="vn-sc-title">Analiz Yürütülüyor</div>
                    <div className="vn-sc-node">{currentNode}</div>
                  </div>
                  {modePill}
                </div>
                <div className="vn-pipeline">
                  {NODES.map((_, i) => (
                    <div
                      key={i}
                      className={`vn-p-step${i < pipelineStep ? " done" : i === pipelineStep ? " live" : ""}`}
                    />
                  ))}
                </div>
              </div>
              {/* Skeleton */}
              <div className="vn-skel-card">
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
                  <div className="vn-skel" style={{ width: 160 }} />
                  <div className="vn-skel" style={{ width: 72 }} />
                </div>
                <div className="vn-skel-3col" style={{ marginBottom: 20 }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} className="vn-skel-chip">
                      <div className="vn-skel" style={{ width: 44, height: 22, borderRadius: 4 }} />
                      <div className="vn-skel" style={{ width: 60 }} />
                    </div>
                  ))}
                </div>
                <div className="vn-skel" style={{ width: 90, marginBottom: 10 }} />
                <div className="vn-skel" style={{ width: "100%", marginBottom: 8 }} />
                <div className="vn-skel" style={{ width: "88%", marginBottom: 8 }} />
                <div className="vn-skel" style={{ width: "55%" }} />
              </div>
            </div>
          </div>
        )}

        {/* ── STATE 3: DONE ── */}
        {appState === "done" && (
          <div className="vn-s-done">
            <div className="vn-content-shell">

              {/* Status bar */}
              <div className="vn-status-card vn-done-card">
                <div className="vn-sc-top vn-no-mb">
                  <span style={{ fontSize: 20 }}>✨</span>
                  <div className="vn-sc-info">
                    <div className="vn-sc-title">Analiz Tamamlandı</div>
                    <div className="vn-sc-done">{currentNode}</div>
                  </div>
                  {modePill}
                  <button className="vn-reset-btn" onClick={goEmpty}>↩ Yeni Tarama</button>
                </div>
              </div>

              {/* Report */}
              {(reportJson || report) && (
                <div>
                  {/* Status / title bar */}
                  <div className="vn-card-head" style={{ background: "rgba(17,12,29,.6)", backdropFilter: "blur(20px)", border: "1px solid rgba(255,255,255,.06)", borderRadius: 16, padding: "16px 22px", marginBottom: 20 }}>
                    <div>
                      <div className="vn-card-title">{reportJson?.idea_title ?? `Pazar Analiz Raporu — ${category}`}</div>
                      <div className="vn-card-meta">
                        13 AI Ajan · {new Date().toLocaleDateString("tr-TR", { month: "long", year: "numeric" })}
                      </div>
                    </div>
                    {modePill}
                  </div>
                  {reportJson ? (
                    <ReportDisplay
                      reportJson={reportJson}
                      onCreateWaitlist={handleCreateWaitlist}
                      isCreatingWaitlist={isCreatingWaitlist}
                    />
                  ) : (
                    <div className="vn-glass-card">
                      <div className="vn-card-body">
                        <div className="prose prose-invert prose-primary">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Leads */}
              {leads.length > 0 && (
                <div className="vn-leads-wrap">
                  <div className="vn-card-head">
                    <div>
                      <div className="vn-card-title">Lead Fırsatları</div>
                      <div className="vn-card-meta">{leads.length} potansiyel alıcı bulundu</div>
                    </div>
                  </div>
                  <table className="vn-leads-table">
                    <thead>
                      <tr>
                        <th>Platform</th>
                        <th>Gönderi / Ağrı Noktası</th>
                        <th>DM Şablonu</th>
                      </tr>
                    </thead>
                    <tbody>
                      {leads.map((lead, i) => (
                        <tr key={i}>
                          <td><span className="vn-pchip">{lead.source}</span></td>
                          <td>
                            <p className="vn-post-text">{lead.title}</p>
                            {lead.desc && (
                              <p style={{ color: "var(--t3)", fontSize: 12, marginTop: 3 }}>{lead.desc}</p>
                            )}
                            {lead.url && (
                              <a href={lead.url} target="_blank" rel="noreferrer"
                                style={{ color: "var(--p400)", fontSize: 12, display: "inline-block", marginTop: 4 }}>
                                Sinyale Git →
                              </a>
                            )}
                          </td>
                          <td className="vn-dm-text">{lead.sales_pitch || "Şablon oluşturulamadı."}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* CTA — only shown when falling back to markdown (no reportJson) */}
              {!reportJson && report && (
                <div className="vn-cta-card">
                  <div>
                    <div className="vn-cta-title">Bu Fikri Doğrulamak İster Misin?</div>
                    <div className="vn-cta-sub">
                      Otomatik landing page, waitlist formu ve pitch deck oluştur.<br />
                      5 dakikada doğrulama sürecini başlat.
                    </div>
                  </div>
                  <button
                    className="vn-cta-btn"
                    onClick={handleCreateWaitlist}
                    disabled={isCreatingWaitlist}
                  >
                    {isCreatingWaitlist ? "Sayfa Kuruluyor..." : "✦ Doğrulama Sayfası Oluştur"}
                  </button>
                </div>
              )}

            </div>
          </div>
        )}
      </div>

      {/* Chat Panel */}
      {(appState === "done" || report) && (
        <ChatPanel scanId={scanId} reportContext={report} alwaysVisible={true} />
      )}
    </main>
  );
}
