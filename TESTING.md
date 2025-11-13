# Testing Guide for mini-Atlas Desktop Application

This guide explains how to test the Electron desktop application integrated with the Python backend.

## Prerequisites

1. **Python Backend**: Installed and configured
2. **Node.js**: Version 16 or higher
3. **npm packages**: Installed via `npm install`

## Test Setup

### 1. Start the Python Backend

In one terminal:

```bash
cd /home/runner/work/miniATLAS/miniATLAS
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Wait for the message: `Uvicorn running on http://0.0.0.0:8000`

### 2. Verify Backend Health

In another terminal:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "playwright": true,
  "sessions_active": 0,
  "sessions_total": 0
}
```

### 3. Launch Desktop Application

```bash
cd /home/runner/work/miniATLAS/miniATLAS
npm start
```

Or use the startup scripts:
```bash
./start-desktop.sh  # Linux/Mac
start-desktop.bat   # Windows
```

## Testing Phases

### Phase 1: Basic Navigation

**Test 1.1: URL Navigation**
1. Enter `https://www.google.com` in the address bar
2. Click "Go" button
3. Expected: 
   - Status changes to "running"
   - Session ID appears
   - After ~2 seconds, status updates with step count

**Test 1.2: Alternative URLs**
- Try: `https://example.com`
- Try: `www.github.com` (without https://)
- Expected: Both should work, protocol added automatically

### Phase 2: Page Summarization

**Test 2.1: Summarize a Page**
1. Navigate to `https://example.com`
2. Wait for navigation to complete
3. Click "Summarize Page" button
4. Expected:
   - "Analyzing page..." status message
   - Loading spinner appears
   - After 5-10 seconds, summary appears in left panel
   - Summary describes the page content

**Test 2.2: Summarize Different Pages**
- Try: Wikipedia article
- Try: News website
- Expected: Different summaries reflecting page content

### Phase 3: AI Task Execution

**Test 3.1: Simple Search Task**
1. Navigate to `https://www.google.com`
2. Enter task: "Search for Playwright automation"
3. Click "Execute Task"
4. Expected:
   - Agent finds search box
   - Types the query
   - Steps appear in action history
   - Screenshots update showing progress

**Test 3.2: Multi-Step Task**
1. Navigate to `https://www.google.com`
2. Enter task: "Search for GitHub and click the first result"
3. Click "Execute Task"
4. Expected:
   - Multiple steps in action history
   - Search performed
   - First result clicked
   - Final screenshot shows GitHub page

**Test 3.3: Complex Workflow**
1. Navigate to a website with forms
2. Enter task: "Fill in the contact form with test data"
3. Expected:
   - Agent identifies form fields
   - Fills appropriate data
   - May show reasoning for each field

## Verification Checklist

### UI Elements
- [ ] Address bar accepts input
- [ ] Go button navigates to URLs
- [ ] Task input accepts natural language
- [ ] Execute Task button starts agent
- [ ] Refresh button updates status
- [ ] Backend status badge shows connection

### Status Updates
- [ ] Session ID displays correctly
- [ ] Status changes (idle → running → completed/failed)
- [ ] Current URL updates
- [ ] Step count increments

### Visual Feedback
- [ ] Loading spinner shows during operations
- [ ] Screenshots appear and update
- [ ] Action history populates with steps
- [ ] Reasoning text updates
- [ ] Summary displays (Phase 2)

### Error Handling
- [ ] Invalid URL shows error message
- [ ] Backend disconnected shows warning
- [ ] Task failures display error in action list
- [ ] Timeout errors handled gracefully

## Manual Testing Scenarios

### Scenario 1: Google Search Flow
```
1. Launch app
2. Navigate to google.com
3. Task: "Search for Python tutorials"
4. Verify: Search executed, results shown
```

### Scenario 2: Form Interaction
```
1. Navigate to a form page
2. Task: "Fill the email field with test@example.com"
3. Verify: Email field populated
```

### Scenario 3: Multi-Page Navigation
```
1. Navigate to any site
2. Task: "Click the first link on the page"
3. Verify: Navigation occurs, new page loads
```

## Known Limitations

1. **API Key Required**: Real LLM calls require valid OpenAI API key or Ollama setup
2. **Timeout**: Complex tasks may timeout (configurable in .env)
3. **CAPTCHA**: May pause and require manual intervention
4. **Dynamic Content**: Heavy JavaScript sites may need longer wait times

## Debugging

### Enable DevTools

```bash
npm run dev
```

Opens Electron with DevTools for debugging.

### Check Console

In renderer DevTools (F12):
- Look for JavaScript errors
- Check network requests to backend
- Verify API responses

### Check Backend Logs

Backend terminal shows:
- Playwright actions
- LLM requests/responses
- Agent reasoning steps
- Error messages

### Common Issues

**Issue**: Backend shows as disconnected
**Fix**: Ensure `uvicorn app.main:app --port 8000` is running

**Issue**: Tasks don't execute
**Fix**: Check OPENAI_API_KEY in .env or configure Ollama

**Issue**: Screenshots not appearing
**Fix**: Ensure `screenshot_every_step: true` in configs/config.yaml

**Issue**: Slow response
**Fix**: Reduce AGENT_MAX_STEPS in .env for faster testing

## Test Data

### Good Test URLs
- `https://www.google.com` - Search functionality
- `https://example.com` - Simple page for summarization
- `https://httpbin.org/forms/post` - Form testing
- `https://www.wikipedia.org` - Complex content

### Sample Tasks
- "Search for [topic]"
- "Click the [element description]"
- "Fill the [field name] with [value]"
- "Navigate to [page name]"

## Automated Tests

To run the Python backend tests:

```bash
source .venv/bin/activate
pytest tests/
```

## Success Criteria

All three phases should work:
- ✓ Phase 1: Manual URL navigation works
- ✓ Phase 2: Page summarization produces results
- ✓ Phase 3: Natural language tasks execute correctly

## Next Steps

After testing:
1. Document any bugs found
2. Take screenshots of the UI
3. Test on different operating systems
4. Performance testing with complex tasks
5. User experience feedback
