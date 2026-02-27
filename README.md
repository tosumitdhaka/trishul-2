# Trishul — FCAPS Simulation, Parsing & Visualization Platform

A lab-grade platform for simulating, ingesting, parsing, normalizing, and visualizing FCAPS
(Fault, Configuration, Accounting, Performance, Security) data from network elements.

## Architecture

- **core-api** — FastAPI app (controller + worker layers in one process)
- **NATS JetStream** — async message bus between HTTP ingest and transformer processing
- **Redis** — JWT blocklist, API key store, rate limiting, dedup cache
- **InfluxDB** — PM (Performance Management) time-series metrics
- **VictoriaLogs** — FM (Fault Management) alarms + structured logs
- **SQLite** — users, API keys, audit log (embedded in core-api)
- **Traefik** — reverse proxy, single host-exposed port (80)

See [`docs/architecture.md`](docs/architecture.md) for full system design, data flows, and user flows.

---

## Quick Start

### Prerequisites
- Docker + Docker Compose v2
- Python 3.12+ (for local dev / running tests)

### 1. Clone and configure
```bash
git clone https://github.com/tosumitdhaka/trishul-2.git
cd trishul-2
cp .env.example .env
```

Edit `.env` and set:
```env
JWT_SECRET=<run: python -c "import secrets; print(secrets.token_hex(32))">
INFLUX_TOKEN=<run: python -c "import secrets; print(secrets.token_hex(24))">
```

### 2. Start all containers
```bash
make up
# or: docker compose up --build -d
```

Services come up in dependency order. Check status:
```bash
make ps
# or: docker compose ps
```

### 3. Verify
```bash
curl http://localhost/health
# Expected: {"status": "healthy", ...}

curl http://localhost/docs
# OpenAPI UI
```

---

## Development Setup (Tests + Local Run)

### Install dependencies
```bash
# Create and activate virtualenv first (recommended)
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

# Install app + dev dependencies
make install-dev
# equivalent: pip install -e ".[dev]"
```

### Run tests (no Docker needed)
```bash
make test
# or: pytest tests/ -v
```

### Run with coverage
```bash
make test-cov
```

### Run locally (Docker infra up, app local)
```bash
make up          # start infra containers only
make run-local   # run FastAPI with --reload
```

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install app dependencies only |
| `make install-dev` | Install app + dev dependencies (pytest, ruff, mypy) |
| `make up` | Build and start all containers (detached) |
| `make up-fg` | Start containers in foreground |
| `make down` | Stop containers |
| `make down-v` | Stop containers and remove volumes |
| `make restart` | Restart core-api only |
| `make logs` | Tail core-api logs |
| `make logs-all` | Tail all container logs |
| `make test` | Run all tests |
| `make test-cov` | Run tests with coverage report |
| `make test-fast` | Run tests, stop on first failure |
| `make lint` | Ruff lint check |
| `make fmt` | Ruff auto-format |
| `make typecheck` | Mypy type check |
| `make shell` | Shell into core-api container |
| `make run-local` | Run FastAPI locally with hot reload |
| `make clean` | Remove `__pycache__`, `.pytest_cache`, build artefacts |

---

## Project Structure

```
trishul-2/
├── core/                    # Controller + shared foundation
│   ├── app.py               # FastAPI factory + lifespan
│   ├── config/settings.py   # All env var config (pydantic-settings)
│   ├── auth/                # JWT, API keys, RBAC middleware
│   ├── bus/                 # NATS client, stream provisioner, publisher
│   ├── storage/             # InfluxDB + VictoriaLogs adapters
│   ├── middleware/          # RateLimit, Logging, ErrorHandler
│   ├── models/              # MessageEnvelope, TrishulResponse
│   ├── health/              # GET /health
│   └── notifications/       # NATS fcaps.done.> → storage dispatch
├── transformer/             # Pipeline stages (ABCs in Phase 1, impls in Phase 2)
│   ├── base.py              # Reader/Decoder/Normalizer/Encoder/Writer ABCs
│   ├── pipeline.py          # TransformPipeline + PipelineRegistry
│   └── normalizer.py        # FCAPSNormalizer (implemented, shared)
├── plugins/
│   └── webhook/             # Reference plugin (Phase 1)
├── tests/                   # pytest suite
├── docs/                    # Architecture + phase docs
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── Makefile
```

---

## API Endpoints (Phase 1)

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | None | Login → JWT token pair |
| POST | `/api/v1/auth/refresh` | Refresh JWT | New access token |
| POST | `/api/v1/auth/logout` | Bearer JWT | Blocklist token |
| GET | `/api/v1/auth/me` | Bearer JWT | Current user info |
| POST | `/api/v1/auth/apikeys` | admin | Create API key |
| GET | `/api/v1/auth/apikeys` | admin | List API keys |
| DELETE | `/api/v1/auth/apikeys/{id}` | admin | Revoke API key |

### Webhook Plugin
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/webhook/receive` | operator | Ingest event → 202 |
| POST | `/api/v1/webhook/send` | operator | POST to target URL |
| POST | `/api/v1/webhook/simulate` | operator | Generate synthetic events |
| GET | `/api/v1/webhook/status/{id}` | operator | Envelope status |
| GET | `/api/v1/webhook/health` | None | Plugin health |

### Platform
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Full dependency health |
| GET | `/docs` | None | OpenAPI UI |

---

## Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 — Core Foundation | 🟡 In Progress | Framework, auth, bus, storage, webhook plugin |
| 2 — Transformer Engine | 🔵 Design Frozen | Decoders, encoders, readers, writers |
| 3 — Protocol Plugins | ⚪ Not Started | SNMP, VES, Protobuf, Avro, SFTP |
| 4 — Shell UI | ⚪ Not Started | React + Module Federation dashboard |
