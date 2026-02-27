# Phase 2 — Transformer Engine

**Status**: 🔵 In Design  
**Depends on**: Phase 1 (Core Foundation)  
**Prerequisite for**: Phase 3 (Protocol Plugins)

---

## Goal

Implement all Decoder, Encoder, Reader, and Writer stage implementations in the `transformer/` module (stubs defined in Phase 1). This unlocks the full pipeline for all protocol plugins in Phase 3.

---

## Placement (Frozen)

The Transformer Engine runs **inside `core-api`** as async NATS consumer workers. It is a code module (`transformer/`), not a separate container.

**Why not a separate container:**
- NATS JetStream already provides the decoupling between HTTP receive and processing. Container boundary is redundant.
- Plugin HTTP endpoints (e.g. `/simulate`) need to call transformer stages directly — a separate container would add internal HTTP round-trips for zero benefit.
- Future scaling path: extract `transformer/` consumers into `worker/app.py` (new entrypoint, same module imports, one new docker-compose service) — zero business logic changes needed.

---

## Module Structure

```
transformer/
├── base.py          ← ABCs: Reader, Decoder, Normalizer, Encoder, Writer  [Phase 1 stub]
├── pipeline.py      ← TransformPipeline + PipelineRegistry               [Phase 1 stub]
├── normalizer.py    ← FCAPSNormalizer (single shared impl)                [Phase 1]
├── router.py        ← /api/v1/transform/* endpoints                      [Phase 2]
├── readers/
│   ├── sftp.py        ← SFTPReader (paramiko)                             [Phase 2]
│   ├── webhook.py     ← WebhookReader (passthrough from HTTP body)         [Phase 2]
│   ├── nats.py        ← NATSReader (consume from JetStream subject)        [Phase 2]
│   ├── http_poll.py   ← HTTPPollReader (periodic GET)                     [Phase 2]
│   └── file.py        ← FileReader (local/mounted, for testing)            [Phase 2]
├── decoders/
│   ├── json.py        ← JSONDecoder                                       [Phase 2]
│   ├── csv.py         ← CSVDecoder                                        [Phase 2]
│   ├── xml.py         ← XMLDecoder                                        [Phase 2]
│   ├── protobuf.py    ← ProtobufDecoder (dynamic .proto loading)          [Phase 2]
│   ├── avro.py        ← AvroDecoder (fastavro + Schema Registry)          [Phase 2]
│   ├── ves.py         ← VESDecoder (VES 7.x schema validation)            [Phase 2]
│   └── snmp.py        ← SNMPDecoder (pysnmp TLV/OID → dict)               [Phase 2]
├── encoders/
│   ├── json.py        ← JSONEncoder                                       [Phase 2]
│   ├── csv.py         ← CSVEncoder                                        [Phase 2]
│   ├── protobuf.py    ← ProtobufEncoder                                   [Phase 2]
│   └── avro.py        ← AvroEncoder (fastavro)                            [Phase 2]
└── writers/
    ├── nats.py        ← NATSWriter (publish to JetStream)                 [Phase 2]
    ├── influxdb.py    ← InfluxDBWriter (line protocol)                    [Phase 2]
    ├── victorialogs.py← VictoriaLogsWriter (JSON Lines push)              [Phase 2]
    ├── webhook.py     ← WebhookWriter (HTTP POST to target)               [Phase 2]
    ├── sftp.py        ← SFTPWriter (write file to remote SFTP)            [Phase 2]
    └── csv.py         ← CSVWriter (append to local CSV)                   [Phase 2]
```

---

## Abstract Base Classes (Defined in Phase 1, Implemented in Phase 2)

```python
# transformer/base.py
from abc import ABC, abstractmethod
from core.models.envelope import MessageEnvelope

class Reader(ABC):
    protocol: str
    @abstractmethod
    async def read(self, source_config: dict) -> bytes | dict: ...

class Decoder(ABC):
    format: str
    @abstractmethod
    async def decode(self, raw: bytes | dict) -> dict: ...

class Normalizer(ABC):
    @abstractmethod
    async def normalize(self, decoded: dict, meta: dict) -> MessageEnvelope: ...

class Encoder(ABC):
    format: str
    @abstractmethod
    async def encode(self, envelope: MessageEnvelope) -> bytes | dict: ...

class Writer(ABC):
    target: str
    @abstractmethod
    async def write(self, data: bytes | dict, sink_config: dict) -> None: ...
```

---

## Pipeline Assembly (Defined in Phase 1)

```python
# transformer/pipeline.py
class TransformPipeline:
    def __init__(self, decoder: Decoder, normalizer: Normalizer,
                 encoder: Encoder, writer: Writer,
                 reader: Reader | None = None):
        # Reader is optional — for plugin-bound pipelines,
        # data is already in-hand from the HTTP handler.
        ...

    async def run(self, raw: bytes | dict, meta: dict,
                  sink_config: dict) -> MessageEnvelope:
        decoded   = await self.decoder.decode(raw)
        envelope  = await self.normalizer.normalize(decoded, meta)
        encoded   = await self.encoder.encode(envelope)
        await self.writer.write(encoded, sink_config)
        return envelope

    async def run_with_reader(self, source_config: dict,
                               sink_config: dict) -> MessageEnvelope:
        # Used for ad-hoc / async job pipelines with a Reader stage
        raw = await self.reader.read(source_config)
        return await self.run(raw, source_config, sink_config)


class PipelineRegistry:
    """Auto-discovers all stage implementations via pkgutil.
       Plugins call register_decoder(), register_writer() etc.
       TransformRouter uses this to assemble ad-hoc pipelines."""
    _decoders:  dict[str, Decoder]  = {}
    _encoders:  dict[str, Encoder]  = {}
    _readers:   dict[str, Reader]   = {}
    _writers:   dict[str, Writer]   = {}

    def get_pipeline(self, config: PipelineJobConfig) -> TransformPipeline: ...
```

---

## FCAPSNormalizer (Implemented in Phase 1 — Used by Webhook Plugin)

The single shared Normalizer. Every protocol decoder outputs a plain `dict`; the Normalizer maps it to a `MessageEnvelope`.

```python
# transformer/normalizer.py
class FCAPSNormalizer(Normalizer):
    async def normalize(self, decoded: dict, meta: dict) -> MessageEnvelope:
        return MessageEnvelope(
            domain     = meta["domain"],         # set by plugin
            protocol   = meta["protocol"],        # set by plugin
            source_ne  = meta.get("source_ne") or decoded.get("source_ne", "unknown"),
            direction  = meta.get("direction", Direction.INBOUND),
            severity   = decoded.get("severity"),
            raw_payload= meta.get("raw_payload", {}),
            normalized = decoded,
            trace_id   = meta.get("trace_id"),
            tags       = meta.get("tags", []),
        )
```

---

## Plugin — Transformer Relationship (Frozen)

```
Plugin role (Phase 1 / Phase 3):
  1. Receive / validate inbound data at protocol boundary
  2. Publish raw + meta to fcaps.ingest.{proto} via NATS
  3. Simulate — generate synthetic protocol-native messages

Transformer role (Phase 2):
  1. Consume from fcaps.ingest.{proto}
  2. Decode raw bytes/dict using protocol-specific Decoder
  3. Normalize to MessageEnvelope via FCAPSNormalizer
  4. Encode to output format
  5. Write to sink (NATS / InfluxDB / VictoriaLogs / Webhook / SFTP)

Plugin registers its decoder with PipelineRegistry at on_startup():
  registry.register_decoder("ves",    VESDecoder())
  registry.register_decoder("snmp",   SNMPDecoder())
  registry.register_decoder("webhook",JSONDecoder())   # simplest

Transformer auto-selects decoder by protocol field in NATS message metadata.
```

---

## Pipeline Control Mechanisms (Frozen)

| Mechanism | Trigger | Use Case | Returns |
|-----------|---------|----------|---------|
| **Static (plugin-bound)** | Inbound NATS message | Live protocol traffic, always-on | async, no return |
| **Dynamic sync** | `POST /api/v1/transform/run` | One-off conversion, testing | 200 + envelope |
| **Async job** | `POST /api/v1/transform/submit` | Batch import, SFTP file, large data | 202 + job_id |
| **Simulated** | `POST /api/v1/{proto}/simulate` | Test data generation, NE simulation | 200 + envelope_ids |

---

## Pipeline Job Config Schema

```python
class StageConfig(BaseModel):
    type: str           # decoder/encoder/reader/writer type name
    model_config = ConfigDict(extra="allow")  # all extra fields passed to stage

class PipelineJobConfig(BaseModel):
    reader:     StageConfig | None = None   # optional: for ad-hoc with Reader
    decoder:    StageConfig
    normalizer: NormalizerConfig            # domain, protocol, source_ne, direction
    encoder:    StageConfig
    writer:     StageConfig
```

**Example configs:**
```json
// SFTP Avro → InfluxDB
{
  "reader":     { "type": "sftp",    "host": "10.0.0.1", "path": "/pm/data.avro" },
  "decoder":    { "type": "avro",    "schema_id": "pm-v2" },
  "normalizer": { "domain": "PM",    "source_ne": "router-01", "protocol": "avro" },
  "encoder":    { "type": "json" },
  "writer":     { "type": "influxdb", "bucket": "fcaps_pm" }
}

// Webhook VES → VictoriaLogs
{
  "decoder":    { "type": "ves" },
  "normalizer": { "domain": "FM",    "source_ne": "ems-01", "protocol": "ves" },
  "encoder":    { "type": "json" },
  "writer":     { "type": "victorialogs" }
}

// NATS Protobuf → CSV → SFTP
{
  "reader":     { "type": "nats",    "subject": "fcaps.ingest.protobuf" },
  "decoder":    { "type": "protobuf", "schema_id": "gnmi-v1" },
  "normalizer": { "domain": "PM",    "source_ne": "router-02", "protocol": "protobuf" },
  "encoder":    { "type": "csv" },
  "writer":     { "type": "sftp",    "host": "archive.lab", "path": "/export/" }
}
```

---

## Transform API Endpoints (Phase 2)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/transform/run` | operator | Sync pipeline (small payload, inline) |
| POST | `/api/v1/transform/submit` | operator | Async pipeline job → NATS job queue |
| GET | `/api/v1/transform/jobs/{id}` | operator | Job status + result envelope_ids |
| GET | `/api/v1/transform/stages` | operator | All registered readers/decoders/encoders/writers |

---

## Schema Registry (Phase 2 — SQLite-backed)

For Avro and Protobuf schema management, stored in `fcaps.db`:

```sql
CREATE TABLE schemas (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    format      TEXT NOT NULL,   -- 'avro' | 'protobuf'
    version     TEXT NOT NULL,
    content     TEXT NOT NULL,   -- JSON schema or .proto content
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/schemas` | Register Avro/Protobuf schema |
| GET | `/api/v1/schemas` | List all schemas |
| GET | `/api/v1/schemas/{id}` | Get schema by ID |
| DELETE | `/api/v1/schemas/{id}` | Remove schema |

For production: can point `AvroDecoder` to an external Confluent-compatible Schema Registry URL via env var.

---

## Deliverables Checklist

### ABCs + Core (from Phase 1 stubs)
- [ ] `transformer/base.py` — all 5 ABCs
- [ ] `transformer/pipeline.py` — TransformPipeline + PipelineRegistry
- [ ] `transformer/normalizer.py` — FCAPSNormalizer

### Readers
- [ ] `SFTPReader` (paramiko)
- [ ] `WebhookReader` (passthrough)
- [ ] `NATSReader` (JetStream pull)
- [ ] `HTTPPollReader` (periodic GET)
- [ ] `FileReader` (local mount)

### Decoders
- [ ] `JSONDecoder`
- [ ] `CSVDecoder`
- [ ] `XMLDecoder`
- [ ] `ProtobufDecoder` (dynamic .proto)
- [ ] `AvroDecoder` (fastavro + schema registry)
- [ ] `VESDecoder` (VES 7.x validation)
- [ ] `SNMPDecoder` (pysnmp TLV/OID)

### Encoders
- [ ] `JSONEncoder`
- [ ] `CSVEncoder`
- [ ] `ProtobufEncoder`
- [ ] `AvroEncoder`

### Writers
- [ ] `NATSWriter`
- [ ] `InfluxDBWriter` (line protocol)
- [ ] `VictoriaLogsWriter` (JSON Lines)
- [ ] `WebhookWriter` (HTTP POST)
- [ ] `SFTPWriter`
- [ ] `CSVWriter`

### API + Schema Registry
- [ ] `transformer/router.py` — run, submit, jobs, stages endpoints
- [ ] Schema registry SQLite table + 4 CRUD endpoints
- [ ] `PipelineJobConfig` Pydantic model + validation

### Tests
- [ ] Unit tests per decoder (valid + invalid input)
- [ ] Unit tests per encoder
- [ ] Unit tests per writer (mocked sinks)
- [ ] Integration test: full SFTP → Avro → InfluxDB pipeline
- [ ] Integration test: full Webhook → VES → VictoriaLogs pipeline
- [ ] Integration test: NATS → Protobuf → CSV → SFTP pipeline
