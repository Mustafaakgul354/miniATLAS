/**
 * Electron preload script - Context bridge for secure IPC
 * Exposes safe API to renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process
// to use ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Backend health check
  checkHealth: () => ipcRenderer.invoke('backend:health'),

  // Session management
  startNavigation: (url) => ipcRenderer.invoke('session:start-navigation', url),
  startSummarization: (url) => ipcRenderer.invoke('session:start-summarization', url),
  startTask: (url, task) => ipcRenderer.invoke('session:start-task', url, task),
  getSessionStatus: (sessionId) => ipcRenderer.invoke('session:get-status', sessionId),
  getSessionFull: (sessionId) => ipcRenderer.invoke('session:get-full', sessionId),
  stopSession: (sessionId) => ipcRenderer.invoke('session:stop', sessionId),
  getAllSessions: () => ipcRenderer.invoke('session:get-all'),

  // Polling
  startPolling: (sessionId) => ipcRenderer.invoke('session:start-polling', sessionId),
  stopPolling: (sessionId) => ipcRenderer.invoke('session:stop-polling', sessionId),

  // Event listeners
  onSessionUpdate: (callback) => {
    ipcRenderer.on('session:update', (event, data) => callback(data));
  },
  onSessionComplete: (callback) => {
    ipcRenderer.on('session:complete', (event, data) => callback(data));
  },
  onSessionError: (callback) => {
    ipcRenderer.on('session:error', (event, data) => callback(data));
  },

  // Remove listeners
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

