# Trishul — Architecture Overview

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        Traefik v3                                 │
│              (TLS termination, routing, rate limiting)            │
└────────────┬─────────────────────────────────────┬───────────────┘
             │                                     │
    ┌────────▼────────┐                   ┌────────▼────────┐
    │  Shell UI        │                   │  Core API       │
    │  (React + Vite   │◄─── REST/WS ─────►│  (FastAPI)      │
    │  Module Fed.)    │                   │  Plugin Registry│
    └────────┬────────┘                   └────────┬────────┘
             │                                     │
    ┌────────▼───────────────────────────────────────────────┐
    │             NATS JetStream (Message Bus)                │
    │    fcaps.ingest.*  |  fcaps.process.*  |  fcaps.done.* │
    └──┬──────────┬──────────┬──────────┬──────────┬─────────┘
       │          │          │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
  │ SNMP   │ │Protobuf│ │  VES   │ │Webhook │ │  SFTP  │
  │ Plugin │ │ Plugin │ │ Plugin │ │ Plugin │ │ Plugin │
  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
       │          │          │          │          │
  ┌──────────────────────────────────────────────────────┐
  │           Transformer Engine (Phase 2)                │
  │   Reader → Decoder → Normalizer → Encoder → Writer   │
  └──────────────────────────────────────────────────────┘
       │
  ┌────▼──────────────────────────┐
  │  Storage Layer                 │
  │  InfluxDB  │  VictoriaLogs     │
  │  (PM)      │  (FM + Logs)      │
  └───────────────────────────────┘
```

## Core Contracts

### MessageEnvelope
All protocol messages are normalized into a single `MessageEnvelope` before any storage or notification:

```python
class FCAPSDomain(str, Enum):
    FM  = "FM"   # Fault Management
    PM  = "PM"   # Performance Management
    LOG = "LOG"

class MessageEnvelope(BaseModel):
    id: str                   # UUID
    timestamp: datetime
    domain: FCAPSDomain
    protocol: str             # snmp | ves | protobuf | avro | webhook | sftp
    source_ne: str            # Network Element identifier
    direction: str            # inbound | outbound | simulated
    severity: str | None      # FM: CRITICAL | MAJOR | MINOR | WARNING | CLEARED
    raw_payload: dict
    normalized: dict          # Protocol-agnostic fields
    tags: list[str] = []
```

### Plugin Contract
Every protocol plugin must satisfy:
- Implement `FCAPSPlugin` base class → export `plugin` instance
- Place in `plugins/` directory (auto-discovered at startup)
- Normalize all events to `MessageEnvelope` before publishing to NATS
- Expose `GET /health` and Prometheus `/metrics`
- All config via env vars / pydantic-settings
- Publish notifications only via shared `NotificationService`

## Auth Flow

```
HTTP Request
  → Auth Middleware
    ├─ Authorization: Bearer <JWT>  → decode + validate claims
    ├─ X-API-Key: <key>             → Redis lookup → client metadata
    └─ Public path (/health, /docs) → pass-through
  → RBAC check (role vs route scope)
  → Route Handler
```

## Async Call Flow

```
HTTP POST /api/v1/{protocol}/receive
  → Auth Middleware
  → Plugin Handler (validate + assign envelope_id)
  → NATS Publish → fcaps.ingest.{protocol}
  → HTTP 202 Accepted { envelope_id }

[Async — decoupled from HTTP response]
  → Ingest Worker (NATS JetStream consumer)
  → Transformer Pipeline (Phase 2)
  → Storage Writers (InfluxDB / VictoriaLogs)
  → NATS Publish → fcaps.done.{domain}
  → NotificationService → WebSocket broadcast (Phase 4)
```

## RBAC Roles

| Role | Permissions |
|------|-------------|
| `admin` | All plugins, read + write + simulate + config |
| `operator` | All plugins, read + simulate |
| `viewer` | All plugins, read only |
| `plugin:{name}` | Scoped to one protocol only |

## Storage Routing

```
MessageEnvelope
  ├─ domain=PM  → InfluxDB (measurement: pm_metrics)
  ├─ domain=FM  → VictoriaLogs (stream: fm_alarms)
  └─ domain=LOG → VictoriaLogs (stream: fcaps_logs)
```
