# Quick Start Guide - mini-Atlas Desktop

5-minute setup guide for mini-Atlas Electron desktop application.

## Step 1: Install Dependencies

```bash
# Install Node.js dependencies
npm install
```

## Step 2: Start Backend

```bash
# Terminal 1: Start Python backend
cd mini-atlas
source .venv/bin/activate  # or your virtual environment
uvicorn app.main:app --port 8000
```

Wait for: `Application startup complete.`

## Step 3: Launch Desktop App

```bash
# Terminal 2: Start Electron app
npm start
```

## Step 4: Use the App

### Navigation (Phase 1)
1. Enter URL: `https://example.com`
2. Click "Go"
3. Watch real-time screenshot updates

### Summarization (Phase 2)
1. Enter URL: `https://example.com`
2. Click "Summarize"
3. Wait for completion
4. View summary in activity panel

### Task Execution (Phase 3)
1. Enter task: `"Search for Playwright automation and click first result"`
2. Click "Go"
3. Watch agent execute multi-step workflow
4. View reasoning and actions in real-time

## Troubleshooting

**Backend not connected?**
- Check Terminal 1 for errors
- Verify port 8000 is not in use
- Check firewall settings

**Session not starting?**
- Verify OpenAI API key in `.env`
- Check backend logs
- Ensure backend is healthy (green indicator)

**Need help?**
- See `ELECTRON_README.md` for detailed documentation
- Check `TESTING.md` for test scenarios

## Next Steps

- Read `ELECTRON_README.md` for architecture details
- Check `UI_OVERVIEW.md` for interface documentation
- Review `IMPLEMENTATION_SUMMARY.md` for technical details

