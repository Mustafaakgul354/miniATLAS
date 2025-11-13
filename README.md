# mini-Atlas · LLM-Powered Browser Agent

mini-Atlas is a self-hosted browser automation agent inspired by ChatGPT Atlas. It enables large language models to plan, execute, and verify actions inside a real Chromium instance using the loop **Plan → Act → Observe → Evaluate**. The project ships with a modern monitoring UI, a CLI, and a complete REST API so you can automate web workflows or study agent behaviour end-to-end.

---

## Highlights

- **Reasoning-first automation** – iterative observation, action generation, validation, and feedback.
- **Real browser control** – powered by Playwright; optionally persist session storage.
- **Multiple LLM providers** – OpenAI (GPT-4o-mini), Ollama, and compatible HTTP APIs.
- **Human-aware safeguards** – CAPTCHA detection, sensitive-action validation, network monitors.
- **Rich observability** – live screenshots, structured JSON logging, session timelines.
- **Flexible deployment** – run locally, in Docker, or behind your own API gateway.
- **Desktop application** – Native Electron-based desktop app with intuitive UI for browser automation.

For a tour of the ATLAS interface see `ATLAS_INTERFACE.md`. For the desktop app see `ELECTRON_README.md`. Release notes live in `CHANGELOG_ATLAS.md`, and quick recipes in `QUICKSTART_ATLAS.md`.

---

## Architecture at a Glance

```
                          ┌─────────────────────┐
                          │ Electron Desktop    │
                          │    Application      │
                          └──────────┬──────────┘
                                     │ HTTP
┌───────────────┐      REST / WebSocket      ┌─────────────────────┐
│   Web & CLI   │ ─────────────────────────▶ │ FastAPI Application │
└───────────────┘                            │  (Session control)  │
                                              └──────────┬──────────┘
                                                         │
                                           ┌─────────────▼─────────────┐
                                           │  Agent Loop (reasoning)   │
                                           └─────────────┬─────────────┘
                                                         │
                                ┌────────────────────────▼────────────────────┐
                                │        Playwright Runner (Chromium)          │
                                └────────────────────────┬────────────────────┘
                                                         │
                                             Optional external services
                                             (Redis, MongoDB, custom APIs)
```

---

## Quick Start

### Prerequisites

- Python 3.11 or newer
- Playwright dependencies (`playwright install-deps chromium`)
- OpenAI API key **or** a local Ollama endpoint
- Docker (optional but recommended for production)

### 1. Clone & create a virtual environment

```bash
git clone https://github.com/yourusername/mini-atlas.git
cd mini-atlas
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

### 2. Install runtime dependencies

```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium      # Safe to re-run
```

### 3. Configure environment variables

```bash
cp .env.example .env
# open .env and set OPENAI_API_KEY (or configure Ollama)
```

Key variables to review:

| Variable | Purpose | Example |
|----------|---------|---------|
| `LLM_PROVIDER` | `openai`, `ollama`, or `vllm` | `openai` |
| `OPENAI_API_KEY` | Secret for OpenAI provider | `sk-...` |
| `AGENT_MAX_STEPS` | Max reasoning iterations | `30` |
| `BROWSER` | `headless` or `headed` | `headless` |
| `TIMEZONE` | Browser timezone | `Europe/Istanbul` |

### 4. Launch the development server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` (classic dashboard) or `http://localhost:8000/atlas` (ATLAS split view).

---

## Run with Docker

```bash
# make sure .env exists in the repository root
docker-compose -f docker/docker-compose.yml up -d
```

or build manually:

```bash
docker build -f docker/Dockerfile -t mini-atlas .
docker run -p 8000:8000 --env-file .env mini-atlas
```

`./logs` and `./storage` volumes give you persistent history when `storage_mode` is set to `persistent`. Redis and MongoDB services are provided but optional; enable them in `docker/docker-compose.yml` if you need them.

---

## Configuration Deep Dive

### Environment variables (`.env`)

```ini
LLM_PROVIDER=openai        # openai | ollama | vllm
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini

AGENT_MAX_STEPS=30
AGENT_STEP_TIMEOUT=30      # seconds per step
AGENT_TOTAL_TIMEOUT=300    # seconds per session

BROWSER=headless           # headless | headed
PROXY_URL=                 # http://user:pass@host:port (optional)
USER_AGENT=                # leave blank for Playwright default
TIMEZONE=Europe/Istanbul

API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379/0
MONGO_URL=mongodb://localhost:27017
```

### Advanced tuning (`configs/config.yaml`)

```yaml
agent:
  max_steps: 30
  allow_navigation: true
  screenshot_every_step: true
  vision_enabled: true
  action_schema_strict: true
  wait_after_action_ms: 500

browser:
  default_timeout_ms: 15000
  navigation_timeout_ms: 30000
  storage_mode: ephemeral      # switch to persistent for long sessions
  persistent_dir: ./storage
  locale: tr-TR
  timezone: Europe/Istanbul
  viewport:
    width: 1366
    height: 768

telemetry:
  json_logging: true
  redact_secrets: true
  sink: stdout
```

Environment variables override YAML values at runtime. Extend the schema in `app/config.py` if you need additional switches.

---

## Ways to Run mini-Atlas

### Desktop application (Electron)

**Best for**: Local development, testing, and daily use with a native app experience.

```bash
# Install Node.js dependencies
npm install

# Start the Python backend (in a separate terminal)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Launch the desktop app
npm start
```

Features:
- **Phase 1**: Address bar for manual navigation to any URL
- **Phase 2**: "Summarize Page" button for AI-powered page analysis
- **Phase 3**: Natural language task execution with real-time monitoring
- Real-time screenshots and action history
- Session status monitoring
- Intuitive UI for browser automation

For detailed setup and usage instructions, see `ELECTRON_README.md`.

### Web interfaces

| Interface | URL | Best for | Notes |
|-----------|-----|----------|-------|
| ATLAS split-view | `http://localhost:8000/atlas` | Live monitoring, demos | Real-time screenshot pane with reasoning feed |
| Classic dashboard | `http://localhost:8000/` | Managing lots of sessions | Quick filters, status badges, history |

Workflow:
1. Provide the start URL and one goal per line.
2. Launch the session and observe step updates (≈2s interval).
3. Inspect screenshots, DOM summaries, network events.
4. If a CAPTCHA halts progress, solve it manually and press “Continue” once you’re done.

### Command-line interface

Interactive mode:

```bash
python cli.py
```

Direct mode:

```bash
python cli.py \
  --url "https://example.com/login" \
  --goal "Log in with demo credentials" \
  --goal "Download monthly report" \
  --email "user@example.com" \
  --password "s3cret!" \
  --max-steps 30
```

Flags worth remembering:

- `--url` (required) – initial navigation target
- `--goal` – repeatable; each adds a new objective
- `--email`, `--password` – optional profile credentials
- `--max-steps` – overrides the default limit
- `--base-url` – point the CLI at a remote mini-Atlas instance

The CLI streams live status updates, highlights CAPTCHAs, and mirrors the dashboard summaries.

### REST API

Start a session:

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
        "url": "https://example.com/login",
        "goals": ["Log in", "Open account dashboard"],
        "profile": {"email": "user@example.com", "password": "hunter2"},
        "session_mode": "ephemeral"
      }'
```

Check status:

```bash
curl http://localhost:8000/status/sess_abc123
```

Resume after manual intervention:

```bash
curl -X POST http://localhost:8000/agent/continue/sess_abc123 \
  -H "Content-Type: application/json" \
  -d '{"note": "Solved CAPTCHA at step 4"}'
```

Browse all sessions via `GET /sessions` or fetch the full transcript (screenshots included) with `GET /api/session/{session_id}/full`.

---

## Development Workflow

```bash
# format code
black app/ tests/

# lint and static analysis
ruff app/ tests/

# unit & integration tests
pytest tests/
```

Project layout (abbreviated):

```
mini-atlas/
├── app/
│   ├── main.py              # FastAPI entry point & routes
│   ├── agent_loop.py        # Plan/act/review reasoning core
│   ├── llm_client.py        # Provider abstraction for LLM calls
│   ├── actions.py           # Action execution helpers
│   ├── captcha_handler.py   # Detection plus optional solving
│   ├── playwright_runner.py # Browser and context lifecycle
│   ├── utils/               # Logging, selectors, misc helpers
│   └── templates.py         # HTML for dashboard + ATLAS interface
├── configs/
│   └── config.yaml
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── examples/
│   └── basic_usage.py
├── tests/
├── cli.py
├── requirements.txt
└── README.md
```

Before opening a pull request:
1. Ensure tests pass (`pytest`).
2. Run the agent locally and validate at least one end-to-end session.
3. Update relevant docs (`ATLAS_SUMMARY.md` tracks feature highlights).

---

## Troubleshooting

| Symptom | Likely Cause | Suggested Fix |
|---------|--------------|---------------|
| `OPENAI_API_KEY required` | Missing key when `LLM_PROVIDER=openai` | Provide the key or switch provider |
| Browser exits immediately | Port 8000 busy, or Playwright deps missing | Free the port (`lsof -i :8000`), rerun `playwright install-deps chromium` |
| Repeated CAPTCHA failures | Site demands manual verification | Switch to headed mode, slow down steps, or solve manually then call `/agent/continue/...` |
| Docker memory errors | Chromium shared memory exhausted | Increase `shm_size` or reduce concurrent sessions |
| LLM timeouts | Provider is slow or rate limited | Increase `AGENT_STEP_TIMEOUT`, lower goal complexity, or choose a faster model |

More scenarios and fixes are collected in `ATLAS_SUMMARY.md`. Please share reproductions when reporting bugs.

---

## Security Notes

- Keep `.env` secrets out of version control.
- `validators.py` blocks destructive actions by default; extend it to match your domain rules.
- Run behind authentication if exposing the dashboard to the public internet.
- Enable Redis + rate limiting when operating in multi-tenant environments.

---

## Contributing

We welcome bug reports, feature ideas, and pull requests.

1. Fork the repository.
2. Create a branch: `git checkout -b feature/my-feature`.
3. Make your changes and add tests where possible.
4. Run `pytest` and the linters.
5. Submit a pull request with context and screenshots/logs if relevant.

Check the issue tracker for `good first issue` labels if you are new to the project.

---

## License

mini-Atlas is released under the MIT License. See `LICENSE` for the full text.

---

## Acknowledgements

- Built with **FastAPI**, **Playwright**, and **Loguru**.
- Uses OpenAI GPT models by default, but works with any provider that fits the abstraction.
- Inspired by the broader community of autonomous web agent research.
