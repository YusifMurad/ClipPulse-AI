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
      if (!confirm("All downloaded videos and generated clips will be deleted. Continue?")) return;
      try {
        await fetch(API + "/api/cleanup", { method: "POST" });
        alert("Disk cleaned successfully!");
        location.reload();
      } catch (e) {
        alert("Cleanup error: " + e.message);
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
    // API key is never sent back — show masked version in placeholder
    if (data.has_api_key) {
      document.getElementById("api-key-input").placeholder = data.api_key_masked || "••••••••";
    }
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
      msg.textContent = "Settings saved!";
      setTimeout(() => (msg.style.display = "none"), 2500);
      checkApiKey();
    } catch (e) {
      msg.style.display = "block";
      msg.className = "settings-msg";
      msg.style.background = "rgba(239,68,68,0.12)";
      msg.style.color = "#ef4444";
      msg.style.border = "1px solid rgba(239,68,68,0.2)";
      msg.textContent = "Error: " + e.message;
    }
  });
}

async function checkApiKey() {
  try {
    const r = await fetch(API + "/api/settings");
    const data = await r.json();
    const notice = document.getElementById("api-key-notice");
    notice.style.display = data.has_api_key ? "none" : "flex";
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
  const drop = document.getElementById("file-drop");
  const title = drop.querySelector(".file-drop-title");
  const hint = drop.querySelector(".file-drop-hint");

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) {
      title.textContent = fileInput.files[0].name;
      hint.textContent = "Ready to process";
    }
  });

  // Drag and drop
  ["dragover", "dragenter"].forEach(e => {
    drop.addEventListener(e, (ev) => {
      ev.preventDefault();
      drop.style.borderColor = "var(--accent)";
      drop.style.background = "var(--accent-glow)";
    });
  });
  ["dragleave", "drop"].forEach(e => {
    drop.addEventListener(e, (ev) => {
      ev.preventDefault();
      drop.style.borderColor = "";
      drop.style.background = "";
    });
  });
  drop.addEventListener("drop", (ev) => {
    const files = ev.dataTransfer.files;
    if (files.length && files[0].type.startsWith("video/")) {
      fileInput.files = files;
      title.textContent = files[0].name;
      hint.textContent = "Ready to process";
    }
  });

  document.getElementById("process-file-btn").addEventListener("click", () => {
    if (!fileInput.files || !fileInput.files[0]) {
      alert("Please select a video file first.");
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
    alert("Please add your Google Gemini API key in Settings.");
    return;
  }

  const btn = document.getElementById("process-file-btn");
  btn.disabled = true;
  btn.textContent = "Uploading...";

  // Step 1: upload file to server
  let serverPath;
  try {
    const fd = new FormData();
    fd.append("file", file);
    const up = await fetch(API + "/api/upload", { method: "POST", body: fd });
    if (!up.ok) {
      const errText = await up.text();
      throw new Error("Server error: " + errText);
    }
    const upData = await up.json();
    if (upData.error) {
      alert("Upload error: " + upData.error);
      btn.disabled = false;
      btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Generate Clips';
      return;
    }
    serverPath = upData.path;
  } catch (e) {
    alert("Upload error: " + e.message);
    btn.disabled = false;
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Generate Clips';
    return;
  }

  // Step 2: process uploaded file
  btn.textContent = "Processing...";
  try {
    const r = await fetch(API + "/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: "", api_key: apiKey, clip_count: clipCount, local_file: serverPath, whisper_model: whisperModel, language: language }),
    });
    const data = await r.json();
    if (data.error) {
      alert("Error: " + data.error);
      btn.disabled = false;
      btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Generate Clips';
      return;
    }
    currentJobId = data.job_id;
    showProgress();
    pollStatus();
  } catch (e) {
    alert("Connection error: " + e.message);
    btn.disabled = false;
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Generate Clips';
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
    alert("Please add your Google Gemini API key in Settings.");
    return;
  }

  const btn = document.getElementById("process-btn");
  btn.disabled = true;
  btn.textContent = "Starting...";

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
    alert("Connection error: " + e.message);
    btn.disabled = false;
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Generate Clips';
  }
}

function showProgress() {
  document.getElementById("progress-section").style.display = "block";
  document.getElementById("clips-section").style.display = "none";
}

const STATUS_LABELS = {
  starting: "Initializing...",
  downloading: "Downloading video...",
  downloaded: "Download complete, starting transcription...",
  transcribing: "Transcribing audio...",
  transcribed: "Transcription ready, AI analyzing...",
  analyzing: "AI finding best moments...",
  moments_found: "Moments found, cutting clips...",
  cutting_clip: "Cutting clip...",
  done: "Done!",
  error: "An error occurred",
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
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Generate Clips';
        const fbtn = document.getElementById("process-file-btn");
        if (fbtn) { fbtn.disabled = false; fbtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Generate Clips'; }
        if (data.status === "done") showClips(data);
        else alert("Error: " + (data.error || "Unknown error"));
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
    detail.textContent = `Cutting clip ${data.clip_index + 1}/${data.total}...`;
  else if (data.segment_count) detail.textContent = `${data.segment_count} segments found`;
  else if (data.count) detail.textContent = `${data.count} clip moments detected`;
  else detail.textContent = "";

  const progress = data.progress || 0;
  bar.style.width = progress + "%";
  pct.textContent = progress + "%";
}

function showClips(data) {
  document.getElementById("progress-section").style.display = "none";
  document.getElementById("clips-section").style.display = "block";
  document.getElementById("clips-title").textContent = (data.result?.title || "Video") + " — Clips";

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
    const scoreColor = score >= 80 ? "#1db954" : score >= 60 ? "#fbbf24" : "#ef4444";

    card.innerHTML = `
      <video src="${previewUrl}" preload="metadata" muted loop></video>
      <div class="clip-info">
        <div class="clip-header">
          <div class="clip-hook">${escapeHtml(clip.hook)}</div>
          <div class="clip-score" style="background:${scoreColor};">${score}</div>
        </div>
        <div class="clip-reason">${escapeHtml(clip.reason)} (${startMin}:${String(startSec).padStart(2,"0")} — ${endMin}:${String(endSec).padStart(2,"0")})</div>
        <div class="clip-actions">
          <button onclick="playClip(this)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            Play
          </button>
          <button class="btn-edit" onclick='openEditor(${JSON.stringify(clip).replace(/'/g, "&apos;")})'>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            Edit
          </button>
          <a href="${downloadUrl}" download style="text-decoration:none;">
            <button>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download
            </button>
          </a>
        </div>
      </div>
    `;

    // Hover play preview
    const video = card.querySelector("video");
    card.addEventListener("mouseenter", () => { video.play().catch(() => {}); });
    card.addEventListener("mouseleave", () => { video.pause(); video.currentTime = 0; video.muted = true; });

    grid.appendChild(card);
  });

  document.getElementById("open-folder-btn").onclick = () => {
    if (window.electronAPI) {
      window.electronAPI.openFolder(jobDir);
    } else {
      alert("Folder: " + jobDir);
    }
  };
}

function playClip(btn) {
  const card = btn.closest(".clip-card");
  const video = card.querySelector("video");
  video.muted = false;
  video.loop = false;
  video.play();
  btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Pause';
  btn.onclick = () => {
    video.pause();
    video.muted = true;
    video.currentTime = 0;
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Play';
    btn.onclick = () => playClip(btn);
  };
}

/* ---- History ---- */
let jobHistory = [];

function loadHistory() {
  const list = document.getElementById("history-list");
  if (jobHistory.length === 0) {
    list.innerHTML = `
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <p>No processed videos yet</p>
      </div>`;
    return;
  }
  list.innerHTML = "";
  jobHistory.forEach((j) => {
    const item = document.createElement("div");
    item.className = "history-item";
    item.innerHTML = `
      <div class="history-thumb"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="2"><path d="M8 5v14l11-7z"/></svg></div>
      <div class="history-info">
        <div class="history-title">${escapeHtml(j.title || "Video")}</div>
        <div class="history-meta">${j.clipCount || 0} clips generated</div>
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
  
  title.textContent = `Edit: ${clip.hook}`;
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
    .catch(() => { assArea.value = "Could not load subtitles."; });
    
  modal.style.display = "block";
}

function setupEditor() {
  document.getElementById("close-editor-btn").onclick = () => {
    document.getElementById("editor-modal").style.display = "none";
  };

  // Close on overlay click
  document.querySelector(".modal-overlay")?.addEventListener("click", () => {
    document.getElementById("editor-modal").style.display = "none";
  });
  
  document.getElementById("save-clip-btn").onclick = async () => {
    if (!currentEditingClip) return;
    const btn = document.getElementById("save-clip-btn");
    btn.disabled = true;
    btn.textContent = "Re-rendering...";
    
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
        document.getElementById("editor-modal").style.display = "none";
        
        // Update the video in the grid without reloading
        const cards = document.querySelectorAll(".clip-card");
        cards.forEach(card => {
          const video = card.querySelector("video");
          if (video && video.src.includes(currentEditingClip.filename)) {
            video.src = video.src.split('?')[0] + "?t=" + Date.now();
            video.load();
          }
        });
      } else {
        alert("Error: " + data.error);
      }
    } catch (e) {
      alert("Save error: " + e.message);
    }
    
    btn.disabled = false;
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg> Save & Re-render';
  };
}
