# Phase 1 — Core Foundation

**Status**: 🟡 Design Frozen  
**Depends on**: None  
**Prerequisite for**: Phase 2, Phase 3, Phase 4

---

## Goal

Build the complete, production-ready skeleton of Trishul. All subsequent phases plug into this foundation **without modifying it**. This phase defines every shared contract, interface, and infrastructure component. Nothing is provisional.

---

## 1. Stack — Lab Mode (Frozen)

| Component | Technology | Version | RAM Target | Notes |
|-----------|------------|---------|------------|-------|
| API Framework | FastAPI | 0.115+ | ~80–120MB | Async-first, OpenAPI auto-docs |
| ASGI Server | Uvicorn | 0.32+ | (included) | 1 worker, async I/O sufficient |
| Auth (JWT) | python-jose + passlib[bcrypt] | latest | ~5MB | HS256 signing |
| Auth (state) | Redis 7 Alpine | 7.x | ~20MB | Blocklist + API keys + rate limit |
| User/session store | SQLite + SQLModel | 0.0.21+ | ~0MB | Users, audit log, schema registry (Phase 2) |
| Message bus | NATS JetStream | 2.10 Alpine | ~15–25MB | File-backed persistence |
| Hot cache / dedup | Redis 7 Alpine | (shared) | — | Same Redis instance, separate key prefix |
| PM Metrics store | InfluxDB 2 OSS | 2.x Alpine | ~80–150MB | TSM engine, 30d retention |
| FM / Log store | VictoriaLogs | latest | ~30–50MB | ~30x lighter than OpenSearch |
| Reverse proxy | Traefik | v3 | ~30MB | Auto-discovers containers via Docker labels |
| **Total** | | | **~350–450MB** | Runs on 4GB RAM / 2 vCPU comfortably |

> **No dev mode.** Lab mode is the minimum. `STORAGE_MODE` only switches between `lab` and `prod` (clustered).

---

## 2. Directory Structure (Frozen)

```
trishul/
├── core/
│   ├── app.py                   ← FastAPI app factory + lifespan hooks
│   ├── plugin_registry.py       ← FCAPSPlugin ABC + PluginRegistry singleton
│   │
│   ├── models/
│   │   ├── envelope.py          ← MessageEnvelope, FCAPSDomain, Severity
│   │   ├── base.py              ← TrishulBaseModel (shared Pydantic config)
│   │   └── responses.py         ← Uniform API response wrappers
│   │
│   ├── auth/
│   │   ├── middleware.py        ← AuthMiddleware (JWT + API Key, RBAC)
│   │   ├── jwt_handler.py       ← encode_jwt / decode_jwt / refresh
│   │   ├── apikey_store.py      ← Redis API key CRUD
│   │   ├── router.py            ← /api/v1/auth/* endpoints
│   │   └── models.py            ← User, APIKey, TokenPair SQLModel tables
│   │
│   ├── bus/
│   │   ├── client.py            ← NATS connection singleton + reconnect
│   │   ├── streams.py           ← JetStream stream/consumer provisioning
│   │   └── publisher.py         ← publish_envelope() helper
│   │
│   ├── storage/
│   │   ├── base.py              ← MetricsStore + EventStore ABC
│   │   ├── influxdb.py          ← InfluxDBMetrics (lab + prod)
│   │   ├── victorialogs.py      ← VictoriaLogsEvents (lab + prod)
│   │   └── factory.py           ← get_stores(STORAGE_MODE) → (MetricsStore, EventStore)
│   │
│   ├── config/
│   │   └── settings.py          ← pydantic-settings BaseSettings (single source of truth)
│   │
│   ├── notifications/
│   │   └── service.py           ← NATS fcaps.done.* → WebSocket fan-out broadcaster
│   │
│   ├── middleware/
│   │   ├── logging.py           ← Structured request/response logging
│   │   ├── rate_limit.py        ← Redis token-bucket rate limiter
│   │   └── error_handler.py     ← Global exception → uniform JSON error response
│   │
│   └── health/
│       └── router.py            ← GET /health + GET /metrics
│
├── plugins/
│   └── webhook/                 ← Reference plugin (Phase 1 only)
│       ├── __init__.py          ← exports plugin = WebhookPlugin()
│       ├── router.py            ← /api/v1/webhook/* endpoints
│       ├── models.py            ← WebhookPayload Pydantic model
│       └── config.py            ← WebhookSettings (extends BaseSettings)
│
├── tests/
│   ├── test_auth.py
│   ├── test_envelope.py
│   ├── test_health.py
│   ├── test_nats.py
│   └── test_webhook_plugin.py
│
├── docker-compose.yml
├── .env.example
├── Dockerfile
├── pyproject.toml               ← deps: fastapi, uvicorn, sqlmodel, python-jose,
│                                   passlib, nats-py, influxdb-client, redis, prometheus-client
└── .dockerignore
```

---

## 3. Shared Models (Frozen Contracts)

### 3.1 MessageEnvelope

The **single normalized unit** flowing through the entire system. Every protocol plugin, transformer, and storage writer works with this model.

```python
# core/models/envelope.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timezone
import uuid

class FCAPSDomain(str, Enum):
    FM  = "FM"    # Fault Management
    PM  = "PM"    # Performance Management
    LOG = "LOG"   # Log / Audit

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR    = "MAJOR"
    MINOR    = "MINOR"
    WARNING  = "WARNING"
    CLEARED  = "CLEARED"
    INFO     = "INFO"    # for PM/LOG, non-alarm

class Direction(str, Enum):
    INBOUND   = "inbound"
    OUTBOUND  = "outbound"
    SIMULATED = "simulated"

class MessageEnvelope(BaseModel):
    id:          str          = Field(default_factory=lambda: str(uuid.uuid4()))
    schema_ver:  str          = "1.0"             # bump on breaking envelope changes
    timestamp:   datetime     = Field(default_factory=lambda: datetime.now(timezone.utc))
    domain:      FCAPSDomain
    protocol:    str                              # snmp | ves | protobuf | avro | webhook | sftp
    source_ne:   str                              # Network Element identifier
    direction:   Direction
    severity:    Severity | None = None           # required for FM, None for PM/LOG
    raw_payload: dict            = Field(default_factory=dict)
    normalized:  dict            = Field(default_factory=dict)  # protocol-agnostic fields
    tags:        list[str]       = Field(default_factory=list)
    trace_id:    str | None      = None           # for distributed tracing (optional)
```

### 3.2 Uniform API Response Wrappers

Every endpoint returns one of these — never a bare dict.

```python
# core/models/responses.py
from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")

class TrishulResponse(BaseModel, Generic[T]):
    success: bool
    data:    T | None    = None
    error:   str | None  = None
    trace_id: str | None = None

# Usage in router:
# return TrishulResponse(success=True, data={"envelope_id": env.id})
# return TrishulResponse(success=False, error="Invalid payload")

class AcceptedResponse(BaseModel):
    """For async 202 responses"""
    envelope_id: str
    status: str = "accepted"
    message: str
```

---

## 4. Authentication Design (Frozen)

### 4.1 Dual-Mode Auth

| Mode | Consumer | Token | Storage | Lifetime |
|------|----------|-------|---------|----------|
| JWT Bearer | UI / human users | HS256 signed | Redis blocklist only | 15min access / 7d refresh |
| API Key | Machines / plugins / CI | SHA-256 hash | Redis hash | Until revoked |

### 4.2 Middleware Execution Order

```
HTTP Request
  1. RateLimitMiddleware      ← Redis token bucket (per IP or API key)
  2. RequestLoggingMiddleware ← structured log: method, path, client_ip, trace_id
  3. AuthMiddleware
     ├─ PUBLIC_PATHS bypass   → /health, /metrics, /docs, /openapi.json,
     │                           /api/v1/auth/login, /api/v1/auth/refresh
     ├─ Bearer <JWT>          → decode_jwt() → check Redis blocklist → 401 if hit
     ├─ X-API-Key: <key>      → SHA-256 hash → Redis lookup → 401 if missing
     └─ attach request.state.user = { id, username, roles, auth_type }
  4. RBAC check               ← route decorator declares required_role
  5. Route Handler
  6. ErrorHandlerMiddleware   ← catches all unhandled exceptions → TrishulResponse(error=...)
```

### 4.3 RBAC Roles

| Role | Permissions |
|------|-------------|
| `admin` | All endpoints including user + API key management |
| `operator` | All plugin endpoints (read + write + simulate). No user mgmt. |
| `viewer` | GET endpoints only across all plugins |
| `plugin:{name}` | Scoped to `/api/v1/{name}/*` only (for machine clients) |

### 4.4 Rate Limiting

- Default: **60 requests / minute per client** (IP for anonymous, user_id for authenticated)
- Configurable per route via decorator: `@rate_limit(requests=10, window=60)`
- Simulated bursts (e.g. SNMP sim sending 1000 traps): `plugin:{x}` API keys get a **higher limit** (600 req/min) set at key creation time
- Limit counters stored in Redis with TTL = window size

---

## 5. Plugin Registry (Frozen Contract)

Every Phase 3+ plugin must satisfy this contract **exactly** to be auto-loaded.

```python
# core/plugin_registry.py
from abc import ABC, abstractmethod
from fastapi import APIRouter

class FCAPSPlugin(ABC):
    name:         str          # unique, lowercase, no spaces: "snmp", "ves"
    version:      str          # semver: "1.0.0"
    description:  str
    fcaps_domains: list[str]   # ["FM"], ["PM"], ["FM", "PM", "LOG"]
    protocols:    list[str]    # ["snmpv2c", "snmpv3"]

    @abstractmethod
    def get_router(self) -> APIRouter:
        """Return configured APIRouter. Prefix applied by registry."""
        ...

    @abstractmethod
    def get_nats_subjects(self) -> dict:
        """{ 'publish': ['fcaps.ingest.snmp'], 'subscribe': ['fcaps.done.snmp'] }"""
        ...

    @abstractmethod
    async def on_startup(self): ...
    
    @abstractmethod
    async def on_shutdown(self): ...

    def get_metadata(self) -> dict:
        """Auto-serialized for GET /api/v1/plugins/registry — used by Phase 4 UI."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "fcaps_domains": self.fcaps_domains,
            "protocols": self.protocols,
            "router_prefix": f"/api/v1/{self.name}",
            "ui_remote_url": None,   # filled in Phase 5
        }
```

**Auto-discovery at startup:**
```python
# core/app.py (lifespan)
async def lifespan(app: FastAPI):
    # startup
    await nats_client.connect()
    await provision_streams()
    load_all_plugins()          # pkgutil.iter_modules(["plugins"])
    yield
    # shutdown
    await nats_client.drain()
```

---

## 6. NATS JetStream — Stream Definitions (Frozen)

| Stream | Subject Pattern | Retention | Storage | Max Age | Max Msgs | Purpose |
|--------|-----------------|-----------|---------|---------|----------|---------|
| `FCAPS_INGEST` | `fcaps.ingest.>` | Limits | **File** | 1 hour | 10,000 | Raw inbound — survives restart |
| `FCAPS_PROCESS` | `fcaps.process.>` | WorkQueue | **Memory** | — | — | Once-and-only-once transform queue |
| `FCAPS_DONE` | `fcaps.done.>` | Limits | **Memory** | 30 min | 50,000 | Processed envelopes → WS + storage fan-out |
| `FCAPS_SIM` | `fcaps.sim.>` | Limits | **Memory** | 1 hour | 5,000 | Simulated outbound messages (audit) |

**Subject naming convention:**
```
fcaps.ingest.{protocol}         e.g. fcaps.ingest.snmp
fcaps.process.{protocol}        e.g. fcaps.process.ves
fcaps.done.{domain}             e.g. fcaps.done.fm  | fcaps.done.pm
fcaps.sim.{protocol}            e.g. fcaps.sim.snmp
```

**Consumer groups (provisioned at startup):**
- `transformer-worker` → subscribes `fcaps.ingest.>` (Phase 2 transformer)
- `storage-writer` → subscribes `fcaps.done.>` (storage adapters)
- `ws-broadcaster` → subscribes `fcaps.done.>` (notification service)

---

## 7. Storage Adapters (Frozen Interface)

```python
# core/storage/base.py
from abc import ABC, abstractmethod
from core.models.envelope import MessageEnvelope

class MetricsStore(ABC):
    """For PM domain — InfluxDB in lab/prod."""
    @abstractmethod
    async def write_pm(self, envelope: MessageEnvelope) -> None: ...

    @abstractmethod
    async def query_pm(
        self,
        source_ne: str,
        start: str,    # ISO8601 or relative: "-1h"
        end: str,
        metric_name: str | None = None
    ) -> list[dict]: ...

    @abstractmethod
    async def health(self) -> bool: ...


class EventStore(ABC):
    """For FM + LOG domain — VictoriaLogs in lab/prod."""
    @abstractmethod
    async def write_fm(self, envelope: MessageEnvelope) -> None: ...

    @abstractmethod
    async def write_log(self, envelope: MessageEnvelope) -> None: ...

    @abstractmethod
    async def search(
        self,
        query: str,      # LogsQL for VictoriaLogs
        domain: str,     # "FM" | "LOG"
        start: str,
        end: str,
        limit: int = 100
    ) -> list[dict]: ...

    @abstractmethod
    async def health(self) -> bool: ...
```

**Factory:**
```python
# core/storage/factory.py
def get_stores(mode: str) -> tuple[MetricsStore, EventStore]:
    match mode:
        case "lab" | "prod":  return InfluxDBMetrics(), VictoriaLogsEvents()
        case _: raise ValueError(f"Unknown STORAGE_MODE: {mode}")
```

---

## 8. Configuration (Frozen — pydantic-settings)

```python
# core/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_env:       str  = "lab"
    log_level:     str  = "INFO"
    storage_mode:  str  = "lab"

    # Auth
    jwt_secret:            str
    jwt_access_ttl_min:    int  = 15
    jwt_refresh_ttl_days:  int  = 7
    rate_limit_default:    int  = 60   # req/min
    rate_limit_plugin:     int  = 600  # req/min for plugin:{x} API keys

    # NATS
    nats_url: str = "nats://nats:4222"

    # Redis
    redis_url: str = "redis://redis:6379"

    # InfluxDB
    influx_url:    str
    influx_token:  str
    influx_org:    str  = "trishul"
    influx_bucket: str  = "fcaps_pm"

    # VictoriaLogs
    victoria_url: str  = "http://victorialogs:9428"

    # SQLite
    sqlite_path: str = "/data/fcaps.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

All modules import `get_settings()` — **never instantiate Settings() directly.** This enables clean test overrides.

---

## 9. Error Handling Strategy (Frozen)

All errors return a `TrishulResponse(success=False, error=...)` with consistent HTTP status codes:

| Exception | HTTP Status | Error Message Pattern |
|-----------|-------------|----------------------|
| `AuthenticationError` | 401 | "Authentication required" or "Token expired" |
| `AuthorizationError` | 403 | "Insufficient permissions: requires {role}" |
| `RateLimitExceeded` | 429 | "Rate limit exceeded. Retry after {n}s" |
| `ValidationError` (Pydantic) | 422 | Field-level detail from Pydantic |
| `PluginNotFoundError` | 404 | "Plugin '{name}' not registered" |
| `BusPublishError` | 503 | "Message bus unavailable" |
| `StorageError` | 503 | "Storage write failed: {store}" |
| Unhandled exception | 500 | "Internal error" + trace_id logged |

- All 5xx errors log **full traceback** at ERROR level with `trace_id`
- All 4xx errors log at WARNING level with `client_id` + `path`
- No stack traces ever exposed in API responses

---

## 10. Structured Logging (Frozen Format)

All log output is **JSON** (parsed by VictoriaLogs). No plain-text logs anywhere.

```json
{
  "timestamp": "2026-02-27T08:30:00.123Z",
  "level": "INFO",
  "service": "core-api",
  "trace_id": "abc123",
  "event": "envelope_ingested",
  "protocol": "snmp",
  "domain": "FM",
  "source_ne": "router-01",
  "envelope_id": "uuid-here",
  "duration_ms": 4
}
```

**Standard event names (frozen):**
```
request_received        plugin_loaded
request_completed       plugin_startup_failed
auth_success            envelope_ingested
auth_failure            envelope_processed
rate_limit_exceeded     storage_write_failed
nats_connected          health_check_failed
nats_disconnected
```

---

## 11. Health Check Design (Frozen)

`GET /health` returns overall status + per-dependency status:

```json
{
  "status": "healthy",       // "healthy" | "degraded" | "unhealthy"
  "timestamp": "2026-02-27T08:30:00Z",
  "version": "1.0.0",
  "dependencies": {
    "nats":         { "status": "ok",   "latency_ms": 1  },
    "redis":        { "status": "ok",   "latency_ms": 0  },
    "influxdb":     { "status": "ok",   "latency_ms": 12 },
    "victorialogs": { "status": "ok",   "latency_ms": 5  }
  },
  "plugins": {
    "webhook": { "status": "ok", "version": "1.0.0" }
  }
}
```

**Rules:**
- Any dep `"error"` → overall = `"degraded"` (app still runs)
- NATS or Redis `"error"` → overall = `"unhealthy"` (critical path)
- Health check itself has 2s timeout per dependency
- Traefik uses `/health` for container health routing

---

## 12. API Endpoints — Phase 1 (Frozen)

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | None | Username + password → `TokenPair` |
| POST | `/api/v1/auth/refresh` | Refresh JWT | New access token |
| POST | `/api/v1/auth/logout` | Access JWT | Add to Redis blocklist |
| GET | `/api/v1/auth/me` | Any JWT | Current user info + roles |
| GET | `/api/v1/auth/apikeys` | admin | List all API keys |
| POST | `/api/v1/auth/apikeys` | admin | Create API key → returns raw key once |
| DELETE | `/api/v1/auth/apikeys/{id}` | admin | Revoke API key |

### Platform
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/plugins/registry` | operator | All loaded plugins + metadata |
| GET | `/health` | None | Full dependency health |
| GET | `/metrics` | None | Prometheus text format |

### Webhook Plugin (Reference)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/webhook/receive` | operator | Accept JSON payload → ingest |
| POST | `/api/v1/webhook/send` | operator | POST to a target URL |
| POST | `/api/v1/webhook/simulate` | operator | Generate N synthetic events |
| GET | `/api/v1/webhook/status/{id}` | operator | Envelope processing status |
| GET | `/api/v1/webhook/health` | None | Plugin health |

---

## 13. docker-compose.yml (Frozen — Lab Mode)

```yaml
services:

  traefik:
    image: traefik:v3
    mem_limit: 64m
    restart: unless-stopped
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--log.level=ERROR"
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

  core-api:
    build:
      context: ./trishul
      dockerfile: Dockerfile
    mem_limit: 150m
    restart: unless-stopped
    environment:
      APP_ENV:          lab
      LOG_LEVEL:        INFO
      STORAGE_MODE:     lab
      JWT_SECRET:       ${JWT_SECRET}
      NATS_URL:         nats://nats:4222
      REDIS_URL:        redis://redis:6379
      INFLUX_URL:       http://influxdb:8086
      INFLUX_TOKEN:     ${INFLUX_TOKEN}
      INFLUX_ORG:       trishul
      INFLUX_BUCKET:    fcaps_pm
      VICTORIA_URL:     http://victorialogs:9428
      SQLITE_PATH:      /data/fcaps.db
    volumes:
      - sqlite-data:/data
    depends_on:
      nats:         { condition: service_started }
      redis:        { condition: service_healthy }
      influxdb:     { condition: service_healthy }
      victorialogs: { condition: service_started }
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=PathPrefix(`/api`) || PathPrefix(`/docs`) || PathPrefix(`/openapi.json`) || Path(`/health`) || Path(`/metrics`)"
      - "traefik.http.routers.api.entrypoints=web"

  nats:
    image: nats:2.10-alpine
    mem_limit: 64m
    restart: unless-stopped
    command: ["-js", "-sd", "/data", "-m", "8222"]
    volumes:
      - nats-data:/data
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8222/healthz"]
      interval: 10s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    mem_limit: 64m
    restart: unless-stopped
    command: redis-server --maxmemory 50mb --maxmemory-policy allkeys-lru --save ""
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  influxdb:
    image: influxdb:2-alpine
    mem_limit: 200m
    restart: unless-stopped
    environment:
      DOCKER_INFLUXDB_INIT_MODE:         setup
      DOCKER_INFLUXDB_INIT_ORG:          trishul
      DOCKER_INFLUXDB_INIT_BUCKET:       fcaps_pm
      DOCKER_INFLUXDB_INIT_RETENTION:    30d
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN:  ${INFLUX_TOKEN}
    volumes:
      - influx-data:/var/lib/influxdb2
    healthcheck:
      test: ["CMD", "influx", "ping"]
      interval: 15s
      timeout: 5s
      retries: 5

  victorialogs:
    image: victoriametrics/victoria-logs:latest
    mem_limit: 128m
    restart: unless-stopped
    command:
      - "-storageDataPath=/vlogs-data"
      - "-retentionPeriod=30d"
      - "-httpListenAddr=:9428"
    volumes:
      - vlogs-data:/vlogs-data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.vlogs.rule=PathPrefix(`/vlogs`)"
      - "traefik.http.routers.vlogs.entrypoints=web"

volumes:
  nats-data:
  influx-data:
  vlogs-data:
  sqlite-data:
```

---

## 14. .env.example (Frozen)

```env
# ── App ──────────────────────────────────────────────
APP_ENV=lab
LOG_LEVEL=INFO
STORAGE_MODE=lab

# ── Auth ─────────────────────────────────────────────
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=change-me-to-a-32-byte-hex-string
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=7
RATE_LIMIT_DEFAULT=60
RATE_LIMIT_PLUGIN=600

# ── NATS ─────────────────────────────────────────────
NATS_URL=nats://nats:4222

# ── Redis ────────────────────────────────────────────
REDIS_URL=redis://redis:6379

# ── InfluxDB ─────────────────────────────────────────
INFLUX_URL=http://influxdb:8086
# Generate: python -c "import secrets; print(secrets.token_hex(24))"
INFLUX_TOKEN=change-me-influx-admin-token
INFLUX_ORG=trishul
INFLUX_BUCKET=fcaps_pm

# ── VictoriaLogs ─────────────────────────────────────
VICTORIA_URL=http://victorialogs:9428

# ── SQLite ───────────────────────────────────────────
SQLITE_PATH=/data/fcaps.db
```

---

## 15. Dockerfile (Frozen — Multi-Stage)

```dockerfile
# Stage 1: build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .

# Non-root user
RUN adduser --disabled-password --gecos "" trishul
USER trishul

EXPOSE 8000
CMD ["uvicorn", "core.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
```

---

## 16. Deliverables Checklist

### Infrastructure
- [ ] `docker-compose.yml` with all 5 services + healthchecks
- [ ] `.env.example` with all required vars documented
- [ ] `Dockerfile` multi-stage, non-root user

### Core App Factory
- [ ] `core/app.py` — FastAPI factory + lifespan (startup/shutdown)
- [ ] `core/config/settings.py` — pydantic-settings with `lru_cache`
- [ ] Middleware stack wired in order: rate_limit → logging → auth → error_handler

### Models
- [ ] `MessageEnvelope` with `schema_ver`, `trace_id`, `Direction`, `Severity`
- [ ] `TrishulResponse[T]` generic wrapper + `AcceptedResponse`
- [ ] `TrishulBaseModel` shared Pydantic config (UTC datetime, alias gen)

### Auth
- [ ] `AuthMiddleware` (JWT + API Key, PUBLIC_PATHS bypass)
- [ ] `jwt_handler.py` (encode, decode, refresh — HS256)
- [ ] SQLite `users` table (SQLModel) with bcrypt-hashed passwords
- [ ] Redis API key store (`apikey:{sha256}` → JSON metadata)
- [ ] Redis JWT blocklist (`blocklist:{jti}` with TTL = remaining token lifetime)
- [ ] Auth router: login, refresh, logout, me, apikeys CRUD
- [ ] RBAC role decorator `@require_role("operator")`

### Bus
- [ ] NATS singleton client with auto-reconnect
- [ ] Stream provisioner: `FCAPS_INGEST`, `FCAPS_PROCESS`, `FCAPS_DONE`, `FCAPS_SIM`
- [ ] `publish_envelope(subject, envelope)` helper

### Storage
- [ ] `MetricsStore` ABC + `EventStore` ABC
- [ ] `InfluxDBMetrics` — `write_pm`, `query_pm`, `health`
- [ ] `VictoriaLogsEvents` — `write_fm`, `write_log`, `search`, `health`
- [ ] `StorageFactory` — `get_stores(mode)`

### Middleware
- [ ] `RateLimitMiddleware` — Redis token bucket, configurable per route
- [ ] `RequestLoggingMiddleware` — JSON structured logs, injects `trace_id`
- [ ] `ErrorHandlerMiddleware` — all exceptions → `TrishulResponse(error=...)`

### Health + Metrics
- [ ] `GET /health` — all dep checks with 2s timeout, `"healthy"|"degraded"|"unhealthy"`
- [ ] `GET /metrics` — Prometheus format (prometheus-client)
- [ ] Core metrics: `trishul_envelope_ingest_total`, `trishul_auth_failure_total`, `trishul_request_duration_seconds`

### Plugin Registry
- [ ] `FCAPSPlugin` ABC with all abstract methods
- [ ] `PluginRegistry` singleton with `load_all()` auto-discovery
- [ ] `GET /api/v1/plugins/registry` endpoint

### Reference Plugin (Webhook)
- [ ] `WebhookPlugin` implementing `FCAPSPlugin`
- [ ] All 5 standard endpoints: receive, send, simulate, status, health
- [ ] Full ingest → NATS publish → 202 response flow working end-to-end

### Tests
- [ ] `test_auth.py` — login, refresh, logout, RBAC, rate limit
- [ ] `test_envelope.py` — model validation, serialization
- [ ] `test_health.py` — healthy / degraded / unhealthy states
- [ ] `test_nats.py` — publish + consume round-trip
- [ ] `test_webhook_plugin.py` — full receive → NATS → 202 flow
