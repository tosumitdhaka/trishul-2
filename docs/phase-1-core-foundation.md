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

## 2. Container Architecture (Frozen)

### One Container = One Concern

Each infrastructure component runs in its own container. Only Traefik exposes a host port. Everything else communicates over the internal Docker bridge network `trishul-net`.

| Container | Image | Exposes (internal) | Persistent Storage |
|-----------|-------|--------------------|--------------------|
| `traefik` | `traefik:v3` | Host port 80 only | None |
| `core-api` | `python:3.12-slim` (our build) | :8000 | `sqlite-data:/data` |
| `nats` | `nats:2.10-alpine` | :4222, :8222 | `nats-data:/data` |
| `redis` | `redis:7-alpine` | :6379 | **None** (ephemeral by design) |
| `influxdb` | `influxdb:2-alpine` | :8086 | `influx-data:/var/lib/influxdb2` |
| `victorialogs` | `victoriametrics/victoria-logs` | :9428 | `vlogs-data:/vlogs-data` |
| `shell-ui` | `nginx:alpine` (Phase 4) | :80 | None |

### Why Redis Has No Volume
Redis stores only short-lived, re-derivable state: JWT blocklist (TTL = token lifetime), rate-limit counters (TTL = 60s), dedup cache (TTL = 15min), API key lookups (re-loadable from SQLite). A Redis restart is fully acceptable — nothing is permanently lost.

### Docker Named Volumes (All Persistent Data)
```
nats-data     → nats:/data                     JetStream file-backed stream data
influx-data   → influxdb:/var/lib/influxdb2     PM time-series metrics
vlogs-data    → victorialogs:/vlogs-data        FM alarms + log entries
sqlite-data   → core-api:/data                 fcaps.db (users, api_keys, audit_log)
```

### Inter-Container Communication
```
core-api  ──TCP──►  nats:4222          NATS client protocol (nats-py)
core-api  ──TCP──►  redis:6379         Redis RESP protocol (redis-py async)
core-api  ──HTTP─►  influxdb:8086      InfluxDB v2 REST API (influxdb-client)
core-api  ──HTTP─►  victorialogs:9428  VictoriaLogs HTTP push/query API
core-api  ──FILE─►  /data/fcaps.db     SQLite (embedded, same process, volume mount)
traefik   ──Docker socket► labels            Container label-based route discovery
```

---

## 3. What core-api Owns (Single Container, Two Logical Layers)

**Decision (Frozen):** Transformer Engine and Plugins run inside `core-api` — NOT in a separate container.

**Rationale:** NATS JetStream already provides the decoupling between HTTP receive and async processing. A container boundary adds operational complexity (shared code packaging, internal HTTP calls, split health checks, two Dockerfiles) for zero benefit at lab scale. The split is logical (code modules), not physical (containers).

**Future-proof:** If horizontal scaling is ever needed, the transformer consumers can be extracted into a `worker/app.py` entrypoint that imports the same transformer and plugin modules, adds a second service to docker-compose, and requires zero business logic changes.

```
core-api process
│
├── CONTROLLER LAYER (HTTP-facing)
│   ├── FastAPI app factory + lifespan
│   ├── Middleware stack (RateLimit → Logging → Auth → ErrorHandler)
│   ├── AuthRouter        /api/v1/auth/*
│   ├── RegistryRouter    /api/v1/plugins/*
│   ├── TransformRouter   /api/v1/transform/*  (ad-hoc pipelines)
│   ├── Plugin Routers    /api/v1/{proto}/*    (HTTP entry points per protocol)
│   ├── HealthRouter      /health
│   ├── MetricsRouter     /metrics
│   └── NATS Publisher    publish_envelope() → fcaps.ingest.*
│
└── WORKER LAYER (NATS consumer-facing)   [same process, different async tasks]
    ├── Transformer Engine                  consumes fcaps.ingest.*
    │   ├── PipelineRegistry (stage lookup)
    │   ├── Decoders:   JSON, CSV, Protobuf, Avro, VES, SNMP
    │   ├── Normalizer: FCAPSNormalizer (single shared)
    │   ├── Encoders:   JSON, CSV, Protobuf, Avro
    │   └── Writers:    NATS, InfluxDB, VictoriaLogs, Webhook, SFTP, CSV
    ├── Plugin Processing Logic             wired into transformer pipelines
    ├── storage-writer consumer             writes fcaps.done.* → InfluxDB/VLogs
    └── ws-broadcaster consumer             pushes fcaps.done.* → WebSocket (Phase 4)
```

---

## 4. Role of Plugins vs Transformer (Frozen)

Plugins and the Transformer Engine are **complementary layers**, not alternatives.

| Concern | Plugin | Transformer Engine |
|---------|--------|--------------------|
| Protocol I/O binding | ✅ HTTP endpoint, UDP socket, SFTP poller, gRPC listener | ❌ Does not care how data arrives |
| Input validation | ✅ Validates raw incoming format (VES schema, SNMP version check) | ❌ Expects valid raw bytes/dict |
| Simulation / test data gen | ✅ Generates synthetic protocol-native messages | ❌ Not its job |
| Protocol-specific routing | ✅ Sets domain (FM/PM/LOG) from protocol context | ❌ |
| Decoding + normalizing | ❌ Delegates entirely to Transformer | ✅ Owns this |
| Encoding + writing to sink | ❌ Delegates entirely to Transformer | ✅ Owns this |
| Pipeline assembly | ❌ | ✅ Assembles Reader→Decoder→Normalizer→Encoder→Writer |

> **Mental model:** Plugin = protocol border guard (knows how traffic enters/exits the network boundary). Transformer = processing factory (converts anything to anything).

### Plugin Responsibility (Thin by Design)
```
Plugin does exactly 3 things:
  1. Receive/validate inbound data (HTTP POST, UDP trap, SFTP poll, etc.)
  2. Publish raw payload + metadata to fcaps.ingest.{proto} via NATS
  3. Expose simulate API to generate synthetic test data

Plugin does NOT:
  - Parse protocol formats (Transformer's Decoder does this)
  - Normalize to MessageEnvelope (Transformer's Normalizer does this)
  - Write to storage (Transformer's Writer does this)
  - Implement retry/backpressure (NATS JetStream does this)
```

---

## 5. Pipeline Control (Frozen)

Pipelines are controlled through four mechanisms, covering all use cases:

### Mechanism 1 — Static Plugin-Bound Pipeline
Each plugin pre-wires its default pipeline at `on_startup()`. Runs automatically for every inbound message:
```
VES Plugin on_startup():
  registers default pipeline:
    Decoder:    VESDecoder
    Normalizer: FCAPSNormalizer  (domain=FM, source_ne from payload)
    Encoder:    JSONEncoder
    Writer:     NATSWriter       (→ fcaps.done.fm)

Every POST /api/v1/ves/receive automatically uses this pipeline.
```

### Mechanism 2 — Dynamic Ad-hoc Pipeline (Synchronous)
Operators wire any stage combination on demand for one-off conversions:
```
POST /api/v1/transform/run
{
  "reader":     { "type": "sftp",    ... },
  "decoder":    { "type": "avro",    ... },
  "normalizer": { "domain": "PM",    ... },
  "encoder":    { "type": "json" },
  "writer":     { "type": "influxdb", ... }
}
→ Returns: 200 { envelope_id, normalized_data }
```

### Mechanism 3 — Async Job Pipeline (Large/Batch)
For SFTP file imports, large batch conversions, scheduled pulls:
```
POST /api/v1/transform/submit  (same config JSON)
→ Returns: 202 { job_id }

GET /api/v1/transform/jobs/{job_id}
→ Returns: { status: processing|done|failed, envelope_ids: [...] }
```

### Mechanism 4 — Simulated Pipeline
Plugin simulators generate synthetic data that goes through the same transformer path:
```
POST /api/v1/snmp/simulate { trap_type, target_host, count }
  → Simulator.generate() → list[MessageEnvelope] (direction=simulated)
  → TransformPipeline(SNMPEncoder, SNMPWriter) → sent to target
  → Published to fcaps.sim.snmp (audit trail)
  → Returns: 200 { sent: N, envelope_ids: [...] }
```

### Pipeline Control Summary
```
Mechanism              Trigger              Use Case
──────────────────────────────────────────────────────────────────────────
Static (plugin)        Inbound message      Live protocol traffic (always-on)
Dynamic sync           API call             One-off conversion, testing
Async job              API call             Batch import, large files, SFTP
Simulated              API call             Test data generation, NE simulation
```

---

## 6. Directory Structure (Frozen)

```
trishul/
├── core/
│   ├── app.py                   ← FastAPI app factory + lifespan hooks
│   ├── plugin_registry.py       ← FCAPSPlugin ABC + PluginRegistry singleton
│   ├── dependencies.py          ← All FastAPI Depends() wrappers
│   │
│   ├── models/
│   │   ├── envelope.py          ← MessageEnvelope, FCAPSDomain, Severity, Direction
│   │   ├── base.py              ← TrishulBaseModel (shared Pydantic config)
│   │   └── responses.py         ← TrishulResponse[T], AcceptedResponse
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
│   │   ├── influxdb.py          ← InfluxDBMetrics impl
│   │   ├── victorialogs.py      ← VictoriaLogsEvents impl
│   │   └── factory.py           ← get_stores(mode) factory
│   │
│   ├── config/
│   │   └── settings.py          ← pydantic-settings BaseSettings (lru_cache)
│   │
│   ├── middleware/
│   │   ├── logging.py           ← JSON structured request/response logging
│   │   ├── rate_limit.py        ← Redis token-bucket rate limiter
│   │   └── error_handler.py     ← Global exception → TrishulResponse(error=...)
│   │
│   ├── notifications/
│   │   └── service.py           ← NATS fcaps.done.* → WebSocket broadcaster
│   │
│   └── health/
│       └── router.py            ← GET /health + GET /metrics
│
├── transformer/                 ← WORKER LAYER (Phase 2) — stub interfaces only in Phase 1
│   ├── base.py              ← Reader, Decoder, Normalizer, Encoder, Writer ABCs
│   ├── pipeline.py          ← TransformPipeline + PipelineRegistry
│   ├── normalizer.py        ← FCAPSNormalizer (shared, implemented in Phase 1)
│   ├── decoders/            ← (Phase 2)
│   ├── encoders/            ← (Phase 2)
│   ├── readers/             ← (Phase 2)
│   └── writers/             ← (Phase 2)
│
├── plugins/
│   └── webhook/                 ← Reference plugin (Phase 1 only)
│       ├── __init__.py          ← exports plugin = WebhookPlugin()
│       ├── router.py            ← /api/v1/webhook/* (5 standard endpoints)
│       ├── models.py            ← WebhookPayload Pydantic model
│       ├── simulator.py         ← Synthetic webhook event generator
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
├── pyproject.toml
└── .dockerignore
```

> **Note on `transformer/` in Phase 1**: The ABCs (`base.py`), `TransformPipeline`, `PipelineRegistry`, and `FCAPSNormalizer` are stubbed/defined in Phase 1 so the Webhook reference plugin can wire a minimal pipeline. All decoder/encoder/reader/writer implementations are Phase 2 work.

---

## 7. Authentication Design (Frozen)

### Dual-Mode Auth

| Mode | Consumer | Token | Storage | Lifetime |
|------|----------|-------|---------|----------|
| JWT Bearer | UI / human users | HS256 signed | Redis blocklist only | 15min access / 7d refresh |
| API Key | Machines / plugins / CI | SHA-256 hash | Redis hash | Until revoked |

### Middleware Execution Order
```
Request
  1. RateLimitMiddleware      ← Redis token bucket (per IP or client_id)
  2. RequestLoggingMiddleware ← JSON log: method, path, client_ip, trace_id
  3. AuthMiddleware
     ├─ PUBLIC_PATHS bypass   → /health, /metrics, /docs, /openapi.json,
     │                           /api/v1/auth/login, /api/v1/auth/refresh
     ├─ Bearer <JWT>          → decode_jwt() → check Redis blocklist → 401 if hit
     ├─ X-API-Key: <key>      → SHA-256 hash → Redis lookup → 401 if missing
     └─ attach request.state.user = { id, username, roles, auth_type }
  4. RBAC check               ← route decorator declares required_role
  5. Route Handler
  6. ErrorHandlerMiddleware   ← catches all exceptions → TrishulResponse(error=...)
```

### RBAC Roles
| Role | Permissions |
|------|-------------|
| `admin` | All endpoints including user + API key management |
| `operator` | All plugin endpoints (read + write + simulate). No user mgmt. |
| `viewer` | GET endpoints only across all plugins |
| `plugin:{name}` | Scoped to `/api/v1/{name}/*` only (for machine clients) |

### Rate Limiting
- Default: **60 req/min** per client (IP for anon, `user_id` for authenticated)
- Plugin API keys: **600 req/min** (set at key creation)
- Redis key: `ratelimit:{client_id}` with INCR + TTL = 60s window

---

## 8. NATS JetStream — Stream Definitions (Frozen)

| Stream | Subject Pattern | Retention | Storage | Max Age | Purpose |
|--------|-----------------|-----------|---------|---------|--------|
| `FCAPS_INGEST` | `fcaps.ingest.>` | Limits | **File** | 1hr | Raw inbound — survives restart |
| `FCAPS_PROCESS` | `fcaps.process.>` | WorkQueue | **Memory** | — | Once-and-only-once transform queue |
| `FCAPS_DONE` | `fcaps.done.>` | Limits | **Memory** | 30min | Processed envelopes → fan-out |
| `FCAPS_SIM` | `fcaps.sim.>` | Limits | **Memory** | 1hr | Simulated outbound audit |

**Subject naming (frozen):**
```
fcaps.ingest.{protocol}     e.g. fcaps.ingest.snmp
fcaps.process.{protocol}    e.g. fcaps.process.ves
fcaps.done.{domain}         e.g. fcaps.done.fm | fcaps.done.pm | fcaps.done.log
fcaps.sim.{protocol}        e.g. fcaps.sim.snmp
```

**Consumers (provisioned at startup):**
- `transformer-worker` → pull consumer on `fcaps.ingest.>` (Phase 2 does the processing; Phase 1 stubs the consumer)
- `storage-writer` → push consumer on `fcaps.done.>`
- `ws-broadcaster` → push consumer on `fcaps.done.>`

---

## 9. Storage Adapters (Frozen Interface)

```python
class MetricsStore(ABC):          # InfluxDB in lab/prod
    async def write_pm(self, envelope: MessageEnvelope) -> None: ...
    async def query_pm(self, source_ne, start, end, metric_name=None) -> list[dict]: ...
    async def health(self) -> bool: ...

class EventStore(ABC):            # VictoriaLogs in lab/prod
    async def write_fm(self, envelope: MessageEnvelope) -> None: ...
    async def write_log(self, envelope: MessageEnvelope) -> None: ...
    async def search(self, query, domain, start, end, limit=100) -> list[dict]: ...
    async def health(self) -> bool: ...
```

Factory: `get_stores(STORAGE_MODE)` → `(MetricsStore, EventStore)`
- `lab` | `prod` → `InfluxDBMetrics` + `VictoriaLogsEvents`

---

## 10. Shared Models (Frozen)

```python
# MessageEnvelope — the single unit of data across the entire system
class MessageEnvelope(BaseModel):
    id:           str           # UUID, auto-generated
    schema_ver:   str = "1.0"   # bump on breaking changes
    timestamp:    datetime      # UTC, auto-generated
    domain:       FCAPSDomain   # FM | PM | LOG
    protocol:     str           # snmp | ves | protobuf | avro | webhook | sftp
    source_ne:    str           # Network Element identifier
    direction:    Direction     # inbound | outbound | simulated
    severity:     Severity | None  # required for FM; None for PM/LOG
    raw_payload:  dict          # original inbound data
    normalized:   dict          # protocol-agnostic decoded fields
    tags:         list[str]
    trace_id:     str | None    # for distributed tracing

# Uniform API response — every endpoint returns one of these
class TrishulResponse(BaseModel, Generic[T]):
    success:  bool
    data:     T | None    = None
    error:    str | None  = None
    trace_id: str | None  = None

class AcceptedResponse(BaseModel):  # for 202 async responses
    envelope_id: str
    status:  str = "accepted"
    message: str
```

---

## 11. Error Handling (Frozen)

| Exception | HTTP | Error Message |
|-----------|------|---------------|
| `AuthenticationError` | 401 | "Authentication required" / "Token expired" |
| `AuthorizationError` | 403 | "Insufficient permissions: requires {role}" |
| `RateLimitExceeded` | 429 | "Rate limit exceeded. Retry after {n}s" |
| `ValidationError` | 422 | Pydantic field-level detail |
| `PluginNotFoundError` | 404 | "Plugin '{name}' not registered" |
| `BusPublishError` | 503 | "Message bus unavailable" |
| `StorageError` | 503 | "Storage write failed: {store}" |
| Unhandled | 500 | "Internal error" + trace_id |

- All 5xx: log full traceback at ERROR level with `trace_id`
- All 4xx: log at WARNING with `client_id` + `path`
- **No stack traces ever in API responses**

---

## 12. Structured Logging (Frozen Format)

All log output is JSON — parsed natively by VictoriaLogs.

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
request_received        envelope_ingested
request_completed       envelope_processed
auth_success            storage_write_failed
auth_failure            pipeline_started
rate_limit_exceeded     pipeline_completed
nats_connected          pipeline_failed
nats_disconnected       plugin_loaded
health_check_failed     plugin_startup_failed
```

---

## 13. Health Check (Frozen)

```json
{
  "status": "healthy",
  "timestamp": "2026-02-27T08:30:00Z",
  "version": "1.0.0",
  "dependencies": {
    "nats":         { "status": "ok", "latency_ms": 1  },
    "redis":        { "status": "ok", "latency_ms": 0  },
    "influxdb":     { "status": "ok", "latency_ms": 12 },
    "victorialogs": { "status": "ok", "latency_ms": 5  }
  },
  "plugins": {
    "webhook": { "status": "ok", "version": "1.0.0" }
  }
}
```

**Status rules:**
- `nats` or `redis` error → `"unhealthy"` (critical path broken)
- `influxdb` or `victorialogs` error → `"degraded"` (app runs, storage fails)
- All ok → `"healthy"`
- 2s timeout per dependency check

---

## 14. API Endpoints — Phase 1 (Frozen)

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | None | Username + password → TokenPair |
| POST | `/api/v1/auth/refresh` | Refresh JWT | New access token |
| POST | `/api/v1/auth/logout` | Access JWT | Add jti to Redis blocklist |
| GET | `/api/v1/auth/me` | Any JWT | Current user info + roles |
| GET | `/api/v1/auth/apikeys` | admin | List API keys |
| POST | `/api/v1/auth/apikeys` | admin | Create key → raw key shown once |
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
| POST | `/api/v1/webhook/receive` | operator | Accept JSON → publish to NATS → 202 |
| POST | `/api/v1/webhook/send` | operator | POST to target URL |
| POST | `/api/v1/webhook/simulate` | operator | Generate N synthetic events |
| GET | `/api/v1/webhook/status/{id}` | operator | Envelope processing status |
| GET | `/api/v1/webhook/health` | None | Plugin health |

---

## 15. docker-compose.yml (Frozen — Lab Mode)

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
    ports: ["80:80"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

  core-api:
    build:
      context: ./trishul
      dockerfile: Dockerfile
    mem_limit: 150m
    restart: unless-stopped
    environment:
      APP_ENV:       lab
      LOG_LEVEL:     INFO
      STORAGE_MODE:  lab
      JWT_SECRET:    ${JWT_SECRET}
      NATS_URL:      nats://nats:4222
      REDIS_URL:     redis://redis:6379
      INFLUX_URL:    http://influxdb:8086
      INFLUX_TOKEN:  ${INFLUX_TOKEN}
      INFLUX_ORG:    trishul
      INFLUX_BUCKET: fcaps_pm
      VICTORIA_URL:  http://victorialogs:9428
      SQLITE_PATH:   /data/fcaps.db
    volumes:
      - sqlite-data:/data
    depends_on:
      nats:         { condition: service_healthy }
      redis:        { condition: service_healthy }
      influxdb:     { condition: service_healthy }
      victorialogs: { condition: service_started }
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=PathPrefix(`/api`) || PathPrefix(`/docs`) || PathPrefix(`/openapi.json`) || Path(`/health`) || Path(`/metrics`)"

  nats:
    image: nats:2.10-alpine
    mem_limit: 64m
    restart: unless-stopped
    command: ["-js", "-sd", "/data", "-m", "8222"]
    volumes: ["nats-data:/data"]
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
      DOCKER_INFLUXDB_INIT_MODE:        setup
      DOCKER_INFLUXDB_INIT_ORG:         trishul
      DOCKER_INFLUXDB_INIT_BUCKET:      fcaps_pm
      DOCKER_INFLUXDB_INIT_RETENTION:   30d
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: ${INFLUX_TOKEN}
    volumes: ["influx-data:/var/lib/influxdb2"]
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
    volumes: ["vlogs-data:/vlogs-data"]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.vlogs.rule=PathPrefix(`/vlogs`)"

volumes:
  nats-data:
  influx-data:
  vlogs-data:
  sqlite-data:
```

---

## 16. .env.example (Frozen)

```env
# App
APP_ENV=lab
LOG_LEVEL=INFO
STORAGE_MODE=lab

# Auth (generate: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET=change-me-32-byte-hex
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=7
RATE_LIMIT_DEFAULT=60
RATE_LIMIT_PLUGIN=600

# NATS
NATS_URL=nats://nats:4222

# Redis
REDIS_URL=redis://redis:6379

# InfluxDB (generate token: python -c "import secrets; print(secrets.token_hex(24))")
INFLUX_URL=http://influxdb:8086
INFLUX_TOKEN=change-me-influx-token
INFLUX_ORG=trishul
INFLUX_BUCKET=fcaps_pm

# VictoriaLogs
VICTORIA_URL=http://victorialogs:9428

# SQLite
SQLITE_PATH=/data/fcaps.db
```

---

## 17. Dockerfile (Frozen)

```dockerfile
# Stage 1: build deps
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN adduser --disabled-password --gecos "" trishul
USER trishul
EXPOSE 8000
CMD ["uvicorn", "core.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
```

---

## 18. Deliverables Checklist

### Infrastructure
- [ ] `docker-compose.yml` — all 5 services + healthchecks
- [ ] `.env.example` — all vars documented
- [ ] `Dockerfile` — multi-stage, non-root user
- [ ] `pyproject.toml` — all deps pinned

### Core App Factory
- [ ] `core/app.py` — FastAPI factory + lifespan (8-step startup sequence)
- [ ] `core/config/settings.py` — pydantic-settings with `lru_cache`
- [ ] `core/dependencies.py` — all `Depends()` wrappers
- [ ] Middleware stack wired: rate_limit → logging → auth → error_handler

### Models
- [ ] `MessageEnvelope` (schema_ver, trace_id, Direction, Severity enums)
- [ ] `TrishulResponse[T]` + `AcceptedResponse`
- [ ] `TrishulBaseModel` shared config

### Auth
- [ ] `AuthMiddleware` (JWT + API Key, PUBLIC_PATHS, RBAC)
- [ ] `jwt_handler.py` (encode, decode, refresh — HS256)
- [ ] SQLite `users` table + bcrypt password auth
- [ ] Redis API key store + JWT blocklist
- [ ] Auth router: all 7 endpoints
- [ ] `@require_role()` decorator

### Bus
- [ ] NATS singleton client + auto-reconnect
- [ ] Stream provisioner: 4 streams on startup
- [ ] `publish_envelope()` helper

### Transformer (Stubs for Phase 1)
- [ ] `transformer/base.py` — Reader, Decoder, Normalizer, Encoder, Writer ABCs
- [ ] `transformer/pipeline.py` — TransformPipeline + PipelineRegistry (empty)
- [ ] `transformer/normalizer.py` — FCAPSNormalizer (implemented, used by Webhook plugin)

### Storage
- [ ] `MetricsStore` + `EventStore` ABCs
- [ ] `InfluxDBMetrics` (write_pm, query_pm, health)
- [ ] `VictoriaLogsEvents` (write_fm, write_log, search, health)
- [ ] `StorageFactory`

### Middleware
- [ ] `RateLimitMiddleware` — Redis token bucket
- [ ] `RequestLoggingMiddleware` — JSON, injects trace_id
- [ ] `ErrorHandlerMiddleware` — all exceptions → TrishulResponse

### Health + Metrics
- [ ] `GET /health` — 3-state, 2s timeout, per-dep status
- [ ] `GET /metrics` — Prometheus format
- [ ] Core counters: `trishul_envelope_ingest_total`, `trishul_auth_failure_total`, `trishul_request_duration_seconds`

### Plugin Registry
- [ ] `FCAPSPlugin` ABC (name, version, domains, get_router, get_nats_subjects, on_startup, on_shutdown, get_metadata)
- [ ] `PluginRegistry` singleton with `load_all()` auto-discovery
- [ ] `GET /api/v1/plugins/registry`

### Reference Plugin (Webhook)
- [ ] `WebhookPlugin` implementing `FCAPSPlugin`
- [ ] All 5 endpoints: receive, send, simulate, status, health
- [ ] Full ingest → NATS → 202 flow working end-to-end
- [ ] Simulator generating synthetic events

### Tests
- [ ] `test_auth.py` — login, refresh, logout, RBAC, rate limit
- [ ] `test_envelope.py` — model validation, serialization
- [ ] `test_health.py` — healthy/degraded/unhealthy states
- [ ] `test_nats.py` — publish + consume round-trip
- [ ] `test_webhook_plugin.py` — full receive → NATS → 202 flow
