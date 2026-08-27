const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

let mainWindow;
let backendProcess;

const BACKEND_URL = "http://127.0.0.1:5555";
const isDev = !app.isPackaged;

function findPython() {
  if (process.platform === "win32") {
    const venvPython = path.join(__dirname, "..", "backend", "venv", "Scripts", "python.exe");
    if (fs.existsSync(venvPython)) return venvPython;
    return "python";
  }
  const venvPython = path.join(__dirname, "..", "backend", "venv", "bin", "python3");
  if (fs.existsSync(venvPython)) return venvPython;
  return "python3";
}

function startBackend() {
  const py = findPython();
  const serverPath = path.join(__dirname, "..", "backend", "server.py");
  backendProcess = spawn(py, [serverPath], {
    cwd: path.join(__dirname, "..", "backend"),
    stdio: ["ignore", "pipe", "pipe"],
  });
  backendProcess.stdout.on("data", (d) =>
    console.log("[backend]", d.toString().trim())
  );
  backendProcess.stderr.on("data", (d) =>
    console.log("[backend]", d.toString().trim())
  );
  backendProcess.on("error", (e) =>
    console.error("Backend failed to start:", e.message)
  );
  backendProcess.on("exit", (code) => {
    console.log("Backend exited with code", code);
  });
}

function waitForBackend(retries = 30, delay = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = () => {
      fetch(BACKEND_URL + "/api/settings")
        .then(() => resolve())
        .catch(() => {
          if (++attempts >= retries) reject(new Error("Backend timeout"));
          else setTimeout(check, delay);
        });
    };
    check();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    backgroundColor: "#0a0a0a",
    titleBarStyle: "hiddenInset",
    frame: process.platform === "darwin" ? false : true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, "..", "assets", "icon.png"),
  });

  mainWindow.loadFile(path.join(__dirname, "..", "index.html"));

  if (isDev) mainWindow.webContents.openDevTools({ mode: "detach" });
}

app.whenReady().then(async () => {
  startBackend();
  try {
    await waitForBackend();
  } catch (e) {
    console.error(e.message);
  }
  createWindow();
});

app.on("window-all-closed", () => {
  if (backendProcess) backendProcess.kill();
  app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) backendProcess.kill();
});

// IPC handlers
ipcMain.handle("get-backend-url", () => BACKEND_URL);
ipcMain.handle("open-folder", async (_, folderPath) => {
  shell.openPath(folderPath);
});
