// Global state
let currentSessionId = null;
let statusCheckInterval = null;

// DOM Elements
const urlInput = document.getElementById('url-input');
const goBtn = document.getElementById('go-btn');
const summarizeBtn = document.getElementById('summarize-btn');
const taskInput = document.getElementById('task-input');
const executeTaskBtn = document.getElementById('execute-task-btn');
const refreshBtn = document.getElementById('refresh-btn');
const backendStatus = document.getElementById('backend-status');
const sessionIdEl = document.getElementById('session-id');
const sessionStatusEl = document.getElementById('session-status');
const currentUrlEl = document.getElementById('current-url');
const stepsCountEl = document.getElementById('steps-count');
const summaryDisplay = document.getElementById('summary-display');
const summaryContent = document.getElementById('summary-content');
const reasoningContent = document.getElementById('reasoning-content');
const loadingIndicator = document.getElementById('loading-indicator');
const screenshotContainer = document.getElementById('screenshot-container');
const actionList = document.getElementById('action-list');
const statusMessage = document.getElementById('status-message');

// Initialize
async function init() {
  await checkBackendConnection();
  setupEventListeners();
  setStatusMessage('Ready to browse');
}

// Check backend connection
async function checkBackendConnection() {
  try {
    const result = await window.electronAPI.checkBackend();
    if (result.success && result.healthy) {
      backendStatus.textContent = '✓ Backend Connected';
      backendStatus.classList.add('connected');
      backendStatus.classList.remove('disconnected');
    } else {
      backendStatus.textContent = '✗ Backend Disconnected';
      backendStatus.classList.add('disconnected');
      backendStatus.classList.remove('connected');
      setStatusMessage('Warning: Backend server not responding. Please start it with: uvicorn app.main:app');
    }
  } catch (error) {
    backendStatus.textContent = '✗ Backend Error';
    backendStatus.classList.add('disconnected');
    backendStatus.classList.remove('connected');
    setStatusMessage('Error: Cannot connect to backend');
  }
}

// Setup event listeners
function setupEventListeners() {
  goBtn.addEventListener('click', handleNavigate);
  urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleNavigate();
  });
  
  summarizeBtn.addEventListener('click', handleSummarize);
  
  executeTaskBtn.addEventListener('click', handleExecuteTask);
  taskInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleExecuteTask();
  });
  
  refreshBtn.addEventListener('click', () => {
    if (currentSessionId) {
      updateSessionStatus(currentSessionId);
    }
  });
}

// Handle navigation
async function handleNavigate() {
  const url = urlInput.value.trim();
  
  if (!url) {
    setStatusMessage('Please enter a URL');
    return;
  }
  
  // Add protocol if missing
  let fullUrl = url;
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    fullUrl = 'https://' + url;
  }
  
  setStatusMessage(`Navigating to ${fullUrl}...`);
  showLoading(true);
  
  try {
    const result = await window.electronAPI.navigate(fullUrl);
    
    if (result.success) {
      currentSessionId = result.sessionId;
      sessionIdEl.textContent = result.sessionId;
      setStatusMessage(`Navigated to ${fullUrl}`);
      
      // Start monitoring session
      startStatusMonitoring(result.sessionId);
    } else {
      setStatusMessage(`Navigation failed: ${result.error}`);
      showLoading(false);
    }
  } catch (error) {
    setStatusMessage(`Error: ${error.message}`);
    showLoading(false);
  }
}

// Handle page summarization
async function handleSummarize() {
  if (!currentSessionId) {
    setStatusMessage('Please navigate to a URL first');
    return;
  }
  
  setStatusMessage('Analyzing page...');
  showLoading(true);
  summaryDisplay.style.display = 'none';
  
  try {
    const result = await window.electronAPI.summarizePage();
    
    if (result.success) {
      summaryContent.innerHTML = `<p>${result.summary}</p>`;
      summaryDisplay.style.display = 'block';
      setStatusMessage('Page summarized successfully');
      
      // Display steps if available
      if (result.steps && result.steps.length > 0) {
        displaySteps(result.steps);
      }
    } else {
      summaryContent.innerHTML = `<p class="error">Failed to summarize: ${result.error}</p>`;
      summaryDisplay.style.display = 'block';
      setStatusMessage(`Summarization failed: ${result.error}`);
    }
  } catch (error) {
    setStatusMessage(`Error: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

// Handle task execution
async function handleExecuteTask() {
  const task = taskInput.value.trim();
  
  if (!task) {
    setStatusMessage('Please enter a task');
    return;
  }
  
  if (!currentSessionId) {
    setStatusMessage('Please navigate to a URL first');
    return;
  }
  
  setStatusMessage(`Executing task: ${task}...`);
  showLoading(true);
  summaryDisplay.style.display = 'none';
  
  try {
    const result = await window.electronAPI.executeTask(task);
    
    if (result.success) {
      currentSessionId = result.sessionId;
      sessionIdEl.textContent = result.sessionId;
      setStatusMessage('Task execution started');
      
      // Clear task input
      taskInput.value = '';
      
      // Start monitoring
      startStatusMonitoring(result.sessionId);
    } else {
      setStatusMessage(`Task execution failed: ${result.error}`);
      showLoading(false);
    }
  } catch (error) {
    setStatusMessage(`Error: ${error.message}`);
    showLoading(false);
  }
}

// Start status monitoring
function startStatusMonitoring(sessionId) {
  // Clear any existing interval
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
  }
  
  // Initial update
  updateSessionStatus(sessionId);
  
  // Poll every 2 seconds
  statusCheckInterval = setInterval(() => {
    updateSessionStatus(sessionId);
  }, 2000);
}

// Update session status
async function updateSessionStatus(sessionId) {
  try {
    const result = await window.electronAPI.getSessionFull(sessionId);
    
    if (result.success) {
      const data = result.data;
      
      // Update session info
      sessionStatusEl.textContent = data.status;
      currentUrlEl.textContent = data.current_url || data.url;
      stepsCountEl.textContent = data.steps_count || 0;
      
      // Display steps
      if (data.steps && data.steps.length > 0) {
        displaySteps(data.steps);
        
        // Show latest screenshot
        const lastStep = data.steps[data.steps.length - 1];
        if (lastStep.screenshot) {
          displayScreenshot(lastStep.screenshot);
        }
        
        // Show latest reasoning
        if (lastStep.reasoning) {
          reasoningContent.innerHTML = `<p><strong>Step ${lastStep.step_number}:</strong> ${lastStep.reasoning}</p>`;
        }
      }
      
      // Stop monitoring if session is complete
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'stopped') {
        if (statusCheckInterval) {
          clearInterval(statusCheckInterval);
          statusCheckInterval = null;
        }
        showLoading(false);
        
        if (data.status === 'completed') {
          setStatusMessage('Task completed successfully');
        } else if (data.status === 'failed') {
          setStatusMessage('Task failed');
        } else {
          setStatusMessage('Task stopped');
        }
      }
    }
  } catch (error) {
    console.error('Status update error:', error);
  }
}

// Display steps as action items
function displaySteps(steps) {
  if (!steps || steps.length === 0) {
    actionList.innerHTML = '<p class="placeholder">No actions yet...</p>';
    return;
  }
  
  actionList.innerHTML = '';
  
  // Show last 10 steps
  const recentSteps = steps.slice(-10);
  
  recentSteps.forEach(step => {
    const actionItem = document.createElement('div');
    actionItem.className = 'action-item';
    
    if (step.error) {
      actionItem.classList.add('error');
    } else if (step.result && step.result.includes('Success')) {
      actionItem.classList.add('success');
    }
    
    const actionType = step.action ? step.action.action : 'observation';
    const actionDesc = step.action ? 
      (step.action.summary || step.action.selector || 'Action executed') : 
      'Page observation';
    
    actionItem.innerHTML = `
      <div class="action-type">${actionType}</div>
      <div class="action-description">${actionDesc}</div>
      ${step.result ? `<div class="action-description">Result: ${step.result}</div>` : ''}
      ${step.error ? `<div class="action-description" style="color: #ef4444;">Error: ${step.error}</div>` : ''}
      <div class="action-time">Step ${step.step_number} • ${new Date(step.timestamp).toLocaleTimeString()}</div>
    `;
    
    actionList.appendChild(actionItem);
  });
  
  // Scroll to bottom
  actionList.scrollTop = actionList.scrollHeight;
}

// Display screenshot
function displayScreenshot(base64Image) {
  screenshotContainer.innerHTML = `
    <img src="data:image/png;base64,${base64Image}" alt="Page screenshot">
  `;
}

// Show/hide loading indicator
function showLoading(show) {
  loadingIndicator.style.display = show ? 'flex' : 'none';
}

// Set status message
function setStatusMessage(message) {
  statusMessage.textContent = message;
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);

// Re-check backend connection every 30 seconds
setInterval(checkBackendConnection, 30000);
