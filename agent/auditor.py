"""
Auditor Agent — Rapor doğrulama ve Hibrit Güven Endeksi.

İş akışı:
  1. Rapor JSON'undaki sayısal iddiaları ayıkla (kritik/maddi/açıklayıcı sınıfla).
  2. Her iddiayı kaynak havuzuyla eşleştir.
  3. Eşleşmeyeni "(Kaynak: doğrulanamadı)" olarak işaretle.
  4. Hibrit skor hesapla: 0.4 × Kaynak Kalitesi (S) + 0.6 × Çapraz Doğrulama (X).
  5. 3-bant banner ekle ve audit_trail'e yaz.
"""

import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from lib.source_routing import get_confidence

# İddia sınıfı ağırlıkları
CLAIM_WEIGHTS = {
    "critical":    3.0,   # TAM/SAM/SOM, MRR, fiyat, kurucu adı, yatırım
    "material":    2.0,   # Rakip özellik, pazar payı, şikayet sıklığı
    "descriptive": 1.0,   # Sektör trendi, genel ifade
}

# Kritik iddia örüntüleri
CRITICAL_PATTERNS = re.compile(
    r"\$[\d.,]+[BMK]?|\bTAM\b|\bSAM\b|\bSOM\b|\bMRR\b|\bARR\b|"
    r"\bCAC\b|\bLTV\b|\byatırım\b|\bfunding\b|\bvaluation\b",
    re.IGNORECASE,
)
MATERIAL_PATTERNS = re.compile(
    r"\bpazar payı\b|\bmarket share\b|\bşikayet\b|\brating\b|\breviews?\b",
    re.IGNORECASE,
)


def _classify_claim(text: str) -> str:
    if CRITICAL_PATTERNS.search(text):
        return "critical"
    if MATERIAL_PATTERNS.search(text):
        return "material"
    return "descriptive"


def extract_claims(report_json: dict) -> list[dict]:
    """
    Rapor JSON'undan sayısal/kritik iddiaları çıkarır.
    Her iddia: {text, field, claim_class}
    """
    claims = []

    def _walk(obj, field_path=""):
        if isinstance(obj, str) and len(obj) > 10:
            # Sayı veya kritik kelime içerenleri al
            if re.search(r"\d|TAM|SAM|SOM|MRR|\$", obj, re.IGNORECASE):
                claims.append({
                    "text":        obj[:300],
                    "field":       field_path,
                    "claim_class": _classify_claim(obj),
                })
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _walk(v, f"{field_path}.{k}" if field_path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _walk(item, f"{field_path}[{i}]")

    _walk(report_json)
    return claims


def verify_claims(claims: list[dict], sources: list[dict]) -> list[dict]:
    """
    Her iddiayı kaynak listesiyle eşleştirir.
    Eşleşme: iddia metninde kaynak URL'inden domain adı geçiyorsa.
    """
    source_domains = set()
    source_confidence_map: dict[str, float] = {}

    for src in sources:
        url = src.get("url", "")
        if url:
            domain = url.split("/")[2] if url.startswith("http") else url
            source_domains.add(domain)
            # Kaynağın adını source_routing'e göre eşleştir
            for key in ["g2", "capterra", "crunchbase", "statista", "producthunt",
                        "reddit", "github", "upwork", "tavily"]:
                if key in domain:
                    source_confidence_map[domain] = get_confidence(key)
                    break
            else:
                source_confidence_map[domain] = 0.30

    verified = []
    for claim in claims:
        text = claim["text"]
        matched_sources = [d for d in source_domains if d in text.lower()]
        verified.append({
            **claim,
            "verified":       len(matched_sources) > 0,
            "matched_sources": matched_sources,
            "source_quality": max((source_confidence_map.get(s, 0.30) for s in matched_sources), default=0.0),
        })
    return verified


def compute_hybrid_score(verified_claims: list[dict]) -> dict:
    """
    Hibrit Güven Endeksi: 0.4 × S (kaynak kalitesi) + 0.6 × X (çapraz doğrulama).
    Her iddia ağırlıklı; kritik iddialar daha çok etkiler.
    """
    if not verified_claims:
        return {"s_score": 0.0, "x_score": 0.0, "confidence_index": 0.0, "banner": "red"}

    total_weight = 0.0
    s_weighted = 0.0
    x_weighted = 0.0

    for claim in verified_claims:
        w = CLAIM_WEIGHTS.get(claim["claim_class"], 1.0)
        total_weight += w

        # S: En iyi kaynak kalitesi
        s = claim.get("source_quality", 0.0)

        # X: Çapraz doğrulama (farklı kaynak sayısına göre 0-1)
        n_sources = len(claim.get("matched_sources", []))
        x = min(1.0, n_sources / 3.0)  # 3 kaynakta 1.0

        # Doğrulanamamış iddia → skor 0
        if not claim.get("verified"):
            s = 0.0
            x = 0.0

        s_weighted += s * w
        x_weighted += x * w

    s_score = s_weighted / total_weight
    x_score = x_weighted / total_weight
    confidence_index = round(0.4 * s_score + 0.6 * x_score, 3)

    if confidence_index >= 0.75:
        banner = "green"
    elif confidence_index >= 0.50:
        banner = "yellow"
    else:
        banner = "red"

    return {
        "s_score": round(s_score, 3),
        "x_score": round(x_score, 3),
        "confidence_index": confidence_index,
        "banner": banner,
    }


def mark_unverified(report_json: dict, verified_claims: list[dict]) -> dict:
    """
    Doğrulanamayan iddialara '(Kaynak: doğrulanamadı)' etiketi ekler.
    report_json'u değiştirmez — kopyasını döner.
    """
    unverified_texts = {
        c["text"][:50] for c in verified_claims if not c.get("verified")
    }
    if not unverified_texts:
        return report_json

    raw = json.dumps(report_json, ensure_ascii=False)
    for text_prefix in unverified_texts:
        # Değer içinde geçen ilk 50 karakteri işaretle
        escaped = re.escape(text_prefix)
        raw = re.sub(
            escaped,
            text_prefix + " (Kaynak: doğrulanamadı)",
            raw,
            count=1,
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return report_json


def save_to_audit_trail(report_id: str, verified_claims: list[dict], score: dict) -> None:
    """Supabase audit_trail tablosuna yazar. Hata durumunda sessizce geçer."""
    try:
        from lib.supabase_client import supabase
        rows = [
            {
                "report_id":   report_id,
                "claim_text":  c["text"][:500],
                "claim_class": c["claim_class"],
                "source_url":  c["matched_sources"][0] if c.get("matched_sources") else None,
                "verified":    c.get("verified", False),
                "confidence":  score.get("confidence_index"),
            }
            for c in verified_claims
        ]
        if rows:
            supabase.table("audit_trail").insert(rows).execute()
    except Exception as e:
        print(f"[Auditor] audit_trail yazma hatası (devam ediyor): {e}")


def run_audit(report_json: dict, report_id: str = "unknown") -> dict:
    """
    Ana audit fonksiyonu. Rapor JSON'u alır, zenginleştirilmiş JSON döner.

    Returns: {
        "report_json":        dict,   # doğrulanamadı etiketleriyle
        "confidence_index":   float,
        "s_score":            float,
        "x_score":            float,
        "banner":             str,    # green | yellow | red
        "unverified_count":   int,
        "total_claims":       int,
    }
    """
    sources = report_json.get("sources", [])
    claims = extract_claims(report_json)
    verified = verify_claims(claims, sources)
    score = compute_hybrid_score(verified)
    annotated = mark_unverified(report_json, verified)

    save_to_audit_trail(report_id, verified, score)

    unverified_count = sum(1 for c in verified if not c.get("verified"))
    print(
        f"[Auditor] {len(claims)} iddia | {len(claims)-unverified_count} doğrulandı | "
        f"Güven: {score['confidence_index']:.0%} ({score['banner']})"
    )

    return {
        "report_json":      annotated,
        "confidence_index": score["confidence_index"],
        "s_score":          score["s_score"],
        "x_score":          score["x_score"],
        "banner":           score["banner"],
        "unverified_count": unverified_count,
        "total_claims":     len(claims),
    }
