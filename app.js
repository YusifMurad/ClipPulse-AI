const API = (window.electronAPI && window.electronAPI.backendUrl) || window.location.origin || "http://127.0.0.1:5555";
let currentJobId = null;
let pollInterval = null;
let currentJobDir = null;
let currentLang = "en";

function tr(key) {
  if (!window.I18N) return null;
  const d = window.I18N[currentLang];
  if (d && Object.prototype.hasOwnProperty.call(d, key)) return d[key];
  const e = window.I18N.en;
  if (e && Object.prototype.hasOwnProperty.call(e, key)) return e[key];
  return null;
}

function t(key, params) {
  let s = tr(key);
  if (s == null) s = key;
  if (params) {
    for (const k in params) s = s.split("{" + k + "}").join(params[k]);
  }
  return s;
}

function applyEffectOptionLabels() {
  const map = { none: "eff_none", "zoom-in": "eff_zoomin", "zoom-out": "eff_zoomout", "ken-burns": "eff_kenburns", "pop": "eff_pop" };
  document.querySelectorAll("#st-effect option").forEach((o) => {
    const k = map[o.value];
    if (k) o.textContent = t(k);
  });
}

function applyLang(lang) {
  currentLang = (window.I18N && window.I18N[lang]) ? lang : "en";
  document.documentElement.lang = currentLang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const k = el.getAttribute("data-i18n");
    if (!k) return;
    const v = tr(k);
    if (v != null) el.textContent = v;
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    const k = el.getAttribute("data-i18n-ph");
    if (!k) return;
    const v = tr(k);
    if (v != null) el.setAttribute("placeholder", v);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    const k = el.getAttribute("data-i18n-title");
    if (!k) return;
    const v = tr(k);
    if (v != null) el.setAttribute("title", v);
  });
  document.querySelectorAll("[data-i18n-summary]").forEach((el) => {
    const k = el.getAttribute("data-i18n-summary");
    if (!k) return;
    const v = tr(k);
    if (v != null) el.textContent = v;
  });
  applyEffectOptionLabels();
}

 document.addEventListener("DOMContentLoaded", () => {
  applyLang("en");
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
      if (!confirm(t("cleanup_confirm"))) return;
      try {
        await fetch(API + "/api/cleanup", { method: "POST" });
        alert(t("cleanup_done"));
        location.reload();
      } catch (e) {
        alert(t("cleanup_error") + e.message);
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
    // Show masked key so user knows it's saved (actual key never leaves server)
    if (data.has_api_key) {
      const input = document.getElementById("api-key-input");
      input.value = data.api_key_masked || "";
      input.dataset.saved = "true";
    }
    if (data.clip_count) document.getElementById("clip-count-input").value = data.clip_count;
    if (data.whisper_model) document.getElementById("whisper-model").value = data.whisper_model;
    if (data.language) document.getElementById("subtitle-language").value = data.language;
    applyLang(data.language || "en");
  } catch {
    applyLang("en");
  }
}

function setupSaveSettings() {
  document.getElementById("save-settings-btn").addEventListener("click", async () => {
    const apiKeyInput = document.getElementById("api-key-input").value.trim();
    const clipCount = parseInt(document.getElementById("clip-count-input").value) || 6;
    const whisperModel = document.getElementById("whisper-model").value;
    const language = document.getElementById("subtitle-language").value;
    const msg = document.getElementById("settings-msg");

    // If input still shows masked text, don't overwrite the real key
    const apiKey = (apiKeyInput && !apiKeyInput.includes("...")) ? apiKeyInput : "";

    try {
      const body = { clip_count: clipCount, whisper_model: whisperModel, language: language };
      if (apiKey) body.api_key = apiKey;

      const r = await fetch(API + "/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      msg.style.display = "block";
      msg.className = "settings-msg success";
      msg.textContent = t("settings_saved");
      setTimeout(() => (msg.style.display = "none"), 2500);
      checkApiKey();
      applyLang(language || "en");
      loadSettings();
    } catch (e) {
      msg.style.display = "block";
      msg.className = "settings-msg";
      msg.style.background = "rgba(239,68,68,0.12)";
      msg.style.color = "#ef4444";
      msg.style.border = "1px solid rgba(239,68,68,0.2)";
      msg.textContent = t("settings_error") + e.message;
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
      hint.textContent = t("ready_process");
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
      hint.textContent = t("ready_process");
    }
  });

  document.getElementById("process-file-btn").addEventListener("click", () => {
    if (!fileInput.files || !fileInput.files[0]) {
      alert(t("alert_select_file"));
      return;
    }
    uploadAndProcess(fileInput.files[0]);
  });
}

async function uploadAndProcess(file) {
  let clipCount = 6;
  let whisperModel = "base";
  let language = "";
  try {
    const r = await fetch(API + "/api/settings");
    const data = await r.json();
    if (!data.has_api_key) {
      alert(t("alert_add_key"));
      return;
    }
    clipCount = data.clip_count || 6;
    whisperModel = data.whisper_model || "base";
    language = data.language || "";
  } catch {
    alert(t("alert_connect"));
    return;
  }

  const btn = document.getElementById("process-file-btn");
  btn.disabled = true;
  btn.textContent = t("btn_uploading");

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
      btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ' + t("btn_generate");
      return;
    }
    serverPath = upData.path;
  } catch (e) {
    alert("Upload error: " + e.message);
    btn.disabled = false;
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ' + t("btn_generate");
    return;
  }

  // Step 2: process uploaded file
  btn.textContent = t("btn_processing");
  try {
    const r = await fetch(API + "/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: "", clip_count: clipCount, local_file: serverPath, whisper_model: whisperModel, language: language }),
    });
    const data = await r.json();
    if (data.error) {
      alert("Error: " + data.error);
      btn.disabled = false;
      btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ' + t("btn_generate");
      return;
    }
    currentJobId = data.job_id;
    showProgress();
    pollStatus();
  } catch (e) {
    alert(t("alert_connect") + " " + e.message);
    btn.disabled = false;
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ' + t("btn_generate");
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

  let clipCount = 6;
  let language = "";
  try {
    const r = await fetch(API + "/api/settings");
    const data = await r.json();
    if (!data.has_api_key) {
      alert(t("alert_add_key"));
      return;
    }
    clipCount = data.clip_count || 6;
    language = data.language || "";
  } catch {
    alert(t("alert_connect"));
    return;
  }

  const btn = document.getElementById("process-btn");
  btn.disabled = true;
  btn.textContent = t("btn_starting");

  try {
    const r = await fetch(API + "/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, clip_count: clipCount, language: language }),
    });
    const data = await r.json();
    currentJobId = data.job_id;
    showProgress();
    pollStatus();
  } catch (e) {
    alert(t("alert_connect") + " " + e.message);
    btn.disabled = false;
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ' + t("btn_generate");
  }
}

function showProgress() {
  document.getElementById("progress-section").style.display = "block";
  document.getElementById("clips-section").style.display = "none";
}

const STATUS_KEYS = {
  starting: "status_starting",
  downloading: "status_downloading",
  downloaded: "status_downloaded",
  transcribing: "status_transcribing",
  transcribed: "status_transcribed",
  analyzing: "status_analyzing",
  moments_found: "status_moments_found",
  cutting_clip: "status_cutting_clip",
  done: "progress_done",
  error: "progress_error",
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
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ' + t("btn_generate");
        const fbtn = document.getElementById("process-file-btn");
        if (fbtn) { fbtn.disabled = false; fbtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ' + t("btn_generate"); }
        if (data.status === "done") showClips(data);
        else alert(t("progress_error") + " " + (data.error || t("alert_unknown")));
      }
    } catch {}
  }, 1000);
}

function updateProgress(data) {
  const title = document.getElementById("progress-title");
  const detail = document.getElementById("progress-detail");
  const bar = document.getElementById("progress-bar");
  const pct = document.getElementById("progress-percent");

  title.textContent = t(STATUS_KEYS[data.status] || data.status);
  if (data.title) detail.textContent = data.title;
  else if (data.clip_index !== undefined)
    detail.textContent = t("progress_cutting", { cur: data.clip_index + 1, total: data.total });
  else if (data.segment_count) detail.textContent = t("progress_segments", { n: data.segment_count });
  else if (data.count) detail.textContent = t("progress_moments", { n: data.count });
  else detail.textContent = "";

  const progress = data.progress || 0;
  bar.style.width = progress + "%";
  pct.textContent = progress + "%";
}

function showClips(data) {
  document.getElementById("progress-section").style.display = "none";
  document.getElementById("clips-section").style.display = "block";
  document.getElementById("clips-title").textContent = (data.result?.title || t("clips_title")) + " — " + t("clips_title");

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
    const thumbUrl = API + "/api/thumbnail/" + currentJobId + "/" + encodeURIComponent(clip.filename);
    const downloadUrl = API + "/api/download/" + currentJobId + "/" + encodeURIComponent(clip.filename);

    const startMin = Math.floor(clip.start / 60);
    const startSec = Math.floor(clip.start % 60);
    const endMin = Math.floor(clip.end / 60);
    const endSec = Math.floor(clip.end % 60);

    const score = clip.viral_score || 0;
    const scoreColor = score >= 80 ? "#1db954" : score >= 60 ? "#ffc400" : "#ef4444";

    card.innerHTML = `
      <div class="clip-preview-container">
        <video src="${previewUrl}" preload="metadata" muted poster="${thumbUrl}"></video>
        <div class="play-overlay"><svg width="48" height="48" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg></div>
      </div>
      <div class="clip-info">

        <div class="clip-header">
          <div class="clip-hook">${escapeHtml(clip.hook)}</div>
          <div class="clip-score" style="background:${scoreColor};">${score}</div>
        </div>
        <div class="clip-reason">${escapeHtml(clip.reason)} (${startMin}:${String(startSec).padStart(2,"0")} — ${endMin}:${String(endSec).padStart(2,"0")})</div>
        <div class="clip-actions">
          <button onclick="playClip(this)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            ${t("card_play")}
          </button>
          <button class="btn-edit" onclick='openEditor(${JSON.stringify(clip).replace(/'/g, "&apos;")})'>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            ${t("card_edit")}
          </button>
          <a href="${downloadUrl}" download style="text-decoration:none;">
            <button>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              ${t("card_download")}
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
  btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> ' + t("card_pause");
  btn.onclick = () => {
    video.pause();
    video.muted = true;
    video.currentTime = 0;
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ' + t("card_play");
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
const FONTS = [
  "Arial", "DejaVu Sans", "Liberation Sans", "Noto Sans", "Roboto", "Open Sans",
  "Montserrat", "Carlito", "Verdana", "Tahoma", "Trebuchet MS", "Georgia",
  "Times New Roman", "Courier New", "Comic Sans MS", "Impact"
];
const DEFAULT_STYLE = {
  primary: "#ffffff", secondary: "#ffff00", outline: "#000000", back: "#ec4899",
  fontsize: 74, bold: true, outline_w: 6, shadow: 4, marginv: 100,
  fontname: "Arial",
  gradient: false, gradient_a: "#ec4899", gradient_b: "#a855f7"
};

// Timeline state (deleted ranges + current selection, both clip-relative seconds)
let tl = { dur: 0, cuts: [], sel: null };

// Zoom/pan state (draggable focus + animation length)
let zoomFx = 0.5, zoomFy = 0.5, zoomLength = 1.0;

function openEditor(clip) {
  currentEditingClip = clip;
  const modal = document.getElementById("editor-modal");
  const video = document.getElementById("editor-video");
  const title = document.getElementById("editor-title");

  // Reset timeline state so no stale deletions carry over
  tl = { dur: 0, cuts: [], sel: null };

  title.textContent = clip.hook;

  video.src = API + "/api/preview/" + currentJobId + "/" + encodeURIComponent(clip.filename);
  video.load();

  fetch(API + "/api/clip_data/" + currentJobId + "/" + encodeURIComponent(clip.filename))
    .then(r => r.json())
    .then(data => {
      renderCues(data.cues && data.cues.length ? data.cues : []);
      document.getElementById("editor-ass").value = data.ass_content || "";
      const s = Object.assign({}, DEFAULT_STYLE, data.current_style || {});
      applyStyleToInputs(s);
      const fx = document.getElementById("st-effect");
      if (fx) fx.value = data.effect || "none";
      // Zoom/pan state
      const f = data.focus || [0.5, 0.5];
      zoomFx = Math.max(0, Math.min(1, +f[0] || 0.5));
      zoomFy = Math.max(0, Math.min(1, +f[1] || 0.5));
      zoomLength = +data.length || 1.0;
      const lnEl = document.getElementById("st-length");
      if (lnEl) { lnEl.value = zoomLength; document.getElementById("rv-length").textContent = zoomLength.toFixed(2); }
      syncZoomUI();
      video.addEventListener("loadedmetadata", () => {
        initTimeline(video.duration);
        syncZoomUI();
      }, { once: true });
      updatePreview();
    })
    .catch(() => {
      renderCues([]);
      applyStyleToInputs(DEFAULT_STYLE);
      updatePreview();
    });

  modal.style.display = "flex";
}

function syncZoomUI() {
  const effect = document.getElementById("st-effect")?.value || "none";
  const controls = document.getElementById("zoom-controls");
  const box = document.getElementById("zoom-focus");
  const show = effect !== "none";
  if (controls) controls.style.display = show ? "block" : "none";
  if (!box) return;
  box.style.display = show ? "flex" : "none";
  if (!show) {
    const v = document.getElementById("editor-video");
    if (v) v.style.transform = "";
    return;
  }
  const sizePct = 100 / zoomStrength;
  box.style.width = sizePct + "%";
  box.style.height = sizePct + "%";
  box.style.left = (zoomFx * 100) + "%";
  box.style.top = (zoomFy * 100) + "%";
  box.style.transform = "translate(-50%, -50%)";
  applyZoomPreview();
}

function applyZoomPreview() {
  const v = document.getElementById("editor-video");
  if (!v) return;
  const effect = document.getElementById("st-effect")?.value || "none";
  if (effect === "none" || !v.duration) { v.style.transform = ""; return; }
  const dur = v.duration;
  const t = v.currentTime || 0;
  const span = Math.max(0.001, zoomLength * dur);
  const p = Math.min(1, t / span);
  let z;
  if (effect === "zoom-out") z = zoomStrength - (zoomStrength - 1) * p;
  else if (effect === "pop") z = 1 + (zoomStrength - 1) * Math.sin(Math.PI * p);
  else z = 1 + (zoomStrength - 1) * p; // zoom-in / ken-burns
  v.style.transformOrigin = (zoomFx * 100) + "% " + (zoomFy * 100) + "%";
  v.style.transform = `translate(${(0.5 - zoomFx) * 100}%, ${(0.5 - zoomFy) * 100}%) scale(${z})`;
}

function setupZoomHandlers() {
  const box = document.getElementById("zoom-focus");
  const frame = box ? box.parentElement : null;
  if (!box || !frame) return;
  let dragging = false;
  box.addEventListener("pointerdown", (e) => {
    dragging = true;
    try { box.setPointerCapture(e.pointerId); } catch (_) {}
    e.preventDefault();
  });
  box.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const r = frame.getBoundingClientRect();
    zoomFx = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
    zoomFy = Math.max(0, Math.min(1, (e.clientY - r.top) / r.height));
    box.style.left = (zoomFx * 100) + "%";
    box.style.top = (zoomFy * 100) + "%";
    applyZoomPreview();
  });
  const stop = (e) => { dragging = false; try { box.releasePointerCapture(e.pointerId); } catch (_) {} };
  box.addEventListener("pointerup", stop);
  box.addEventListener("pointercancel", stop);

  document.getElementById("st-length")?.addEventListener("input", (e) => {
    zoomLength = +e.target.value;
    document.getElementById("rv-length").textContent = zoomLength.toFixed(2);
    applyZoomPreview();
  });
  document.getElementById("st-effect")?.addEventListener("change", syncZoomUI);
  document.getElementById("editor-video")?.addEventListener("timeupdate", applyZoomPreview);
}

function renderCues(cues) {
  const list = document.getElementById("cue-list");
  list.innerHTML = "";
  cues.forEach((c, i) => list.appendChild(makeCueRow(c, i)));
  if (!cues.length) list.appendChild(makeCueRow({ start: 0, end: 1, text: "" }, 0));
}

function makeCueRow(c, idx) {
  const row = document.createElement("div");
  row.className = "cue-row";
  row.innerHTML = `
    <input type="number" step="0.1" min="0" class="cue-start" value="${(+c.start).toFixed(2)}" title="${t("cue_start_title")}">
    <span class="cue-dash">–</span>
    <input type="number" step="0.1" min="0" class="cue-end" value="${(+c.end).toFixed(2)}" title="${t("cue_end_title")}">
    <input type="text" class="cue-text" value="${escapeAttr(c.text || "")}" placeholder="${t("preview_placeholder")}">
    <button type="button" class="cue-del" title="${t("cue_del_title")}">✕</button>
  `;
  row.querySelector(".cue-del").addEventListener("click", () => {
    row.remove();
    updatePreview();
  });
  row.querySelectorAll("input").forEach(inp => inp.addEventListener("input", updatePreview));
  return row;
}

function escapeAttr(s) {
  return (s || "").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function collectCues() {
  const cues = [];
  document.querySelectorAll("#cue-list .cue-row").forEach(row => {
    const start = parseFloat(row.querySelector(".cue-start").value) || 0;
    const end = parseFloat(row.querySelector(".cue-end").value) || 0;
    const text = row.querySelector(".cue-text").value.trim();
    if (text) cues.push({ start: +start.toFixed(3), end: +end.toFixed(3), text });
  });
  return cues;
}

function initTimeline(dur) {
  tl.dur = dur || 0;
  tl.cuts = [];
  tl.sel = null;
  updateTimelineUI();
}

function tlPos(t) {
  if (!tl.dur) return "0%";
  return ((t / tl.dur) * 100).toFixed(2) + "%";
}

function tlClamp(t) {
  return Math.max(0, Math.min(tl.dur, t));
}

function fmtT(s) {
  s = Math.max(0, s);
  const m = Math.floor(s / 60);
  const sec = (s % 60).toFixed(1);
  return `${m}:${sec.padStart(4, "0")}`;
}

function updateTimelineUI() {
  const layer = document.getElementById("tl-segs");
  layer.innerHTML = "";
  // Already-deleted ranges (red hatched); click to undo
  tl.cuts.forEach((c, i) => {
    const d = document.createElement("div");
    d.className = "tl-cut";
    d.style.left = tlPos(c[0]);
    d.style.width = `calc(${tlPos(c[1])} - ${tlPos(c[0])})`;
    d.title = t("tl_cut_title");
    d.dataset.cut = i;
    layer.appendChild(d);
  });
  // Current selection being chosen (translucent red)
  if (tl.sel && tl.sel[1] - tl.sel[0] > 0.02) {
    const d = document.createElement("div");
    d.className = "tl-sel";
    d.style.left = tlPos(tl.sel[0]);
    d.style.width = `calc(${tlPos(tl.sel[1])} - ${tlPos(tl.sel[0])})`;
    layer.appendChild(d);
  }
  const v = document.getElementById("editor-video");
  if (v && v.duration) document.getElementById("tl-play").style.left = tlPos(v.currentTime);
  const totalCut = tl.cuts.reduce((s, c) => s + (c[1] - c[0]), 0);
  document.getElementById("tl-times").textContent =
    t("tl_times", { dur: fmtT(tl.dur), n: tl.cuts.length, cut: fmtT(totalCut) });
}

// Add the current selection to the deleted ranges list
function tlDeleteSelection() {
  if (!tl.sel || tl.sel[1] - tl.sel[0] < 0.05) return;
  tl.cuts.push([+tl.sel[0].toFixed(3), +tl.sel[1].toFixed(3)]);
  tl.sel = null;
  updateTimelineUI();
}

function tlClearCuts() {
  tl.cuts = [];
  tl.sel = null;
  updateTimelineUI();
}

function setupTimelineHandlers() {
  const track = document.getElementById("tl-track");
  let dragging = false;
  let moved = false;

  function tFromEvent(e) {
    const r = track.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width;
    return tlClamp(x * tl.dur);
  }

  track.addEventListener("pointerdown", (e) => {
    // Click an already-deleted range -> undo it
    if (e.target.classList.contains("tl-cut")) {
      const i = +e.target.dataset.cut;
      tl.cuts.splice(i, 1);
      updateTimelineUI();
      return;
    }
    dragging = true;
    moved = false;
    const t = tFromEvent(e);
    tl.sel = [t, t];
    try { track.setPointerCapture(e.pointerId); } catch (_) {}
    e.preventDefault();
  });

  track.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const t = tFromEvent(e);
    if (Math.abs(t - tl.sel[0]) > 0.03) moved = true;
    tl.sel = [Math.min(tl.sel[0], t), Math.max(tl.sel[0], t)];
    updateTimelineUI();
  });

  function endDrag(e) {
    if (!dragging) return;
    dragging = false;
    try { track.releasePointerCapture(e.pointerId); } catch (_) {}
    if (!moved) {
      // Plain click without drag -> seek the playhead
      const v = document.getElementById("editor-video");
      if (v && v.duration) v.currentTime = tl.sel[0];
      tl.sel = null;
    }
    updateTimelineUI();
  }
  track.addEventListener("pointerup", endDrag);
  track.addEventListener("pointercancel", endDrag);

  document.getElementById("editor-video")?.addEventListener("timeupdate", () => {
    document.getElementById("tl-play").style.left =
      tlPos(document.getElementById("editor-video").currentTime);
  });

  document.getElementById("tl-del-btn")?.addEventListener("click", tlDeleteSelection);
  document.getElementById("tl-clear-btn")?.addEventListener("click", tlClearCuts);

  // Backspace/Delete commits the current selection as a deleted range
  document.addEventListener("keydown", (e) => {
    const modal = document.getElementById("editor-modal");
    if (!modal || modal.style.display !== "flex") return;
    if (e.key === "Backspace" || e.key === "Delete") {
      if (tl.sel && tl.sel[1] - tl.sel[0] >= 0.05) {
        e.preventDefault();
        tlDeleteSelection();
      }
    }
  });
}

function applyStyleToInputs(s) {
  document.getElementById("st-primary").value = s.primary;
  document.getElementById("st-secondary").value = s.secondary;
  document.getElementById("st-outline").value = s.outline;
  document.getElementById("st-back").value = s.back;
  document.getElementById("st-fontsize").value = s.fontsize;
  document.getElementById("st-outline_w").value = s.outline_w;
  document.getElementById("st-shadow").value = s.shadow;
  document.getElementById("st-marginv").value = s.marginv;
  document.getElementById("st-bold").checked = !!s.bold;
  document.getElementById("st-gradient").checked = !!s.gradient;
  document.getElementById("st-grad-a").value = s.gradient_a || "#ec4899";
  document.getElementById("st-grad-b").value = s.gradient_b || "#a855f7";
  const fn = document.getElementById("st-fontname");
  if (fn && s.fontname) {
    if (![...fn.options].some(o => o.value === s.fontname)) fn.value = FONTS[0];
    else fn.value = s.fontname;
  }
  document.getElementById("grad-row").style.display = s.gradient ? "flex" : "none";
  ["fontsize","outline_w","shadow","marginv"].forEach(k => {
    document.getElementById("rv-"+k).textContent = s[k];
  });
}

function collectStyle() {
  const fn = document.getElementById("st-fontname");
  return {
    primary: document.getElementById("st-primary").value,
    secondary: document.getElementById("st-secondary").value,
    outline: document.getElementById("st-outline").value,
    back: document.getElementById("st-back").value,
    fontsize: parseInt(document.getElementById("st-fontsize").value),
    bold: document.getElementById("st-bold").checked,
    outline_w: parseInt(document.getElementById("st-outline_w").value),
    shadow: parseInt(document.getElementById("st-shadow").value),
    marginv: parseInt(document.getElementById("st-marginv").value),
    fontname: fn ? fn.value : "Arial",
    gradient: document.getElementById("st-gradient").checked,
    gradient_a: document.getElementById("st-grad-a").value,
    gradient_b: document.getElementById("st-grad-b").value
  };
}

function updatePreview() {
  const cues = collectCues();
  const txt = cues.map(c => c.text).join("  /  ") || "Your caption preview";
  const p = document.getElementById("editor-preview");
  const s = collectStyle();
  p.textContent = txt;
  p.style.fontWeight = s.bold ? "800" : "400";
  p.style.fontSize = Math.max(18, s.fontsize / 3) + "px";
  p.style.textShadow = `0 0 ${s.shadow * 2}px ${s.back}`;
  p.style.fontFamily = `'${s.fontname}', sans-serif`;
  if (s.gradient) {
    p.style.background = `linear-gradient(90deg, ${s.gradient_a}, ${s.gradient_b})`;
    p.style.webkitBackgroundClip = "text";
    p.style.backgroundClip = "text";
    p.style.color = "transparent";
    p.style.webkitTextFillColor = "transparent";
  } else {
    p.style.background = "none";
    p.style.webkitBackgroundClip = "border-box";
    p.style.backgroundClip = "border-box";
    p.style.color = s.primary;
    p.style.webkitTextFillColor = s.primary;
  }
}

function setupEditor() {
  // Populate fonts once
  const fnSel = document.getElementById("st-fontname");
  if (fnSel && !fnSel.options.length) {
    FONTS.forEach(f => {
      const o = document.createElement("option");
      o.value = f; o.textContent = f;
      fnSel.appendChild(o);
    });
  }

  document.getElementById("close-editor-btn").onclick = () => {
    document.getElementById("editor-modal").style.display = "none";
  };
  document.querySelector(".modal-overlay")?.addEventListener("click", () => {
    document.getElementById("editor-modal").style.display = "none";
  });

  setupTimelineHandlers();
  setupZoomHandlers();

  // Live preview bindings
  ["st-primary","st-secondary","st-outline","st-back","st-fontsize","st-outline_w",
   "st-shadow","st-marginv","st-bold","st-gradient","st-grad-a","st-grad-b",
   "st-fontname","st-effect"]
   .forEach(id => {
     document.getElementById(id)?.addEventListener("input", updatePreview);
   });

  document.getElementById("add-cue-btn")?.addEventListener("click", () => {
    const list = document.getElementById("cue-list");
    list.appendChild(makeCueRow({ start: 0, end: 1, text: "" }, list.children.length));
    updatePreview();
  });
  document.getElementById("st-gradient")?.addEventListener("change", e => {
    document.getElementById("grad-row").style.display = e.target.checked ? "flex" : "none";
    updatePreview();
  });
  ["fontsize","outline_w","shadow","marginv"].forEach(k => {
    document.getElementById("st-"+k)?.addEventListener("input", e => {
      document.getElementById("rv-"+k).textContent = e.target.value;
    });
  });

  document.getElementById("reset-style-btn").onclick = () => {
    applyStyleToInputs(DEFAULT_STYLE);
    updatePreview();
  };

  document.getElementById("save-clip-btn").onclick = async () => {
    if (!currentEditingClip) return;
    const btn = document.getElementById("save-clip-btn");
    btn.disabled = true;
    const original = btn.innerHTML;
    btn.textContent = t("btn_rerendering");

    const style = collectStyle();
    const cues = collectCues();
    const effect = document.getElementById("st-effect")?.value || "none";

    // Build cut list from deleted ranges + current selection (clip-relative s)
    const cuts = tl.cuts.map(c => [+c[0].toFixed(3), +c[1].toFixed(3)]);
    if (tl.sel && tl.sel[1] - tl.sel[0] >= 0.05) {
      cuts.push([+tl.sel[0].toFixed(3), +tl.sel[1].toFixed(3)]);
    }

    const payload = {
      start: 0,
      end: tl.dur,
      dur: tl.dur,
      effect: effect,
      focus: [+zoomFx.toFixed(4), +zoomFy.toFixed(4)],
      length: zoomLength,
      strength: 1.3,
      cues: cues,
      style: style
    };
    if (cuts.length) payload.cuts = cuts;

    try {
      const r = await fetch(API + "/api/update_clip/" + currentJobId + "/" + encodeURIComponent(currentEditingClip.filename), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await r.json();
      if (data.ok) {
        document.getElementById("editor-modal").style.display = "none";
        const cards = document.querySelectorAll(".clip-card");
        cards.forEach(card => {
          const video = card.querySelector("video");
          if (video && video.src.includes(currentEditingClip.filename)) {
            video.src = video.src.split('?')[0] + "?t=" + Date.now();
            video.load();
          }
        });
      } else {
      alert(t("progress_error") + " " + data.error);
      }
    } catch (e) {
      alert(t("progress_error") + " " + e.message);
    }
    btn.disabled = false;
    btn.innerHTML = original;
  };
}
