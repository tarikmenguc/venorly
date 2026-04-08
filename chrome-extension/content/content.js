/**
 * content.js — Sayfa bilgisi çıkaran content script
 * Manifest V3 uyumlu
 *
 * Görevleri:
 * 1. Mevcut sayfanın domain, title, description ve meta verilerini toplar
 * 2. Background service worker'a mesaj gönderir (veya popup'tan gelen mesajı yanıtlar)
 */

// Popup veya background'dan gelen mesajları dinle
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_PAGE_INFO") {
    const pageInfo = extractPageInfo();
    sendResponse(pageInfo);
  }
  return true; // async response için
});

/**
 * Sayfadan anahtar bilgileri çıkarır
 */
function extractPageInfo() {
  const url = window.location.href;
  const hostname = window.location.hostname.replace(/^www\./, "");
  const title = document.title || "";

  // Meta description
  const metaDesc =
    document.querySelector('meta[name="description"]')?.getAttribute("content") ||
    document.querySelector('meta[property="og:description"]')?.getAttribute("content") ||
    "";

  // OG tags
  const ogTitle =
    document.querySelector('meta[property="og:title"]')?.getAttribute("content") || title;
  const ogSiteName =
    document.querySelector('meta[property="og:site_name"]')?.getAttribute("content") || "";

  // Pricing sayfası tespiti
  const isPricingPage = /pricing|fiyat|plan|subscribe|checkout/i.test(url + title);

  // SaaS/product keywords in page text (ilk 2000 karakter)
  const bodyText = document.body?.innerText?.slice(0, 2000) || "";

  // Kategori tahmini (basit heuristic)
  const categoryGuess = guessCategory(hostname + " " + title + " " + metaDesc + " " + bodyText);

  return {
    url,
    domain: hostname,
    title: ogTitle || title,
    description: metaDesc,
    site_name: ogSiteName,
    is_pricing_page: isPricingPage,
    category_guess: categoryGuess,
    timestamp: Date.now(),
  };
}

/**
 * Basit heuristic kategori tahmini
 */
function guessCategory(text) {
  const lower = text.toLowerCase();
  if (/video.*generat|text.*to.*video|ai.*video/.test(lower)) return "video generation";
  if (/image.*generat|text.*to.*image|ai.*art/.test(lower)) return "image generation";
  if (/text.*to.*speech|voice.*generat|tts/.test(lower)) return "text to speech";
  if (/speech.*to.*text|transcri|whisper/.test(lower)) return "speech to text";
  if (/code.*generat|ai.*cod|copilot/.test(lower)) return "code generation";
  if (/music.*generat|ai.*music|suno|udio/.test(lower)) return "music generation";
  if (/document|pdf.*ai|ai.*pdf/.test(lower)) return "document AI";
  if (/chatbot|conversational ai|llm/.test(lower)) return "chatbot";
  if (/automat|workflow|zapier|n8n|make\.com/.test(lower)) return "automation";
  if (/marketing|content.*generat|seo.*tool/.test(lower)) return "marketing";
  if (/analytics|data.*analys|business.*intel/.test(lower)) return "analytics";
  if (/developer|devtool|api.*platform/.test(lower)) return "developer tools";
  if (/audio.*edit|podcast|audio.*ai/.test(lower)) return "audio processing";
  if (/computer.*vision|image.*recognit|visual.*detect/.test(lower)) return "computer vision";
  return "general AI tools";
}
