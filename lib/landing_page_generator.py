"""
Landing Page Uretici - Venorly
report_json["validation"] iceriginden deploy-ready tek dosya HTML uretir.
Dis bagimlilik yok; saf Python string formatting.
"""

import re


def _esc(text) -> str:
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .strip())


_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --brand: #8b5cf6; --brand-dark: #6d28d9;
  --dark: #0f0f0f; --light: #f9fafb;
}
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       background: var(--dark); color: #fff; min-height: 100vh; }
nav { display: flex; justify-content: space-between; align-items: center;
      padding: 1.2rem 2rem; border-bottom: 1px solid rgba(255,255,255,0.08); }
.logo { font-size: 1.2rem; font-weight: 700; color: var(--brand); }
.badge { padding: 0.3rem 0.9rem; border-radius: 999px; font-size: 0.75rem;
         font-weight: 600; }
.hero { max-width: 760px; margin: 0 auto; padding: 5rem 2rem 3rem; text-align: center; }
.hero h1 { font-size: clamp(2rem, 5vw, 3.2rem); font-weight: 800;
           line-height: 1.15; letter-spacing: -1px; margin-bottom: 1.2rem; }
.hero h1 span { color: var(--brand); }
.hero h2 { font-size: 1.15rem; color: rgba(255,255,255,0.65); font-weight: 400;
           line-height: 1.6; max-width: 560px; margin: 0 auto 1rem; }
.value-prop { font-size: 1rem; color: rgba(255,255,255,0.5); margin-bottom: 2.5rem; }
.form-wrap { display: flex; gap: 0.5rem; max-width: 480px; margin: 0 auto 1rem;
             flex-wrap: wrap; justify-content: center; }
.form-wrap input { flex: 1; min-width: 220px; padding: 0.85rem 1.2rem;
                   border-radius: 10px; border: 1px solid rgba(255,255,255,0.15);
                   background: rgba(255,255,255,0.06); color: #fff;
                   font-size: 0.95rem; outline: none; }
.form-wrap input:focus { border-color: var(--brand); }
.form-wrap button { padding: 0.85rem 1.6rem; border-radius: 10px;
                    background: var(--brand); color: #fff; font-weight: 700;
                    font-size: 0.95rem; border: none; cursor: pointer;
                    transition: background 0.2s; white-space: nowrap; }
.form-wrap button:hover { background: var(--brand-dark); }
.form-note { font-size: 0.8rem; color: rgba(255,255,255,0.35); margin-bottom: 3rem; }
.tam { font-size: 0.9rem; color: rgba(255,255,255,0.4); margin-top: 0.5rem; }
.features { max-width: 680px; margin: 0 auto 4rem; padding: 0 2rem; }
.features h3 { text-align: center; font-size: 1.4rem; font-weight: 700;
               margin-bottom: 1.5rem; color: rgba(255,255,255,0.9); }
.feature-list { list-style: none; display: flex; flex-direction: column; gap: 0.9rem; }
.feature-item { display: flex; align-items: flex-start; gap: 0.75rem;
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 10px; padding: 0.9rem 1.2rem;
                font-size: 0.95rem; color: rgba(255,255,255,0.8); }
.check { color: var(--brand); font-size: 1.1rem; flex-shrink: 0; padding-top: 1px; }
.meta { max-width: 680px; margin: 0 auto 4rem; padding: 0 2rem;
        display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; }
.meta-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
             border-radius: 10px; padding: 1rem 1.4rem; font-size: 0.88rem;
             color: rgba(255,255,255,0.6); text-align: center; min-width: 160px; }
.meta-card strong { display: block; color: #fff; font-size: 0.95rem; margin-bottom: 0.2rem; }
footer { text-align: center; padding: 2rem; font-size: 0.8rem;
         color: rgba(255,255,255,0.2); border-top: 1px solid rgba(255,255,255,0.06); }
footer a { color: var(--brand); text-decoration: none; }
@media (max-width: 520px) {
  .hero { padding: 3rem 1.2rem 2rem; }
  .form-wrap { flex-direction: column; }
  .form-wrap input, .form-wrap button { width: 100%; }
}
"""

_JS = """
function handleSignup() {
  var email = document.getElementById("email").value.trim();
  if (!email || email.indexOf("@") < 0) { alert("Gecerli bir e-posta girin."); return; }
  document.querySelector(".form-wrap").innerHTML =
    '<p style="color:#22c55e;font-size:1.1rem;font-weight:700">Kaydedildi! Haberdar edileceksiniz.</p>';
}
"""


def generate_landing_page(report_json: dict) -> str:
    """report_json (FeasibilityReport dict) -> deploy-ready HTML string."""
    v  = report_json.get("validation") or {}
    es = report_json.get("executive_summary") or {}
    m  = report_json.get("market") or {}
    t  = report_json.get("technical") or {}

    title      = _esc(report_json.get("idea_title") or "Yeni SaaS")
    h1         = _esc(v.get("waitlist_h1") or title)
    h2         = _esc(v.get("waitlist_h2") or "Erken erisim listesine katil.")
    value_prop = _esc(v.get("value_prop") or "")
    icp        = _esc(v.get("icp") or "")
    pricing    = _esc(t.get("pricing_model") or "")
    tam        = _esc(m.get("tam") or "")
    decision   = es.get("decision", "Go")

    badge_colors = {"Go": "#22c55e", "Hold": "#eab308", "No-Go": "#ef4444"}
    badge_color  = badge_colors.get(decision, "#8b5cf6")
    badge_labels = {"Go": "Yatirimci Onayi: Git", "Hold": "Dikkatli Devam", "No-Go": "Yuksek Risk"}
    badge_label  = badge_labels.get(decision, decision)

    # Feature listesi — cold_email_sequence adimlarini donustur
    feature_items = []
    for step in (v.get("cold_email_sequence") or [])[:4]:
        feature_items.append(
            '<li class="feature-item">'
            '<span class="check">&#10003;</span>'
            '<span>' + _esc(step) + '</span>'
            '</li>'
        )

    # Opsiyonel bloklar
    value_block   = '<p class="value-prop">' + value_prop + '</p>' if value_prop else ''
    tam_block     = '<p class="tam">Adreslenebilir Pazar: <strong>' + tam + '</strong></p>' if tam else ''
    icp_card      = '<div class="meta-card"><strong>Hedef Kitle</strong>' + icp + '</div>' if icp else ''
    pricing_card  = '<div class="meta-card"><strong>Fiyatlandirma</strong>' + pricing + '</div>' if pricing else ''

    features_section = ''
    if feature_items:
        features_section = (
            '<section class="features">'
            '<h3>Neden bu araci kullanmaliyim?</h3>'
            '<ul class="feature-list">'
            + ''.join(feature_items) +
            '</ul></section>'
        )

    badge_style = (
        'background:' + badge_color + '22;'
        'color:' + badge_color + ';'
        'border:1px solid ' + badge_color + '44;'
    )

    parts = [
        '<!DOCTYPE html><html lang="tr"><head>',
        '<meta charset="UTF-8"/>',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>',
        '<title>' + h1 + '</title>',
        '<style>' + _CSS + '</style>',
        '</head><body>',
        '<nav>',
        '  <span class="logo">&#9670; ' + title + '</span>',
        '  <span class="badge" style="' + badge_style + '">' + badge_label + '</span>',
        '</nav>',
        '<section class="hero">',
        '  <h1>' + h1 + '</h1>',
        '  <h2>' + h2 + '</h2>',
        value_block,
        '  <div class="form-wrap">',
        '    <input type="email" placeholder="E-posta adresiniz" id="email"/>',
        '    <button onclick="handleSignup()">Erken Erisim Listesine Katil</button>',
        '  </div>',
        '  <p class="form-note">Ucretsiz &bull; Spam yok &bull; Istediginizde cikabilirsiniz</p>',
        tam_block,
        '</section>',
        features_section,
        '<div class="meta">',
        icp_card,
        pricing_card,
        '  <div class="meta-card"><strong>Durum</strong>Erken Erisim</div>',
        '</div>',
        '<footer>',
        '  <p>Venorly tarafindan uretildi &bull; <a href="https://venorly.com">venorly.com</a></p>',
        '</footer>',
        '<script>' + _JS + '</script>',
        '</body></html>',
    ]

    return '\n'.join(p for p in parts if p)
