# Testing Guide - mini-Atlas Desktop

Test scenarios and procedures for Electron desktop application.

## Integration Tests

### Running Tests

```bash
# Run all integration tests
pytest tests/test_electron_integration.py -v

# Run specific test
pytest tests/test_electron_integration.py::TestElectronIntegration::test_health_endpoint -v
```

### Test Coverage

The integration tests verify all 6 backend endpoints used by Electron:

1. ✅ `GET /health` - Health check endpoint
2. ✅ `POST /run` - Navigation session (Phase 1)
3. ✅ `POST /run` - Summarization session (Phase 2)
4. ✅ `POST /run` - Task execution session (Phase 3)
5. ✅ `GET /status/{session_id}` - Session status
6. ✅ `GET /api/session/{session_id}/full` - Full session data
7. ✅ `POST /stop/{session_id}` - Stop session
8. ✅ `GET /sessions` - List all sessions

## Manual Test Scenarios

### Scenario 1: Basic Navigation

**Steps:**
1. Start backend: `uvicorn app.main:app --port 8000`
2. Launch desktop app: `npm start`
3. Enter URL: `https://example.com`
4. Click "Go"
5. Verify: Screenshot appears, status shows "Running"
6. Wait for completion
7. Verify: Status shows "Completed", screenshot updated

**Expected:**
- Backend status: Connected (green)
- Session ID displayed in status bar
- Browser view shows screenshot
- Activity panel shows navigation steps

### Scenario 2: Page Summarization

**Steps:**
1. Enter URL: `https://example.com`
2. Click "Summarize"
3. Wait for completion
4. Verify: Activity panel shows summarization reasoning

**Expected:**
- Multi-step execution
- Reasoning displayed for each step
- Summary extracted from final step

### Scenario 3: Task Execution

**Steps:**
1. Enter task: `"Search for Playwright automation and click first result"`
2. Click "Go"
3. Verify: Multi-step execution visible
4. Watch real-time updates

**Expected:**
- Agent executes multiple steps
- Each step shows action and reasoning
- Screenshots update in real-time
- Final step shows completion

### Scenario 4: Stop Session

**Steps:**
1. Start a session
2. Click "Stop" button
3. Verify: Session stops, polling ends

**Expected:**
- Status changes to "Stopped"
- Polling stops
- UI resets

### Scenario 5: Backend Disconnection

**Steps:**
1. Start desktop app
2. Stop backend server
3. Verify: Status indicator shows "Disconnected"

**Expected:**
- Backend status: Disconnected (red)
- Error message on session start attempt

### Scenario 6: Error Handling

**Steps:**
1. Enter invalid URL: `not-a-url`
2. Click "Go"
3. Verify: Error message displayed

**Expected:**
- User-friendly error message
- UI remains functional
- Can retry with correct input

## Test Data

### Valid URLs
- `https://example.com`
- `example.com` (auto-adds https://)
- `http://example.com`

### Valid Tasks
- `"Search for Playwright automation and click first result"`
- `"Navigate to login page and fill email field"`
- `"Click on the first link"`

### Invalid Inputs
- Empty string
- Invalid URL format
- Malformed task

## Performance Tests

### Polling Performance
- Verify polling interval: 2 seconds
- Check memory usage with long-running sessions
- Verify polling stops on session completion

### UI Responsiveness
- Test with rapid session starts/stops
- Verify UI updates don't block
- Check screenshot rendering performance

## Cross-Platform Testing

### macOS
- ✅ Window creation
- ✅ Menu bar integration
- ✅ Keyboard shortcuts
- ✅ File system access

### Windows
- ✅ Window creation
- ✅ Taskbar integration
- ✅ Keyboard shortcuts
- ✅ File system access

### Linux
- ✅ Window creation
- ✅ Desktop integration
- ✅ Keyboard shortcuts
- ✅ File system access

## Security Tests

- ✅ Context isolation enabled
- ✅ Node integration disabled
- ✅ Secure IPC communication
- ✅ No direct backend access from renderer
- ✅ Input sanitization

## Known Issues

None currently. All tests pass.

## Reporting Issues

When reporting test failures, include:
1. Platform (macOS/Windows/Linux)
2. Node.js version
3. Electron version
4. Backend logs
5. Error messages
6. Steps to reproduce

