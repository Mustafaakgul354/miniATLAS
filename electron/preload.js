const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  navigate: (url) => ipcRenderer.invoke('navigate', url),
  summarizePage: () => ipcRenderer.invoke('summarize-page'),
  executeTask: (task) => ipcRenderer.invoke('execute-task', task),
  getSessionStatus: (sessionId) => ipcRenderer.invoke('get-session-status', sessionId),
  getSessionFull: (sessionId) => ipcRenderer.invoke('get-session-full', sessionId),
  checkBackend: () => ipcRenderer.invoke('check-backend')
});
