const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  getBackendUrl: () => ipcRenderer.invoke("get-backend-url"),
  openFolder: (path) => ipcRenderer.invoke("open-folder", path),
});
