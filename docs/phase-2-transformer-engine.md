# Phase 2 — Transformer Engine

**Status**: 🔵 In Design  
**Depends on**: Phase 1 (Core Foundation)  
**Prerequisite for**: Phase 3 (Protocol Plugins)

---

## Goal

Build the protocol-agnostic transformation pipeline that converts any inbound data format into a normalized `MessageEnvelope` and routes it to any output sink. This is the most reusable and critical engine in Trishul — all protocol plugins in Phase 3 are thin wrappers over this.

---

## Pipeline Architecture

```
[Reader] → [Decoder] → [Normalizer] → [Encoder] → [Writer]
   │           │            │              │           │
SFTP/WH/   Protobuf/   →MessageEnv    JSON/Avro/  NATS/OS/
SNMP/VES   Avro/JSON/                 Protobuf/   InfluxDB/
Webhook    CSV/XML                    CSV         Webhook/VictoriaLogs
```

### Stage Responsibilities

| Stage | Input | Output | Examples |
|-------|-------|--------|----------|
| **Reader** | source config | raw bytes/dict | SFTPReader, WebhookReader, NATSReader, HTTPPollReader |
| **Decoder** | raw bytes/dict | decoded dict | ProtobufDecoder, AvroDecoder, JSONDecoder, CSVDecoder, VESDecoder, SNMPDecoder |
| **Normalizer** | decoded dict + meta | MessageEnvelope | FCAPSNormalizer (shared), per-protocol overrides |
| **Encoder** | MessageEnvelope | encoded bytes/dict | JSONEncoder, AvroEncoder, ProtobufEncoder, CSVEncoder |
| **Writer** | encoded data + sink config | stored/sent | NATSWriter, VictoriaLogsWriter, InfluxDBWriter, WebhookWriter, SFTPWriter |

---

## Abstract Base Classes

```python
class Reader(ABC):
    protocol: str
    async def read(self, source_config: dict) -> bytes | dict: ...

class Decoder(ABC):
    format: str
    async def decode(self, raw: bytes | dict) -> dict: ...

class Normalizer(ABC):
    async def normalize(self, decoded: dict, meta: dict) -> MessageEnvelope: ...

class Encoder(ABC):
    format: str
    async def encode(self, envelope: MessageEnvelope) -> bytes | dict: ...

class Writer(ABC):
    target: str
    async def write(self, data: bytes | dict, sink_config: dict): ...
```

---

## Pipeline Job Config (JSON)

Pipelines are assembled dynamically — no code changes to add a new route:

```json
{
  "reader":     { "type": "sftp", "host": "10.0.0.1", "path": "/pm/data.avro" },
  "decoder":    { "type": "avro", "schema_registry": "http://schema-reg:8081" },
  "normalizer": { "domain": "PM", "source_ne": "router-01", "protocol": "avro" },
  "encoder":    { "type": "json" },
  "writer":     { "type": "influxdb", "bucket": "fcaps_pm" }
}
```

Example routes (no code changes):
- `SFTP → Avro → Normalize → JSON → InfluxDB`
- `Webhook → VES JSON → Normalize → JSON → VictoriaLogs`
- `SNMP Trap → TLV → Normalize → JSON → NATS`
- `NATS → Protobuf → Normalize → CSV → SFTP`

---

## API Endpoints (Phase 2)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/transform/run` | Synchronous pipeline run (small payloads) |
| POST | `/api/v1/transform/submit` | Async pipeline job via NATS |
| GET | `/api/v1/transform/jobs/{id}` | Job status + result envelope_id |
| GET | `/api/v1/transform/readers` | List registered Reader types |
| GET | `/api/v1/transform/decoders` | List registered Decoder types |
| GET | `/api/v1/transform/writers` | List registered Writer types |

---

## Built-in Implementations

### Readers
- `SFTPReader` — paramiko-based SFTP file pull
- `WebhookReader` — passthrough from HTTP body
- `NATSReader` — consume from JetStream subject
- `HTTPPollReader` — periodic GET poll
- `FileReader` — local/mounted file (for testing)

### Decoders
- `JSONDecoder`, `CSVDecoder`, `XMLDecoder`
- `ProtobufDecoder` — descriptor-based, dynamic `.proto` loading
- `AvroDecoder` — fastavro + optional Schema Registry
- `VESDecoder` — VES 7.x JSON schema validation + field extraction
- `SNMPDecoder` — pysnmp TLV/OID parsing → dict

### Encoders
- `JSONEncoder`, `CSVEncoder`
- `ProtobufEncoder`, `AvroEncoder`

### Writers
- `NATSWriter` — publish to JetStream subject
- `InfluxDBWriter` — line protocol write to InfluxDB
- `VictoriaLogsWriter` — JSON log push to VictoriaLogs
- `WebhookWriter` — HTTP POST to target URL
- `SFTPWriter` — write file to remote SFTP
- `CSVWriter` — append to local CSV (for export)

---

## Schema Registry

For Avro and Protobuf, a lightweight in-process schema registry backed by SQLite:

```
POST /api/v1/schemas          → register schema (Avro or .proto)
GET  /api/v1/schemas          → list schemas
GET  /api/v1/schemas/{id}     → get schema by ID
DELETE /api/v1/schemas/{id}   → remove schema
```

For production, can point to external Confluent-compatible Schema Registry.

---

## Deliverables Checklist

- [ ] `Reader`, `Decoder`, `Normalizer`, `Encoder`, `Writer` ABC hierarchy
- [ ] `TransformPipeline` assembler + `PipelineJobConfig` Pydantic model
- [ ] `PipelineRegistry` (auto-discovers and registers all stage implementations)
- [ ] All Reader implementations (SFTP, Webhook, NATS, HTTPPoll, File)
- [ ] All Decoder implementations (JSON, CSV, Protobuf, Avro, VES, SNMP)
- [ ] All Encoder implementations (JSON, CSV, Protobuf, Avro)
- [ ] All Writer implementations (NATS, InfluxDB, VictoriaLogs, Webhook, SFTP, CSV)
- [ ] Synchronous pipeline API: `POST /api/v1/transform/run`
- [ ] Async pipeline API: `POST /api/v1/transform/submit` + job status
- [ ] Lightweight schema registry (SQLite-backed)
- [ ] Unit tests for each stage implementation
- [ ] Integration test: full SFTP→Avro→InfluxDB pipeline
