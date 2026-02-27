# Phase 2 — Transformer Engine

**Status**: ✅ Complete  
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
├── base.py             ← ABCs: Reader, Decoder, Normalizer, Encoder, Writer   ✅
├── pipeline.py         ← TransformPipeline + PipelineRegistry                 ✅
├── normalizer.py       ← FCAPSNormalizer (single shared impl)                  ✅
├── schema_registry.py  ← SQLite-backed Avro/Protobuf schema store               ✅
├── router.py           ← /api/v1/transform/* + /api/v1/schemas/* endpoints      ✅
├── readers/
│   ├── sftp.py           ← SFTPReader (paramiko)                                 ✅
│   ├── webhook.py        ← WebhookReader (passthrough)                           ✅
│   ├── nats.py           ← NATSReader (JetStream pull)                           ✅
│   ├── http_poll.py      ← HTTPPollReader (periodic GET)                        ✅
│   └── file.py           ← FileReader (local/mounted)                            ✅
├── decoders/
│   ├── json.py           ← JSONDecoder                                           ✅
│   ├── csv.py            ← CSVDecoder                                            ✅
│   ├── xml.py            ← XMLDecoder                                            ✅
│   ├── protobuf.py       ← ProtobufDecoder (JSON fallback; full impl Phase 3)    ✅
│   ├── avro.py           ← AvroDecoder (fastavro + schema registry)              ✅
│   ├── ves.py            ← VESDecoder (VES 7.x schema validation)                ✅
│   └── snmp.py           ← SNMPDecoder (OID alias map + severity heuristic)      ✅
├── encoders/
│   ├── json.py           ← JSONEncoder                                           ✅
│   ├── csv.py            ← CSVEncoder                                            ✅
│   ├── protobuf.py       ← ProtobufEncoder (JSON fallback; full impl Phase 3)    ✅
│   └── avro.py           ← AvroEncoder (fastavro)                                ✅
└── writers/
    ├── nats.py           ← NATSWriter (JetStream publish)                        ✅
    ├── influxdb.py       ← InfluxDBWriter (line protocol via storage adapter)    ✅
    ├── victorialogs.py   ← VictoriaLogsWriter (JSON Lines via storage adapter)   ✅
    ├── webhook.py        ← WebhookWriter (httpx POST)                            ✅
    ├── sftp.py           ← SFTPWriter (paramiko + ThreadPoolExecutor)            ✅
    └── csv.py            ← CSVWriter (append/overwrite local file)               ✅
```

---

## App Wiring (core/app.py)

All stage singletons are registered with `pipeline_registry` at startup in two phases:

**Phase A — static (no connections needed), called before NATS connect:**
- All decoders: `json`, `csv`, `xml`, `ves`, `snmp`, `protobuf`, `avro`
- All encoders: `json`, `csv`, `protobuf`, `avro`
- Readers: `file`, `webhook`, `http_poll`

**Phase B — connection-dependent, registered after NATS + storage are up:**
- `NATSReader`, `NATSWriter` (require live NATS connection)
- `InfluxDBWriter`, `VictoriaLogsWriter` (require storage adapters)
- `WebhookWriter`, `SFTPReader`, `SFTPWriter` (registered by plugins in Phase 3)

---

## Transform API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/transform/run` | operator | Sync pipeline — decode+normalise+encode+write, returns envelope |
| POST | `/api/v1/transform/submit` | operator | Async job → NATS queue, returns `job_id` |
| GET | `/api/v1/transform/jobs/{id}` | operator | Job status from Redis |
| GET | `/api/v1/transform/stages` | operator | All registered readers/decoders/encoders/writers |

## Schema Registry Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/schemas` | Register Avro/Protobuf schema |
| GET | `/api/v1/schemas` | List all schemas |
| GET | `/api/v1/schemas/{id}` | Get schema by ID |
| DELETE | `/api/v1/schemas/{id}` | Remove schema |

---

## Pipeline Job Config Schema

```python
class StageConfig(BaseModel):
    type: str
    model_config = ConfigDict(extra="allow")  # stage-specific fields passthrough

class NormalizerConfig(BaseModel):
    domain:    str
    protocol:  str
    source_ne: str
    direction: str = "inbound"

class PipelineJobConfig(BaseModel):
    reader:     StageConfig | None = None
    decoder:    StageConfig
    normalizer: NormalizerConfig
    encoder:    StageConfig
    writer:     StageConfig
```

**Example — Webhook VES → VictoriaLogs:**
```json
{
  "payload": { "event": { "commonEventHeader": { ... } } },
  "config": {
    "decoder":    { "type": "ves" },
    "normalizer": { "domain": "FM", "source_ne": "ems-01", "protocol": "ves" },
    "encoder":    { "type": "json" },
    "writer":     { "type": "victorialogs" }
  }
}
```

---

## Deliverables Checklist

### ABCs + Core
- [x] `transformer/base.py` — all 5 ABCs
- [x] `transformer/pipeline.py` — TransformPipeline + PipelineRegistry
- [x] `transformer/normalizer.py` — FCAPSNormalizer
- [x] `transformer/schema_registry.py` — SQLite schema store
- [x] `transformer/router.py` — 8 endpoints (transform + schemas)

### Readers
- [x] `SFTPReader`
- [x] `WebhookReader`
- [x] `NATSReader`
- [x] `HTTPPollReader`
- [x] `FileReader`

### Decoders
- [x] `JSONDecoder`
- [x] `CSVDecoder`
- [x] `XMLDecoder`
- [x] `ProtobufDecoder`
- [x] `AvroDecoder`
- [x] `VESDecoder`
- [x] `SNMPDecoder`

### Encoders
- [x] `JSONEncoder`
- [x] `CSVEncoder`
- [x] `ProtobufEncoder`
- [x] `AvroEncoder`

### Writers
- [x] `NATSWriter`
- [x] `InfluxDBWriter`
- [x] `VictoriaLogsWriter`
- [x] `WebhookWriter`
- [x] `SFTPWriter`
- [x] `CSVWriter`

### Tests
- [x] `tests/test_decoders.py` — 14 tests (JSON, CSV, XML, VES, SNMP)
- [x] `tests/test_encoders.py` — 5 tests (JSON, CSV, Protobuf)
- [x] `tests/test_writers.py` — 9 tests (NATS, InfluxDB, VictoriaLogs, Webhook, CSV)
- [x] `tests/test_pipeline.py` — 4 tests (end-to-end, registry, missing stage, list_stages)
