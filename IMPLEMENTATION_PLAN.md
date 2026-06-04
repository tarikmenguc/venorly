# Venorly — UI/UX İyileştirme Implementasyon Planı

## Mimari Kararlar

### Temel Kural: Yeni özellik = yeni dosya
Mevcut dosyalar (idea_agent.py, schemas.py) minimal değişiklik alır.
Her yeni özellik kendi modülünde yaşar, bağımsız test edilebilir.

### Değişmeyecek şeyler
- `lib/schemas.py` — sadece Optional yeni alan eklenir, mevcut alanlar dokunulmaz
- `agent/idea_agent.py` — sadece graph wiring + AgentState satırları değişir
- Router'lar — sadece final state kayıt mantığı eklenir

---

## Mevcut Durum (Gerçek)

| Bileşen | Durum |
|---------|-------|
| reddit_signals (scraper + AgentState + prompt) | ✅ Çalışıyor |
| reddit_signals_block (generate_opportunity_node) | ✅ Çalışıyor |
| buyer_leads_node FONKSIYONU | ❌ KAYIP (overwrite) |
| buyer_leads graph bağlantısı | ❌ auditor→END hala |
| pivot_suggestions_node | ❌ Yok |
| actions[] array | ❌ Yok |
| pitch_deck_generator | ❌ Yok |

---

## Implementasyon Planı

### Adım 1 — buyer_leads_node Fix (idea_agent.py)
**Ne:** Fonksiyon kayıp, graph auditor→END'de bitiyor.
**Nasıl:** idea_agent.py'ye fonksiyonu ekle, graph'ı güncelle.
**Bağımlılık:** scrapers/reality_intel.py, agent/buyer_matcher.py (ikisi mevcut)
**Değişen dosyalar:** agent/idea_agent.py (2 yer: fonksiyon + graph)

### Adım 2 — pivot_node.py (Yeni dosya)
**Ne:** Skor < 50/100 ise 3 alternatif pivot önerisi üret.
**Nerede:** agent/pivot_node.py (yeni dosya)
**Nasıl:**
- `pivot_node(state)` → LLM'e "bu fikir neden düşük skoru aldı, 3 pivot öner" sorar
- state["report_json"]["pivot_suggestions"] = [str, str, str]
- buyer_leads'den sonra çalışır (son node)
**schemas.py değişikliği:** FeasibilityReport'a `pivot_suggestions: Optional[list[str]] = None`
**Değişen dosyalar:** agent/pivot_node.py (yeni), lib/schemas.py (+1 alan), agent/idea_agent.py (graph)

### Adım 3 — report_actions.py (Yeni dosya)
**Ne:** Rapor bittikten sonra frontend'in render edeceği CTA listesi.
**Nerede:** lib/report_actions.py (yeni dosya)
**Nasıl:**
- `compute_actions(scan_id, report_json, buyer_leads)` → list[dict]
- Her action: {type, url, label, count?}
- scan_discover.py final event'te bu listeyi ekle
**Değişen dosyalar:** lib/report_actions.py (yeni), routers/scan_discover.py (+5 satır)

### Adım 4 — pitch_deck_generator.py (Yeni dosya)
**Ne:** report_json'dan 10 slide investor-ready PPTX.
**Nerede:** lib/pitch_deck_generator.py (yeni dosya)
**Nasıl:**
- python-pptx ile 10 slide: cover, problem, solution, market, competition,
  business model, traction, team, financials, ask
- Her slide report_json alanlarını kullanır
**Değişen dosyalar:** lib/pitch_deck_generator.py (yeni), api.py (+endpoint), requirements.txt (+python-pptx)

---

## Pipeline Akışı (Hedef)

```
expand_query
→ fetch_market_data
→ fetch_trending_models
→ match_to_market
→ scrape_competitor_reviews  [+ reddit_signal_analysis]
→ cluster_complaints
→ find_store_app
→ scrape_store_reviews
→ cluster_store_problems
→ competition_matrix
→ generate_opportunity       [+ tam_source, ensemble, reddit_signals_block]
→ validate_idea              [+ scorecard→report_json bridge]
→ auditor                    [+ hybrid trust index]
→ buyer_leads_node           [+ Upwork RSS + Reddit desperation]
→ pivot_node                 [+ 3 pivot önerisi if score<50]
→ END
```

---

## Dosya Bağımlılık Grafiği

```
lib/report_actions.py
  ← routers/scan_discover.py

agent/pivot_node.py
  ← lib/llm.py
  ← lib/schemas.py (pivot_suggestions alanı)
  ← agent/idea_agent.py (graph)

lib/pitch_deck_generator.py
  ← python-pptx
  ← api.py (endpoint)
```

Döngüsel bağımlılık yok.
