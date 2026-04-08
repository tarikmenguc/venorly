/**
 * options.js — Chrome Extension Options Page
 */

const apiUrlInput = document.getElementById("apiUrl");
const apiKeyInput = document.getElementById("apiKey");
const appUrlInput = document.getElementById("appUrl");
const saveBtn = document.getElementById("saveBtn");
const successMsg = document.getElementById("successMsg");

// Mevcut ayarları yükle
chrome.storage.sync.get(["apiUrl", "apiKey", "appUrl"], (result) => {
  apiUrlInput.value = result.apiUrl || "http://127.0.0.1:8000";
  apiKeyInput.value = result.apiKey || "";
  appUrlInput.value = result.appUrl || "http://localhost:3000";
});

// Kaydet
saveBtn.addEventListener("click", () => {
  const apiUrl = apiUrlInput.value.trim().replace(/\/$/, ""); // trailing slash kaldır
  const apiKey = apiKeyInput.value.trim();
  const appUrl = appUrlInput.value.trim().replace(/\/$/, "");

  if (!apiUrl) {
    alert("API URL boş olamaz.");
    return;
  }

  chrome.storage.sync.set({ apiUrl, apiKey, appUrl }, () => {
    successMsg.style.display = "block";
    setTimeout(() => {
      successMsg.style.display = "none";
    }, 3000);
  });
});

// Enter ile kaydet
[apiUrlInput, apiKeyInput, appUrlInput].forEach((input) => {
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveBtn.click();
  });
});
