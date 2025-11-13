const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');

// Configuration
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

let mainWindow = null;
let currentSessionId = null;

function createWindow() {
  mainWindow = BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    title: 'mini-Atlas Browser Agent'
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // Open DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC Handlers

// Navigate to URL
ipcMain.handle('navigate', async (event, url) => {
  try {
    // For simple navigation, we create a session that just visits the URL
    const response = await axios.post(`${BACKEND_URL}/run`, {
      url: url,
      goals: ['Navigate to the page'],
      max_steps: 1
    });
    
    currentSessionId = response.data.session_id;
    return { success: true, sessionId: currentSessionId };
  } catch (error) {
    console.error('Navigation error:', error);
    return { success: false, error: error.message };
  }
});

// Summarize current page
ipcMain.handle('summarize-page', async (event) => {
  try {
    if (!currentSessionId) {
      throw new Error('No active session. Please navigate to a URL first.');
    }

    // Get current session status to find the URL
    const statusResponse = await axios.get(`${BACKEND_URL}/status/${currentSessionId}`);
    const currentUrl = statusResponse.data.current_url;

    // Create new session for summarization
    const response = await axios.post(`${BACKEND_URL}/run`, {
      url: currentUrl,
      goals: ['Analyze this page and provide a brief summary of what it contains'],
      max_steps: 5
    });

    const summarySessionId = response.data.session_id;
    
    // Poll for completion
    let attempts = 0;
    const maxAttempts = 30; // 30 seconds max
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const status = await axios.get(`${BACKEND_URL}/status/${summarySessionId}`);
      
      if (status.data.state === 'completed' || status.data.state === 'failed') {
        // Get full session data
        const fullData = await axios.get(`${BACKEND_URL}/api/session/${summarySessionId}/full`);
        
        // Extract summary from the steps
        const steps = fullData.data.steps;
        if (steps && steps.length > 0) {
          const lastStep = steps[steps.length - 1];
          return {
            success: true,
            summary: lastStep.reasoning || lastStep.result || 'Page analyzed',
            steps: steps
          };
        }
        
        return { success: true, summary: 'Analysis completed' };
      }
      
      attempts++;
    }
    
    return { success: false, error: 'Summarization timed out' };
  } catch (error) {
    console.error('Summarization error:', error);
    return { success: false, error: error.message };
  }
});

// Execute AI task
ipcMain.handle('execute-task', async (event, task) => {
  try {
    if (!currentSessionId) {
      throw new Error('No active session. Please navigate to a URL first.');
    }

    // Get current URL
    const statusResponse = await axios.get(`${BACKEND_URL}/status/${currentSessionId}`);
    const currentUrl = statusResponse.data.current_url;

    // Create session for the task
    const response = await axios.post(`${BACKEND_URL}/run`, {
      url: currentUrl,
      goals: [task],
      max_steps: 30
    });

    const taskSessionId = response.data.session_id;
    currentSessionId = taskSessionId;
    
    return { success: true, sessionId: taskSessionId };
  } catch (error) {
    console.error('Task execution error:', error);
    return { success: false, error: error.message };
  }
});

// Get session status
ipcMain.handle('get-session-status', async (event, sessionId) => {
  try {
    const response = await axios.get(`${BACKEND_URL}/status/${sessionId || currentSessionId}`);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Status check error:', error);
    return { success: false, error: error.message };
  }
});

// Get full session data
ipcMain.handle('get-session-full', async (event, sessionId) => {
  try {
    const response = await axios.get(`${BACKEND_URL}/api/session/${sessionId || currentSessionId}/full`);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('Session data error:', error);
    return { success: false, error: error.message };
  }
});

// Check backend health
ipcMain.handle('check-backend', async (event) => {
  try {
    const response = await axios.get(`${BACKEND_URL}/health`, { timeout: 5000 });
    return { success: true, healthy: response.data.status === 'healthy' };
  } catch (error) {
    return { success: false, error: error.message };
  }
});
