"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

// ── Types ────────────────────────────────────────────────────────────────────

interface DashboardStats {
  total_scans: number;
  completed: number;
  total_leads: number;
  total_angles: number;
  waitlist_count: number;
  total_emails: number;
  modes: { discover: number; deep: number; orchestrate: number; reverse: number; trends: number };
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
  confidence_score?: number;
}

// ── SVG Icons ────────────────────────────────────────────────────────────────

const IcoChart = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <rect x="1" y="7" width="3" height="8" rx=".5" fill="currentColor"/>
    <rect x="6.5" y="4" width="3" height="11" rx=".5" fill="currentColor"/>
    <rect x="12" y="1" width="3" height="14" rx=".5" fill="currentColor"/>
  </svg>
);
const IcoPerson = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="5" r="3" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M2.5 14.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);
const IcoDiamond = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M8 1.5L13.5 8 8 14.5 2.5 8z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
  </svg>
);
const IcoEnvelope = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <rect x="1.5" y="3.5" width="13" height="9" rx="1" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M1.5 5.5l6.5 4 6.5-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);
const IcoSearch = () => (
  <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
    <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M11 11l3.5 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);
const IcoLightning = () => (
  <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
    <path d="M9 1.5L3.5 9H8l-1.5 5.5 7.5-9H10z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
  </svg>
);
const IcoNetwork = () => (
  <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
    <circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.5"/>
    <circle cx="2.5" cy="2.5" r="1.5" stroke="currentColor" strokeWidth="1.25"/>
    <circle cx="13.5" cy="2.5" r="1.5" stroke="currentColor" strokeWidth="1.25"/>
    <circle cx="2.5" cy="13.5" r="1.5" stroke="currentColor" strokeWidth="1.25"/>
    <circle cx="13.5" cy="13.5" r="1.5" stroke="currentColor" strokeWidth="1.25"/>
    <path d="M4 4L6.3 6.3M12 4L9.7 6.3M4 12L6.3 9.7M12 12L9.7 9.7" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/>
  </svg>
);
const IcoEye = ({ size = 15 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <path d="M1 8s2.5-5.5 7-5.5S15 8 15 8s-2.5 5.5-7 5.5S1 8 1 8z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
    <circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.5"/>
  </svg>
);
const IcoTrend = ({ size = 15 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <polyline points="1.5,13 5,8.5 8.5,10.5 14.5,3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <polyline points="10.5,3.5 14.5,3.5 14.5,7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);
const IcoBook = ({ size = 15 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <path d="M3 2.5h7a1 1 0 011 1v9a1 1 0 01-1 1H3a1 1 0 01-1-1v-9a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.5"/>
    <line x1="2" y1="7" x2="11" y2="7" stroke="currentColor" strokeWidth="1.5"/>
    <path d="M11 3.5h1a1 1 0 011 1v8a1 1 0 01-1 1h-1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);
const IcoWrench = ({ size = 15 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <path d="M11 2a3.5 3.5 0 00-3.3 4.7L2 13.3l.7.7 5.6-5.7A3.5 3.5 0 1011 2z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="11" cy="5.5" r="1.5" stroke="currentColor" strokeWidth="1.2"/>
  </svg>
);

// ── Mode config ───────────────────────────────────────────────────────────────

const MODE_MAP: Record<string, { label: string; Icon: React.FC<{ size?: number }> }> = {
  discover:    { label: "Scout",        Icon: IcoEye     },
  deep:        { label: "Analyst",      Icon: IcoTrend   },
  orchestrate: { label: "Orchestrator", Icon: ({ size }) => <IcoNetwork /> },
  reverse:     { label: "Engineer",     Icon: IcoWrench  },
  trends:      { label: "Researcher",   Icon: IcoBook    },
};

// ── Count-up hook ─────────────────────────────────────────────────────────────

function useCountUp(target: number, duration = 1400) {
  const [val, setVal] = useState(0);
  const started = useRef(false);
  useEffect(() => {
    if (target === 0 || started.current) return;
    started.current = true;
    const t0 = Date.now();
    const tick = () => {
      const p = Math.min((Date.now() - t0) / duration, 1);
      const e = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(target * e));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [target, duration]);
  return val;
}

// ── KPI Card ──────────────────────────────────────────────────────────────────

function KpiCard({ label, value, desc, icon, sparkPoints }: {
  label: string; value: number; desc: string;
  icon: React.ReactNode; sparkPoints: string;
}) {
  const displayed = useCountUp(value, 1400);
  return (
    <div style={{ background: "#0F1320", border: "1px solid rgba(255,255,255,.05)", borderRadius: 12, padding: 20, transition: "border-color .15s, background .15s, transform .15s", cursor: "default" }}
      onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,.08)"; (e.currentTarget as HTMLDivElement).style.background = "#161C2D"; (e.currentTarget as HTMLDivElement).style.transform = "translateY(-1px)"; }}
      onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,.05)"; (e.currentTarget as HTMLDivElement).style.background = "#0F1320"; (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)"; }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <span style={{ fontSize: 10, fontWeight: 500, textTransform: "uppercase", letterSpacing: ".12em", color: "#3F4B5C" }}>{label}</span>
        <span style={{ color: "#3F4B5C" }}>{icon}</span>
      </div>
      <div style={{ fontSize: 32, fontWeight: 600, color: "#F1F5F9", letterSpacing: "-0.03em", fontVariantNumeric: "tabular-nums", lineHeight: 1, marginBottom: 5 }}>
        {displayed.toLocaleString("tr-TR")}
      </div>
      <div style={{ fontSize: 12, color: "#3F4B5C", marginBottom: 0 }}>{desc}</div>
      <svg viewBox="0 0 100 20" preserveAspectRatio="none" fill="none"
        style={{ display: "block", width: "calc(100% + 40px)", height: 20, margin: "14px -20px -20px", borderRadius: "0 0 11px 11px" }}>
        <polyline points={sparkPoints} stroke="rgba(139,92,246,.4)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </div>
  );
}

// ── Score color ───────────────────────────────────────────────────────────────

function scoreColor(s: number) {
  if (s >= 70) return "#10B981";
  if (s >= 45) return "#F59E0B";
  return "#EF4444";
}

// ── Strip markdown preview ────────────────────────────────────────────────────

function cleanPreview(raw: string): string {
  return raw
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/#{1,6}\s/g, "")
    .replace(/\[.*?\]\(.*?\)/g, "")
    .replace(/`/g, "")
    .replace(/\n+/g, " ")
    .trim()
    .slice(0, 100);
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [scans, setScans]   = useState<ScanRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/dashboard")
      .then(r => r.json())
      .then(d => { setStats(d.stats); setScans(d.recent_scans || []); })
      .catch(e => console.error("Dashboard:", e))
      .finally(() => setLoading(false));
  }, []);

  const s = stats;

  // Sparkline paths — each card has a different trend
  const sparks = [
    "0,16 12,14 25,17 37,12 50,15 63,10 75,13 87,8 100,6",
    "0,18 12,16 25,15 37,17 50,13 63,11 75,9 87,7 100,5",
    "0,15 12,17 25,11 37,14 50,9 63,13 75,8 87,11 100,6",
    "0,19 12,17 25,18 37,15 50,16 63,12 75,10 87,7 100,4",
  ];

  const modeCounts = s ? [
    { key: "discover",    count: s.modes.discover,    Icon: IcoEye,    name: "Scout"        },
    { key: "deep",        count: s.modes.deep,        Icon: IcoTrend,  name: "Analyst"      },
    { key: "trends",      count: s.modes.trends,      Icon: IcoBook,   name: "Researcher"   },
    { key: "reverse",     count: s.modes.reverse,     Icon: IcoWrench, name: "Engineer"     },
    { key: "orchestrate", count: s.modes.orchestrate, Icon: IcoNetwork, name: "Orchestrator" },
  ] : [];
  const topMode = modeCounts.length ? modeCounts.reduce((a, b) => a.count > b.count ? a : b).key : "";

  // CSS vars inlined via style tag
  return (
    <>
      <style>{`
        .db-nav-link { padding:6px 11px;font-size:13px;font-weight:400;color:#3F4B5C;text-decoration:none;border-radius:6px;transition:color .12s;cursor:pointer;border:none;background:none;font-family:inherit; }
        .db-nav-link:hover { color:#64748B; }
        .db-nav-link.active { color:#F1F5F9;font-weight:500; }
        .db-card { background:#0F1320;border:1px solid rgba(255,255,255,.05);border-radius:12px;transition:border-color .15s,background .15s,transform .15s; }
        .db-card:hover { border-color:rgba(255,255,255,.08);background:#161C2D;transform:translateY(-1px); }
        .db-qa:hover { border-color:rgba(139,92,246,.25) !important;transform:translateY(-1px); }
        .db-qa:hover .db-qa-arrow { transform:translateX(2px);color:#64748B; }
        .db-qa:hover .db-ico { color:#8B5CF6; }
        .db-scan-row { display:flex;align-items:center;gap:14px;padding:0 18px;height:52px;background:#0F1320;border-bottom:1px solid rgba(255,255,255,.04);transition:background .12s; }
        .db-scan-row:last-child { border-bottom:none; }
        .db-scan-row:hover { background:#161C2D; }
        .db-pill { display:inline-flex;align-items:center;padding:1px 7px;border-radius:100px;font-size:10px;font-weight:500;line-height:1.6;white-space:nowrap;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);color:#64748B;transition:border-color .15s,color .15s; }
        .db-pill:hover { border-color:rgba(139,92,246,.3);color:#A78BFA; }
        .db-eye { font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:.12em;color:#3F4B5C; }
        .db-ico { color:#3F4B5C;transition:color .15s; }
        .db-back { font-size:12px;color:#3F4B5C;text-decoration:none;transition:color .12s;white-space:nowrap;margin-top:4px; }
        .db-back:hover { color:#64748B; }
      `}</style>

      <div style={{ background: "#080B14", color: "#64748B", fontFamily: "Inter, -apple-system, sans-serif", fontSize: 14, lineHeight: 1.6, WebkitFontSmoothing: "antialiased", minHeight: "100vh" }}>

        {/* NAV */}
        <nav style={{ position: "sticky", top: 0, zIndex: 100, height: 48, background: "#080B14", borderBottom: "1px solid rgba(255,255,255,.05)", display: "flex", alignItems: "center", padding: "0 24px", gap: 0 }}>
          <Link href="/" style={{ fontSize: 14, fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.02em", textDecoration: "none", flexShrink: 0 }}>Venorly</Link>
          <div style={{ width: 1, height: 16, background: "rgba(255,255,255,.08)", margin: "0 20px", flexShrink: 0 }} />
          <div style={{ display: "flex", alignItems: "center" }}>
            <button className="db-nav-link active">Dashboard</button>
            <Link href="/gallery" className="db-nav-link">Taramalar</Link>
            <Link href="/" className="db-nav-link">Keşfet</Link>
          </div>
          <div style={{ marginLeft: "auto" }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#1E2535", border: "1px solid rgba(255,255,255,.08)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 600, color: "#3F4B5C", cursor: "pointer" }} onClick={() => router.push("/profile")}>U</div>
          </div>
        </nav>

        {/* PAGE */}
        <div style={{ maxWidth: 960, margin: "0 auto", padding: "40px 24px 80px" }}>

          {/* Header */}
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, marginBottom: 40 }}>
            <div>
              <h1 style={{ fontSize: 24, fontWeight: 600, color: "#F1F5F9", letterSpacing: "-0.025em", lineHeight: 1.15 }}>Dashboard</h1>
              <p style={{ fontSize: 13, color: "#3F4B5C", marginTop: 4 }}>Venorly — Genel Bakış</p>
            </div>
            <Link href="/" className="db-back">← Ana Sayfa</Link>
          </div>

          {loading ? (
            <div style={{ textAlign: "center", padding: "80px 0", color: "#3F4B5C" }}>Yükleniyor…</div>
          ) : (
            <>
              {/* KPI Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12 }}>
                <KpiCard label="Toplam Tarama"    value={s?.total_scans  ?? 0} desc={`${s?.completed ?? 0} tamamlandı`}    icon={<IcoChart />}    sparkPoints={sparks[0]} />
                <KpiCard label="Bulunan Lead'ler" value={s?.total_leads  ?? 0} desc="Toplam potansiyel"                    icon={<IcoPerson />}   sparkPoints={sparks[1]} />
                <KpiCard label="İş Fikirleri"     value={s?.total_angles ?? 0} desc="Doğrulamaya hazır"                   icon={<IcoDiamond />}  sparkPoints={sparks[2]} />
                <KpiCard label="Waitlist Kayıtları" value={s?.total_emails ?? 0} desc={`${s?.waitlist_count ?? 0} aktif`} icon={<IcoEnvelope />} sparkPoints={sparks[3]} />
              </div>

              {/* Quick Actions */}
              <div style={{ marginTop: 40 }}>
                <div style={{ marginBottom: 16 }}><span className="db-eye">Hızlı İşlemler</span></div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12 }}>
                  {[
                    { name: "Yeni Keşfet",  desc: "Pazar segmentleri tara",  Icon: IcoSearch,    href: "/?mode=discover"    },
                    { name: "Derin Analiz", desc: "Tam fizibilite raporu",   Icon: IcoLightning, href: "/?mode=deep"        },
                    { name: "Orkestratör",  desc: "Otonom araştırma ajanı", Icon: IcoNetwork,   href: "/?mode=orchestrate" },
                  ].map(a => (
                    <Link key={a.name} href={a.href} className="db-card db-qa" style={{ padding: 20, display: "flex", alignItems: "center", gap: 14, textDecoration: "none" }}>
                      <span className="db-ico"><a.Icon /></span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 14, fontWeight: 500, color: "#F1F5F9", marginBottom: 2 }}>{a.name}</div>
                        <div style={{ fontSize: 12, color: "#3F4B5C" }}>{a.desc}</div>
                      </div>
                      <span className="db-qa-arrow" style={{ color: "#3F4B5C", fontSize: 14, transition: "transform .15s, color .15s", flexShrink: 0 }}>→</span>
                    </Link>
                  ))}
                </div>
              </div>

              {/* Mode Distribution */}
              <div style={{ marginTop: 40 }}>
                <div style={{ marginBottom: 16 }}><span className="db-eye">Mod Dağılımı</span></div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 10 }}>
                  {modeCounts.map(({ key, count, Icon, name }) => (
                    <div key={key} className="db-card" style={{ padding: "18px 16px", borderColor: key === topMode ? "rgba(139,92,246,.2)" : undefined }}>
                      <div className="db-ico" style={{ marginBottom: 10 }}><Icon size={15} /></div>
                      <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: "-0.03em", fontVariantNumeric: "tabular-nums", lineHeight: 1, color: key === topMode ? "#8B5CF6" : "#F1F5F9" }}>{count}</div>
                      <div style={{ fontSize: 11, color: "#3F4B5C", marginTop: 3 }}>{name}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Scans */}
              <div style={{ marginTop: 40 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                  <span className="db-eye">Son Taramalar</span>
                  <Link href="/gallery" style={{ fontSize: 12, color: "#3F4B5C", textDecoration: "none", transition: "color .12s" }}
                    onMouseEnter={e => (e.currentTarget.style.color = "#64748B")}
                    onMouseLeave={e => (e.currentTarget.style.color = "#3F4B5C")}>
                    Tümünü Gör →
                  </Link>
                </div>

                {scans.length === 0 ? (
                  <div style={{ background: "#0F1320", border: "1px solid rgba(255,255,255,.05)", borderRadius: 12, padding: "48px 24px", textAlign: "center", color: "#3F4B5C", fontSize: 13 }}>
                    Henüz tarama yapılmadı. Ana sayfadan bir tarama başlat.
                  </div>
                ) : (
                  <div style={{ borderRadius: 12, overflow: "hidden", border: "1px solid rgba(255,255,255,.05)" }}>
                    {scans.map(scan => {
                      const cfg = MODE_MAP[scan.mode] ?? MODE_MAP.discover;
                      const preview = cleanPreview(scan.report_preview || "");
                      const score = scan.confidence_score;
                      const dateStr = new Date(scan.created_at).toLocaleDateString("tr-TR", { day: "numeric", month: "short", year: "numeric" });
                      return (
                        <div key={scan.id} className="db-scan-row" onClick={() => router.push(`/scan/${scan.id}`)}>
                          {/* Mode icon */}
                          <div style={{ width: 32, height: 32, borderRadius: 8, background: "#080B14", border: "1px solid rgba(255,255,255,.05)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, color: "#3F4B5C" }}>
                            <cfg.Icon size={14} />
                          </div>
                          {/* Category */}
                          <span style={{ fontSize: 14, fontWeight: 500, color: "#F1F5F9", whiteSpace: "nowrap", flexShrink: 0 }}>
                            {scan.category || "Genel Tarama"}
                          </span>
                          {/* Dot separator */}
                          <span style={{ width: 4, height: 4, borderRadius: "50%", background: "rgba(255,255,255,.08)", flexShrink: 0 }} />
                          {/* Badge */}
                          <span className="db-pill" style={{ flexShrink: 0 }}>{cfg.label}</span>
                          {/* Preview */}
                          <span style={{ fontSize: 13, color: "#64748B", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", flex: 1, minWidth: 0 }}>
                            {preview || "Rapor bekleniyor…"}
                          </span>
                          {/* Score */}
                          {score != null ? (
                            <span style={{ display: "flex", alignItems: "center", gap: 7, flexShrink: 0 }}>
                              <span style={{ width: 3, height: 16, borderRadius: 1.5, background: scoreColor(score), flexShrink: 0 }} />
                              <span style={{ fontSize: 14, fontWeight: 600, color: "#F1F5F9", fontVariantNumeric: "tabular-nums" }}>{score}</span>
                            </span>
                          ) : (
                            <span style={{ width: 3, height: 16, borderRadius: 1.5, background: scan.status === "completed" ? "#10B981" : scan.status === "running" ? "rgba(139,92,246,.5)" : "#EF4444", flexShrink: 0 }} />
                          )}
                          {/* Date */}
                          <span style={{ fontSize: 12, color: "#3F4B5C", flexShrink: 0, minWidth: 72, textAlign: "right" }}>{dateStr}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

            </>
          )}
        </div>
      </div>
    </>
  );
}
