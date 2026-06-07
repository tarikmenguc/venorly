"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function FeaturesPage() {
  const { user } = useAuth();
  const router   = useRouter();

  return (
    <>
      <style>{`
        .lp-root{background:#080B14;color:#64748B;font-family:'Inter',-apple-system,sans-serif;font-size:15px;line-height:1.65;-webkit-font-smoothing:antialiased;min-height:100vh}
        .lp-root *,.lp-root *::before,.lp-root *::after{box-sizing:border-box;margin:0;padding:0}
        .lp-root a{text-decoration:none;color:inherit}
        .lp-root button{font-family:inherit;cursor:pointer}

        /* NAV */
        .lp-nav{position:sticky;top:0;z-index:200;height:48px;background:rgba(8,11,20,.92);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid rgba(255,255,255,.05);display:flex;align-items:center;padding:0 24px;gap:0}
        .lp-logo{font-size:15px;font-weight:700;color:#F1F5F9;letter-spacing:-.02em}
        .lp-sep{width:1px;height:16px;background:rgba(255,255,255,.08);margin:0 20px;flex-shrink:0}
        .lp-nav-links{display:flex;align-items:center;gap:2px}
        .lp-nav-lnk{padding:5px 10px;font-size:13px;color:#3F4B5C;border-radius:6px;transition:color .12s;border:none;background:none;cursor:pointer}
        .lp-nav-lnk:hover{color:#64748B}
        .lp-nav-right{margin-left:auto;display:flex;align-items:center;gap:8px}
        .lp-btn-ghost-sm{padding:5px 13px;font-size:13px;font-weight:500;color:#3F4B5C;background:transparent;border:1px solid rgba(255,255,255,.05);border-radius:7px;transition:color .12s,border-color .12s}
        .lp-btn-ghost-sm:hover{color:#64748B;border-color:rgba(255,255,255,.08)}
        .lp-btn-vi-sm{padding:5px 14px;height:32px;font-size:13px;font-weight:500;color:#fff;background:#8B5CF6;border:none;border-radius:7px;transition:opacity .15s}
        .lp-btn-vi-sm:hover{opacity:.88}

        /* WRAP */
        .lp-wrap{max-width:1080px;margin:0 auto;padding:0 24px}

        /* HERO */
        .lp-hero{padding:88px 0 80px;display:flex;align-items:center;justify-content:space-between;gap:56px;flex-wrap:wrap}
        .lp-hero-text{flex:1;min-width:300px;max-width:520px}
        .lp-eyebrow{display:inline-flex;align-items:center;gap:7px;padding:4px 12px 4px 8px;border:1px solid rgba(139,92,246,.3);border-radius:100px;background:rgba(139,92,246,.07);font-size:12px;font-weight:500;color:rgba(167,139,250,.9);margin-bottom:24px}
        .lp-pulse{width:7px;height:7px;border-radius:50%;background:#8B5CF6;flex-shrink:0;animation:lp-pulse 2s ease-in-out infinite}
        @keyframes lp-pulse{0%,100%{box-shadow:0 0 0 0 rgba(139,92,246,.55)}50%{box-shadow:0 0 0 5px rgba(139,92,246,0)}}
        .lp-h1{font-size:56px;font-weight:700;color:#F1F5F9;letter-spacing:-.035em;line-height:1.06;margin-bottom:20px}
        .lp-sub{font-size:18px;color:#64748B;line-height:1.65;max-width:440px;margin-bottom:32px}
        .lp-ctas{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:24px}
        .lp-btn-vi{padding:10px 22px;font-size:14px;font-weight:600;color:#fff;background:#8B5CF6;border:none;border-radius:9px;transition:opacity .15s;cursor:pointer}
        .lp-btn-vi:hover{opacity:.88}
        .lp-btn-ghost{padding:10px 18px;font-size:14px;font-weight:500;color:#64748B;background:transparent;border:1px solid rgba(255,255,255,.05);border-radius:9px;display:flex;align-items:center;gap:7px;transition:color .12s,border-color .12s;cursor:pointer}
        .lp-btn-ghost:hover{color:#F1F5F9;border-color:rgba(255,255,255,.08)}
        .lp-play-ico{width:16px;height:16px;border-radius:50%;border:1px solid rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;flex-shrink:0}
        .lp-trust{display:flex;align-items:center;gap:9px;font-size:12px;color:#3F4B5C}
        .lp-avatars{display:flex}
        .lp-avatar{width:22px;height:22px;border-radius:50%;border:2px solid #080B14;background:#161C2D;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;color:#3F4B5C;margin-left:-6px}
        .lp-avatars .lp-avatar:first-child{margin-left:0}

        /* HERO VISUAL */
        .lp-hero-visual{flex-shrink:0;position:relative;flex:0 0 440px;width:440px}
        @media(max-width:900px){.lp-hero-visual{flex:none;width:100%;max-width:420px;margin:0 auto}}
        .lp-glow{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:380px;height:260px;background:radial-gradient(ellipse 60% 50% at 50% 50%,rgba(139,92,246,.12) 0%,transparent 70%);filter:blur(40px);pointer-events:none;z-index:0}
        .lp-mock{position:relative;z-index:1;width:420px;background:#0F1320;border:1px solid rgba(255,255,255,.05);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:14px;transform:translateY(-8px)}
        @media(max-width:480px){.lp-mock{width:100%;transform:none}}
        .lp-mock-header{display:flex;align-items:center;justify-content:space-between}
        .lp-mock-label{font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:.1em;color:#3F4B5C}
        .lp-mock-badge{padding:2px 8px;border-radius:100px;font-size:10px;font-weight:700;background:rgba(16,185,129,.1);color:#10B981;border:1px solid rgba(16,185,129,.2)}
        .lp-mock-cat{font-size:12px;color:#64748B;margin-top:-4px}
        .lp-mock-guven{display:flex;align-items:center;gap:8px}
        .lp-mock-guven-l{font-size:10px;color:#3F4B5C;flex-shrink:0;width:76px}
        .lp-mock-guven-v{font-size:12px;font-weight:600;color:#F1F5F9;flex-shrink:0}
        .lp-mock-divider{height:1px;background:rgba(255,255,255,.05)}
        .lp-mock-rows{display:flex;flex-direction:column;gap:8px}
        .lp-mock-row{display:flex;align-items:center;gap:10px}
        .lp-mock-row-lbl{font-size:11px;color:#64748B;flex-shrink:0;width:110px}
        .lp-track{flex:1;height:3px;background:rgba(255,255,255,.06);border-radius:2px;overflow:hidden}
        .lp-fill{height:100%;border-radius:2px}
        .lp-mock-row-val{font-size:11px;font-weight:600;color:#F1F5F9;width:28px;text-align:right;flex-shrink:0}
        .lp-mock-insight{display:flex;align-items:flex-start;gap:7px;font-size:11px;color:#64748B;line-height:1.5}
        .lp-mock-footer{display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(255,255,255,.05);font-size:10px;color:#3F4B5C;margin-top:auto}
        .lp-mock-dot{width:6px;height:6px;border-radius:50%;background:#10B981;display:inline-block;margin-right:5px}

        /* SECTION */
        .lp-section{padding:80px 0;border-top:1px solid rgba(255,255,255,.05)}
        .lp-eye{font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:.12em;color:#3F4B5C;margin-bottom:10px}
        .lp-section-h{font-size:34px;font-weight:700;color:#F1F5F9;letter-spacing:-.025em;line-height:1.15;margin-bottom:12px}
        .lp-section-sub{font-size:16px;color:#64748B;max-width:460px;line-height:1.65;margin-bottom:48px}

        /* FEATURES */
        .lp-feat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
        @media(max-width:580px){.lp-feat-grid{grid-template-columns:1fr}}
        .lp-feat-card{padding:24px;background:#0F1320;border:1px solid rgba(255,255,255,.05);border-radius:12px;transition:border-color .15s,background .15s}
        .lp-feat-card:hover{border-color:rgba(139,92,246,.2);background:rgba(139,92,246,.04)}
        .lp-feat-ico{color:rgba(139,92,246,.6);margin-bottom:14px;display:block;transition:color .15s}
        .lp-feat-card:hover .lp-feat-ico{color:#8B5CF6}
        .lp-feat-eye{font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:.1em;color:#3F4B5C;margin-bottom:6px}
        .lp-feat-name{font-size:15px;font-weight:600;color:#F1F5F9;margin-bottom:5px}
        .lp-feat-body{font-size:13px;color:#64748B;line-height:1.6}
        .lp-feat-frag{margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.04);font-size:11px;color:#3F4B5C;font-family:'SF Mono','Fira Code',monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

        /* ACTIVITY BAR */
        .lp-activity{background:#0F1320;border-top:1px solid rgba(255,255,255,.05);border-bottom:1px solid rgba(255,255,255,.05);padding:20px 0}
        .lp-activity-inner{display:flex;align-items:center;justify-content:center;gap:40px;flex-wrap:wrap}
        .lp-activity-stat{display:flex;flex-direction:column;align-items:center;gap:5px}
        .lp-activity-lbl{font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:.12em;color:#3F4B5C}
        .lp-activity-val{font-size:16px;font-weight:500;color:#F1F5F9;font-variant-numeric:tabular-nums}
        .lp-activity-vsep{width:1px;height:28px;background:rgba(255,255,255,.06)}

        /* HOW IT WORKS */
        .lp-steps{display:flex;align-items:flex-start;gap:0}
        .lp-step{flex:1;text-align:center;padding:0 16px}
        .lp-step-num{width:32px;height:32px;border-radius:50%;background:rgba(139,92,246,.12);border:1px solid rgba(139,92,246,.3);color:rgba(167,139,250,.9);font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;margin:0 auto 16px}
        .lp-step-icon{color:rgba(139,92,246,.5);margin:6px auto 10px;display:flex;align-items:center;justify-content:center}
        .lp-step-title{font-size:15px;font-weight:600;color:#F1F5F9;margin-bottom:6px}
        .lp-step-desc{font-size:13px;color:#64748B;line-height:1.6}
        .lp-step-conn{flex-shrink:0;width:60px;align-self:flex-start;border-top:1px dashed rgba(255,255,255,.08);margin-top:15px}
        @media(max-width:600px){.lp-steps{flex-direction:column;align-items:center}.lp-step-conn{width:1px;height:32px;border-top:none;border-left:1px dashed rgba(255,255,255,.08);margin:0}}

        /* FINAL CTA */
        .lp-final-cta{padding:96px 0;border-top:1px solid rgba(255,255,255,.05);text-align:center}
        .lp-final-cta-sub{font-size:16px;color:#64748B;margin-bottom:32px}
        .lp-final-meta{font-size:12px;color:#3F4B5C;margin-top:14px}
        .lp-final-meta span{margin:0 6px}

        /* FOOTER */
        .lp-footer{padding:24px 0;border-top:1px solid rgba(255,255,255,.05);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
        .lp-foot-logo{font-size:14px;font-weight:700;color:#F1F5F9}
        .lp-foot-links{display:flex;gap:20px}
        .lp-foot-link{font-size:13px;color:#3F4B5C;transition:color .12s}
        .lp-foot-link:hover{color:#64748B}
        .lp-foot-copy{font-size:12px;color:#3F4B5C}
      `}</style>

      {/* SVG SPRITE */}
      <svg xmlns="http://www.w3.org/2000/svg" style={{ display: "none" }}>
        <symbol id="ic-pipeline" viewBox="0 0 18 18" fill="none">
          <circle cx="3" cy="9" r="2" stroke="currentColor" strokeWidth="1.4"/>
          <circle cx="9" cy="4" r="2" stroke="currentColor" strokeWidth="1.4"/>
          <circle cx="9" cy="14" r="2" stroke="currentColor" strokeWidth="1.4"/>
          <circle cx="15" cy="9" r="2" stroke="currentColor" strokeWidth="1.4"/>
          <path d="M5 9h2M11 9h2M9 6v2M9 12v-2M10.4 5.6l3.2 2.4M10.4 12.4l3.2-2.4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
        </symbol>
        <symbol id="ic-gauge" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="6.5" stroke="currentColor" strokeWidth="1.4"/>
          <circle cx="9" cy="9" r="3.5" stroke="currentColor" strokeWidth="1.4" strokeDasharray="10 12"/>
          <circle cx="9" cy="9" r="1.5" fill="currentColor" opacity=".4"/>
        </symbol>
        <symbol id="ic-radar" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.4"/>
          <circle cx="9" cy="9" r="3.5" stroke="currentColor" strokeWidth="1.4"/>
          <line x1="9" y1="1" x2="9" y2="17" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          <line x1="1" y1="9" x2="17" y2="9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
        </symbol>
        <symbol id="ic-bolt" viewBox="0 0 18 18" fill="none">
          <path d="M10.5 2L4 10h5.5L7 16l8-9.5H10z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
        </symbol>
        <symbol id="ic-play" viewBox="0 0 10 10" fill="none">
          <path d="M3 2l5 3-5 3V2z" fill="currentColor"/>
        </symbol>
        <symbol id="ic-cursor" viewBox="0 0 20 20" fill="none">
          <path d="M7 3h6M10 3v14M7 17h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </symbol>
        <symbol id="ic-gear" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="2.8" stroke="currentColor" strokeWidth="1.5"/>
          <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.22 4.22l1.42 1.42M14.36 14.36l1.42 1.42M4.22 15.78l1.42-1.42M14.36 5.64l1.42-1.42" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </symbol>
        <symbol id="ic-doc" viewBox="0 0 20 20" fill="none">
          <path d="M5 2h7l4 4v12a1 1 0 01-1 1H5a1 1 0 01-1-1V3a1 1 0 011-1z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
          <path d="M12 2v4h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M7 12l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </symbol>
        <symbol id="ic-bulb" viewBox="0 0 16 16" fill="none">
          <path d="M8 1.5a4 4 0 00-2 7.4V11h4V8.9a4 4 0 00-2-7.4z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
          <path d="M6.5 13h3M7 14.5h2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
        </symbol>
      </svg>

      <div className="lp-root">
        {/* NAV */}
        <nav className="lp-nav">
          <Link href="/" className="lp-logo">Venorly</Link>
          <div className="lp-sep" />
          <div className="lp-nav-links">
            <Link href="/dashboard" className="lp-nav-lnk">Dashboard</Link>
            <Link href="/features" className="lp-nav-lnk">Özellikler</Link>
            <Link href="/pricing" className="lp-nav-lnk">Fiyatlandırma</Link>
          </div>
          <div className="lp-nav-right">
            {user ? (
              <div
                onClick={() => router.push("/profile")}
                style={{width:30,height:30,borderRadius:"50%",background:"#1E293B",border:"1px solid rgba(255,255,255,.08)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:600,color:"#94A3B8",cursor:"pointer"}}
              >
                {user.email?.charAt(0).toUpperCase() ?? "U"}
              </div>
            ) : (
              <>
                <Link href="/sign-in" className="lp-btn-ghost-sm">Giriş Yap</Link>
                <Link href="/sign-up" className="lp-btn-vi-sm">Başla</Link>
              </>
            )}
          </div>
        </nav>

        {/* HERO */}
        <div className="lp-wrap">
          <div className="lp-hero">
            <div className="lp-hero-text">
              <div className="lp-eyebrow">
                <span className="lp-pulse" />
                AI Pazar Araştırması
              </div>
              <h1 className="lp-h1">Fikrinizi 3 Dakikada<br />Doğrulayın</h1>
              <p className="lp-sub">Venorly&apos;nin 13 aşamalı AI pipeline&apos;ı pazar büyüklüğünü, rekabeti ve teknik fizibiliteyi otomatik olarak analiz eder.</p>
              <div className="lp-ctas">
                <Link href="/" className="lp-btn-vi">Ücretsiz Dene</Link>
                <button className="lp-btn-ghost">
                  <span className="lp-play-ico">
                    <svg width="10" height="10"><use href="#ic-play" /></svg>
                  </span>
                  Demo İzle
                </button>
              </div>
              <div className="lp-trust">
                <div className="lp-avatars">
                  <div className="lp-avatar">A</div>
                  <div className="lp-avatar">K</div>
                  <div className="lp-avatar">M</div>
                </div>
                <span>500+ girişimci kullanıyor</span>
              </div>
            </div>

            {/* HERO CARD MOCKUP */}
            <div className="lp-hero-visual">
              <div className="lp-glow" />
              <div className="lp-mock">
                <div className="lp-mock-header">
                  <span className="lp-mock-label">Fizibilite Raporu</span>
                  <span className="lp-mock-badge">GİT</span>
                </div>
                <div className="lp-mock-cat">fintech AI asistan</div>
                <div className="lp-mock-guven">
                  <span className="lp-mock-guven-l">Güven Skoru</span>
                  <div className="lp-track"><div className="lp-fill" style={{ width: "87%", background: "#8B5CF6" }} /></div>
                  <span className="lp-mock-guven-v">87</span>
                </div>
                <div className="lp-mock-divider" />
                <div className="lp-mock-rows">
                  <div className="lp-mock-row">
                    <span className="lp-mock-row-lbl">Teknik Fizibilite</span>
                    <div className="lp-track"><div className="lp-fill" style={{ width: "90%", background: "#8B5CF6" }} /></div>
                    <span className="lp-mock-row-val">9/10</span>
                  </div>
                  <div className="lp-mock-row">
                    <span className="lp-mock-row-lbl">Pazar Büyüklüğü</span>
                    <div className="lp-track"><div className="lp-fill" style={{ width: "80%", background: "rgba(139,92,246,.6)" }} /></div>
                    <span className="lp-mock-row-val">8/10</span>
                  </div>
                  <div className="lp-mock-row">
                    <span className="lp-mock-row-lbl">Rekabet Analizi</span>
                    <div className="lp-track"><div className="lp-fill" style={{ width: "70%", background: "rgba(139,92,246,.35)" }} /></div>
                    <span className="lp-mock-row-val">7/10</span>
                  </div>
                </div>
                <div className="lp-mock-divider" />
                <div className="lp-mock-insight">
                  <svg width="14" height="14" style={{ color: "rgba(139,92,246,.6)", flexShrink: 0, marginTop: 1 }}><use href="#ic-bulb" /></svg>
                  <span>&ldquo;SaaS muhasebe araçlarında boşluk: B2B segmentinde %34 kullanıcı şikayeti mevcut&rdquo;</span>
                </div>
                <div className="lp-mock-footer">
                  <span><span className="lp-mock-dot" />Analiz tamamlandı</span>
                  <span>13 / 13 adım</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* FEATURES */}
        <section className="lp-section">
          <div className="lp-wrap">
            <p className="lp-eye">Özellikler</p>
            <h2 className="lp-section-h">Tek Pipeline,<br />Eksiksiz Analiz</h2>
            <p className="lp-section-sub">Pazar araştırmasından GTM stratejisine kadar her şey otomatik — manuel araştırmaya gerek yok.</p>
            <div className="lp-feat-grid">
              <div className="lp-feat-card">
                <span className="lp-feat-ico"><svg width="18" height="18"><use href="#ic-pipeline" /></svg></span>
                <span className="lp-feat-eye">Pipeline</span>
                <div className="lp-feat-name">13 Aşamalı Pipeline</div>
                <p className="lp-feat-body">Rakip analizi, şikayet kümeleme, trend eşleştirme — hepsi tek çalıştırmada.</p>
                <div className="lp-feat-frag">expand_query → fetch_market → … → auditor</div>
              </div>
              <div className="lp-feat-card">
                <span className="lp-feat-ico"><svg width="18" height="18"><use href="#ic-gauge" /></svg></span>
                <span className="lp-feat-eye">Güvenilirlik</span>
                <div className="lp-feat-name">Güven Endeksi</div>
                <p className="lp-feat-body">Kaynak çapraz doğrulama ile 0–100 güvenilirlik skoru. Hangi iddiaya inanılacağını bilirsiniz.</p>
                <div className="lp-feat-frag">0.4×S + 0.6×X · Son skor: 0.82 ✓</div>
              </div>
              <div className="lp-feat-card">
                <span className="lp-feat-ico"><svg width="18" height="18"><use href="#ic-radar" /></svg></span>
                <span className="lp-feat-eye">Hedef Kitle</span>
                <div className="lp-feat-name">Lead Radar</div>
                <p className="lp-feat-body">Hedef kitleyi otomatik belirle, ICP profili oluştur, erişim kanallarını önceliklendir.</p>
                <div className="lp-feat-frag">ICP: B2B SaaS · 11–50 çalışan · Türkiye</div>
              </div>
              <div className="lp-feat-card">
                <span className="lp-feat-ico"><svg width="18" height="18"><use href="#ic-bolt" /></svg></span>
                <span className="lp-feat-eye">Çıktılar</span>
                <div className="lp-feat-name">GTM Varlıkları</div>
                <p className="lp-feat-body">Waitlist landing page, e-posta sekansı, pitch deck — rapor bitince hazır.</p>
                <div className="lp-feat-frag">Waitlist sayfası + 3 e-posta + pitch taslağı</div>
              </div>
            </div>
          </div>
        </section>

        {/* ACTIVITY BAR */}
        <div className="lp-activity">
          <div className="lp-wrap">
            <div className="lp-activity-inner">
              <div className="lp-activity-stat">
                <span className="lp-activity-lbl">Bu hafta</span>
                <span className="lp-activity-val">143 tarama</span>
              </div>
              <div className="lp-activity-vsep" />
              <div className="lp-activity-stat">
                <span className="lp-activity-lbl">Tamamlanan</span>
                <span className="lp-activity-val" style={{ color: "#10B981" }}>89%</span>
              </div>
              <div className="lp-activity-vsep" />
              <div className="lp-activity-stat">
                <span className="lp-activity-lbl">Ort. süre</span>
                <span className="lp-activity-val">2.4 dakika</span>
              </div>
            </div>
          </div>
        </div>

        {/* HOW IT WORKS */}
        <section className="lp-section">
          <div className="lp-wrap">
            <p className="lp-eye">Nasıl Çalışır</p>
            <h2 className="lp-section-h">Üç Adımda<br />Cevabınız Hazır</h2>
            <div className="lp-steps">
              <div className="lp-step">
                <div className="lp-step-num">1</div>
                <div className="lp-step-icon"><svg width="20" height="20"><use href="#ic-cursor" /></svg></div>
                <div className="lp-step-title">Kategori Gir</div>
                <p className="lp-step-desc">&ldquo;fintech&rdquo; veya &ldquo;sağlık AI&rdquo; gibi bir kategori ya da fikir yazın.</p>
              </div>
              <div className="lp-step-conn" />
              <div className="lp-step">
                <div className="lp-step-num">2</div>
                <div className="lp-step-icon"><svg width="20" height="20"><use href="#ic-gear" /></svg></div>
                <div className="lp-step-title">Pipeline Çalışır</div>
                <p className="lp-step-desc">13 düğümlü AI ağı gerçek zamanlı veri akışıyla analizi tamamlar.</p>
              </div>
              <div className="lp-step-conn" />
              <div className="lp-step">
                <div className="lp-step-num">3</div>
                <div className="lp-step-icon"><svg width="20" height="20"><use href="#ic-doc" /></svg></div>
                <div className="lp-step-title">Rapor Hazır</div>
                <p className="lp-step-desc">Git / Geliştir / Vazgeç kararı + tam fizibilite analizi elinizde.</p>
              </div>
            </div>
          </div>
        </section>

        {/* FINAL CTA */}
        <div className="lp-final-cta">
          <div className="lp-wrap">
            <p className="lp-eye" style={{ textAlign: "center" }}>Başlayın</p>
            <h2 className="lp-section-h" style={{ textAlign: "center", margin: "0 auto 10px" }}>Bugün Başlayın</h2>
            <p className="lp-final-cta-sub">İlk analiziniz 3 dakika içinde hazır.</p>
            <Link href="/" className="lp-btn-vi" style={{ fontSize: 15, padding: "12px 28px", display: "inline-block" }}>Ücretsiz Başla</Link>
            <p className="lp-final-meta">
              <span>Kredi kartı gerekmez</span>·<span>3 ücretsiz tarama</span>
            </p>
          </div>
        </div>

        {/* FOOTER */}
        <div className="lp-wrap">
          <footer className="lp-footer">
            <span className="lp-foot-logo">Venorly</span>
            <div className="lp-foot-links">
              <a href="#" className="lp-foot-link">Gizlilik</a>
              <a href="#" className="lp-foot-link">Kullanım Koşulları</a>
              <a href="#" className="lp-foot-link">İletişim</a>
            </div>
            <span className="lp-foot-copy">© 2025 Venorly</span>
          </footer>
        </div>
      </div>
    </>
  );
}
