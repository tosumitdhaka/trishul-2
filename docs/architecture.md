# Trishul — Complete Architecture

**App**: Trishul — FCAPS Simulation, Parsing & Visualization Platform  
**Stack**: FastAPI · NATS JetStream · InfluxDB · VictoriaLogs · Redis · SQLite · Traefik  
**Mode**: Lab (single-node, containerized)

---

## 1. Full System Component Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Traefik v3 (Port 80)                             │
│         Reverse proxy · routing · container-label auto-discovery            │
└──────────────┬──────────────────────────────────────────┬───────────────────┘
               │  /api/*  /health  /metrics  /docs         │  /vlogs/*
               │                                           │
  ┌────────────▼────────────────────────────┐    ┌────────▼────────────┐
  │          core-api  (FastAPI)             │    │  victorialogs:9428  │
  │                                          │    │  (direct query UI)  │
  │  Middleware Stack (in order):            │    └─────────────────────┘
  │  1. RateLimitMiddleware (Redis)          │
  │  2. RequestLoggingMiddleware (JSON)      │
  │  3. AuthMiddleware (JWT / API Key)       │
  │  4. ErrorHandlerMiddleware               │
  │                                          │
  │  Routers:                                │
  │  ├─ /api/v1/auth/*    (AuthRouter)       │
  │  ├─ /api/v1/plugins/* (RegistryRouter)   │
  │  ├─ /api/v1/webhook/* (WebhookPlugin)    │
  │  ├─ /health           (HealthRouter)     │
  │  └─ /metrics          (PrometheusRouter) │
  │                                          │
  │  Plugin Registry (singleton)             │
  │  └─ auto-loads plugins/ at startup       │
  │                                          │
  │  Lifespan Hooks:                         │
  │  startup  → NATS connect                 │
  │           → provision JetStream streams  │
  │           → load all plugins             │
  │           → storage health check         │
  │  shutdown → NATS drain                   │
  └──────────┬──────────────────────┬────────┘
             │                      │
   ┌─────────▼──────────┐  ┌───────▼──────────────────────┐
   │  Redis 7 Alpine     │  │  NATS JetStream 2.10 Alpine   │
   │  :6379              │  │  :4222  (client)              │
   │                     │  │  :8222  (monitoring HTTP)     │
   │  Key namespaces:    │  │                               │
   │  apikey:{sha256}    │  │  Streams:                     │
   │  blocklist:{jti}    │  │  FCAPS_INGEST  (file-backed)  │
   │  ratelimit:{id}     │  │  FCAPS_PROCESS (workqueue)    │
   │  dedup:{env_id}     │  │  FCAPS_DONE    (memory)       │
   └─────────────────────┘  │  FCAPS_SIM     (memory)       │
                             │                               │
   ┌─────────────────────┐  │  Consumers (Phase 1):         │
   │  SQLite             │  │  ws-broadcaster ← fcaps.done.>│
   │  /data/fcaps.db     │  │  storage-writer ← fcaps.done.>│
   │                     │  └───────────────────────────────┘
   │  Tables:            │
   │  users              │  ┌───────────────────────────────┐
   │  api_keys           │  │  InfluxDB 2 OSS Alpine        │
   │  audit_log          │  │  :8086                        │
   └─────────────────────┘  │  org: trishul                 │
                             │  bucket: fcaps_pm             │
                             │  retention: 30d               │
                             │  → PM metrics (time-series)   │
                             └───────────────────────────────┘

                             ┌───────────────────────────────┐
                             │  VictoriaLogs                 │
                             │  :9428                        │
                             │  retention: 30d               │
                             │  → FM alarms (structured)     │
                             │  → LOG entries (full-text)    │
                             └───────────────────────────────┘
```

---

## 2. Middleware Execution Order

Every HTTP request passes through this exact stack before reaching any route handler:

```
Incoming HTTP Request
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 1. RateLimitMiddleware                               │
│    • lookup Redis key: ratelimit:{client_id}         │
│    • default: 60 req/min (token bucket)              │
│    • plugin API keys: 600 req/min                    │
│    • exceeded → 429 TrishulResponse(error=...)       │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│ 2. RequestLoggingMiddleware                          │
│    • generate trace_id (UUID) → attach to request    │
│    • log JSON: {timestamp, method, path,             │
│                 client_ip, trace_id}                 │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│ 3. AuthMiddleware                                    │
│    • PUBLIC_PATHS? → skip to handler                 │
│    • Authorization: Bearer <JWT>?                    │
│      → decode_jwt() → check Redis blocklist          │
│      → 401 if expired / blocklisted                  │
│    • X-API-Key: <key>?                               │
│      → SHA-256(key) → Redis lookup                   │
│      → 401 if not found                              │
│    • attach request.state.user, .auth_type, .roles   │
│    • RBAC: route requires role? → 403 if mismatch    │
└─────────────────────┬───────────────────────────────┘
                      │
              ┌───────▼────────┐
              │  Route Handler  │
              └───────┬────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│ 4. ErrorHandlerMiddleware (wraps entire stack)       │
│    • AuthenticationError  → 401                      │
│    • AuthorizationError   → 403                      │
│    • RateLimitExceeded    → 429                      │
│    • ValidationError      → 422                      │
│    • BusPublishError      → 503                      │
│    • StorageError         → 503                      │
│    • Unhandled            → 500 + log traceback      │
│    • All → TrishulResponse(success=False, error=...) │
└─────────────────────────────────────────────────────┘
```

---

## 3. User Flows

### 3.1 First-Time Login (Human User / UI)

```
User                      core-api                  Redis        SQLite
 │                            │                       │             │
 │  POST /api/v1/auth/login   │                       │             │
 │  { username, password }    │                       │             │
 │ ─────────────────────────► │                       │             │
 │                            │  SELECT user          │             │
 │                            │  WHERE username=?  ─────────────────►
 │                            │                       │             │
 │                            │◄── user row (hashed_pw, roles) ─────┤
 │                            │                       │             │
 │                            │  bcrypt.verify()      │             │
 │                            │  → 401 if fail        │             │
 │                            │                       │             │
 │                            │  encode_jwt(access)   │             │
 │                            │  encode_jwt(refresh)  │             │
 │                            │  (no Redis write for login)         │
 │                            │                       │             │
 │◄── 200 { access_token,     │                       │             │
 │         refresh_token,     │                       │             │
 │         token_type: bearer}│                       │             │
```

### 3.2 Token Refresh

```
User                      core-api                  Redis
 │                            │                       │
 │  POST /api/v1/auth/refresh │                       │
 │  Authorization: Bearer     │                       │
 │  <refresh_token>           │                       │
 │ ─────────────────────────► │                       │
 │                            │  decode_jwt()         │
 │                            │  verify type=refresh  │
 │                            │  check blocklist:{jti}─►
 │                            │◄── not found (ok) ────┤
 │                            │  encode new access_token
 │◄── 200 { access_token }    │                       │
```

### 3.3 Logout

```
User                      core-api                  Redis
 │                            │                       │
 │  POST /api/v1/auth/logout  │                       │
 │  Authorization: Bearer     │                       │
 │  <access_token>            │                       │
 │ ─────────────────────────► │                       │
 │                            │  decode_jwt()         │
 │                            │  extract jti, exp     │
 │                            │  ttl = exp - now()    │
 │                            │  SET blocklist:{jti}  │
 │                            │  EX {ttl}          ──►│
 │◄── 200 { success: true }   │                       │
```

### 3.4 API Key Creation (Admin)

```
Admin                     core-api                  Redis        SQLite
 │                            │                       │             │
 │  POST /api/v1/auth/apikeys │                       │             │
 │  { client_id, roles,       │                       │             │
 │    description, rate_limit}│                       │             │
 │ ─────────────────────────► │                       │             │
 │                            │  generate raw_key     │             │
 │                            │  = secrets.token_hex(32)
 │                            │  hashed = SHA-256(raw_key)
 │                            │                       │             │
 │                            │  INSERT api_keys ──────────────────►│
 │                            │  (store hash, never raw)            │
 │                            │                       │             │
 │                            │  HSET apikey:{hash}   │             │
 │                            │  {client_id, roles,   │             │
 │                            │   rate_limit, active} ►             │
 │                            │                       │             │
 │◄── 201 { key: raw_key }    │                       │             │
 │    (shown ONCE, never again)                        │             │
```

---

## 4. Data Flows

### 4.1 Inbound Message Flow (Receive → Store)

This is the primary ingestion path. HTTP returns fast (202), all heavy work is async.

```
External Source           core-api                  NATS              Workers
(NE / simulator)          Plugin Handler             JetStream         (async)
       │                       │                       │                  │
       │  POST                 │                       │                  │
       │  /api/v1/{proto}      │                       │                  │
       │  /receive             │                       │                  │
       │  { raw payload }      │                       │                  │
       │ ─────────────────────►│                       │                  │
       │                       │ [middleware stack]     │                  │
       │                       │ validate raw payload   │                  │
       │                       │ assign envelope_id     │                  │
       │                       │ check dedup:           │                  │
       │                       │  Redis GET dedup:{id}  │                  │
       │                       │  → skip if exists      │                  │
       │                       │                       │                  │
       │                       │ PUBLISH                │                  │
       │                       │ fcaps.ingest.{proto}  ►│                  │
       │                       │ { envelope_id,         │                  │
       │                       │   raw_payload,         │                  │
       │                       │   meta }               │                  │
       │                       │                       │                  │
       │◄── 202 Accepted ──────│                       │                  │
       │  { envelope_id,       │                       │                  │
       │    status: accepted } │                       │                  │
       │                       │                       │                  │
       │             [ASYNC — HTTP response already sent]                  │
       │                       │                       │                  │
       │                       │           ┌───────────┘                  │
       │                       │           │ FCAPS_INGEST                 │
       │                       │           │ consumer:                    │
       │                       │           │ transformer-worker ──────────►
       │                       │           │                              │
       │                       │           │           Phase 2 Transformer │
       │                       │           │           decode raw_payload  │
       │                       │           │           → MessageEnvelope   │
       │                       │           │                              │
       │                       │           │           PUBLISH             │
       │                       │           │           fcaps.done.{domain}►│
       │                       │           │                              │
       │                       │           │      ┌───────────────────────┘
       │                       │           │      │ FCAPS_DONE consumers:
       │                       │           │      │
       │                       │           │      ├─► storage-writer
       │                       │           │      │     ├─ domain=PM → InfluxDB
       │                       │           │      │     ├─ domain=FM → VictoriaLogs
       │                       │           │      │     └─ domain=LOG → VictoriaLogs
       │                       │           │      │
       │                       │           │      └─► ws-broadcaster
       │                       │           │            → WebSocket clients (Phase 4)
```

### 4.2 Outbound Simulation Flow (Simulate → Send)

```
Operator                  core-api                  NATS
 │                        Plugin Handler              JetStream
 │                             │                       │
 │  POST                       │                       │
 │  /api/v1/{proto}/simulate   │                       │
 │  { target, count,           │                       │
 │    interval, params }       │                       │
 │ ────────────────────────────►                       │
 │                             │ [middleware stack]     │
 │                             │                       │
 │                             │ Simulator.generate()  │
 │                             │ → list[MessageEnvelope]
 │                             │ direction=simulated   │
 │                             │                       │
 │                             │ for each envelope:    │
 │                             │   encode to protocol  │
 │                             │   send to target      │
 │                             │   PUBLISH             │
 │                             │   fcaps.sim.{proto} ─►│
 │                             │   (audit trail)       │
 │                             │                       │
 │◄── 200 { success: true,     │                       │
 │    sent: N,                 │                       │
 │    envelope_ids: [...] }    │                       │
```

### 4.3 Query / Visualization Flow

```
UI / Client               core-api                InfluxDB    VictoriaLogs
 │                        Query Handler              │              │
 │                             │                     │              │
 │  GET /api/v1/pm/metrics     │                     │              │
 │  ?source_ne=router-01       │                     │              │
 │  &start=-1h&end=now         │                     │              │
 │ ────────────────────────────►                     │              │
 │                             │ MetricsStore        │              │
 │                             │ .query_pm()         │              │
 │                             │ Flux/InfluxQL ──────►              │
 │                             │◄── [{time, value}] ─┤              │
 │◄── 200 TrishulResponse      │                     │              │
 │    { data: [...metrics] }   │                     │              │
 │                             │                     │              │
 │  GET /api/v1/fm/alarms      │                     │              │
 │  ?query=severity:CRITICAL   │                     │              │
 │  &start=-6h                 │                     │              │
 │ ────────────────────────────►                     │              │
 │                             │ EventStore          │              │
 │                             │ .search()           │              │
 │                             │ LogsQL ─────────────────────────── ►
 │                             │◄── [{alarm docs}] ──────────────── ┤
 │◄── 200 TrishulResponse      │                     │              │
 │    { data: [...alarms] }    │                     │              │
```

### 4.4 Envelope Processing Status Check

```
Client                    core-api                  Redis
 │                             │                       │
 │  GET                        │                       │
 │  /api/v1/{proto}            │                       │
 │  /status/{envelope_id}      │                       │
 │ ────────────────────────────►                       │
 │                             │ GET dedup:{env_id} ──►│
 │                             │◄── { status,          │
 │                             │     processed_at,     │
 │                             │     domain,           │
 │                             │     error? }          │
 │◄── 200 TrishulResponse      │                       │
 │    { data: { status,        │                       │
 │              envelope_id,   │                       │
 │              ... } }        │                       │
```

---

## 5. NATS JetStream Flow Detail

```
                    NATS JetStream Streams

  PUBLISH                     STREAM              CONSUMERS
  ───────                     ──────              ─────────

  Plugin.receive()           FCAPS_INGEST          transformer-worker
  ──────────────►  fcaps.ingest.{proto}  ────────► (Phase 2, pull consumer)
                   [File-backed, 1hr TTL]          Acks after transform done

                             FCAPS_PROCESS         (Phase 2 internal)
  Transformer    fcaps.process.{proto}  ────────► WorkQueue: consumed once
  ──────────────►  [Memory, workqueue]

  Transformer              FCAPS_DONE              storage-writer  (push)
  ──────────────►  fcaps.done.{domain}  ──────┬──► writes InfluxDB / VictoriaLogs
                   [Memory, 30min TTL]  ───────┴──► ws-broadcaster (push)
                                                    → WebSocket clients (Phase 4)

  Plugin.simulate()          FCAPS_SIM             (audit / Phase 4 feed)
  ──────────────►  fcaps.sim.{proto}    ────────► ws-broadcaster (optional)
                   [Memory, 1hr TTL]
```

**Subject naming convention (frozen):**
```
fcaps.ingest.{protocol}     fcaps.ingest.snmp  | fcaps.ingest.ves
fcaps.process.{protocol}    fcaps.process.snmp
fcaps.done.{domain}         fcaps.done.fm      | fcaps.done.pm  | fcaps.done.log
fcaps.sim.{protocol}        fcaps.sim.snmp
```

---

## 6. Storage Write Detail

### 6.1 InfluxDB — PM Metrics

```
MessageEnvelope (domain=PM)
  │
  ▼  InfluxDBMetrics.write_pm()
  │
  │  Line protocol:
  │  pm_metrics,
  │    protocol=snmp,
  │    source_ne=router-01,
  │    metric_name=ifInOctets
  │  value=12345.0
  │  <timestamp ns>
  │
  └──────────────────► InfluxDB bucket: fcaps_pm
                        retention: 30d
                        query: Flux / InfluxQL
```

### 6.2 VictoriaLogs — FM Alarms + Logs

```
MessageEnvelope (domain=FM | LOG)
  │
  ▼  VictoriaLogsEvents.write_fm() or write_log()
  │
  │  JSON Lines (push to /insert/jsonline?_stream_fields=protocol,source_ne,domain):
  │  {
  │    _time: "2026-02-27T08:30:00Z",
  │    _msg: "linkDown on router-01 (ifIndex 2)",
  │    domain: "FM",
  │    protocol: "snmp",
  │    source_ne: "router-01",
  │    severity: "MAJOR",
  │    envelope_id: "uuid",
  │    ...normalized fields
  │  }
  │
  └──────────────────► VictoriaLogs :9428
                        query: LogsQL
                        e.g.: domain:FM AND severity:CRITICAL
```

---

## 7. Auth Data Flow Detail

### Redis Key Structure

```
Key                          Type     TTL          Value
──────────────────────────   ──────   ──────────   ─────────────────────────────────
blocklist:{jti}              STRING   rem(exp)     "1" (presence = blocked)
apikey:{sha256(raw_key)}     HASH     none         client_id, roles, rate_limit, active
ratelimit:{client_id}        STRING   60s window   request count (INCR + EXPIRE)
dedup:{envelope_id}          HASH     15min        status, processed_at, domain, error
```

### SQLite Schema

```sql
CREATE TABLE users (
    id          TEXT PRIMARY KEY,  -- UUID
    username    TEXT UNIQUE NOT NULL,
    hashed_pw   TEXT NOT NULL,     -- bcrypt
    roles       TEXT NOT NULL,     -- JSON array: ["admin"]
    is_active   BOOLEAN DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_keys (
    id          TEXT PRIMARY KEY,  -- UUID
    client_id   TEXT NOT NULL,
    key_hash    TEXT UNIQUE NOT NULL,  -- SHA-256, never store raw
    roles       TEXT NOT NULL,         -- JSON array
    rate_limit  INTEGER DEFAULT 60,
    description TEXT,
    is_active   BOOLEAN DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used   DATETIME
);

CREATE TABLE audit_log (
    id          TEXT PRIMARY KEY,
    user_id     TEXT,
    action      TEXT NOT NULL,  -- "login", "api_key_created", "plugin_loaded"
    detail      TEXT,           -- JSON
    ip_address  TEXT,
    trace_id    TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8. Health Check Flow

```
Client              core-api            NATS    Redis   InfluxDB  VictoriaLogs
 │                      │                 │       │         │           │
 │  GET /health         │                 │       │         │           │
 │ ────────────────────►│                 │       │         │           │
 │                      │  ping (2s TO) ─►│       │         │           │
 │                      │  ping (2s TO) ──────── ►│         │           │
 │                      │  ping (2s TO) ─────────────────── ►           │
 │                      │  ping (2s TO) ───────────────────────────────►│
 │                      │                 │       │         │           │
 │◄── 200 / 503         │                 │       │         │           │
 │  {                   │                 │       │         │           │
 │    status: healthy|  │                 │       │         │           │
 │            degraded| │                 │       │         │           │
 │            unhealthy,│                 │       │         │           │
 │    dependencies: {   │                 │       │         │           │
 │      nats:    ok|err,│                 │       │         │           │
 │      redis:   ok|err,│                 │       │         │           │
 │      influxdb: ...,  │                 │       │         │           │
 │      victorialogs:...│                 │       │         │           │
 │    },                │                 │       │         │           │
 │    plugins: { ... }  │                 │       │         │           │
 │  }                   │                 │       │         │           │

Rules:
  NATS error   → status = unhealthy  (cannot process anything)
  Redis error  → status = unhealthy  (auth broken)
  InfluxDB err → status = degraded   (PM writes fail, reads fail)
  VLogs error  → status = degraded   (FM/Log writes fail)
  All ok       → status = healthy
```

---

## 9. Plugin Startup Flow

```
create_app() called
  │
  ▼
[lifespan: startup]
  │
  ├─1. settings = get_settings()          load + validate all env vars
  │
  ├─2. nats_client.connect()              connect to NATS :4222
  │    └─ provision_streams()             create FCAPS_INGEST/PROCESS/DONE/SIM
  │                                       if not already existing
  │
  ├─3. redis_client.ping()                verify Redis connectivity
  │
  ├─4. metrics_store, event_store =       instantiate storage adapters
  │    StorageFactory.get_stores(mode)    based on STORAGE_MODE env
  │
  ├─5. PluginRegistry.load_all()          pkgutil.iter_modules(["plugins"])
  │    for each module:                   importlib.import_module()
  │      plugin = module.plugin           get plugin instance
  │      await plugin.on_startup()        plugin-level init
  │      app.include_router(              register routes at /api/v1/{name}
  │        plugin.get_router(),
  │        prefix=/api/v1/{plugin.name})
  │      registry.register(plugin)        add to in-memory registry
  │      log: plugin_loaded               JSON log event
  │
  ├─6. start ws-broadcaster consumer     subscribe fcaps.done.> on NATS
  ├─7. start storage-writer consumer     subscribe fcaps.done.> on NATS
  │
  └─8. log: startup_complete

[lifespan: shutdown]
  ├─1. await plugin.on_shutdown() (all)   graceful plugin teardown
  ├─2. nats_client.drain()                flush pending NATS publishes
  └─3. log: shutdown_complete
```

---

## 10. Dependency Injection Pattern

All shared resources are injected via FastAPI's `Depends()` — never global singletons accessed directly in handlers.

```python
# core/dependencies.py
from fastapi import Depends, Request
from core.config.settings import get_settings, Settings
from core.storage.factory import get_stores
from core.bus.client import get_nats_client

# Settings
def settings_dep() -> Settings:
    return get_settings()

# Storage (created once at startup, reused)
_metrics_store, _event_store = None, None

def metrics_store_dep():
    return _metrics_store   # InfluxDBMetrics instance

def event_store_dep():
    return _event_store     # VictoriaLogsEvents instance

# Auth
def current_user(request: Request) -> dict:
    return request.state.user   # set by AuthMiddleware

# NATS
def nats_dep():
    return get_nats_client()    # singleton

# Usage in any route handler:
async def my_handler(
    user  = Depends(current_user),
    store = Depends(event_store_dep),
    nats  = Depends(nats_dep)
):
    ...
```

---

## 11. Uniform Response Contract

Every endpoint — across all plugins, all phases — returns one of these two shapes:

```
Synchronous result (200):
{
  "success": true,
  "data": { ... },      ← typed per endpoint
  "error": null,
  "trace_id": "abc123"
}

Async accepted (202):
{
  "envelope_id": "uuid",
  "status": "accepted",
  "message": "Message queued for processing"
}

Error (4xx / 5xx):
{
  "success": false,
  "data": null,
  "error": "Human-readable message",
  "trace_id": "abc123"  ← always present, matches server log
}
```

---

## 12. MessageEnvelope Lifecycle

```
[CREATED]                    Plugin handler assigns id, timestamp, direction=inbound
     │
     ▼
[RAW_QUEUED]                 raw_payload populated, published to fcaps.ingest.*
     │
     ▼
[PROCESSING]  (Phase 2)      Transformer decodes + normalizes → normalized dict filled
     │
     ▼
[PROCESSED]                  Published to fcaps.done.*
     │
     ├──────────────────────► Stored in InfluxDB (PM) or VictoriaLogs (FM/LOG)
     │
     └──────────────────────► Pushed to WebSocket clients (Phase 4)

[SIMULATED]                  direction=simulated, goes through same pipeline
                             but published to fcaps.sim.* (not fcaps.ingest.*)
```

---

## 13. Key Design Rules (Frozen)

1. **HTTP always returns fast**: Plugin handlers publish to NATS and return 202. No blocking I/O in handlers.
2. **Envelope is the unit**: Everything that moves through the system is a `MessageEnvelope`. No raw dicts after the plugin handler.
3. **Storage is abstract**: Plugin and transformer code never imports InfluxDB or VictoriaLogs clients directly. Always uses `MetricsStore` / `EventStore` ABC.
4. **Config is central**: All settings come from `get_settings()`. No hardcoded values anywhere.
5. **Logs are JSON**: No plain-text logs. Every log line is a parseable JSON object with `trace_id`.
6. **Errors are uniform**: Every error response is `TrishulResponse(success=False, error=...)`. No naked HTTP exceptions.
7. **Plugins are self-contained**: A plugin directory drop-in is all that's needed to add a new protocol. Core never needs modification.
8. **Auth is layered**: JWT for humans, API Keys for machines. Both flow through the same RBAC check.
9. **NATS is the only async bridge**: No celery, no background threads. Async workers are NATS consumers.
10. **Deduplication at ingest**: Redis `dedup:{envelope_id}` prevents double-processing on retries.
