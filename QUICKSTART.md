# Quick Start Guide - mini-Atlas Desktop App

## 🚀 5-Minute Setup

### Step 1: Prerequisites
```bash
# Check versions
node --version   # Need 16+
python3 --version # Need 3.11+
```

### Step 2: Install Dependencies

**Python (Backend):**
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

**Node.js (Desktop App):**
```bash
npm install
```

### Step 3: Configure

```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-key-here
```

### Step 4: Run

**Terminal 1 - Start Backend:**
```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Desktop App:**
```bash
npm start
```

Or use the startup script:
```bash
./start-desktop.sh    # Linux/Mac
start-desktop.bat     # Windows
```

## 🎯 Quick Usage

### Phase 1: Navigate
1. Enter URL: `https://www.google.com`
2. Click **"Go"**
3. Wait for page to load

### Phase 2: Summarize
1. Navigate to any page
2. Click **"Summarize Page"**
3. View AI summary in left panel

### Phase 3: Execute Task
1. Navigate to starting page
2. Enter task: `"Search for Python tutorials"`
3. Click **"Execute Task"**
4. Watch the agent work!

## 📚 Full Documentation

- **Setup & Usage**: `ELECTRON_README.md`
- **Testing Guide**: `TESTING.md`
- **UI Overview**: `UI_OVERVIEW.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`

## ⚡ Quick Test

```bash
# Start backend (Terminal 1)
uvicorn app.main:app --port 8000

# Run integration test (Terminal 2)
python test_electron_integration.py
# Expected: 6/6 tests passing ✅
```

## 🐛 Troubleshooting

**Backend not connecting?**
```bash
# Check if backend is running
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

**Port 8000 busy?**
```bash
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Missing dependencies?**
```bash
# Python
pip install -r requirements.txt
playwright install chromium

# Node.js
npm install
```

## 🎨 Example Tasks

Try these natural language tasks:

1. **Simple Search**
   ```
   Search for "Python tutorials"
   ```

2. **Multi-Step**
   ```
   Search for GitHub and click the first result
   ```

3. **Form Interaction**
   ```
   Fill the email field with test@example.com
   ```

## 📞 Support

- Check `TESTING.md` for detailed test scenarios
- Review `ELECTRON_README.md` for configuration options
- See `UI_OVERVIEW.md` for interface documentation

## ⚙️ Configuration

### Backend (.env)
```ini
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
BROWSER=headless
AGENT_MAX_STEPS=30
```

### Desktop App
```bash
# Change backend URL
BACKEND_URL=http://localhost:8000 npm start
```

## ✅ Success Indicators

- ✓ "Backend Connected" badge is green
- ✓ Session ID appears after navigation
- ✓ Screenshots update automatically
- ✓ Action history populates with steps

## 🔧 Development Mode

```bash
# Run with DevTools open
npm run dev
```

---

**Ready to go? Run:** `./start-desktop.sh` or `npm start`
