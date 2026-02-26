# Phase 3 — Protocol Plugins

**Status**: ⚪ Planned  
**Depends on**: Phase 1 (Core Foundation), Phase 2 (Transformer Engine)  
**Prerequisite for**: Phase 5 (Protocol UIs)

---

## Goal

Implement all protocol-specific plugins as thin wrappers over the Phase 2 Transformer Engine. Each plugin handles: inbound receive, outbound simulation/send, and protocol-specific parsing/validation. No business logic lives in plugins — only protocol specifics.

---

## Plugin Contract

Every plugin must:
1. Implement `FCAPSPlugin` base class and export a `plugin` instance
2. Register its own `APIRouter` at `plugins/{name}/router.py`
3. Assemble pipelines exclusively from Phase 2 stage implementations
4. Normalize all events to `MessageEnvelope` before any NATS publish
5. Declare its FCAPS domains: `["FM"]`, `["PM"]`, or `["FM", "PM", "LOG"]`
6. Expose `GET /api/v1/{name}/health` and plugin-level Prometheus metrics

---

## Planned Plugins

| Plugin | Protocol | FCAPS Domain | Inbound | Outbound (Sim) |
|--------|----------|-------------|---------|----------------|
| `snmp` | SNMP v1/v2c/v3 | FM, PM | Trap receiver, SNMP GET poller | Trap generator, GET simulator |
| `ves` | VES 7.x JSON | FM, PM, LOG | HTTP POST endpoint | VES event generator |
| `protobuf` | Protobuf (gNMI/custom) | PM | NATS/gRPC consumer | Protobuf publisher |
| `avro` | Apache Avro | PM, LOG | SFTP / NATS pull | Avro file writer |
| `webhook` | JSON over HTTP | FM, LOG | HTTP POST endpoint | HTTP POST sender |
| `sftp` | File over SFTP | PM, LOG | SFTP poll / push trigger | SFTP file upload |

---

## Plugin Directory Structure

```
plugins/
└── snmp/
    ├── __init__.py       ← exports plugin = SNMPPlugin()
    ├── router.py         ← /api/v1/snmp/* endpoints
    ├── models.py         ← SNMPTrap, SNMPGetRequest Pydantic models
    ├── config.py         ← SNMPSettings (extends BaseSettings)
    ├── simulator.py      ← synthetic trap / metric generator
    └── pipeline.py       ← assemble TransformPipeline for SNMP
```

---

## Standard Plugin API Pattern

Every plugin exposes a consistent set of endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/{proto}/receive` | Accept inbound message (ingest + NATS publish) |
| POST | `/api/v1/{proto}/send` | Send outbound message to target |
| POST | `/api/v1/{proto}/simulate` | Generate synthetic messages |
| GET | `/api/v1/{proto}/status/{envelope_id}` | Processing status for a message |
| GET | `/api/v1/{proto}/health` | Plugin health check |

---

## SNMP Plugin (Reference Detail)

```
Inbound trap flow:
  UDP :162 (pysnmp TrapReceiver)
    → SNMPDecoder → FCAPSNormalizer
    → NATS publish: fcaps.ingest.snmp
    → Worker: TransformPipeline → VictoriaLogs (FM) or InfluxDB (PM)

Simulate flow:
  POST /api/v1/snmp/simulate { trap_type, target_host, count, interval }
    → SNMPSimulator generates TrapPDU(s)
    → TransformPipeline(SNMPDecoder, FCAPSNormalizer, JSONEncoder, NATSWriter)
    → NATS publish: fcaps.simulated.snmp
```

---

## Deliverables Checklist

- [ ] SNMP plugin (trap receiver + simulator + GET poller)
- [ ] VES plugin (HTTP receiver + event generator)
- [ ] Protobuf plugin (NATS consumer + publisher)
- [ ] Avro plugin (SFTP pull + file writer)
- [ ] Webhook plugin (HTTP POST receiver + sender) ← promoted from Phase 1 scaffold
- [ ] SFTP plugin (poll + push)
- [ ] Shared simulator base class (synthetic data generators)
- [ ] Plugin integration tests (receive → NATS → storage)
