/**
 * Electron main process - IPC handlers and backend API client
 * Communicates with Python FastAPI backend via REST API
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');

// Backend API configuration
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const POLL_INTERVAL = 2000; // 2 seconds

// Store active session polling intervals
const activePollers = new Map();

/**
 * Create main application window
 */
function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    },
    icon: path.join(__dirname, '../assets/icon.png'), // Optional icon
    titleBarStyle: 'default',
    backgroundColor: '#0a0a0a'
  });

  // Load renderer
  mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));

  // Open DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  return mainWindow;
}

/**
 * Backend API client
 */
class BackendClient {
  constructor(baseURL = BACKEND_URL) {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  /**
   * Start a new agent session
   */
  async startSession(url, goals) {
    try {
      const response = await this.client.post('/run', {
        url,
        goals: Array.isArray(goals) ? goals : [goals],
        max_steps: 30
      });
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Get session status
   */
  async getSessionStatus(sessionId) {
    try {
      const response = await this.client.get(`/status/${sessionId}`);
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Get full session data including screenshots and steps
   */
  async getSessionFull(sessionId) {
    try {
      const response = await this.client.get(`/api/session/${sessionId}/full`);
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Stop a session
   */
  async stopSession(sessionId) {
    try {
      const response = await this.client.post(`/stop/${sessionId}`);
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Get all sessions
   */
  async getAllSessions() {
    try {
      const response = await this.client.get('/sessions');
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Check backend health
   */
  async checkHealth() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw this._handleError(error);
    }
  }

  /**
   * Handle API errors
   */
  _handleError(error) {
    if (error.response) {
      return new Error(`Backend error: ${error.response.status} - ${error.response.data?.detail || error.message}`);
    } else if (error.request) {
      return new Error('Backend not reachable. Make sure the Python server is running on port 8000.');
    } else {
      return new Error(`Request error: ${error.message}`);
    }
  }
}

// Initialize backend client
const backendClient = new BackendClient();

/**
 * IPC Handlers
 */

// Check backend connection
ipcMain.handle('backend:health', async () => {
  try {
    const health = await backendClient.checkHealth();
    return { success: true, data: health };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Start navigation session (Phase 1)
ipcMain.handle('session:start-navigation', async (event, url) => {
  try {
    const result = await backendClient.startSession(url, ['Navigate to the page']);
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Start summarization session (Phase 2)
ipcMain.handle('session:start-summarization', async (event, url) => {
  try {
    const result = await backendClient.startSession(url, [
      'Navigate to the page',
      'Summarize the main content and purpose of this page'
    ]);
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Start task execution session (Phase 3)
ipcMain.handle('session:start-task', async (event, url, task) => {
  try {
    const goals = Array.isArray(task) ? task : task.split('\n').filter(g => g.trim());
    const result = await backendClient.startSession(url, goals);
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Get session status
ipcMain.handle('session:get-status', async (event, sessionId) => {
  try {
    const status = await backendClient.getSessionStatus(sessionId);
    return { success: true, data: status };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Get full session data
ipcMain.handle('session:get-full', async (event, sessionId) => {
  try {
    const data = await backendClient.getSessionFull(sessionId);
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Stop session
ipcMain.handle('session:stop', async (event, sessionId) => {
  try {
    const result = await backendClient.stopSession(sessionId);
    // Stop polling for this session
    if (activePollers.has(sessionId)) {
      clearInterval(activePollers.get(sessionId));
      activePollers.delete(sessionId);
    }
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Get all sessions
ipcMain.handle('session:get-all', async () => {
  try {
    const data = await backendClient.getAllSessions();
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Start polling for session updates
ipcMain.handle('session:start-polling', async (event, sessionId) => {
  // Clear existing poller if any
  if (activePollers.has(sessionId)) {
    clearInterval(activePollers.get(sessionId));
  }

  // Create new poller
  const poller = setInterval(async () => {
    try {
      const result = await backendClient.getSessionFull(sessionId);
      event.sender.send('session:update', { sessionId, data: result });
      
      // Stop polling if session is complete
      if (result.status === 'completed' || result.status === 'failed' || result.status === 'stopped') {
        clearInterval(poller);
        activePollers.delete(sessionId);
        event.sender.send('session:complete', { sessionId, status: result.status });
      }
    } catch (error) {
      event.sender.send('session:error', { sessionId, error: error.message });
    }
  }, POLL_INTERVAL);

  activePollers.set(sessionId, poller);
  return { success: true };
});

// Stop polling for session
ipcMain.handle('session:stop-polling', async (event, sessionId) => {
  if (activePollers.has(sessionId)) {
    clearInterval(activePollers.get(sessionId));
    activePollers.delete(sessionId);
    return { success: true };
  }
  return { success: false, error: 'No active poller for session' };
});

/**
 * App lifecycle
 */
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Clear all pollers
  activePollers.forEach(poller => clearInterval(poller));
  activePollers.clear();

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Clear all pollers
  activePollers.forEach(poller => clearInterval(poller));
  activePollers.clear();
});

