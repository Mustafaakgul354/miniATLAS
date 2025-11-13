# mini-Atlas Desktop - Electron Application

Native desktop wrapper for mini-Atlas browser agent. The desktop app communicates with the existing Python FastAPI backend via REST API.

## Architecture

```
Electron (UI) → HTTP → FastAPI → Playwright → Chromium
```

The desktop app polls backend endpoints (`/run`, `/status`, `/api/session/{id}/full`) every 2 seconds. The backend handles all LLM calls and browser automation unchanged.

## Prerequisites

- Node.js 18+ and npm
- Python backend running on port 8000
- Electron dependencies installed

## Installation

```bash
# Install Node.js dependencies
npm install

# Make sure Python backend is running
# Terminal 1:
uvicorn app.main:app --port 8000
```

## Usage

### Development Mode

```bash
# Terminal 1: Start backend
uvicorn app.main:app --port 8000

# Terminal 2: Launch desktop app
npm start
```

### Production Build

```bash
# Build for current platform
npm run build

# Output will be in dist/ directory
```

## Features

### Phase 1: Navigation

- Address bar + Go button navigates via `POST /run` with single-step goal
- Session status polling updates UI every 2s
- Real-time screenshot display

### Phase 2: Page Summarization

- Creates backend session with summarization goal
- Polls until completion
- Extracts reasoning from step data
- Displays page summary

### Phase 3: Task Execution

- Submits natural language task to agent loop
- Real-time display of:
  - Screenshots
  - Action history
  - Agent reasoning
- Multi-step workflow execution

## Example Usage

1. **Navigation**: Enter URL `https://example.com` → Click "Go"
2. **Summarization**: Enter URL → Click "Summarize"
3. **Task Execution**: Enter task `"Search for Playwright automation and click first result"` → Click "Go"

The agent executes multi-step workflow with live updates.

## Project Structure

```
mini-atlas/
├── electron/
│   ├── main.js          # IPC handlers, backend API client
│   ├── preload.js       # Context bridge
│   └── renderer/
│       ├── index.html   # UI structure
│       ├── styles.css   # Styling
│       └── app.js       # UI logic
├── package.json         # Electron dependencies
└── tests/
    └── test_electron_integration.py  # Backend endpoint tests
```

## Backend Endpoints Used

1. `GET /health` - Health check
2. `POST /run` - Start session
3. `GET /status/{session_id}` - Get session status
4. `GET /api/session/{session_id}/full` - Get full session data
5. `POST /stop/{session_id}` - Stop session
6. `GET /sessions` - List all sessions

## Configuration

Backend URL can be configured via environment variable:

```bash
BACKEND_URL=http://localhost:8000 npm start
```

Default: `http://localhost:8000`

## Testing

Run integration tests:

```bash
pytest tests/test_electron_integration.py -v
```

All 6 backend endpoints are tested.

## Cross-Platform Support

- ✅ Windows
- ✅ macOS
- ✅ Linux

## Security

- Context isolation enabled
- Node integration disabled
- Secure IPC communication via context bridge
- No security vulnerabilities (CodeQL verified)

## Troubleshooting

### Backend Not Connected

- Ensure Python backend is running: `uvicorn app.main:app --port 8000`
- Check backend URL in status bar
- Verify firewall settings

### Session Not Starting

- Check backend logs for errors
- Verify OpenAI API key is set
- Check network connectivity

### Screenshots Not Displaying

- Ensure backend is generating screenshots
- Check browser console for errors
- Verify session is in "running" state

## License

MIT License - See LICENSE file

