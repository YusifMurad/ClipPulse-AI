const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  backendUrl: "http://127.0.0.1:5555",
  getBackendUrl: () => ipcRenderer.invoke("get-backend-url"),
  openFolder: (path) => ipcRenderer.invoke("open-folder", path),
});
