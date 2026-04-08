/**
 * service-worker.js — Background Service Worker (Manifest V3)
 *
 * Görevleri:
 * 1. Popup'tan gelen tarama isteğini alır
 * 2. API'ye POST isteği atar (/api/extension/scan)
 * 3. SSE stream'i okuyarak popup'a chunk chunk sonuç iletir
 */

// API URL ve API Key'i storage'dan al
async function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(["apiUrl", "apiKey"], (result) => {
      resolve({
        apiUrl: result.apiUrl || "http://127.0.0.1:8000",
        apiKey: result.apiKey || "",
      });
    });
  });
}

// Geriye dönük uyumluluk için
async function getApiUrl() {
  const { apiUrl } = await getSettings();
  return apiUrl;
}

// Popup'tan gelen mesajları dinle
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "START_SCAN") {
    // Async işlem — hemen true döndür
    handleScan(message.payload).catch(console.error);
    sendResponse({ status: "started" });
    return true;
  }
  if (message.type === "GET_SETTINGS") {
    getApiUrl().then((url) => sendResponse({ apiUrl: url }));
    return true;
  }
});

/**
 * Tarama başlatır ve popup'a SSE olayları iletir
 */
async function handleScan(payload) {
  const { apiUrl, apiKey } = await getSettings();

  broadcastToPopup({ type: "SCAN_STATUS", status: "connecting", message: "API'ye bağlanılıyor..." });

  const headers = { "Content-Type": "application/json" };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  try {
    const response = await fetch(`${apiUrl}/api/extension/scan`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        target_url: payload.url,
        target_domain: payload.domain,
        page_title: payload.title,
        page_description: payload.description,
        category_guess: payload.category_guess,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      broadcastToPopup({ type: "SCAN_ERROR", message: `API Hatası: ${response.status} — ${errorText}` });
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    broadcastToPopup({ type: "SCAN_STATUS", status: "running", message: "Analiz başladı..." });

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let boundaryIndex;
      while ((boundaryIndex = buffer.indexOf("\n\n")) >= 0) {
        const event = buffer.slice(0, boundaryIndex);
        buffer = buffer.slice(boundaryIndex + 2);

        if (event.startsWith("data: ")) {
          try {
            const dataStr = event.replace("data: ", "").trim();
            if (!dataStr) continue;
            const data = JSON.parse(dataStr);

            if (data.status === "done") {
              broadcastToPopup({ type: "SCAN_DONE", report: data.report, leads: data.leads || [] });
            } else if (data.error) {
              broadcastToPopup({ type: "SCAN_ERROR", message: data.error });
            } else if (data.node) {
              broadcastToPopup({ type: "SCAN_PROGRESS", node: data.node, message: `İşleniyor: ${data.node}...` });

              // Partial report varsa gönder
              if (data.state?.final_report || data.state?.investment_memo) {
                broadcastToPopup({
                  type: "SCAN_PARTIAL",
                  report: data.state.final_report || data.state.investment_memo,
                });
              }
            }
          } catch (e) {
            console.error("[SW] JSON parse error:", e);
          }
        }
      }
    }
  } catch (err) {
    broadcastToPopup({ type: "SCAN_ERROR", message: `Bağlantı hatası: ${err.message}` });
  }
}

/**
 * Tüm extension popup pencerelerine mesaj broadcast eder
 */
function broadcastToPopup(message) {
  chrome.runtime.sendMessage(message).catch(() => {
    // Popup kapalıysa ignore et
  });
}
