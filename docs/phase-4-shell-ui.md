# Phase 4 — Shell UI

**Status**: ⚪ Planned  
**Depends on**: Phase 1 (Core Foundation)  
**Prerequisite for**: Phase 5 (Protocol UIs)

---

## Goal

Build the Trishul frontend shell: the host application that dynamically loads protocol UI modules at runtime (Module Federation), provides shared layout, auth, real-time WebSocket event stream, and a consistent design system.

---

## Technology Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Framework | React 19 + Vite | Fastest HMR, Module Federation via vite-plugin-federation |
| Module Federation | vite-plugin-federation | Lightweight Vite-native MFE host |
| Component library | shadcn/ui + Tailwind CSS | Unstyled primitives = consistent design across all modules |
| Charts | Recharts + D3.js | PM trend lines, FM heatmaps, log timelines |
| State | Zustand | Lightweight, works across federated modules |
| Real-time | WebSocket (FastAPI native) | Live FM alerts, PM streams, log tailing |
| HTTP client | Axios + React Query | Caching, loading states, error handling |

---

## Shell Structure

```
frontend/shell/
├── src/
│   ├── App.tsx                   ← Dynamic nav from GET /api/v1/plugins/registry
│   ├── layout/
│   │   ├── Sidebar.tsx            ← Auto-populated from plugin registry
│   │   ├── Topbar.tsx             ← User info, notifications bell
│   │   └── NotificationPanel.tsx  ← Real-time FM/PM alerts via WebSocket
│   ├── design-system/
│   │   ├── tokens.ts              ← Colors, spacing, typography
│   │   ├── components/            ← Button, Badge, Card, Table, Modal (shadcn)
│   │   └── tailwind.config.ts     ← Shared Tailwind config (exported to remotes)
│   ├── store/
│   │   ├── auth.ts                ← JWT token, user, roles
│   │   ├── events.ts              ← Live NATS→WS event buffer
│   │   └── plugins.ts             ← Loaded plugin registry
│   ├── ws/
│   │   └── client.ts              ← WebSocket connection + reconnect logic
│   └── routes/
│       └── index.tsx              ← Dynamic routes for MFE modules
├── vite.config.ts                 ← Module Federation host config
└── Dockerfile
```

---

## Module Federation — Dynamic Plugin Loading

The shell reads `/api/v1/plugins/registry` on startup and loads each plugin's Remote MFE:

```typescript
// Shell auto-discovers and mounts any plugin UI at runtime
const plugins = await fetch('/api/v1/plugins/registry').then(r => r.json());
// Each plugin entry:
// { name: "snmp", version: "1.0", remote_url: "http://snmp-ui:5173/remoteEntry.js", exposed: "./SNMPModule" }
```

No Shell rebuild needed when a new protocol plugin is deployed.

---

## Notification System

All FM alarms, pipeline completions, and errors are pushed via WebSocket from the `fcaps.done.*` NATS subjects:

```
NATS fcaps.done.fm
  → FastAPI WebSocket broadcaster
    → Shell NotificationPanel (toast + panel)
    → Zustand events store
      → FM Console remote module (live table update)
```

---

## Built-in Shell Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Dashboard | Summary cards: active alarms, PM ingestion rate, recent logs |
| `/plugins` | Plugin Registry | All loaded plugins, health, version |
| `/profile` | User Profile | Token info, roles, API key management |
| `/settings` | Settings | App config, storage status, NATS status |

Protocol-specific pages (`/snmp`, `/ves`, `/pm`, `/fm`, `/logs`) are loaded as Remote MFEs from Phase 5.

---

## Deliverables Checklist

- [ ] Vite + React 19 project scaffold with vite-plugin-federation (host)
- [ ] Tailwind + shadcn/ui design system tokens
- [ ] Shell layout: Sidebar (dynamic nav) + Topbar + NotificationPanel
- [ ] Zustand stores: auth, events, plugins
- [ ] WebSocket client with auto-reconnect + event buffering
- [ ] Dynamic route loader for MFE modules
- [ ] Dashboard page (summary cards)
- [ ] Plugin registry page
- [ ] JWT login page (token stored in memory + httpOnly cookie refresh)
- [ ] Dockerfile (multi-stage: node:20-alpine build + nginx serve)
