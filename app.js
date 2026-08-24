const API = window.location.origin || "http://127.0.0.1:5555";
let currentJobId = null;
let pollInterval = null;
let currentJobDir = null;

document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  setupNavigation();
  setupProcessButton();
  setupSaveSettings();
  checkApiKey();
  setupSourceTabs();
  setupFileInput();
  setupCleanup();
  setupEditor();
});

function setupCleanup() {
  const btn = document.getElementById("cleanup-btn");
  if (btn) {
    btn.addEventListener("click", async () => {
      if (!confirm("Tüm indirilen videolar ve oluşturulan klipler silinecek. Emin misiniz?")) return;
      try {
        await fetch(API + "/api/cleanup", { method: "POST" });
        alert("Disk temizlendi!");
        location.reload();
      } catch (e) {
        alert("Temizlik hatası: " + e.message);
      }
    });
  }
}

/* ---- Navigation ---- */
function setupNavigation() {
  document.querySelectorAll(".nav-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-btn[data-view]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const viewId = btn.dataset.view;
      document.querySelectorAll(".view").forEach((v) => {
        v.style.display = "none";
        v.classList.remove("active");
      });
      const view = document.getElementById("view-" + viewId);
      view.style.display = "block";
      view.classList.add("active");
      if (viewId === "history") loadHistory();
    });
  });
}

/* ---- Settings ---- */
async function loadSettings() {
  try {
    const r = await fetch(API + "/api/settings");
    const data = await r.json();
    if (data.api_key) document.getElementById("api-key-input").value = data.api_key;
    if (data.clip_count) document.getElementById("clip-count-input").value = data.clip_count;
    if (data.whisper_model) document.getElementById("whisper-model").value = data.whisper_model;
    if (data.language) document.getElementById("subtitle-language").value = data.language;
  } catch {}
}

function setupSaveSettings() {
  document.getElementById("save-settings-btn").addEventListener("click", async () => {
    const apiKey = document.getElementById("api-key-input").value.trim();
    const clipCount = parseInt(document.getElementById("clip-count-input").value) || 6;
    const whisperModel = document.getElementById("whisper-model").value;
    const language = document.getElementById("subtitle-language").value;
    const msg = document.getElementById("settings-msg");
    try {
      const r = await fetch(API + "/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey, clip_count: clipCount, whisper_model: whisperModel, language: language }),
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      msg.style.display = "block";
      msg.className = "settings-msg success";
      msg.textContent = "Kaydedildi!";
      setTimeout(() => (msg.style.display = "none"), 2500);
      checkApiKey();
    } catch (e) {
      msg.style.display = "block";
      msg.className = "settings-msg";
      msg.style.background = "rgba(226,33,52,0.15)";
      msg.style.color = "#e22134";
      msg.style.border = "1px solid rgba(226,33,52,0.3)";
      msg.textContent = "Kaydetme hatası: " + e.message;
    }
  });
}

async function checkApiKey() {
  try {
    const r = await fetch(API + "/api/settings");
    const data = await r.json();
    const notice = document.getElementById("api-key-notice");
    notice.style.display = data.api_key ? "none" : "flex";
  } catch {}
}

/* ---- Process Video ---- */
function setupSourceTabs() {
  document.querySelectorAll(".source-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".source-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const src = tab.dataset.source;
      document.getElementById("source-url").style.display = src === "url" ? "block" : "none";
      document.getElementById("source-file").style.display = src === "file" ? "block" : "none";
    });
  });
}

function setupFileInput() {
  const fileInput = document.getElementById("file-input");
  const label = document.getElementById("file-label");

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      label.textContent = fileInput.files[0].name + " (yüklemeye hazır)";
    }
  });

  document.getElementById("process-file-btn").addEventListener("click", () => {
    if (!fileInput.files || !fileInput.files[0]) {
      alert("Lütfen önce bir MP4 dosyası seçin.");
      return;
    }
    uploadAndProcess(fileInput.files[0]);
  });
}

async function uploadAndProcess(file) {
  let apiKey = "";
  let clipCount = 6;
  let whisperModel = "base";
  let language = "";
  try {
    const r = await fetch(API + "/api/settings");
    const data = await r.json();
    apiKey = data.api_key || "";
    clipCount = data.clip_count || 6;
    whisperModel = data.whisper_model || "base";
    language = data.language || "";
  } catch {}

  if (!apiKey) {
    alert("Lütfen Ayarlar menüsünden Google Gemini API key girin.");
    return;
  }

  const btn = document.getElementById("process-file-btn");
  btn.disabled = true;
  btn.textContent = "Dosya yükleniyor...";

  // Step 1: upload file to server
  let serverPath;
  try {
    const fd = new FormData();
    fd.append("file", file);
    const up = await fetch(API + "/api/upload", { method: "POST", body: fd });
    if (!up.ok) {
      const errText = await up.text();
      throw new Error("Sunucu hatası: " + errText);
    }
    const upData = await up.json();
    if (upData.error) {
      alert("Yükleme hatası: " + upData.error);
      btn.disabled = false;
      btn.textContent = "Clip Oluştur";
      return;
    }
    serverPath = upData.path;
  } catch (e) {
    alert("Yükleme hatası: " + e.message);
    btn.disabled = false;
    btn.textContent = "Clip Oluştur";
    return;
  }

  // Step 2: process uploaded file
  btn.textContent = "İşleniyor...";
  try {
    const r = await fetch(API + "/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: "", api_key: apiKey, clip_count: clipCount, local_file: serverPath, whisper_model: whisperModel, language: language }),
    });
    const data = await r.json();
    if (data.error) {
      alert("Hata: " + data.error);
      btn.disabled = false;
      btn.textContent = "Clip Oluştur";
      return;
    }
    currentJobId = data.job_id;
    showProgress();
    pollStatus();
  } catch (e) {
    alert("Bağlantı hatası: " + e.message);
    btn.disabled = false;
    btn.textContent = "Clip Oluştur";
  }
}

async function startFileProcessing(filePath) {
  let apiKey = "";
  let clipCount = 6;
  let whisperModel = "base";
  let language = "";
  try {
    const r = await fetch(API + "/api/settings");
    const data = await r.json();
    apiKey = data.api_key || "";
    clipCount = data.clip_count || 6;
    whisperModel = data.whisper_model || "base";
    language = data.language || "";
  } catch {}

  if (!apiKey) {
    alert("Lütfen Ayarlar menüsünden Google Gemini API key girin.");
    return;
  }

  const btn = document.getElementById("process-file-btn");
  btn.disabled = true;
  btn.textContent = "Başlatılıyor...";

  try {
    const r = await fetch(API + "/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: "", api_key: apiKey, clip_count: clipCount, local_file: filePath, whisper_model: whisperModel, language: language }),
    });
    const data = await r.json();
    if (data.error) {
      alert("Hata: " + data.error);
      btn.disabled = false;
      btn.textContent = "Clip Oluştur";
      return;
    }
    currentJobId = data.job_id;
    showProgress();
    pollStatus();
  } catch (e) {
    alert("Bağlantı hatası: " + e.message);
    btn.disabled = false;
    btn.textContent = "Clip Oluştur";
  }
}

function setupProcessButton() {
  const input = document.getElementById("url-input");
  const btn = document.getElementById("process-btn");
  btn.addEventListener("click", startProcessing);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") startProcessing();
  });
}

async function startProcessing() {
  const url = document.getElementById("url-input").value.trim();
  if (!url) return;

  let apiKey = "";
  let clipCount = 6;
  let language = "";
  try {
    const r = await fetch(API + "/api/settings");
    const data = await r.json();
    apiKey = data.api_key || "";
    clipCount = data.clip_count || 6;
    language = data.language || "";
  } catch {}

  if (!apiKey) {
    alert("Lütfen Ayarlar menüsünden Google Gemini API key girin.");
    return;
  }

  const btn = document.getElementById("process-btn");
  btn.disabled = true;
  btn.textContent = "Başlatılıyor...";

  try {
    const r = await fetch(API + "/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, api_key: apiKey, clip_count: clipCount, language: language }),
    });
    const data = await r.json();
    currentJobId = data.job_id;
    showProgress();
    pollStatus();
  } catch (e) {
    alert("Bağlantı hatası: " + e.message);
    btn.disabled = false;
    btn.textContent = "Clip Oluştur";
  }
}

function showProgress() {
  document.getElementById("progress-section").style.display = "block";
  document.getElementById("clips-section").style.display = "none";
}

const STATUS_LABELS = {
  starting: "Başlatılıyor...",
  downloading: "Video indiriliyor...",
  downloaded: "Video indirildi, transkripsiyon başlıyor...",
  transcribing: "Video transkript ediliyor...",
  transcribed: "Transkript hazır, AI analiz ediyor...",
  analyzing: "AI en iyi anları buluyor...",
  moments_found: "Anlar bulundu, clip'ler kesiliyor...",
  cutting_clip: "Clip kesiliyor...",
  done: "Tamamlandı!",
  error: "Hata oluştu!",
};

function pollStatus() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    try {
      const r = await fetch(API + "/api/status/" + currentJobId);
      const data = await r.json();
      updateProgress(data);
      if (data.status === "done" || data.status === "error") {
        clearInterval(pollInterval);
        pollInterval = null;
        document.getElementById("process-btn").disabled = false;
        document.getElementById("process-btn").innerHTML =
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Clip Oluştur';
        const fbtn = document.getElementById("process-file-btn");
        if (fbtn) { fbtn.disabled = false; fbtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Clip Oluştur'; }
        if (data.status === "done") showClips(data);
        else alert("Hata: " + (data.error || "Bilinmeyen hata"));
      }
    } catch {}
  }, 1000);
}

function updateProgress(data) {
  const title = document.getElementById("progress-title");
  const detail = document.getElementById("progress-detail");
  const bar = document.getElementById("progress-bar");
  const pct = document.getElementById("progress-percent");

  title.textContent = STATUS_LABELS[data.status] || data.status;
  if (data.title) detail.textContent = data.title;
  else if (data.clip_index !== undefined)
    detail.textContent = `Clip ${data.clip_index + 1}/${data.total} kesiliyor...`;
  else if (data.segment_count) detail.textContent = `${data.segment_count} segment bulundu`;
  else if (data.count) detail.textContent = `${data.count} clip anı tespit edildi`;
  else detail.textContent = "";

  const progress = data.progress || 0;
  bar.style.width = progress + "%";
  pct.textContent = progress + "%";
}

function showClips(data) {
  document.getElementById("progress-section").style.display = "none";
  document.getElementById("clips-section").style.display = "block";
  document.getElementById("clips-title").textContent = (data.result?.title || "Video") + " — Clip'ler";

  const result = data.result || data;
  const clips = result.clips || [];
  const jobDir = result.job_dir || "";
  currentJobDir = jobDir;

  const grid = document.getElementById("clips-grid");
  grid.innerHTML = "";

  clips.forEach((clip) => {
    const card = document.createElement("div");
    card.className = "clip-card";
    const previewUrl = API + "/api/preview/" + currentJobId + "/" + encodeURIComponent(clip.filename);
    const downloadUrl = API + "/api/download/" + currentJobId + "/" + encodeURIComponent(clip.filename);

    const startMin = Math.floor(clip.start / 60);
    const startSec = Math.floor(clip.start % 60);
    const endMin = Math.floor(clip.end / 60);
    const endSec = Math.floor(clip.end % 60);

    const score = clip.viral_score || 0;
    const scoreColor = score >= 80 ? "#1db954" : score >= 60 ? "#ffc400" : "#e22134";

    card.innerHTML = `
      <video src="${previewUrl}" preload="metadata" muted></video>
      <div class="clip-info">
        <div class="clip-header">
          <div class="clip-hook">${escapeHtml(clip.hook)}</div>
          <div class="clip-score" style="background:${scoreColor};">${score}</div>
        </div>
        <div class="clip-reason">${escapeHtml(clip.reason)} (${startMin}:${String(startSec).padStart(2,"0")} - ${endMin}:${String(endSec).padStart(2,"0")})</div>
        <div class="clip-actions">
          <button onclick="playClip(this)">Oynat</button>
          <button class="btn-edit" onclick='openEditor(${JSON.stringify(clip).replace(/'/g, "&apos;")})'>Düzenle</button>
          <a href="${downloadUrl}" download style="text-decoration:none;"><button>İndir</button></a>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });

  document.getElementById("open-folder-btn").onclick = () => {
    if (window.electronAPI) {
      window.electronAPI.openFolder(jobDir);
    } else {
      alert("Klasör yolu: " + jobDir);
    }
  };
}

function playClip(btn) {
  const card = btn.closest(".clip-card");
  const video = card.querySelector("video");
  video.muted = false;
  video.play();
  btn.textContent = "Duraklat";
  btn.onclick = () => {
    video.pause();
    video.muted = true;
    video.currentTime = 0;
    btn.textContent = "Oynat";
    btn.onclick = () => playClip(btn);
  };
}

/* ---- History ---- */
let jobHistory = [];

function loadHistory() {
  const list = document.getElementById("history-list");
  if (jobHistory.length === 0) {
    list.innerHTML = '<p class="empty-state">Henüz işlenmiş video yok</p>';
    return;
  }
  list.innerHTML = "";
  jobHistory.forEach((j) => {
    const item = document.createElement("div");
    item.className = "history-item";
    item.innerHTML = `
      <div class="history-thumb"><svg width="24" height="24" viewBox="0 0 24 24" fill="var(--text-muted)"><path d="M8 5v14l11-7z"/></svg></div>
      <div class="history-info">
        <div class="history-title">${escapeHtml(j.title || "Video")}</div>
        <div class="history-meta">${j.clipCount || 0} clip oluşturuldu</div>
      </div>
    `;
    list.appendChild(item);
  });
}

/* ---- Util ---- */
function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str || "";
  return d.innerHTML;
}

/* ---- Editor ---- */
let currentEditingClip = null;

function openEditor(clip) {
  currentEditingClip = clip;
  const modal = document.getElementById("editor-modal");
  const video = document.getElementById("editor-video");
  const startInput = document.getElementById("editor-start");
  const endInput = document.getElementById("editor-end");
  const assArea = document.getElementById("editor-ass");
  const title = document.getElementById("editor-title");
  
  title.textContent = `Düzenle: ${clip.hook}`;
  startInput.value = clip.start;
  endInput.value = clip.end;
  
  // Load preview video
  video.src = API + "/api/preview/" + currentJobId + "/" + encodeURIComponent(clip.filename);
  video.load();
  
  // Load ASS content
  fetch(API + "/api/clip_data/" + currentJobId + "/" + encodeURIComponent(clip.filename))
    .then(r => r.json())
    .then(data => {
      assArea.value = data.ass_content || "";
    })
    .catch(() => { assArea.value = "ASS yüklenemedi."; });
    
  modal.style.display = "block";
}

function setupEditor() {
  document.getElementById("close-editor-btn").onclick = () => {
    document.getElementById("editor-modal").style.display = "none";
  };
  
  document.getElementById("save-clip-btn").onclick = async () => {
    if (!currentEditingClip) return;
    const btn = document.getElementById("save-clip-btn");
    btn.disabled = true;
    btn.textContent = "İşleniyor...";
    
    try {
      const r = await fetch(API + "/api/update_clip/" + currentJobId + "/" + encodeURIComponent(currentEditingClip.filename), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start: parseFloat(document.getElementById("editor-start").value),
          end: parseFloat(document.getElementById("editor-end").value),
          ass_content: document.getElementById("editor-ass").value
        })
      });
      const data = await r.json();
      if (data.ok) {
        alert("Klip güncellendi!");
        document.getElementById("editor-modal").style.display = "none";
        
        // Sayfayı yenilemeden sadece düzenlenen videoyu güncelliyoruz
        const cards = document.querySelectorAll(".clip-card");
        cards.forEach(card => {
          const video = card.querySelector("video");
          if (video && video.src.includes(currentEditingClip.filename)) {
            video.src = video.src.split('?')[0] + "?t=" + Date.now();
            video.load();
          }
        });
      } else {
        alert("Hata: " + data.error);
      }
    } catch (e) {
      alert("Kaydetme hatası: " + e.message);
    }
    
    btn.disabled = false;
    btn.textContent = "Değişiklikleri Kaydet ve Yeniden İşle";
  };
}
