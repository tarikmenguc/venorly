# Venorly — Chrome Extension

Ziyaret ettiğiniz herhangi bir web sayfasından (rakip SaaS ürünleri, landing pages, ProductHunt listelemeleri) tek tıklamayla Micro-SaaS fırsat analizi yapan Chrome Extension.

## Kurulum (Geliştirici Modu)

1. Chrome'da `chrome://extensions` adresini açın
2. Sağ üst köşede **"Geliştirici modu"**nu aktif edin
3. **"Paketlenmemiş öğe yükle"** butonuna tıklayın
4. Bu `chrome-extension/` klasörünü seçin

## İkon Oluşturma

`icons/` klasörüne aşağıdaki boyutlarda PNG ikonlar ekleyin:
- `icon16.png` — 16×16 px
- `icon48.png` — 48×48 px
- `icon128.png` — 128×128 px

Hızlı oluşturma için:
```bash
# ImageMagick ile basit mor ikon oluştur (isteğe bağlı)
cd chrome-extension/icons
convert -size 128x128 xc:'#7c3aed' -fill white -font DejaVu-Sans-Bold \
  -pointsize 80 -gravity center -annotate 0 '💡' icon128.png
```

## Kullanım

1. FastAPI backend'in çalıştığından emin olun: `uvicorn api:app --reload`
2. Extension ikonuna tıklayın
3. Analiz etmek istediğiniz sayfada **"Rakip Analizi Başlat"**a tıklayın
4. API, sayfanın domain/title/category bilgisini `reverse` modda analiz eder
5. Sonuç popup'ta önizlenir, tam rapor için web uygulamasına yönlendirilirsiniz

## Ayarlar

Extension ikonunun sağ tıklama menüsünden **"Seçenekler"**e gidin:
- **API URL**: FastAPI backend adresi (varsayılan: `http://127.0.0.1:8000`)
- **Uygulama URL**: Next.js frontend adresi (varsayılan: `http://localhost:3000`)

## Teknik Detaylar

- **Manifest V3** uyumlu
- **Content Script** (`content/content.js`): Sayfa meta verilerini çıkarır
- **Service Worker** (`background/service-worker.js`): API çağrıları ve SSE stream
- **Popup** (`popup/`): Sonuç görüntüleme UI'ı
- **Options** (`options/`): Ayarlar sayfası

## API Endpoint

Extension, backend'de `/api/extension/scan` endpoint'ini kullanır:

```json
POST /api/extension/scan
{
  "target_url": "https://example.com",
  "target_domain": "example.com",
  "page_title": "Example Product",
  "page_description": "...",
  "category_guess": "marketing"
}
```
