# Phase 4 — Shell UI

**Status**: ✅ Complete  
**Depends on**: Phase 1 (Core Foundation)  
**Prerequisite for**: Phase 5 (Protocol UIs)

---

## Goal

Build the Trishul frontend shell: the host application that dynamically loads protocol UI modules at runtime (Module Federation), provides shared layout, auth, real-time WebSocket event stream, and a consistent design system.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | React 18 + Vite 5 |
| MFE host | `@originjs/vite-plugin-federation` |
| UI | shadcn/ui conventions + Tailwind CSS 3 |
| Charts | Recharts |
| State | Zustand 5 |
| Real-time | FastAPI WebSocket (`/ws/events`) |
| HTTP | Axios + TanStack Query v5 |
| Serve | nginx:1.27-alpine (multi-stage Docker) |

---

## File Structure

```
ui/shell/
├── src/
│   ├── main.tsx                  ← React root + QueryClient
│   ├── App.tsx                   ← Routes + RequireAuth guard
│   ├── index.css                 ← Tailwind base + card/badge utilities
│   ├── store/
│   │   ├── auth.ts               ← JWT login/logout (persisted)
│   │   ├── events.ts             ← Live event ring buffer (200 events)
│   │   └── plugins.ts            ← Plugin registry state
│   ├── ws/
│   │   └── client.ts             ← WS connect/reconnect/message parse
│   ├── layout/
│   │   ├── ShellLayout.tsx       ← Root layout (Sidebar + Topbar + Outlet)
│   │   ├── Sidebar.tsx           ← Auto-nav from plugin registry
│   │   ├── Topbar.tsx            ← Health dots, bell, user, logout
│   │   └── NotificationPanel.tsx ← Slide-in FM alert list
│   └── pages/
│       ├── LoginPage.tsx         ← JWT login form
│       ├── DashboardPage.tsx     ← Stats, charts, live event feed
│       ├── PluginsPage.tsx       ← Registry table
│       ├── SettingsPage.tsx      ← Platform config (Phase 6)
│       ├── ProfilePage.tsx       ← User info + sign-out
│       └── RemotePage.tsx        ← MFE loader (Phase 4: placeholder, Phase 5: live)
├── vite.config.ts                ← MFE host + dev proxy
├── tailwind.config.ts            ← Design tokens (brand, severity, surface)
├── nginx.conf                    ← SPA fallback + asset caching
└── Dockerfile                    ← node:20-alpine build + nginx serve
```

---

## Backend additions

- `core/ws/router.py` — `ConnectionManager` + `/ws/events` WebSocket endpoint
- `core/ws/__init__.py`
- `core/app.py` — mounts `ws_router` at root
- `docker-compose.yml` — adds `shell-ui` service + Traefik priority routing

---

## Traefik Routing

| Priority | Rule | Service |
|----------|------|---------|
| 10 | `/api/*`, `/docs`, `/health`, `/ws/*` | core-api:8000 |
| 1  | `/` (catch-all) | shell-ui:80 |

---

## Module Federation — Phase 4 vs Phase 5

| | Phase 4 | Phase 5 |
|---|---|---|
| Remote MFEs | None | `snmp-ui`, `ves-ui`, etc. |
| Plugin pages | Placeholder card | Full React app loaded at runtime |
| Shell rebuild needed? | No | No — dynamic `remoteEntry.js` injection |

---

## Deliverables

- [x] Vite + React 18 + vite-plugin-federation scaffold
- [x] Tailwind design tokens (brand, severity, surface)
- [x] ShellLayout: Sidebar + Topbar + NotificationPanel
- [x] Zustand stores: auth (persist), events (ring buffer), plugins
- [x] WebSocket client: auto-connect, exponential backoff, message parse
- [x] Dynamic sidebar nav from plugin registry
- [x] Dashboard: stat cards, FM timeline chart, severity bar, protocol bars, live feed
- [x] Plugin registry table page
- [x] Login page (JWT)
- [x] RemotePage: Phase 4 placeholder + Phase 5 MFE loader
- [x] nginx SPA config + multi-stage Dockerfile
- [x] docker-compose: shell-ui service + Traefik priority routing
- [x] `core/ws/router.py` WebSocket broadcaster
