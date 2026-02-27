# Phase 5 — Protocol UIs

**Status**: ✅ Complete  
**Depends on**: Phase 3 (Protocol Plugins), Phase 4 (Shell UI)  
**Prerequisite for**: Phase 6 (Observability)

---

## MFE Remotes Delivered

| Remote | Container | Port (dev) | Exposes | Path prefix |
|--------|-----------|------------|---------|-------------|
| `fm-console` | `fm-console` | 5001 | `./FmConsoleModule` | `/mfe/fm-console` |
| `pm-dashboard` | `pm-dashboard` | 5002 | `./PmDashboardModule` | `/mfe/pm-dashboard` |
| `log-viewer` | `log-viewer` | 5003 | `./LogViewerModule` | `/mfe/log-viewer` |
| `snmp-ui` | `snmp-ui` | 5010 | `./SnmpModule` | `/mfe/snmp` |
| `ves-ui` | `ves-ui` | 5011 | `./VesModule` | `/mfe/ves` |
| `webhook-ui` | `webhook-ui` | 5012 | `./WebhookModule` | `/mfe/webhook` |
| `protobuf-ui` | `protobuf-ui` | 5013 | `./ProtobufModule` | `/mfe/protobuf` |
| `sftp-avro-ui` | `sftp-avro-ui` | 5014 | `./SftpModule`, `./AvroModule` | `/mfe/sftp`, `/mfe/avro` |

---

## Directory Structure

```
ui/
├── shared/
│   └── design-system/
│       ├── tokens.ts       ← Colors, severity, surface palettes
│       └── components.tsx  ← SeverityBadge, StatCard, SimulateButton, LiveFeedRow…
├── shell/
│   └── src/design-system/index.ts  ← Re-exports shared tokens for MFE Federation
└── mfe/
    ├── Dockerfile.mfe  ← Shared multi-stage Docker build for all MFEs
    ├── nginx.conf      ← Shared nginx config (CORS headers for remoteEntry.js)
    ├── Makefile        ← install / build / dev all MFEs
    ├── fm-console/
    ├── pm-dashboard/
    ├── log-viewer/
    ├── snmp-ui/
    ├── ves-ui/
    ├── webhook-ui/
    ├── protobuf-ui/
    └── sftp-avro-ui/
```

---

## Backend additions

- `core/plugins_registry_router.py` — `GET /api/v1/plugins/registry`
  Returns all loaded plugins with `remote_url` and `exposed` fields for Module Federation.
- `core/app.py` — mounts `plugins_registry_router`

---

## Module Federation Flow

```
Shell boots
  └→ GET /api/v1/plugins/registry
       └→ [ { name:"snmp", remote_url:"/mfe/snmp/assets/remoteEntry.js", exposed:"./SnmpModule" }, ... ]

User clicks "SNMP" in Sidebar
  └→ RemotePage mounts
       └→ injects <script src="/mfe/snmp/assets/remoteEntry.js">
            └→ container.get("./SnmpModule")
                 └→ renders <SnmpModule /> inline in Shell
```

No shell rebuild ever needed. Deploy a new MFE → update plugin metadata → browser picks it up on next load.

---

## Deliverables

- [x] `ui/shared/design-system/tokens.ts` — shared color/severity tokens
- [x] `ui/shared/design-system/components.tsx` — SeverityBadge, StatCard, SimulateButton, LiveFeedRow
- [x] `ui/shell/src/design-system/index.ts` — Shell re-exports for Federation consumers
- [x] `ui/shell/vite.config.ts` — updated to expose `./design-system`
- [x] `ui/mfe/Dockerfile.mfe` — shared MFE Docker build
- [x] `ui/mfe/nginx.conf` — CORS headers on assets for cross-container Federation
- [x] `ui/mfe/Makefile` — install/build/dev all MFEs
- [x] `fm-console` — alarm table, severity filter, simulate panel
- [x] `pm-dashboard` — ingestion rate line chart, simulate panel
- [x] `log-viewer` — log table, full-text search, level filter
- [x] `snmp-ui` — trap type/NE/count simulator, info cards
- [x] `ves-ui` — VES event type simulator
- [x] `webhook-ui` — JSON payload builder + send
- [x] `protobuf-ui` — gNMI telemetry simulator
- [x] `sftp-avro-ui` — SFTP + Avro simulators (dual-expose)
- [x] `core/plugins_registry_router.py` — registry endpoint with MFE URLs
- [x] `core/app.py` — mounts plugins_registry_router
- [x] `docker-compose.yml` — 8 MFE services + Traefik strip-prefix routes
