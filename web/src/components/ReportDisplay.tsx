"use client";

import { useState, useEffect, useRef } from "react";

// ── Types (mirrors lib/schemas.py) ───────────────────────────────────────────

export interface GoNoGoScore {
  decision: string;
  weighted_score?: number | null;
  market_attractiveness?: number | null;
  technical_barrier?: number | null;
  unit_economics?: number | null;
  gtm_ease?: number | null;
  leap_of_faith?: string[] | null;
  ensemble_note?: string | null;
}

export interface MarketAnalysis {
  tam?: string | null;
  tam_formula?: string | null;
  sam?: string | null;
  som?: string | null;
  cagr?: string | null;
  macro_signals?: string | null;
  tam_source?: string | null;
}

export interface Competitor {
  name: string;
  url?: string | null;
  weakness?: string | null;
  funding?: string | null;
}

export interface TechFeasibility {
  stack?: string | null;
  cpu_cost?: string | null;
  ltv?: string | null;
  cac?: string | null;
  pricing_model?: string | null;
}

export interface FeasibilityReport {
  idea_title: string;
  executive_summary: GoNoGoScore;
  market: MarketAnalysis;
  competition: {
    competitors: Competitor[];
    gap_summary?: string | null;
    entry_barriers?: string | null;
  };
  technical: TechFeasibility;
  validation: {
    icp?: string | null;
    waitlist_h1?: string | null;
    waitlist_h2?: string | null;
    value_prop?: string | null;
  };
  sources: Array<{ url: string; title?: string | null }>;
  confidence_index?: number | null;
  pivot_suggestions?: string[] | null;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function mapDecision(d: string) {
  if (d === "Go")    return { text: "GİT",      cls: "vr-t-em", pCls: "vr-p-em" };
  if (d === "No-Go") return { text: "VAZGEÇ",   cls: "vr-t-ro", pCls: "vr-p-ro" };
  return                    { text: "GELİŞTİR", cls: "vr-t-am", pCls: "vr-p-am" };
}

function easeOut(t: number) { return 1 - Math.pow(1 - t, 3); }

function barGrad(s: number) {
  if (s >= 9) return "linear-gradient(90deg,#10B981,#059669)";
  if (s >= 7) return "linear-gradient(90deg,#6D28D9,#8B5CF6)";
  if (s >= 5) return "linear-gradient(90deg,#F59E0B,#D97706)";
  return             "linear-gradient(90deg,#E11D48,#BE123C)";
}
function textCol(s: number) {
  if (s >= 9) return "#34D399";
  if (s >= 7) return "#A78BFA";
  if (s >= 5) return "#FCD34D";
  return             "#FB7185";
}

// ── Gauge (3-ring, Apple Fitness style) ──────────────────────────────────────

function GaugeSVG({ skor, guven }: { skor: number; guven: number }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    setProgress(0);
    const tid = setTimeout(() => {
      const t0 = Date.now(), dur = 1700;
      const tick = () => {
        const p = Math.min((Date.now() - t0) / dur, 1);
        setProgress(easeOut(p));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, 300);
    return () => clearTimeout(tid);
  }, [skor, guven]);

  const cx = 82, cy = 82;
  const rings = [
    { r: 72, pct: Math.min(skor / 100, 1),   color: "#F59E0B" },
    { r: 58, pct: Math.min(guven, 1),         color: "#E11D48" },
    { r: 44, pct: Math.min(guven * 0.9, 1),   color: "#FB923C" },
  ];

  return (
    <svg width={164} height={164} viewBox="0 0 164 164" style={{ display: "block" }}>
      {rings.map(({ r, pct, color }) => {
        const circ = 2 * Math.PI * r;
        const fill = circ * pct * progress;
        return (
          <g key={r}>
            <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,.06)" strokeWidth={3} />
            <circle
              cx={cx} cy={cy} r={r} fill="none"
              stroke={color} strokeWidth={3} strokeLinecap="round"
              strokeDasharray={`${fill} ${circ - fill}`}
              transform={`rotate(-90 ${cx} ${cy})`}
            />
          </g>
        );
      })}
    </svg>
  );
}

// ── Radar SVG ────────────────────────────────────────────────────────────────

const RADAR_AXES = ["Kullanılabilirlik", "Teknik Güç", "Entegrasyon", "Destek", "Fiyat"];

function RadarSVG({ competitors }: { competitors: Competitor[] }) {
  const cx = 150, cy = 155, maxR = 98, N = 5;
  const angles = Array.from({ length: N }, (_, i) => -Math.PI / 2 + (i * 2 * Math.PI) / N);

  const pt = (i: number, v: number): [number, number] => {
    const r = (v / 10) * maxR;
    return [cx + r * Math.cos(angles[i]), cy + r * Math.sin(angles[i])];
  };
  const poly = (vals: number[]) => vals.map((v, i) => pt(i, v).join(",")).join(" ");

  // Deterministic pseudo-scores from competitor name
  const compVals = (c: Competitor, idx: number) => {
    const s = c.name.charCodeAt(0) % 4;
    return [3 + s, 4 + ((s + idx) % 4), 3 + ((s + 2) % 4), 2 + ((s + idx + 1) % 5), 5 + (s % 3)];
  };

  const oppVals = [9, 8, 8, 7, 7];
  const shown   = competitors.slice(0, 2);
  const compColors = ["rgba(255,255,255,.22)", "rgba(255,255,255,.12)"];
  const compFills  = ["rgba(255,255,255,.03)", "rgba(255,255,255,.02)"];
  const legend = [
    ...shown.map((c, i) => ({ name: c.name, color: compColors[i] })),
    { name: "Fırsat Alanı", color: "rgba(109,40,217,.85)" },
  ];

  return (
    <svg width={300} height={300} viewBox="0 0 300 300">
      {[0.25, 0.5, 0.75, 1].map(lv => (
        <polygon key={lv}
          points={angles.map(a => `${cx + lv * maxR * Math.cos(a)},${cy + lv * maxR * Math.sin(a)}`).join(" ")}
          fill="none" stroke="rgba(255,255,255,.04)" strokeWidth="1"
        />
      ))}
      {angles.map((a, i) => (
        <g key={i}>
          <line x1={cx} y1={cy} x2={cx + maxR * Math.cos(a)} y2={cy + maxR * Math.sin(a)} stroke="rgba(255,255,255,.05)" strokeWidth="1" />
          <text x={cx + (maxR + 20) * Math.cos(a)} y={cy + (maxR + 20) * Math.sin(a)}
            textAnchor="middle" dominantBaseline="middle"
            fontSize="11" fill="rgba(156,163,175,.7)" fontFamily="inherit">{RADAR_AXES[i]}</text>
        </g>
      ))}
      {shown.map((c, i) => (
        <polygon key={i} points={poly(compVals(c, i))} fill={compFills[i]} stroke={compColors[i]} strokeWidth="1.5" />
      ))}
      <polygon points={poly(oppVals)} fill="rgba(109,40,217,.10)" stroke="rgba(109,40,217,.85)" strokeWidth="2" />
      {oppVals.map((v, i) => { const [px, py] = pt(i, v); return <circle key={i} cx={px} cy={py} r="3.5" fill="#8B5CF6" />; })}
      {legend.map((l, i) => (
        <g key={i}>
          <rect x="5" y={i * 16 + 6} width="12" height="3" rx="1.5" fill={l.color} />
          <text x="21" y={i * 16 + 11} fontSize="10" fill="rgba(156,163,175,.65)" fontFamily="inherit">{l.name}</text>
        </g>
      ))}
    </svg>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

interface Props {
  reportJson: FeasibilityReport;
  onCreateWaitlist: () => void;
  isCreatingWaitlist: boolean;
}

export function ReportDisplay({ reportJson, onCreateWaitlist, isCreatingWaitlist }: Props) {
  const [scoreDisplay, setScoreDisplay] = useState(0);
  const revealRefs = useRef<(HTMLDivElement | null)[]>([]);

  const dec   = mapDecision(reportJson.executive_summary.decision);
  const skor  = reportJson.executive_summary.weighted_score ?? 0;
  const guven = reportJson.confidence_index ?? 0;
  const market = reportJson.market;
  const tech   = reportJson.technical;
  const competitors = reportJson.competition.competitors ?? [];

  // Animated score counter
  useEffect(() => {
    setScoreDisplay(0);
    const tid = setTimeout(() => {
      const t0 = Date.now(), dur = 1700;
      const tick = () => {
        const p = Math.min((Date.now() - t0) / dur, 1);
        setScoreDisplay(Math.round(skor * easeOut(p)));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, 300);
    return () => clearTimeout(tid);
  }, [skor]);

  // Reveal animations
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add("in"); obs.unobserve(e.target); }
      }),
      { threshold: 0.05, rootMargin: "0px 0px -40px 0px" }
    );
    revealRefs.current.forEach(el => el && obs.observe(el));
    // Force-reveal elements already in viewport
    setTimeout(() => {
      revealRefs.current.forEach(el => {
        if (!el) return;
        const r = el.getBoundingClientRect();
        if (r.top < window.innerHeight + 80) el.classList.add("in");
      });
    }, 80);
    return () => obs.disconnect();
  }, []);

  const ref = (i: number) => (el: HTMLDivElement | null) => { revealRefs.current[i] = el; };

  // Feasibility rows (from scoring sub-dimensions)
  const feasRows = [
    { icon: "💳", name: "Pazar Çekiciliği",        score: Math.round((reportJson.executive_summary.market_attractiveness ?? 0) / 3), tip: "Pazar büyüme hızı ve toplam pazar büyüklüğü değerlendirmesi." },
    { icon: "🔧", name: "Teknik Fizibilite",        score: Math.round((reportJson.executive_summary.technical_barrier ?? 0) / 3),    tip: "Teknik engeller ve geliştirme karmaşıklığı değerlendirmesi." },
    { icon: "💰", name: "Birim Ekonomisi",          score: Math.round((reportJson.executive_summary.unit_economics ?? 0) / 2),        tip: "LTV/CAC oranı ve finansal sürdürülebilirlik." },
    { icon: "🚀", name: "Pazara Erişim",            score: Math.round((reportJson.executive_summary.gtm_ease ?? 0) / 2),              tip: "Hedef kitleye ulaşma kolaylığı ve dağıtım kanalları." },
    { icon: "⚡", name: "Rekabetten Farklılaşma",  score: competitors.length > 3 ? 6 : 8,                                            tip: "Mevcut rakiplere karşı farklılaşma potansiyeli." },
  ].filter(r => r.score > 0);

  const totalFeas = feasRows.reduce((s, r) => s + r.score, 0);
  const maxFeas   = feasRows.length * 10;
  const feasLabel = totalFeas / maxFeas >= 0.7 ? "Güçlü Fırsat ▲" : totalFeas / maxFeas >= 0.5 ? "Orta Fırsat →" : "Zayıf Fırsat ▼";

  const chips = reportJson.executive_summary.leap_of_faith?.slice(0, 3) ?? [];

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ color: "rgba(156,163,175,1)", fontFamily: "inherit", fontSize: 14, lineHeight: 1.7 }}>

      {/* ① HERO DECISION CARD */}
      <div ref={ref(0)} className="vr-reveal vr-card" style={{ padding: "32px 36px", position: "relative", overflow: "hidden", marginBottom: 20 }}>
        <div aria-hidden="true" style={{ position: "absolute", inset: 0, pointerEvents: "none", background: "radial-gradient(ellipse at 28% 55%,rgba(109,40,217,.9) 0%,transparent 65%)", filter: "blur(60px)", opacity: 0.13 }} />
        <div style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 36, flexWrap: "wrap" }}>
          {/* Left */}
          <div style={{ flex: 1, minWidth: 220 }}>
            <span className="vr-eye">KARAR</span>
            <div className={dec.cls} style={{ fontSize: 72, fontWeight: 600, lineHeight: 0.88, letterSpacing: "-0.045em" }}>
              {dec.text}
            </div>
            <div style={{ marginTop: 10, fontSize: 13 }}>
              Ağırlıklı Skor:{" "}
              <strong style={{ color: "rgba(167,139,250,.9)", fontWeight: 600 }}>{scoreDisplay}</strong> / 100
            </div>
            <div style={{ marginTop: 16, display: "flex", flexWrap: "wrap", gap: 6 }}>
              {chips.map((c, i) => <span key={i} className={`vr-pill ${dec.pCls}`} style={{ fontSize: 10 }}>{c}</span>)}
              {guven > 0 && (
                <span className={`vr-pill ${guven >= 0.75 ? "vr-p-em" : guven >= 0.50 ? "vr-p-am" : "vr-p-ro"}`} style={{ fontSize: 10 }}>
                  Güven: {(guven * 100).toFixed(0)}%
                </span>
              )}
            </div>
          </div>
          {/* Right: 3-ring gauge */}
          <div style={{ flexShrink: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
            <div style={{ position: "relative", width: 164, height: 164 }}>
              <GaugeSVG skor={skor} guven={guven} />
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
                <span style={{ fontSize: 34, fontWeight: 600, color: "rgba(243,244,246,1)", letterSpacing: "-0.03em", lineHeight: 1 }}>{scoreDisplay}</span>
                <span style={{ fontSize: 10, color: "rgba(156,163,175,.8)", marginTop: 2 }}>/ 100 puan</span>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4, alignSelf: "flex-start", paddingLeft: 4 }}>
              {([["#F59E0B", "Ağırlıklı Skor"], ["#E11D48", "Güven Endeksi"], ["#FB923C", "Kaynak Kalitesi"]] as [string, string][]).map(([c, l]) => (
                <div key={l} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10, color: "rgba(156,163,175,.8)" }}>
                  <span style={{ width: 20, height: 2, borderRadius: 1, background: c, display: "inline-block" }} />
                  {l}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ② TAM / SAM / SOM */}
      <div ref={ref(1)} className="vr-reveal" style={{ marginBottom: 20 }}>
        <span className="vr-eye">PAZAR BÜYÜKLÜĞÜ</span>
        <div style={{ display: "grid", gridTemplateColumns: "1fr .78fr .62fr", gap: 12 }}>
          <div className="vr-card vr-tip-wrap" style={{ padding: 24, background: "rgba(109,40,217,.05)", borderColor: "rgba(109,40,217,.16)" }}>
            <span className="vr-eye" style={{ marginBottom: 8 }}>TAM</span>
            <div style={{ fontSize: 32, fontWeight: 600, letterSpacing: "-0.045em", color: "rgba(243,244,246,1)", lineHeight: 1 }}>
              {market.tam ?? "—"}
            </div>
            <div style={{ fontSize: 11, marginTop: 5 }}>Toplam Adreslenebilir Pazar</div>
            {market.cagr && <div style={{ marginTop: 14 }}><span className="vr-pill vr-p-em">{market.cagr} CAGR ↑</span></div>}
            {(market.tam_formula || market.tam_source) && (
              <div className="vr-tip-box" style={{ width: 240 }}>
                {market.tam_formula && <><strong style={{ color: "rgba(243,244,246,1)", display: "block", marginBottom: 4 }}>Formül</strong>{market.tam_formula}</>}
                {market.tam_source && <em style={{ display: "block", marginTop: 4, color: "rgba(255,255,255,.28)", fontSize: 11 }}>Kaynak: {market.tam_source}</em>}
              </div>
            )}
          </div>
          <div className="vr-card" style={{ padding: 20 }}>
            <span className="vr-eye" style={{ marginBottom: 6 }}>SAM</span>
            <div style={{ fontSize: 26, fontWeight: 600, letterSpacing: "-0.04em", color: "rgba(243,244,246,1)", lineHeight: 1 }}>{market.sam ?? "—"}</div>
            <div style={{ fontSize: 11, marginTop: 4 }}>Ulaşılabilir Pazar</div>
          </div>
          <div className="vr-card" style={{ padding: 17, opacity: market.som ? 1 : 0.6 }}>
            <span className="vr-eye" style={{ marginBottom: 5 }}>SOM</span>
            <div style={{ fontSize: 22, fontWeight: 600, color: market.som ? "rgba(243,244,246,1)" : "rgba(255,255,255,.2)", lineHeight: 1 }}>{market.som ?? "—"}</div>
            <div style={{ fontSize: 11, marginTop: 4 }}>İlk Yıl Hedef</div>
          </div>
        </div>
        {market.macro_signals && (
          <div style={{ marginTop: 10, fontSize: 12, color: "rgba(156,163,175,.7)", padding: "10px 14px", borderRadius: 8, background: "rgba(255,255,255,.03)", border: "1px solid rgba(255,255,255,.05)" }}>
            {market.macro_signals}
          </div>
        )}
      </div>

      {/* ③ COMPETITION */}
      {competitors.length > 0 && (
        <div ref={ref(2)} className="vr-reveal" style={{ marginBottom: 20 }}>
          <span className="vr-eye">REKABET ANALİZİ</span>
          <div className="vr-card vr-card-flat" style={{ padding: "24px 16px 16px", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
            <RadarSVG competitors={competitors} />
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ flex: 1, overflowX: "auto", cursor: "grab" }}>
              <div style={{ display: "flex", gap: 10, width: "max-content", paddingBottom: 2 }}>
                {competitors.map((c, i) => (
                  <div key={i} className="vr-card" style={{ padding: 16, width: 188, flexShrink: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 11 }}>
                      <div style={{ width: 34, height: 34, borderRadius: 8, background: "rgba(109,40,217,.14)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 15, color: "rgba(167,139,250,.8)", flexShrink: 0 }}>
                        {(c.name[0] ?? "?").toUpperCase()}
                      </div>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 500, color: "rgba(243,244,246,1)" }}>{c.name}</div>
                        {c.url && <div style={{ fontSize: 11 }}>{c.url.replace(/^https?:\/\//, "").split("/")[0]}</div>}
                      </div>
                    </div>
                    {c.weakness && <div style={{ fontSize: 11, color: "rgba(255,255,255,.3)", lineHeight: 1.5 }}>· {c.weakness.slice(0, 90)}{c.weakness.length > 90 ? "…" : ""}</div>}
                    {c.funding && <div style={{ marginTop: 8 }}><span className="vr-pill vr-p-vi" style={{ fontSize: 10 }}>{c.funding}</span></div>}
                  </div>
                ))}
              </div>
            </div>
            {reportJson.competition.gap_summary && (
              <div style={{ flexShrink: 0, width: 196, padding: 16, borderRadius: 12, background: "rgba(16,185,129,.05)", border: "1px solid rgba(16,185,129,.14)" }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "#34D399", marginBottom: 7 }}>🎯 Tespit Edilen Boşluk</div>
                <p style={{ fontSize: 12, lineHeight: 1.6 }}>{reportJson.competition.gap_summary.slice(0, 240)}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ④ FEASIBILITY */}
      {feasRows.length > 0 && (
        <div ref={ref(3)} className="vr-reveal" style={{ marginBottom: 20 }}>
          <span className="vr-eye">FİZİBİLİTE DEĞERLENDİRMESİ</span>
          <div className="vr-card vr-card-flat" style={{ padding: "20px 24px" }}>
            {feasRows.map((r, i) => (
              <div key={i} className="vr-tip-wrap" style={{ display: "flex", alignItems: "center", gap: 12, padding: "11px 0", borderBottom: i < feasRows.length - 1 ? "1px solid rgba(255,255,255,.04)" : "none" }}>
                <span style={{ fontSize: 15, flexShrink: 0 }}>{r.icon}</span>
                <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,.68)", flexShrink: 0, width: 170 }}>{r.name}</span>
                <div className="vr-prog-track">
                  <div className="vr-prog-fill" style={{ background: barGrad(r.score), width: `${(r.score / 10) * 100}%` }} />
                </div>
                <strong style={{ fontSize: 12, fontWeight: 600, color: textCol(r.score), flexShrink: 0, width: 34, textAlign: "right" }}>{r.score}/10</strong>
                <div className="vr-tip-box" style={{ right: 0, left: "auto", transform: "none" }}>{r.tip}</div>
              </div>
            ))}
            <div style={{ marginTop: 16, padding: 1, borderRadius: 13, background: "linear-gradient(135deg,rgba(109,40,217,.55),rgba(79,70,229,.2))" }}>
              <div style={{ borderRadius: 12, background: "rgba(17,12,29,.9)", padding: "13px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                <span style={{ fontSize: 13 }}>Toplam Puan</span>
                <span style={{ fontSize: 18, fontWeight: 600, color: "rgba(167,139,250,.9)", letterSpacing: "-0.02em" }}>{totalFeas}/{maxFeas} · {feasLabel}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ⑤ TECHNICAL & FINANCIAL */}
      {(tech.cpu_cost || tech.ltv || tech.cac || tech.pricing_model || tech.stack) && (
        <div ref={ref(4)} className="vr-reveal" style={{ marginBottom: 20 }}>
          <span className="vr-eye">TEKNİK & FİNANSAL</span>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(172px,1fr))", gap: 12 }}>
            {tech.cpu_cost && (
              <div className="vr-card" style={{ padding: 20 }}>
                <span style={{ fontSize: 18, display: "block", marginBottom: 10 }}>🖥️</span>
                <span className="vr-eye" style={{ marginBottom: 5 }}>CPU Maliyeti</span>
                <div style={{ fontSize: 24, fontWeight: 600, color: "rgba(243,244,246,1)", lineHeight: 1, marginBottom: 4 }}>{tech.cpu_cost}</div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,.26)" }}>istek başına</div>
              </div>
            )}
            {tech.ltv && (
              <div className="vr-card" style={{ padding: 20 }}>
                <span style={{ fontSize: 18, display: "block", marginBottom: 10 }}>💰</span>
                <span className="vr-eye" style={{ marginBottom: 5 }}>LTV</span>
                <div style={{ fontSize: 24, fontWeight: 600, color: "rgba(243,244,246,1)", lineHeight: 1, marginBottom: 4 }}>{tech.ltv}</div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,.26)" }}>müşteri / yıl</div>
              </div>
            )}
            {tech.cac && (
              <div className="vr-card" style={{ padding: 20 }}>
                <span style={{ fontSize: 18, display: "block", marginBottom: 10 }}>📣</span>
                <span className="vr-eye" style={{ marginBottom: 5 }}>CAC</span>
                <div style={{ fontSize: 24, fontWeight: 600, color: "rgba(243,244,246,1)", lineHeight: 1, marginBottom: 4 }}>{tech.cac}</div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,.26)" }}>edinim maliyeti</div>
              </div>
            )}
            {tech.pricing_model && (
              <div className="vr-card" style={{ padding: 20 }}>
                <span style={{ fontSize: 18, display: "block", marginBottom: 10 }}>📦</span>
                <span className="vr-eye" style={{ marginBottom: 5 }}>Fiyatlandırma</span>
                <div style={{ fontSize: 18, fontWeight: 600, color: "rgba(167,139,250,.9)", lineHeight: 1, marginBottom: 4 }}>{tech.pricing_model}</div>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,.26)" }}>SaaS modeli</div>
              </div>
            )}
            {tech.stack && (
              <div className="vr-card" style={{ padding: 20 }}>
                <span style={{ fontSize: 18, display: "block", marginBottom: 10 }}>⚙️</span>
                <span className="vr-eye" style={{ marginBottom: 5 }}>Teknoloji Stack</span>
                <div style={{ fontSize: 13, fontWeight: 500, color: "rgba(167,139,250,.9)", lineHeight: 1.4 }}>{tech.stack}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ⑥ PIVOT SUGGESTIONS */}
      {reportJson.pivot_suggestions && reportJson.pivot_suggestions.length > 0 && (
        <div ref={ref(5)} className="vr-reveal" style={{ marginBottom: 20 }}>
          <span className="vr-eye">PİVOT ÖNERİLERİ</span>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {reportJson.pivot_suggestions.map((p, i) => (
              <div key={i} className="vr-card" style={{ padding: "14px 18px", display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ fontSize: 16, flexShrink: 0 }}>💡</span>
                <span style={{ fontSize: 13, color: "rgba(243,244,246,.75)", lineHeight: 1.6 }}>{p}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ⑦ ICP / VALUE PROP */}
      {(reportJson.validation.icp || reportJson.validation.value_prop) && (
        <div ref={ref(6)} className="vr-reveal" style={{ marginBottom: 20 }}>
          <span className="vr-eye">DOĞRULAMA & GTM</span>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {reportJson.validation.icp && (
              <div className="vr-card" style={{ padding: "18px 20px" }}>
                <span className="vr-eye" style={{ marginBottom: 6 }}>İdeal Müşteri Profili</span>
                <p style={{ fontSize: 13, color: "rgba(243,244,246,.75)", lineHeight: 1.6 }}>{reportJson.validation.icp}</p>
              </div>
            )}
            {reportJson.validation.value_prop && (
              <div className="vr-card" style={{ padding: "18px 20px" }}>
                <span className="vr-eye" style={{ marginBottom: 6 }}>Değer Önerisi</span>
                <p style={{ fontSize: 13, color: "rgba(243,244,246,.75)", lineHeight: 1.6 }}>{reportJson.validation.value_prop}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ⑧ CTA */}
      <div ref={ref(7)} className="vr-reveal" style={{ borderRadius: 12, padding: "36px 30px", background: "linear-gradient(135deg,rgba(16,185,129,.13),rgba(109,40,217,.09))", border: "1px solid rgba(16,185,129,.12)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 24, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 240 }}>
            <span className="vr-eye" style={{ color: "rgba(52,211,153,.7)" }}>SONRAKİ ADIM</span>
            <h2 style={{ fontSize: 20, fontWeight: 600, color: "rgba(243,244,246,1)", marginBottom: 8, lineHeight: 1.3 }}>Bu Fikri Doğrulamak İster Misin?</h2>
            <p style={{ fontSize: 13, maxWidth: 360 }}>5 dakika içinde kişiselleştirilmiş doğrulama planı oluştur. Müşteri görüşmeleri, MVP testleri ve metrikler dahil.</p>
          </div>
          <button
            onClick={onCreateWaitlist}
            disabled={isCreatingWaitlist}
            style={{ padding: "13px 22px", borderRadius: 10, background: "#10B981", color: "white", fontSize: 14, fontWeight: 600, fontFamily: "inherit", border: "none", cursor: isCreatingWaitlist ? "not-allowed" : "pointer", opacity: isCreatingWaitlist ? 0.6 : 1, display: "flex", alignItems: "center", gap: 8 }}
          >
            {isCreatingWaitlist ? "Kuruluyor..." : "✦ Doğrulama Sayfası Oluştur"}
          </button>
        </div>
      </div>
    </div>
  );
}
