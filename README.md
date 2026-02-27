# Trishul — FCAPS Simulation, Parsing & Visualization Platform

A lab-grade platform for simulating, ingesting, parsing, normalizing, and visualizing FCAPS
(Fault, Configuration, Accounting, Performance, Security) data from network elements.

## Architecture

- **core-api** — FastAPI app (controller + worker layers in one process)
- **NATS JetStream** — async message bus between HTTP ingest and transformer processing
- **Redis** — JWT blocklist, API key store, rate limiting, dedup cache
- **InfluxDB** — PM (Performance Management) time-series metrics
- **VictoriaLogs** — FM (Fault Management) alarms + structured logs
- **SQLite** — users, API keys, audit log, schema registry (embedded in core-api)
- **Traefik** — reverse proxy, single host-exposed port (80)

See [`docs/architecture.md`](docs/architecture.md) for full system design.

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
```

### 3. Verify
```bash
curl http://localhost/health
curl http://localhost/docs       # OpenAPI UI
```

---

## Development Setup

```bash
python -m venv .venv && source .venv/bin/activate
make install-dev
make test           # 75 passed, no Docker needed
make test-cov       # with coverage report
```

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make install-dev` | Install app + dev dependencies |
| `make up` | Build and start all containers |
| `make down` | Stop containers |
| `make down-v` | Stop containers + remove volumes |
| `make logs` | Tail core-api logs |
| `make logs-all` | Tail all container logs |
| `make test` | Run all tests |
| `make test-cov` | Tests with coverage report |
| `make test-fast` | Stop on first failure |
| `make lint` | Ruff lint |
| `make fmt` | Ruff auto-format |
| `make typecheck` | Mypy |
| `make shell` | Shell into core-api container |
| `make run-local` | FastAPI with hot reload |
| `make clean` | Remove caches + build artefacts |

---

## API Endpoints

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | — | Login → JWT pair |
| POST | `/api/v1/auth/refresh` | Refresh JWT | New access token |
| POST | `/api/v1/auth/logout` | Bearer | Blocklist token |
| GET | `/api/v1/auth/me` | Bearer | Current user |
| POST | `/api/v1/auth/apikeys` | admin | Create API key |
| GET | `/api/v1/auth/apikeys` | admin | List API keys |
| DELETE | `/api/v1/auth/apikeys/{id}` | admin | Revoke API key |

### Protocol Plugins (all 6 follow same pattern)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/{proto}/receive` | Ingest event → 202 |
| POST | `/api/v1/{proto}/simulate` | Generate synthetic events |
| GET | `/api/v1/{proto}/status/{id}` | Envelope status |
| GET | `/api/v1/{proto}/health` | Plugin health |

`{proto}` = `webhook` \| `snmp` \| `ves` \| `protobuf` \| `avro` \| `sftp`

### Transformer Engine
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/transform/run` | Sync pipeline → envelope |
| POST | `/api/v1/transform/submit` | Async job → job_id |
| GET | `/api/v1/transform/jobs/{id}` | Job status |
| GET | `/api/v1/transform/stages` | Registered stages |

### Schema Registry
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/schemas` | Register Avro/Protobuf schema |
| GET | `/api/v1/schemas` | List all schemas |
| GET | `/api/v1/schemas/{id}` | Get schema |
| DELETE | `/api/v1/schemas/{id}` | Remove schema |

### Platform
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Full dependency health |
| GET | `/docs` | OpenAPI UI |

---

## Project Structure

```
trishul-2/
├── core/                    # Controller + shared foundation
│   ├── app.py               # FastAPI factory + lifespan
│   ├── auth/                # JWT, API keys, RBAC middleware
│   ├── bus/                 # NATS client, streams, publisher
│   ├── storage/             # InfluxDB + VictoriaLogs adapters
│   ├── middleware/          # RateLimit, Logging, ErrorHandler
│   ├── models/              # MessageEnvelope, TrishulResponse
│   ├── health/              # GET /health
│   └── notifications/       # NATS fcaps.done.> → storage
├── transformer/             # Transformer Engine (Phase 2)
│   ├── readers/             # file, webhook, http_poll, nats, sftp
│   ├── decoders/            # json, csv, xml, ves, snmp, protobuf, avro
│   ├── encoders/            # json, csv, protobuf, avro
│   ├── writers/             # nats, influxdb, victorialogs, webhook, sftp, csv
│   ├── pipeline.py          # TransformPipeline + PipelineRegistry
│   ├── normalizer.py        # FCAPSNormalizer
│   ├── schema_registry.py   # SQLite Avro/Protobuf schema store
│   └── router.py            # /api/v1/transform/* + /api/v1/schemas/*
├── plugins/                 # Protocol plugins (Phase 3)
│   ├── shared/              # SimulatorBase ABC
│   ├── webhook/             # JSON/HTTP plugin
│   ├── snmp/                # SNMP v2c trap plugin
│   ├── ves/                 # VES 7.x plugin
│   ├── protobuf/            # Protobuf/gNMI plugin
│   ├── avro/                # Apache Avro plugin
│   └── sftp/                # SFTP file plugin
├── ui/
│   ├── shell/               # React host app (Phase 4)
│   ├── mfe/                 # MFE remotes (Phase 5)
│   │   ├── snmp-ui/         # SNMP plugin UI
│   │   ├── ves-ui/          # VES plugin UI
│   │   ├── webhook-ui/      # Webhook plugin UI
│   │   ├── protobuf-ui/     # Protobuf/gNMI plugin UI
│   │   ├── sftp-avro-ui/    # SFTP + Avro plugin UI (shared container)
│   │   ├── fm-console/      # FM Alarm Console MFE
│   │   ├── pm-dashboard/    # PM Dashboard MFE
│   │   └── log-viewer/      # Log Viewer MFE
│   └── shared/              # Shared types / utils
├── tests/                   # pytest suite (75 tests)
├── docs/                    # Phase docs + architecture
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── Makefile
└── .env.example
```

---

## Phase Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 — Core Foundation | ✅ Complete | FastAPI, auth, NATS, storage, middleware |
| 2 — Transformer Engine | ✅ Complete | All readers, decoders, encoders, writers, schema registry |
| 3 — Protocol Plugins | ✅ Complete | webhook, snmp, ves, protobuf, avro, sftp |
| 4 — Shell UI | ✅ Complete | React + Module Federation shell, dashboard, live event feed |
| 5 — Protocol UIs | 🔵 In Progress | Per-plugin React MFEs with live WS feeds |
| 6 — Observability | ⚪ Queued | Prometheus, Grafana, distributed tracing |
