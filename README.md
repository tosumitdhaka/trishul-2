# 🔱 Trishul

> **FCAPS Simulation, Parsing & Visualization Platform**  
> Protocol-agnostic | Plug-and-Play | Containerized | FastAPI + NATS + InfluxDB + VictoriaLogs

---

## What is Trishul?

Trishul is a lightweight, containerized platform for simulating, receiving, parsing, transforming, and visualizing **FCAPS** (Fault, Configuration, Accounting, Performance, Security) data across multiple telecom/network protocols — SNMP, VES, Protobuf, Avro, Webhook, SFTP, and more.

It is designed for:
- Network engineers testing NMS/OSS integrations
- Developers building protocol adapters
- Lab environments simulating real network element behavior

---

## Architecture Principles

- **Plug-and-Play**: Add/remove protocol modules without touching core
- **Contract-First**: All messages normalized to a single `MessageEnvelope`
- **Event-Driven**: NATS JetStream as the async spine
- **Lightweight**: Full lab stack runs in ~450MB RAM
- **Uniform**: Shared auth, config, models, notifications across all plugins

---

## Roadmap

| Phase | Name | Description | Status |
|-------|------|-------------|--------|
| **1** | Core Foundation | FastAPI app factory, plugin registry, auth, NATS, storage adapters | 🔵 In Design |
| **2** | Transformer Engine | Protocol-agnostic Read→Decode→Normalize→Encode→Write pipeline | 🔵 In Design |
| **3** | Protocol Plugins | SNMP, VES, Protobuf, Avro, Webhook, SFTP plugin implementations | ⚪ Planned |
| **4** | Shell UI | React + Vite + Module Federation frontend shell | ⚪ Planned |
| **5** | Protocol UIs | Per-protocol Remote MFE modules (send/receive/simulate/visualize) | ⚪ Planned |
| **6** | Observability | Prometheus metrics, alerting, pipeline health dashboards | ⚪ Planned |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| API Framework | FastAPI 0.115+ (Python 3.12) |
| ASGI Server | Uvicorn |
| Auth | JWT (python-jose) + API Keys |
| User Store | SQLite + SQLModel |
| Session/Cache | Redis 7 Alpine |
| Message Bus | NATS JetStream 2.10 |
| PM Metrics | InfluxDB 2 OSS |
| FM / Logs | VictoriaLogs |
| Reverse Proxy | Traefik v3 |
| Frontend | React 19 + Vite + Module Federation |
| UI Components | shadcn/ui + Tailwind CSS |
| Charts | Recharts + D3.js |
| State | Zustand |
| Containers | Docker + Docker Compose |

---

## Documentation

- [Phase 1 — Core Foundation](docs/phase-1-core-foundation.md)
- [Phase 2 — Transformer Engine](docs/phase-2-transformer-engine.md)
- [Phase 3 — Protocol Plugins](docs/phase-3-protocol-plugins.md)
- [Phase 4 — Shell UI](docs/phase-4-shell-ui.md)
- [Phase 5 — Protocol UIs](docs/phase-5-protocol-uis.md)
- [Phase 6 — Observability](docs/phase-6-observability.md)
- [Architecture Overview](docs/architecture.md)

---

## Quick Start (Lab Mode)

```bash
git clone https://github.com/tosumitdhaka/trishul-2.git
cd trishul-2
cp .env.example .env          # fill in secrets
docker compose up -d
# API: http://localhost/api/v1
# Docs: http://localhost/docs
```

---

## License

See [LICENSE](LICENSE).
