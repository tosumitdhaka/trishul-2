# Phase 5 — Protocol UIs

**Status**: ⚪ Planned  
**Depends on**: Phase 3 (Protocol Plugins), Phase 4 (Shell UI)  
**Prerequisite for**: Phase 6 (Observability)

---

## Goal

Build per-protocol Remote MFE (Micro Frontend) modules that are dynamically loaded by the Shell. Each module provides send/receive/simulate/visualize UI for its protocol domain. All modules share the Shell's design system.

---

## Remote Modules Planned

| Module | Protocols | FCAPS Views |
|--------|-----------|-------------|
| `fm-console` | All | Alarm table, severity filter, ACK/clear, timeline |
| `pm-dashboard` | All | Metric charts (Recharts), source_ne selector, time range |
| `log-viewer` | All | Structured log explorer, full-text search (VictoriaLogs) |
| `snmp-ui` | SNMP | Trap sender, trap receiver live feed, OID browser, simulator |
| `ves-ui` | VES | VES event builder, event browser, schema viewer |
| `protobuf-ui` | Protobuf | Message publisher, schema upload, decoded view |
| `sftp-ui` | SFTP/Avro | File upload, poll config, parse preview |
| `webhook-ui` | Webhook | Request builder, listener log, payload inspector |

---

## Standard Module Views (per protocol)

Every protocol Remote MFE exposes these four views:

1. **Send / Simulate** — compose and send/generate messages to a target
2. **Receive / Live Feed** — real-time inbound message stream via WebSocket
3. **Parse / Inspect** — paste raw payload, decode and show normalized envelope
4. **History** — paginated message history (filtered from InfluxDB / VictoriaLogs)

---

## Design Consistency Rules

- All modules import design tokens from Shell's exposed `./design-system`
- Tables use shared `DataTable` component (shadcn/ui)
- Severity badges: CRITICAL=red, MAJOR=orange, MINOR=yellow, WARNING=blue, CLEARED=green
- Charts use shared Recharts theme (colors, fonts, tooltips)
- Loading/error states use shared `Skeleton` and `ErrorBoundary` from Shell

---

## Deliverables Checklist

- [ ] `fm-console` Remote MFE
- [ ] `pm-dashboard` Remote MFE
- [ ] `log-viewer` Remote MFE
- [ ] `snmp-ui` Remote MFE
- [ ] `ves-ui` Remote MFE
- [ ] `protobuf-ui` Remote MFE
- [ ] `sftp-ui` Remote MFE
- [ ] `webhook-ui` Remote MFE
- [ ] Shared design system exposed from Shell as Federation remote
