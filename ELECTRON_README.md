# mini-Atlas Desktop Application

Electron-based desktop browser agent interface for mini-Atlas.

## Prerequisites

1. **Python Backend**: The desktop app requires the mini-Atlas Python backend to be running
2. **Node.js**: Version 16 or higher

## Setup

### 1. Install Node.js dependencies

```bash
npm install
```

### 2. Start the Python backend

In a separate terminal, start the mini-Atlas backend server:

```bash
# From the project root
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium

# Copy and configure .env
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or configure Ollama

# Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Launch the desktop app

```bash
npm start
```

Or in development mode with DevTools:

```bash
npm run dev
```

## Features

### Phase 1: Basic Browser Control ✓
- Address bar for manual URL navigation
- "Go" button to navigate to websites
- Integration with Python backend via REST API

### Phase 2: AI Page Analysis ✓
- "Summarize Page" button to get AI-generated page summaries
- Displays page analysis in the UI
- Real-time status updates

### Phase 3: Interactive AI Agent ✓
- Natural language task input field
- Execute complex multi-step tasks
- Real-time action monitoring
- Screenshot display
- Action history with reasoning
- Step-by-step progress tracking

## Usage

### Basic Navigation
1. Enter a URL in the address bar (e.g., `https://www.google.com`)
2. Click "Go" or press Enter
3. The backend will navigate to the page

### Page Summarization
1. Navigate to any webpage
2. Click "Summarize Page"
3. Wait for the AI to analyze the page
4. View the summary in the left panel

### Task Execution
1. Navigate to a starting page
2. Enter a natural language task in the task input field
   - Example: "Search for Playwright automation and click the first result"
   - Example: "Find the login button and click it"
3. Click "Execute Task" or press Enter
4. Monitor progress in real-time:
   - View agent reasoning
   - See action history
   - Watch screenshots update
   - Track step count and status

## Architecture

```
┌─────────────────────┐
│  Electron Desktop   │
│   (Renderer UI)     │
└──────────┬──────────┘
           │ IPC
┌──────────▼──────────┐
│  Main Process       │
│  (REST API Client)  │
└──────────┬──────────┘
           │ HTTP
┌──────────▼──────────┐
│  Python Backend     │
│  (FastAPI + Agent)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Playwright        │
│   (Chromium)        │
└─────────────────────┘
```

### Components

- **Main Process** (`electron/main.js`): Handles IPC communication and backend API calls
- **Preload Script** (`electron/preload.js`): Secure bridge between renderer and main process
- **Renderer** (`electron/renderer/`): UI implementation with HTML/CSS/JS

### API Integration

The desktop app communicates with the Python backend through these endpoints:

- `POST /run` - Start a new agent session
- `GET /status/{session_id}` - Get session status
- `GET /api/session/{session_id}/full` - Get full session data with steps
- `GET /health` - Check backend health

## Configuration

### Backend URL

By default, the app connects to `http://localhost:8000`. To change this, set the `BACKEND_URL` environment variable:

```bash
BACKEND_URL=http://your-server:8000 npm start
```

### Python Backend Settings

Configure the backend behavior in `.env`:

```ini
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
BROWSER=headless  # or 'headed' to see the browser
AGENT_MAX_STEPS=30
```

## Troubleshooting

### "Backend Disconnected" Warning

**Problem**: Red status badge showing backend is not connected

**Solution**: 
1. Make sure the Python backend is running: `uvicorn app.main:app --port 8000`
2. Check that port 8000 is not blocked by a firewall
3. Verify the backend is accessible at `http://localhost:8000/health`

### Tasks Not Executing

**Problem**: Tasks fail or don't start

**Solution**:
1. Ensure you've navigated to a URL first
2. Check that your `.env` file has a valid `OPENAI_API_KEY` or Ollama is configured
3. Check the backend logs for errors
4. Try a simpler task first to verify the connection

### Screenshots Not Showing

**Problem**: No screenshots appear in the browser view

**Solution**:
1. Check `configs/config.yaml` has `screenshot_every_step: true`
2. Wait for the agent to complete at least one step
3. Refresh the status with the "Refresh Status" button

### Development Mode

To see detailed logs and debug the application:

```bash
npm run dev
```

This opens the Electron DevTools automatically.

## Development

### Project Structure

```
electron/
├── main.js              # Main process (backend communication)
├── preload.js           # Security bridge
└── renderer/
    ├── index.html       # UI layout
    ├── styles.css       # Styling
    └── renderer.js      # UI logic and event handling
```

### Making Changes

1. Edit files in `electron/` directory
2. Restart the app to see changes
3. Use DevTools (F12 in dev mode) to debug renderer issues

## Security Notes

- The app uses `contextIsolation: true` for security
- Node.js APIs are not directly accessible in the renderer
- All backend communication goes through the main process
- Sensitive data (API keys) is kept in the backend, not the Electron app

## License

MIT License - See LICENSE file for details
