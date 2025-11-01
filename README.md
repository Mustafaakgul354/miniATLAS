# mini-Atlas: LLM-Powered Browser Agent

mini-Atlas is a self-hosted, modular browser automation agent that replicates ChatGPT Atlas functionality. It enables an LLM (GPT-4o-mini, Llama-3, etc.) to complete tasks through human-like interactions on a real browser using a reasoning loop: **Plan → Act → Observe → Evaluate**.

## Features

- **LLM-Based Reasoning**: Autonomous decision-making through observe → reason → act → validate cycles
- **Real Browser Interaction**: Playwright integration with Chromium for authentic web interactions
- **Multi-Provider LLM Support**: Works with OpenAI, Ollama, and other providers
- **CAPTCHA Handling**: Autonomous CAPTCHA detection and solving with human-in-the-loop fallback
- **Network Validation**: Backend response verification via network event monitoring
- **Security Guardrails**: Built-in validation for sensitive actions
- **Session Management**: Ephemeral or persistent browser sessions
- **Web Dashboard**: Beautiful web UI to view sessions, steps, and outputs in real-time
- **CLI Tool**: Interactive and direct command-line interface for easy usage
- **Modular Architecture**: Clean separation of concerns with FastAPI + Playwright

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, recommended)
- OpenAI API key (or local Ollama installation)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mini-atlas.git
cd mini-atlas
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings (especially OPENAI_API_KEY)
```

5. Run the server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

6. Open the web dashboard:
```
http://localhost:8000
```

## Web Interface

mini-Atlas includes a modern web dashboard for monitoring and managing agent sessions:

- **Dashboard**: View all active and completed sessions
- **Session Detail**: See real-time step-by-step progress with screenshots
- **Action History**: Track all actions taken by the agent
- **CAPTCHA Handling**: Visual indicators and continue buttons for CAPTCHA interruptions
- **Real-time Updates**: Auto-refreshing status for active sessions

### Using the Web UI

1. **Start a Session**: Fill in the URL and goals on the dashboard (or use CLI: `python cli.py`)
2. **Monitor Progress**: Click on any session to see detailed step-by-step execution
3. **View Screenshots**: Each step includes screenshots (if enabled) - click to enlarge
4. **Handle CAPTCHAs**: If a CAPTCHA is detected, solve it manually and click "Devam Et" (Continue)
5. **Review Actions**: See what the agent did at each step with reasoning and results

**Note:** Web arayüzünde dashboard'da CLI kullanım bilgileri de yer almaktadır.

### Docker Setup

Using Docker Compose (recommended):

```bash
docker-compose -f docker/docker-compose.yml up -d
```

Build and run manually:

```bash
docker build -f docker/Dockerfile -t mini-atlas .
docker run -p 8000:8000 --env-file .env mini-atlas
```

## Usage

mini-Atlas'i kullanmanın üç yolu var:

1. **Web Arayüzü** - Tarayıcıdan http://localhost:8000 adresine gidin
2. **CLI (Komut Satırı)** - İnteraktif veya direkt mod
3. **API** - REST API ile programatik kullanım

### CLI (Komut Satırı) Kullanımı

mini-Atlas, kullanımı kolay bir CLI tool ile birlikte gelir. CLI, URL ve hedeflerinizi belirtmenizi sağlar ve session'ı otomatik olarak başlatır ve izler.

#### İnteraktif Mod

CLI size URL ve hedeflerinizi adım adım sorar:

```bash
python cli.py
```

Örnek çıktı:
```
🤖 mini-Atlas Browser Agent

Başlangıç URL'i [https://www.example.com]: https://example.com/login
Hedeflerinizi belirtin (her hedef için Enter'a basın, bitirmek için boş bırakın):
  Hedef 1: Login ol
  Hedef 2: Dashboard'a git
  Hedef 3: [Enter]

Oturum için profil bilgisi eklemek istiyor musunuz? [y/N]: y
  Email: user@example.com
  Şifre: ****

Maksimum adım sayısı [20]: 30
```

#### Direkt Mod

Tüm parametreleri komut satırından direkt belirtebilirsiniz:

```bash
python cli.py \
  --url "https://example.com/login" \
  --goal "Login ol" \
  --goal "Dashboard'a git" \
  --email "user@example.com" \
  --password "securepassword" \
  --max-steps 30
```

**CLI Parametreleri:**

- `--url` - Başlangıç URL'i (zorunlu)
- `--goal` - Hedef (birden fazla eklenebilir, zorunlu)
- `--email` - Profil email adresi (opsiyonel)
- `--password` - Profil şifresi (opsiyonel)
- `--max-steps` - Maksimum adım sayısı (varsayılan: 20)
- `--base-url` - API base URL (varsayılan: http://localhost:8000)

**CLI Özellikleri:**

- ✅ İnteraktif ve direkt mod desteği
- ✅ Gerçek zamanlı session izleme
- ✅ Renkli ve okunabilir çıktı (rich kütüphanesi)
- ✅ CAPTCHA tespiti ve devam etme desteği
- ✅ Otomatik durum güncellemeleri

**Not:** CLI kullanmadan önce server'ın çalıştığından emin olun:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Kullanımı

### Starting an Agent Session

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/login",
    "goals": ["Login to the website", "Navigate to dashboard"],
    "profile": {
      "email": "user@example.com",
      "password": "securepassword"
    },
    "session_mode": "ephemeral"
  }'
```

Response:
```json
{
  "session_id": "sess_abc123",
  "status": "running"
}
```

### Checking Session Status

```bash
curl http://localhost:8000/status/sess_abc123
```

Response:
```json
{
  "session_id": "sess_abc123",
  "state": "running",
  "current_url": "https://example.com/dashboard",
  "steps_done": 5,
  "last_action": {
    "action": "click",
    "selector": "button[text='Submit']"
  },
  "has_captcha": false
}
```

### Handling CAPTCHAs

When a CAPTCHA is detected:

1. The agent will first attempt autonomous solving (if vision is enabled)
2. If that fails, status will show `waiting_human`
3. Solve the CAPTCHA manually in a browser
4. Continue the session:

```bash
curl -X POST http://localhost:8000/agent/continue/sess_abc123 \
  -H "Content-Type: application/json" \
  -d '{"note": "CAPTCHA solved manually"}'
```

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# LLM Provider
LLM_PROVIDER=openai              # openai | ollama | vllm
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Agent Behavior
AGENT_MAX_STEPS=30               # Maximum steps per session
AGENT_STEP_TIMEOUT=30            # Timeout per step (seconds)
AGENT_TOTAL_TIMEOUT=300          # Total session timeout (seconds)

# Browser Settings
BROWSER=headless                 # headless | headed
PROXY_URL=http://proxy:8080      # Optional proxy
USER_AGENT=                      # Custom user agent
TIMEZONE=Europe/Istanbul         # Browser timezone

# Server
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Configuration File

Advanced settings in `configs/config.yaml`:

```yaml
agent:
  max_steps: 30
  screenshot_every_step: true
  vision_enabled: true
  wait_after_action_ms: 500

browser:
  default_timeout_ms: 15000
  navigation_timeout_ms: 30000
  viewport:
    width: 1366
    height: 768

security:
  block_file_dialogs: true
  confirm_sensitive_actions: true
```

## API Reference

### Endpoints

- `POST /run` - Start new agent session
- `GET /status/{session_id}` - Get session status
- `POST /stop/{session_id}` - Stop running session
- `POST /agent/continue/{session_id}` - Continue after human intervention
- `GET /sessions` - List all sessions
- `DELETE /sessions/{session_id}` - Delete session
- `GET /health` - Health check

### Action Schema

The agent generates actions in JSON format:

```json
// Click
{"action": "click", "selector": "button[text='Submit']"}

// Fill form field
{"action": "fill", "selector": "input[name='email']", "value": "user@example.com"}

// Navigate
{"action": "goto", "url": "https://example.com/page"}

// Wait for element
{"action": "wait_for_selector", "selector": "div.success", "timeout_ms": 5000}

// Complete session
{"action": "done", "summary": "Successfully logged in and navigated to dashboard"}
```

## Architecture

```
┌─────────────────────┐
│   Client/API        │
└──────────┬──────────┘
           │
┌──────────▼──────────┐     ┌─────────────────┐
│   FastAPI Server    │◄───►│     Redis       │
│   (Controller)      │     │   (Optional)    │
└──────────┬──────────┘     └─────────────────┘
           │
┌──────────▼──────────┐
│    Agent Loop       │
│ (Reasoning Engine)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    Playwright       │
│  (Browser Control)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Chromium Browser   │
└─────────────────────┘
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
ruff app/ tests/

# Type checking (optional)
mypy app/
```

### Project Structure

```
mini-atlas/
├── app/
│   ├── main.py              # FastAPI application
│   ├── agent_loop.py        # Core reasoning loop
│   ├── playwright_runner.py # Browser management
│   ├── actions.py           # Action execution
│   ├── llm_client.py        # LLM integration
│   ├── captcha_handler.py   # CAPTCHA detection/handling
│   ├── validators.py        # Security guardrails
│   ├── templates.py        # Web UI templates
│   └── utils/               # Helper utilities
├── configs/
│   └── config.yaml          # Application config
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── examples/
│   └── basic_usage.py       # API usage examples
├── tests/                   # Test suite
├── cli.py                   # CLI tool (interactive/direct mode)
├── requirements.txt
└── README.md
```

## Security Considerations

- **Credentials**: Never embed credentials in LLM prompts
- **Sensitive Actions**: Payment and deletion actions require confirmation
- **Domain Restrictions**: Configure allowed/blocked domains
- **Network Isolation**: Use Docker for sandboxing
- **Rate Limiting**: Implement appropriate delays

## Troubleshooting

### Common Issues

1. **Playwright installation failed**
   ```bash
   playwright install --with-deps chromium
   ```

2. **CAPTCHA loop**
   - Reduce request speed
   - Use better proxies
   - Enable headed mode for debugging

3. **Memory issues in Docker**
   - Increase `shm_size` in docker-compose.yml
   - Limit concurrent sessions

4. **LLM timeouts**
   - Increase `AGENT_STEP_TIMEOUT`
   - Use faster LLM model

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by ChatGPT's Atlas browser agent
- Built with FastAPI and Playwright
- Uses OpenAI GPT models (or compatible alternatives)
