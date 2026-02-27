# Phase 3 — Protocol Plugins

**Status**: ✅ Complete  
**Depends on**: Phase 1 (Core Foundation), Phase 2 (Transformer Engine)  
**Prerequisite for**: Phase 5 (Protocol UIs)

---

## Goal

Implement all protocol-specific plugins as thin wrappers over the Phase 2 Transformer Engine. Each plugin handles: inbound receive, outbound simulation/send, and protocol-specific parsing/validation. No business logic lives in plugins — only protocol specifics.

---

## Plugin Contract

Every plugin implements `FCAPSPlugin` and provides:
- `get_router()` → `APIRouter`
- `get_nats_subjects()` → `list[str]`
- `get_metadata()` → `dict`
- `on_startup(**kwargs)` — registers decoder/writer with `pipeline_registry`
- `on_shutdown()` — graceful teardown
- Module-level `plugin = XPlugin()` instance
- `__init__.py` uses lazy import (`def get_plugin()`) — no eager instantiation

---

## Plugins Delivered

| Plugin | Protocol | FCAPS Domains | Decoder | Ingest Subject | Sim Subject |
|--------|----------|---------------|---------|----------------|-------------|
| `webhook` | JSON/HTTP | FM, LOG | `JSONDecoder` | `fcaps.ingest.webhook` | `fcaps.simulated.webhook` |
| `snmp` | SNMP v2c | FM, PM | `SNMPDecoder` | `fcaps.ingest.snmp` | `fcaps.simulated.snmp` |
| `ves` | VES 7.x | FM, PM, LOG | `VESDecoder` | `fcaps.ingest.ves` | `fcaps.simulated.ves` |
| `protobuf` | Protobuf/gNMI | PM | `ProtobufDecoder` | `fcaps.ingest.protobuf` | `fcaps.simulated.protobuf` |
| `avro` | Apache Avro | PM, LOG | `JSONDecoder` (dict) | `fcaps.ingest.avro` | `fcaps.simulated.avro` |
| `sftp` | SFTP/file | PM, LOG | `JSONDecoder` | `fcaps.ingest.sftp` | `fcaps.simulated.sftp` |

---

## Shared Simulator Base

`plugins/shared/simulator_base.py` — `SimulatorBase` ABC:
- `generate_batch(count, **kwargs)` → `list[dict]`
- `now_iso()` → UTC ISO timestamp string
- `new_id()` → UUID4 string

All plugin simulators extend this and implement `_generate_one(index, **kwargs)`.

---

## Standard Endpoints (per plugin)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/{proto}/receive` | Ingest event → pipeline → NATS (202) |
| POST | `/api/v1/{proto}/simulate` | Generate synthetic events → pipeline → NATS |
| GET | `/api/v1/{proto}/status/{id}` | Envelope status from Redis |
| GET | `/api/v1/{proto}/health` | Plugin health |

---

## Plugin Directory Structure

```
plugins/
├── shared/
│   └── simulator_base.py     ← SimulatorBase ABC
├── webhook/                  ← Phase 1 scaffold, promoted to full plugin
│   ├── __init__.py           ← lazy get_plugin()
│   ├── config.py
│   ├── models.py
│   ├── simulator.py
│   ├── router.py
│   └── plugin.py             ← WebhookPlugin(FCAPSPlugin)
├── snmp/                     ← same structure
├── ves/
├── protobuf/
├── avro/
└── sftp/
```

---

## Deliverables Checklist

- [x] `plugins/shared/simulator_base.py` — SimulatorBase ABC
- [x] `webhook` plugin — promoted from Phase 1 scaffold, full FCAPSPlugin contract
- [x] `snmp` plugin — trap receive, simulate (5 trap types), pipeline
- [x] `ves` plugin — VES 7.x receive, simulate (fault/measurement), pipeline
- [x] `protobuf` plugin — receive, simulate (gNMI-style metrics), pipeline
- [x] `avro` plugin — receive, simulate (PM records), pipeline
- [x] `sftp` plugin — receive, simulate (file-based PM), pipeline; registers SFTPReader + SFTPWriter
- [x] `tests/test_plugin_simulators.py` — 9 tests across all 5 simulators + SimulatorBase
- [x] `tests/test_plugin_snmp.py` — 4 tests: batch gen, linkUp/Down, pipeline run, simulate endpoint
- [x] `tests/test_plugin_ves.py` — 4 tests: fault/measurement gen, pipeline run, simulate endpoint
