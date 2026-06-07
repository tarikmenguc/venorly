"use client";

import Link from "next/link";
import { useState, useMemo } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface IdeaCard {
  id: string;
  cat: "video" | "gorsel" | "ses" | "metin";
  score: number;
  week: number;
  title: string;
  desc: string;
  tags: string[];
  footLabel: string;
  weekLabel: string;
  icon: "video" | "image" | "mic" | "paint" | "text";
}

// ── Static data (replace with API call when /api/gallery is ready) ────────────

const IDEAS: IdeaCard[] = [
  {
    id: "1", cat: "video", score: 65, week: 22, icon: "video",
    title: "Kısa Video İçerik Üreticisi",
    desc: "Sosyal medya platformları için metin girdisinden otomatik kısa video oluşturan SaaS aracı. Reels, TikTok ve YouTube Shorts formatlarını destekler.",
    tags: ["B2C", "SaaS", "AI"], footLabel: "Video Üretim", weekLabel: "Hafta 22 · 2026",
  },
  {
    id: "2", cat: "gorsel", score: 65, week: 22, icon: "image",
    title: "E-ticaret Ürün Görseli Üretici",
    desc: "E-ticaret satıcıları için ürün fotoğrafını profesyonel arka planlarla otomatik düzenleyen ve varyant oluşturan görsel AI aracı.",
    tags: ["B2B", "E-ticaret", "API"], footLabel: "Görsel Üretim", weekLabel: "Hafta 22 · 2026",
  },
  {
    id: "3", cat: "ses", score: 65, week: 22, icon: "mic",
    title: "Podcast Transkripsiyon ve Özet Aracı",
    desc: "Podcast ve toplantı kayıtlarını otomatik transkripsiyona çeviren, bölümlere ayıran ve SEO dostu özet oluşturan SaaS platformu.",
    tags: ["B2B", "API", "SaaS"], footLabel: "Ses İşleme", weekLabel: "Hafta 22 · 2026",
  },
  {
    id: "4", cat: "video", score: 65, week: 21, icon: "video",
    title: "AI Destekli Video Alt Yazı ve Çeviri",
    desc: "Video içeriklerine otomatik alt yazı ekleyen, 40+ dile çeviren ve marka renkleriyle özelleştirilebilen video işleme API'si.",
    tags: ["API", "SaaS", "Çeviri"], footLabel: "Video Üretim", weekLabel: "Hafta 21 · 2026",
  },
  {
    id: "5", cat: "gorsel", score: 65, week: 21, icon: "paint",
    title: "KOBİ'ler için AI Logo ve Marka Kiti",
    desc: "Küçük işletmeler için sektör ve değer önerisi girdisinden logo, renk paleti ve marka kılavuzu otomatik üreten tasarım aracı.",
    tags: ["B2B", "Tasarım", "No-code"], footLabel: "Görsel Üretim", weekLabel: "Hafta 21 · 2026",
  },
  {
    id: "6", cat: "metin", score: 65, week: 21, icon: "text",
    title: "SEO Odaklı Blog İçerik Otomasyonu",
    desc: "Anahtar kelime analizinden taslak hazırlamaya kadar tüm içerik üretim sürecini otomatikleştiren, CMS entegrasyonlu içerik SaaS platformu.",
    tags: ["B2B", "SEO", "SaaS"], footLabel: "Metin Üretim", weekLabel: "Hafta 21 · 2026",
  },
];

// ── Score pill class ───────────────────────────────────────────────────────────

function scoreClass(s: number) {
  if (s >= 70) return "gl-score-ok";
  if (s >= 45) return "gl-score-warn";
  return "gl-score-err";
}

// ── Icons ─────────────────────────────────────────────────────────────────────

function Icon({ name }: { name: IdeaCard["icon"] }) {
  switch (name) {
    case "video": return (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
        <rect x="2" y="5" width="12" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M14 8l4-2v6l-4-2V8z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
      </svg>
    );
    case "image": return (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
        <rect x="2" y="3" width="16" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.5"/>
        <circle cx="7" cy="8" r="1.5" stroke="currentColor" strokeWidth="1.3"/>
        <path d="M2 13l4-4 3 3 3-3 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    );
    case "mic": return (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
        <rect x="7" y="2" width="6" height="9" rx="3" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M4 10a6 6 0 0012 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <line x1="10" y1="16" x2="10" y2="18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <line x1="7" y1="18" x2="13" y2="18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    );
    case "paint": return (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
        <path d="M3 14c0-1 .5-2 1.5-3L12 3.5A2 2 0 0115 6.5L7.5 14c-1 1-2 1.5-3 1.5H3v-1.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
        <circle cx="16.5" cy="16.5" r="1.5" stroke="currentColor" strokeWidth="1.3"/>
      </svg>
    );
    case "text": return (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
        <line x1="3" y1="5" x2="17" y2="5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <line x1="3" y1="9" x2="17" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <line x1="3" y1="13" x2="11" y2="13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    );
  }
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function GalleryPage() {
  const [activeCat, setActiveCat]   = useState<string>("all");
  const [activeSort, setActiveSort] = useState<"score" | "date">("score");

  const filtered = useMemo(() => {
    const f = activeCat === "all" ? IDEAS : IDEAS.filter(c => c.cat === activeCat);
    return [...f].sort((a, b) =>
      activeSort === "score" ? b.score - a.score : b.week - a.week
    );
  }, [activeCat, activeSort]);

  const avgScore = IDEAS.length ? Math.round(IDEAS.reduce((s, c) => s + c.score, 0) / IDEAS.length) : 0;
  const best = [...IDEAS].sort((a, b) => b.score - a.score)[0]?.footLabel ?? "—";

  return (
    <>
      <style>{`
        .gl-root{background:#080B14;color:#64748B;font-family:'Inter',-apple-system,sans-serif;font-size:14px;line-height:1.65;-webkit-font-smoothing:antialiased;min-height:100vh}
        .gl-root *,.gl-root *::before,.gl-root *::after{box-sizing:border-box;margin:0;padding:0}
        .gl-root a{text-decoration:none;color:inherit}

        /* NAV */
        .gl-nav{position:sticky;top:0;z-index:200;height:48px;background:rgba(8,11,20,.92);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid rgba(255,255,255,.05);display:flex;align-items:center;padding:0 24px}
        .gl-logo{font-size:15px;font-weight:700;color:#F1F5F9;letter-spacing:-.02em}
        .gl-sep{width:1px;height:16px;background:rgba(255,255,255,.08);margin:0 20px;flex-shrink:0}
        .gl-nav-links{display:flex;align-items:center;gap:2px}
        .gl-nav-lnk{padding:5px 10px;font-size:13px;color:#3F4B5C;border-radius:6px;border:none;background:none;transition:color .12s;cursor:pointer;text-decoration:none;display:inline-block}
        .gl-nav-lnk:hover{color:#64748B}
        .gl-nav-lnk.active{color:#F1F5F9;font-weight:500}
        .gl-nav-right{margin-left:auto;display:flex;align-items:center;gap:8px}
        .gl-btn-ghost-sm{padding:5px 13px;font-size:13px;font-weight:500;color:#3F4B5C;background:transparent;border:1px solid rgba(255,255,255,.05);border-radius:7px;transition:color .12s,border-color .12s;cursor:pointer;text-decoration:none;display:inline-block}
        .gl-btn-ghost-sm:hover{color:#64748B;border-color:rgba(255,255,255,.08)}
        .gl-btn-vi-sm{padding:5px 14px;height:32px;font-size:13px;font-weight:500;color:#fff;background:#8B5CF6;border:none;border-radius:7px;transition:opacity .15s;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center}
        .gl-btn-vi-sm:hover{opacity:.88}

        /* WRAP */
        .gl-wrap{max-width:1080px;margin:0 auto;padding:0 24px}

        /* HEADER */
        .gl-head{text-align:center;padding:64px 0 48px}
        .gl-eyebrow{display:inline-flex;align-items:center;gap:7px;padding:4px 12px 4px 8px;border:1px solid rgba(139,92,246,.3);border-radius:100px;background:rgba(139,92,246,.07);font-size:12px;font-weight:500;color:rgba(167,139,250,.9);margin-bottom:20px}
        .gl-pulse{width:7px;height:7px;border-radius:50%;background:#8B5CF6;flex-shrink:0;animation:gl-pulse 2s ease-in-out infinite}
        @keyframes gl-pulse{0%,100%{box-shadow:0 0 0 0 rgba(139,92,246,.55)}50%{box-shadow:0 0 0 5px rgba(139,92,246,0)}}
        .gl-title{font-size:48px;font-weight:700;color:#F1F5F9;letter-spacing:-.03em;line-height:1.1;margin-bottom:14px}
        .gl-sub{font-size:16px;color:#64748B;max-width:480px;margin:0 auto 20px;line-height:1.65}
        .gl-stats{display:flex;align-items:center;justify-content:center;gap:10px;font-size:13px;color:#3F4B5C}
        .gl-stats-dot{width:3px;height:3px;border-radius:50%;background:#3F4B5C;opacity:.4}

        /* FILTER */
        .gl-filter-bar{padding-bottom:32px;display:flex;flex-direction:column;gap:12px}
        .gl-filter-row{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
        .gl-filter-pills{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
        .gl-fpill{height:28px;padding:0 12px;border-radius:100px;font-size:12px;font-weight:500;border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.05);color:#64748B;transition:background .12s,border-color .12s,color .12s;cursor:pointer}
        .gl-fpill:hover{background:rgba(255,255,255,.08);color:#F1F5F9}
        .gl-fpill.active{background:#8B5CF6;border-color:#8B5CF6;color:#fff}
        .gl-sort-group{display:flex;align-items:center;gap:4px}
        .gl-sbtn{height:28px;padding:0 12px;border-radius:8px;font-size:12px;font-weight:500;background:transparent;color:#3F4B5C;border:1px solid rgba(255,255,255,.05);transition:border-color .12s,color .12s;cursor:pointer}
        .gl-sbtn:hover{color:#64748B;border-color:rgba(255,255,255,.08)}
        .gl-sbtn.active{border-color:rgba(139,92,246,.4);color:rgba(167,139,250,.9)}
        .gl-result-count{font-size:12px;color:#3F4B5C}

        /* GRID */
        .gl-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
        @media(max-width:720px){.gl-grid{grid-template-columns:repeat(2,1fr)}}
        @media(max-width:480px){.gl-grid{grid-template-columns:1fr}}

        /* CARD */
        .gl-card{background:#0F1320;border:1px solid rgba(255,255,255,.05);border-radius:12px;padding:20px;display:flex;flex-direction:column;transition:border-color .15s,background .15s,transform .15s;cursor:pointer}
        .gl-card:hover{border-color:rgba(139,92,246,.2);background:rgba(139,92,246,.03);transform:translateY(-2px)}
        .gl-card-top{display:flex;align-items:flex-start;justify-content:flex-end}
        .gl-ico{color:rgba(139,92,246,.6);display:block;margin-bottom:14px;transition:color .15s}
        .gl-card:hover .gl-ico{color:#8B5CF6}
        .gl-score-pill{padding:2px 7px;border-radius:100px;font-size:11px;font-weight:600;white-space:nowrap;border:1px solid transparent;flex-shrink:0}
        .gl-score-ok{background:rgba(16,185,129,.1);color:#10B981;border-color:rgba(16,185,129,.2)}
        .gl-score-warn{background:rgba(245,158,11,.1);color:#F59E0B;border-color:rgba(245,158,11,.2)}
        .gl-score-err{background:rgba(239,68,68,.1);color:#EF4444;border-color:rgba(239,68,68,.2)}
        .gl-card-title{font-size:15px;font-weight:600;color:#F1F5F9;line-height:1.35;margin-top:14px;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
        .gl-card-desc{font-size:13px;color:#64748B;line-height:1.6;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;flex:1}
        .gl-card-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:14px}
        .gl-tag{height:22px;padding:0 8px;border-radius:100px;font-size:10px;font-weight:500;background:rgba(255,255,255,.05);color:#3F4B5C;border:1px solid rgba(255,255,255,.06);display:inline-flex;align-items:center}
        .gl-card-foot{display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding-top:10px;border-top:1px solid rgba(255,255,255,.04);font-size:11px;color:#3F4B5C}

        /* EMPTY */
        .gl-empty{grid-column:1/-1;background:#0F1320;border:1px solid rgba(255,255,255,.05);border-radius:12px;padding:48px;text-align:center;font-size:13px;color:#3F4B5C}
      `}</style>

      <div className="gl-root">
        {/* NAV */}
        <nav className="gl-nav">
          <Link href="/" className="gl-logo">Venorly</Link>
          <div className="gl-sep" />
          <div className="gl-nav-links">
            <Link href="/dashboard" className="gl-nav-lnk">Dashboard</Link>
            <Link href="/gallery" className="gl-nav-lnk active">Galeri</Link>
            <Link href="/" className="gl-nav-lnk">Keşfet</Link>
          </div>
          <div className="gl-nav-right">
            <Link href="/" className="gl-btn-ghost-sm">Giriş Yap</Link>
            <Link href="/" className="gl-btn-vi-sm">Başla</Link>
          </div>
        </nav>

        <div className="gl-wrap">
          {/* HEADER */}
          <div className="gl-head">
            <div className="gl-eyebrow">
              <span className="gl-pulse" />
              Haftalık Otomatik Güncelleme
            </div>
            <h1 className="gl-title">Galeri</h1>
            <p className="gl-sub">Yapay zeka tarafından analiz edilen en yüksek potansiyelli Micro-SaaS fırsatları.</p>
            <div className="gl-stats">
              <span>{IDEAS.length} Fikir</span>
              <span className="gl-stats-dot" />
              <span>Ort. Puan: {avgScore}/100</span>
              <span className="gl-stats-dot" />
              <span>En İyi: {best}</span>
            </div>
          </div>

          {/* FILTER BAR */}
          <div className="gl-filter-bar">
            <div className="gl-filter-row">
              <div className="gl-filter-pills">
                {(["all","video","gorsel","ses","metin"] as const).map(cat => (
                  <button
                    key={cat}
                    className={`gl-fpill${activeCat === cat ? " active" : ""}`}
                    onClick={() => setActiveCat(cat)}
                  >
                    {cat === "all" ? "Tümü" : cat === "video" ? "Video" : cat === "gorsel" ? "Görsel" : cat === "ses" ? "Ses" : "Metin"}
                  </button>
                ))}
              </div>
              <div className="gl-sort-group">
                {(["score","date"] as const).map(s => (
                  <button
                    key={s}
                    className={`gl-sbtn${activeSort === s ? " active" : ""}`}
                    onClick={() => setActiveSort(s)}
                  >
                    {s === "score" ? "Puan" : "Tarih"}
                  </button>
                ))}
              </div>
            </div>
            <div className="gl-result-count">{filtered.length} fikir bulundu</div>
          </div>

          {/* CARD GRID */}
          <div className="gl-grid">
            {filtered.length === 0 ? (
              <div className="gl-empty">Henüz fikir bulunamadı</div>
            ) : (
              filtered.map(card => (
                <div key={card.id} className="gl-card">
                  <div className="gl-card-top">
                    <span className={`gl-score-pill ${scoreClass(card.score)}`}>{card.score}</span>
                  </div>
                  <span className="gl-ico"><Icon name={card.icon} /></span>
                  <div className="gl-card-title">{card.title}</div>
                  <p className="gl-card-desc">{card.desc}</p>
                  <div className="gl-card-tags">
                    {card.tags.map(t => <span key={t} className="gl-tag">{t}</span>)}
                  </div>
                  <div className="gl-card-foot">
                    <span>{card.footLabel}</span>
                    <span>{card.weekLabel}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div style={{ height: 80 }} />
      </div>
    </>
  );
}
