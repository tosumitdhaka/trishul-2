# Phase 1 — Core Foundation

**Status**: 🔵 In Design  
**Depends on**: None  
**Prerequisite for**: Phase 2, Phase 3, Phase 4

---

## Goal

Build the skeleton of Trishul: the FastAPI app factory, plugin registry, authentication layer, NATS JetStream bus, storage adapters, shared models, and docker-compose stack. All subsequent phases plug into this foundation without modifying it.

---

## Stack (Lab Mode)

| Component | Technology | RAM Target |
|-----------|------------|------------|
| API Framework | FastAPI 0.115+ | ~80–120MB |
| Auth (JWT) | python-jose + passlib[bcrypt] | ~5MB |
| Auth (state) | Redis 7 Alpine | ~20MB |
| User store | SQLite + SQLModel | ~0MB |
| Message bus | NATS JetStream 2.10 Alpine | ~15–25MB |
| Hot cache / dedup | Redis 7 Alpine (shared) | — |
| PM Metrics store | InfluxDB 2 OSS Alpine | ~80–150MB |
| FM / Log store | VictoriaLogs latest | ~30–50MB |
| Reverse proxy | Traefik v3 | ~30MB |
| **Total estimate** | | **~350–450MB** |

---

## Directory Structure

```
trishul/
├── core/
│   ├── app.py                  ← FastAPI app factory + lifespan + plugin loader
│   ├── plugin_registry.py      ← FCAPSPlugin base class + PluginRegistry
│   ├── models/
│   │   ├── envelope.py         ← MessageEnvelope, FCAPSDomain
│   │   └── base.py             ← Shared Pydantic base model config
│   ├── auth/
│   │   ├── middleware.py       ← AuthMiddleware (JWT + API Key)
│   │   ├── jwt_handler.py      ← encode / decode JWT
│   │   ├── apikey_store.py     ← Redis API key CRUD
│   │   └── models.py           ← User, APIKey SQLModel tables
│   ├── bus/
│   │   ├── nats_client.py      ← NATS connection + JetStream setup
│   │   └── streams.py          ← Stream/consumer definitions
│   ├── storage/
│   │   ├── base.py             ← MetricsStore + EventStore ABC
│   │   ├── influxdb.py         ← InfluxDBMetrics impl
│   │   ├── victorialogs.py     ← VictoriaLogsEvents impl
│   │   └── factory.py          ← get_stores(mode) factory
│   ├── config/
│   │   └── settings.py         ← pydantic-settings BaseSettings
│   └── notifications/
│       └── service.py          ← NATS → WebSocket broadcaster
│
├── plugins/
│   └── webhook/                ← Reference plugin (simplest I/O)
│       ├── __init__.py         ← exports `plugin`
│       ├── router.py
│       ├── models.py
│       └── config.py
│
├── docker-compose.yml
├── .env.example
└── Dockerfile
```

---

## Authentication Design

### Dual-Mode Auth
- **JWT**: Human users / UI clients. 15min access token + 7d refresh token.
- **API Key**: Machine clients / plugin-to-plugin. Stored as Redis hash `apikey:{hash}` → `{client_id, roles, scopes}`.

### Middleware Flow
```
Request
  → skip if PUBLIC_PATH (/health, /metrics, /docs, /openapi.json, /api/v1/auth/login)
  → check Authorization: Bearer <JWT>  → decode_jwt() → 401 if invalid/expired
  → check X-API-Key: <key>             → Redis lookup  → 401 if not found
  → attach request.state.user + request.state.auth_type
  → RBAC scope check vs route tag
  → call_next(request)
```

### RBAC Roles
```
admin        → full access
operator     → read + simulate (no user management)
viewer       → read only
plugin:{x}   → scoped to one protocol plugin
```

---

## NATS JetStream — Stream Definitions

| Stream | Subject | Retention | Storage | TTL / Policy |
|--------|---------|-----------|---------|-------|
| `FCAPS_INGEST` | `fcaps.ingest.>` | Limits | File | 1hr / 10k msgs |
| `FCAPS_PROCESS` | `fcaps.process.>` | WorkQueue | Memory | Until consumed |
| `FCAPS_DONE` | `fcaps.done.>` | Limits | Memory | 30min / 50k msgs |

- `FCAPS_INGEST`: Raw inbound messages. File-backed → survives container restart.
- `FCAPS_PROCESS`: Consumed once-and-only-once by Transformer workers (Phase 2).
- `FCAPS_DONE`: Processed envelopes fan-out to WebSocket broadcaster and storage writers.

---

## Storage Adapters

All plugin/transformer code calls only the abstract interface — never InfluxDB or VictoriaLogs clients directly:

```python
class MetricsStore(ABC):
    async def write_pm(self, envelope: MessageEnvelope): ...
    async def query_pm(self, source_ne, start, end) -> list: ...

class EventStore(ABC):
    async def write_fm(self, envelope: MessageEnvelope): ...
    async def write_log(self, envelope: MessageEnvelope): ...
    async def search(self, query, domain, limit) -> list: ...
```

Factory switches based on `STORAGE_MODE` env var:
```
STORAGE_MODE=lab   → InfluxDBMetrics + VictoriaLogsEvents
STORAGE_MODE=prod  → InfluxDB cluster + VictoriaLogs cluster
```

---

## docker-compose.yml (Lab Mode)

```yaml
services:
  traefik:
    image: traefik:v3
    mem_limit: 64m
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports: ["80:80"]

  core-api:
    build: ./trishul
    mem_limit: 150m
    environment:
      STORAGE_MODE: lab
      JWT_SECRET: ${JWT_SECRET}
      NATS_URL: nats://nats:4222
      REDIS_URL: redis://redis:6379
      INFLUX_URL: http://influxdb:8086
      INFLUX_TOKEN: ${INFLUX_TOKEN}
      INFLUX_BUCKET: fcaps_pm
      VICTORIA_URL: http://victorialogs:9428
      SQLITE_PATH: /data/fcaps.db
    volumes: ["sqlite-data:/data"]
    depends_on: [nats, redis, influxdb, victorialogs]
    labels:
      - "traefik.http.routers.api.rule=PathPrefix(`/api`) || PathPrefix(`/docs`)"

  nats:
    image: nats:2.10-alpine
    mem_limit: 64m
    command: ["-js", "-sd", "/data"]
    volumes: ["nats-data:/data"]

  redis:
    image: redis:7-alpine
    mem_limit: 64m
    command: redis-server --maxmemory 50mb --maxmemory-policy allkeys-lru

  influxdb:
    image: influxdb:2-alpine
    mem_limit: 200m
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_ORG: trishul
      DOCKER_INFLUXDB_INIT_BUCKET: fcaps_pm
      DOCKER_INFLUXDB_INIT_RETENTION: 30d
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: ${INFLUX_TOKEN}
    volumes: ["influx-data:/var/lib/influxdb2"]

  victorialogs:
    image: victoriametrics/victoria-logs:latest
    mem_limit: 128m
    command:
      - "-storageDataPath=/vlogs-data"
      - "-retentionPeriod=30d"
    volumes: ["vlogs-data:/vlogs-data"]
    labels:
      - "traefik.http.routers.vlogs.rule=PathPrefix(`/vlogs`)"

volumes:
  nats-data:
  influx-data:
  vlogs-data:
  sqlite-data:
```

---

## Config: .env.example

```env
# Auth
JWT_SECRET=change-me-to-a-long-random-string
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=7

# Storage
STORAGE_MODE=lab
INFLUX_TOKEN=change-me-influx-token

# App
APP_ENV=lab
LOG_LEVEL=INFO
```

---

## API Endpoints (Phase 1)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | None | Get JWT (username + password) |
| POST | `/api/v1/auth/refresh` | JWT (refresh) | Refresh access token |
| POST | `/api/v1/auth/logout` | JWT | Blocklist token in Redis |
| GET | `/api/v1/auth/apikeys` | admin | List API keys |
| POST | `/api/v1/auth/apikeys` | admin | Create API key |
| DELETE | `/api/v1/auth/apikeys/{id}` | admin | Revoke API key |
| GET | `/api/v1/plugins/registry` | operator | List loaded plugins + metadata |
| GET | `/health` | None | Service health (all deps) |
| GET | `/metrics` | None | Prometheus metrics |

---

## Deliverables Checklist

- [ ] FastAPI app factory with lifespan (startup/shutdown hooks)
- [ ] Plugin registry: base class + dynamic loader
- [ ] `MessageEnvelope` Pydantic model + `FCAPSDomain` enum
- [ ] Auth middleware: JWT + API Key dual-mode
- [ ] SQLite user table (SQLModel) + hashed password auth
- [ ] Redis API key store + JWT blocklist
- [ ] NATS JetStream client + stream provisioning on startup
- [ ] InfluxDB storage adapter (`MetricsStore` impl)
- [ ] VictoriaLogs storage adapter (`EventStore` impl)
- [ ] `StorageFactory` (mode-switching)
- [ ] pydantic-settings config with full `.env` support
- [ ] `GET /health` checking NATS + Redis + InfluxDB + VictoriaLogs
- [ ] `GET /metrics` Prometheus format
- [ ] Webhook plugin scaffold (reference implementation)
- [ ] `docker-compose.yml` (lab mode, all 6 services)
- [ ] `.env.example`
- [ ] `Dockerfile` (multi-stage, python:3.12-slim)
