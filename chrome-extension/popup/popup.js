/**
 * popup.js — Venorly Chrome Extension Popup
 *
 * Akış:
 * 1. Aktif sekme bilgilerini content script'ten çeker
 * 2. Kullanıcı "Analiz Başlat"a tıklar → service worker'a mesaj gönderir
 * 3. Service worker'dan gelen SSE mesajlarını dinler ve UI'ya yansıtır
 */

// DOM referansları
const pageDomain = document.getElementById("pageDomain");
const pageTitle = document.getElementById("pageTitle");
const pageCategory = document.getElementById("pageCategory");
const scanBtn = document.getElementById("scanBtn");
const statusBar = document.getElementById("statusBar");
const statusText = document.getElementById("statusText");
const progressSteps = document.getElementById("progressSteps");
const errorBox = document.getElementById("errorBox");
const errorText = document.getElementById("errorText");
const resultSection = document.getElementById("resultSection");
const resultPreview = document.getElementById("resultPreview");
const openFullReport = document.getElementById("openFullReport");
const copyReport = document.getElementById("copyReport");
const openApp = document.getElementById("openApp");
const openSettings = document.getElementById("openSettings");

let currentPageInfo = null;
let fullReport = "";
let apiBaseUrl = "http://127.0.0.1:8000";

// ── Init ──────────────────────────────────────────────

async function init() {
  // API URL'yi yükle
  chrome.storage.sync.get(["apiUrl", "appUrl"], (result) => {
    if (result.apiUrl) apiBaseUrl = result.apiUrl;
    const appUrl = result.appUrl || "http://localhost:3000";
    openApp.href = appUrl;
  });

  // Settings butonu
  openSettings.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });

  // Aktif sekme
  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const tab = tabs[0];
    if (!tab?.id) return;

    try {
      // Content script'ten sayfa bilgisi al
      chrome.tabs.sendMessage(tab.id, { type: "GET_PAGE_INFO" }, (response) => {
        if (chrome.runtime.lastError) {
          // Content script inject olmamış (chrome:// sayfaları vb.)
          showPageInfoFallback(tab);
          return;
        }
        if (response) {
          currentPageInfo = response;
          updatePageInfoUI(response);
          scanBtn.disabled = false;
        }
      });
    } catch (err) {
      showPageInfoFallback(tab);
    }
  });

  // Service worker'dan gelen mesajları dinle
  chrome.runtime.onMessage.addListener(handleServiceWorkerMessage);

  // Scan butonu
  scanBtn.addEventListener("click", startScan);

  // Copy butonu
  copyReport.addEventListener("click", () => {
    if (fullReport) {
      navigator.clipboard.writeText(fullReport).then(() => {
        copyReport.textContent = "✅ Kopyalandı";
        setTimeout(() => { copyReport.textContent = "📋 Kopyala"; }, 2000);
      });
    }
  });
}

function showPageInfoFallback(tab) {
  const url = new URL(tab.url || "https://example.com");
  currentPageInfo = {
    url: tab.url || "",
    domain: url.hostname.replace(/^www\./, ""),
    title: tab.title || "",
    description: "",
    category_guess: "general AI tools",
  };
  updatePageInfoUI(currentPageInfo);
  scanBtn.disabled = false;
}

function updatePageInfoUI(info) {
  pageDomain.textContent = info.domain || "–";
  pageTitle.textContent = info.title ? info.title.slice(0, 60) + (info.title.length > 60 ? "…" : "") : "";
  pageCategory.textContent = info.category_guess || "genel";
}

// ── Scan ──────────────────────────────────────────────

function startScan() {
  if (!currentPageInfo) return;

  // UI sıfırla
  hideError();
  hideResult();
  setScanning(true);
  showStatus("Servis worker'a bağlanılıyor...");
  showProgress();

  // Service worker'a gönder
  chrome.runtime.sendMessage(
    { type: "START_SCAN", payload: currentPageInfo },
    (response) => {
      if (chrome.runtime.lastError) {
        showError(`Service worker hatası: ${chrome.runtime.lastError.message}`);
        setScanning(false);
      }
    }
  );
}

// ── Service Worker Mesaj Handler ──────────────────────

function handleServiceWorkerMessage(message) {
  switch (message.type) {
    case "SCAN_STATUS":
      showStatus(message.message);
      break;

    case "SCAN_PROGRESS":
      showStatus(message.message);
      updateProgressStep(message.node);
      break;

    case "SCAN_PARTIAL":
      // Partial raporu güncelle (henüz tamamlanmadı)
      if (message.report) {
        fullReport = message.report;
      }
      break;

    case "SCAN_DONE":
      setScanning(false);
      hideStatus();
      hideProgress();
      if (message.report) {
        fullReport = message.report;
        showResult(message.report);
      }
      break;

    case "SCAN_ERROR":
      setScanning(false);
      hideStatus();
      hideProgress();
      showError(message.message);
      break;
  }
}

// ── Progress Steps ──────────────────────────────────

const STEP_MAP = {
  init_research: "step-init",
  match_to_market: "step-research",
  brainstorm_angles: "step-analysis",
  generate_opportunity: "step-report",
  research_agent: "step-init",
  analyst_agent: "step-analysis",
  gtm_agent: "step-report",
};

function updateProgressStep(nodeName) {
  // Tüm adımları sıfırla
  document.querySelectorAll(".step").forEach((el) => {
    el.classList.remove("active");
  });

  // Aktif adımı bul ve işaretle
  const stepId = STEP_MAP[nodeName];
  if (stepId) {
    const stepEl = document.getElementById(stepId);
    if (stepEl) {
      // Önceki adımları done yap
      let sibling = stepEl.previousElementSibling;
      while (sibling) {
        sibling.classList.add("done");
        sibling.classList.remove("active");
        sibling = sibling.previousElementSibling;
      }
      stepEl.classList.add("active");
    }
  }
}

// ── UI Helpers ────────────────────────────────────────

function setScanning(scanning) {
  scanBtn.disabled = scanning;
  if (scanning) {
    scanBtn.classList.add("loading");
    scanBtn.querySelector(".scan-btn-text").textContent = "Analiz Yapılıyor...";
  } else {
    scanBtn.classList.remove("loading");
    scanBtn.querySelector(".scan-btn-text").textContent = "Rakip Analizi Başlat";
  }
}

function showStatus(msg) {
  statusBar.style.display = "flex";
  statusText.textContent = msg;
}

function hideStatus() {
  statusBar.style.display = "none";
}

function showProgress() {
  progressSteps.style.display = "flex";
  // İlk adımı aktif yap
  document.getElementById("step-init").classList.add("active");
}

function hideProgress() {
  progressSteps.style.display = "none";
}

function showError(msg) {
  errorBox.style.display = "flex";
  errorText.textContent = msg;
}

function hideError() {
  errorBox.style.display = "none";
}

function showResult(report) {
  resultSection.style.display = "flex";
  // İlk 300 karakter preview
  const preview = report.replace(/#+\s/g, "").replace(/\*\*/g, "").slice(0, 300) + "…";
  resultPreview.textContent = preview;

  // Full report linkini ayarla
  chrome.storage.sync.get(["appUrl"], (result) => {
    const appUrl = result.appUrl || "http://localhost:3000";
    openFullReport.href = appUrl;
  });
}

function hideResult() {
  resultSection.style.display = "none";
  fullReport = "";
}

// ── Start ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", init);
