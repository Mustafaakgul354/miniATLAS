/**
 * mini-Atlas Desktop Renderer Process
 * Handles UI interactions and backend communication
 */

// Application state
let currentSessionId = null;
let currentMode = 'navigation'; // navigation, summarization, task
let isPolling = false;

// DOM Elements
const addressBar = document.getElementById('addressBar');
const goButton = document.getElementById('goButton');
const summarizeButton = document.getElementById('summarizeButton');
const stopButton = document.getElementById('stopButton');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const browserContent = document.getElementById('browserContent');
const activityContent = document.getElementById('activityContent');
const currentUrl = document.getElementById('currentUrl');
const stepCounter = document.getElementById('stepCounter');
const backendStatus = document.getElementById('backendStatus');
const sessionId = document.getElementById('sessionId');
const currentModeDisplay = document.getElementById('currentMode');

/**
 * Initialize application
 */
async function init() {
    // Check backend connection
    await checkBackendHealth();
    
    // Setup event listeners
    setupEventListeners();
    
    // Setup IPC listeners
    setupIPCListeners();
    
    // Periodic health check
    setInterval(checkBackendHealth, 10000); // Every 10 seconds
}

/**
 * Setup UI event listeners
 */
function setupEventListeners() {
    // Go button - Phase 1: Navigation
    goButton.addEventListener('click', handleNavigation);
    addressBar.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleNavigation();
        }
    });
    
    // Summarize button - Phase 2: Page Summarization
    summarizeButton.addEventListener('click', handleSummarization);
    
    // Stop button
    stopButton.addEventListener('click', handleStop);
}

/**
 * Setup IPC event listeners
 */
function setupIPCListeners() {
    // Session update events
    window.electronAPI.onSessionUpdate((data) => {
        updateUI(data);
    });
    
    // Session complete events
    window.electronAPI.onSessionComplete((data) => {
        handleSessionComplete(data);
    });
    
    // Session error events
    window.electronAPI.onSessionError((data) => {
        showError(data.error);
    });
}

/**
 * Check backend health
 */
async function checkBackendHealth() {
    try {
        const result = await window.electronAPI.checkHealth();
        if (result.success) {
            backendStatus.textContent = 'Connected';
            backendStatus.className = 'value connected';
            return true;
        } else {
            backendStatus.textContent = 'Disconnected';
            backendStatus.className = 'value disconnected';
            return false;
        }
    } catch (error) {
        backendStatus.textContent = 'Error';
        backendStatus.className = 'value disconnected';
        return false;
    }
}

/**
 * Phase 1: Handle Navigation
 */
async function handleNavigation() {
    const input = addressBar.value.trim();
    if (!input) {
        showError('Please enter a URL or task');
        return;
    }
    
    // Detect if input is a task or URL
    const inputType = detectInputType(input);
    
    if (inputType === 'task') {
        // Phase 3: Task Execution
        // Extract URL from task if present, otherwise use current URL or default
        const urlMatch = input.match(/https?:\/\/[^\s]+/);
        const url = urlMatch ? urlMatch[0] : (currentUrl.textContent !== 'No active session' ? currentUrl.textContent : 'https://www.google.com');
        const task = input.replace(/https?:\/\/[^\s]+/g, '').trim() || input;
        
        await handleTaskExecution(url, task);
    } else {
        // Phase 1: Navigation
        const normalizedUrl = normalizeUrl(input);
        
        try {
            updateStatus('running', 'Starting navigation...');
            setButtonsEnabled(false);
            
            const result = await window.electronAPI.startNavigation(normalizedUrl);
            
            if (result.success) {
                currentSessionId = result.data.session_id;
                sessionId.textContent = currentSessionId;
                currentMode = 'navigation';
                currentModeDisplay.textContent = 'Navigation';
                
                // Start polling
                await window.electronAPI.startPolling(currentSessionId);
                isPolling = true;
                
                stopButton.style.display = 'inline-block';
                showSuccess('Navigation started');
            } else {
                showError(result.error);
                resetUI();
            }
        } catch (error) {
            showError(`Failed to start navigation: ${error.message}`);
            resetUI();
        }
    }
}

/**
 * Phase 2: Handle Page Summarization
 */
async function handleSummarization() {
    const url = addressBar.value.trim();
    if (!url) {
        showError('Please enter a URL');
        return;
    }
    
    const normalizedUrl = normalizeUrl(url);
    
    try {
        updateStatus('running', 'Summarizing page...');
        setButtonsEnabled(false);
        
        const result = await window.electronAPI.startSummarization(normalizedUrl);
        
        if (result.success) {
            currentSessionId = result.data.session_id;
            sessionId.textContent = currentSessionId;
            currentMode = 'summarization';
            currentModeDisplay.textContent = 'Summarization';
            
            // Start polling
            await window.electronAPI.startPolling(currentSessionId);
            isPolling = true;
            
            stopButton.style.display = 'inline-block';
            showSuccess('Summarization started');
        } else {
            showError(result.error);
            resetUI();
        }
    } catch (error) {
        showError(`Failed to start summarization: ${error.message}`);
        resetUI();
    }
}

/**
 * Phase 3: Handle Task Execution
 * Called when user enters a task in address bar
 */
async function handleTaskExecution(url, task) {
    const normalizedUrl = normalizeUrl(url);
    
    try {
        updateStatus('running', 'Executing task...');
        setButtonsEnabled(false);
        
        const result = await window.electronAPI.startTask(normalizedUrl, task);
        
        if (result.success) {
            currentSessionId = result.data.session_id;
            sessionId.textContent = currentSessionId;
            currentMode = 'task';
            currentModeDisplay.textContent = 'Task Execution';
            
            // Start polling
            await window.electronAPI.startPolling(currentSessionId);
            isPolling = true;
            
            stopButton.style.display = 'inline-block';
            showSuccess('Task execution started');
        } else {
            showError(result.error);
            resetUI();
        }
    } catch (error) {
        showError(`Failed to start task: ${error.message}`);
        resetUI();
    }
}

/**
 * Handle Stop button
 */
async function handleStop() {
    if (!currentSessionId) return;
    
    try {
        await window.electronAPI.stopPolling(currentSessionId);
        const result = await window.electronAPI.stopSession(currentSessionId);
        
        if (result.success) {
            showSuccess('Session stopped');
            resetUI();
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError(`Failed to stop session: ${error.message}`);
    }
}

/**
 * Update UI with session data
 */
function updateUI(sessionData) {
    if (!sessionData || !sessionData.data) return;
    
    const session = sessionData.data;
    
    // Update status
    updateStatus(session.status, getStatusText(session.status));
    
    // Update step counter
    stepCounter.textContent = `${session.steps_count || session.steps?.length || 0} steps`;
    
    // Update current URL
    if (session.current_url) {
        currentUrl.textContent = session.current_url;
    }
    
    // Update browser view with screenshot
    updateBrowserView(session);
    
    // Update activity panel with steps
    updateActivityPanel(session);
}

/**
 * Update browser view with screenshot
 */
function updateBrowserView(session) {
    if (!session.steps || session.steps.length === 0) {
        return;
    }
    
    // Get latest screenshot
    const latestStep = session.steps[session.steps.length - 1];
    if (latestStep && latestStep.screenshot) {
        browserContent.innerHTML = `
            <img src="data:image/png;base64,${latestStep.screenshot}" 
                 class="screenshot-view" 
                 alt="Browser View">
        `;
    } else if (session.steps.length > 0) {
        browserContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚡</div>
                <h2>Agent Running</h2>
                <p>${session.current_url || 'Processing...'}</p>
            </div>
        `;
    }
}

/**
 * Update activity panel with steps
 */
function updateActivityPanel(session) {
    if (!session.steps || session.steps.length === 0) {
        activityContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <p>Waiting for agent steps...</p>
            </div>
        `;
        return;
    }
    
    // Display steps in reverse order (newest first)
    const stepsHtml = [...session.steps].reverse().map(step => {
        const actionHtml = step.action ? `
            <div class="step-action">
                <span class="step-action-type">${step.action.action}</span>
                ${step.action.selector ? ` → ${step.action.selector}` : ''}
                ${step.action.value ? ` = "${step.action.value}"` : ''}
            </div>
        ` : '';
        
        const reasoningHtml = step.reasoning ? `
            <div class="step-reasoning">${step.reasoning}</div>
        ` : '';
        
        const resultHtml = step.result ? `
            <div class="step-result ${step.error ? 'error' : 'success'}">
                ${step.error ? '❌ ' : '✓ '}${step.result}
            </div>
        ` : '';
        
        return `
            <div class="step-item">
                <div class="step-header">
                    <span class="step-number">Step #${step.step_number}</span>
                    <span class="step-time">${formatTime(step.timestamp)}</span>
                </div>
                ${reasoningHtml}
                ${actionHtml}
                ${resultHtml}
            </div>
        `;
    }).join('');
    
    activityContent.innerHTML = stepsHtml;
}

/**
 * Handle session completion
 */
function handleSessionComplete(data) {
    updateStatus(data.status, getStatusText(data.status));
    
    if (data.status === 'completed') {
        showSuccess('Session completed successfully');
    } else if (data.status === 'failed') {
        showError('Session failed');
    }
    
    // Fetch final session data
    if (currentSessionId) {
        window.electronAPI.getSessionFull(currentSessionId).then(result => {
            if (result.success) {
                updateUI({ data: result.data });
            }
        });
    }
    
    resetUI();
}

/**
 * Update status indicator
 */
function updateStatus(status, text) {
    statusDot.className = `status-dot ${status}`;
    statusText.textContent = text;
}

/**
 * Get status text
 */
function getStatusText(status) {
    const statusMap = {
        'running': 'Running',
        'completed': 'Completed',
        'failed': 'Failed',
        'stopped': 'Stopped',
        'waiting_human': 'Waiting (CAPTCHA)'
    };
    return statusMap[status] || status;
}

/**
 * Format timestamp
 */
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Normalize URL (add protocol if missing)
 */
function normalizeUrl(url) {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        return 'https://' + url;
    }
    return url;
}

/**
 * Set buttons enabled/disabled
 */
function setButtonsEnabled(enabled) {
    goButton.disabled = !enabled;
    summarizeButton.disabled = !enabled;
    addressBar.disabled = !enabled;
}

/**
 * Reset UI to initial state
 */
function resetUI() {
    currentSessionId = null;
    isPolling = false;
    setButtonsEnabled(true);
    stopButton.style.display = 'none';
    updateStatus('ready', 'Ready');
    sessionId.textContent = '-';
}

/**
 * Show error message
 */
function showError(message) {
    console.error(message);
    // You could add a toast notification here
    alert(`Error: ${message}`);
}

/**
 * Show success message
 */
function showSuccess(message) {
    console.log(message);
    // You could add a toast notification here
}

/**
 * Detect if input is a task vs URL
 */
function detectInputType(input) {
    // If it contains action verbs or multiple sentences, it's likely a task
    const taskIndicators = ['click', 'search', 'fill', 'navigate', 'find', 'go to', 'and'];
    const lowerInput = input.toLowerCase();
    
    if (taskIndicators.some(indicator => lowerInput.includes(indicator)) && 
        (lowerInput.includes(' ') || lowerInput.split('.').length > 1)) {
        return 'task';
    }
    
    // Check if it looks like a URL
    if (input.includes('.') && (input.includes('http') || input.split('.').length >= 2)) {
        return 'url';
    }
    
    return 'task'; // Default to task if unclear
}

// Auto-detect input type and handle accordingly
addressBar.addEventListener('input', (e) => {
    const input = e.target.value.trim();
    if (input.length > 0) {
        const inputType = detectInputType(input);
        if (inputType === 'task') {
            goButton.textContent = 'Execute Task';
        } else {
            goButton.textContent = 'Go';
        }
    }
});

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

