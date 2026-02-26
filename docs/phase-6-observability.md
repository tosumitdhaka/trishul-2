# Phase 6 — Observability

**Status**: ⚪ Planned  
**Depends on**: Phase 3 (Protocol Plugins), Phase 4 (Shell UI)  

---

## Goal

Add platform-level observability: Prometheus metrics from all containers, alerting rules, pipeline health tracking, and an ops dashboard. Trishul should be self-observable — you can monitor the monitoring tool.

---

## Components

| Component | Technology | Purpose |
|-----------|------------|--------|
| Metrics scraping | Prometheus | Scrape /metrics from all services |
| Metrics storage | VictoriaMetrics (single-node) | Lightweight Prometheus-compatible TSDB |
| Alerting | Prometheus Alertmanager | Pipeline stall, error rate, storage lag alerts |
| Ops dashboard | Grafana OSS (optional) OR built-in Shell page | Infra health (NATS lag, InfluxDB write rate, etc.) |

> **Note**: VictoriaMetrics (not VictoriaLogs) handles Prometheus metrics. The two are separate products from the same vendor and complement each other well.

---

## Key Metrics Exposed

### Core API
- `trishul_plugin_loaded_total` — count of loaded plugins
- `trishul_envelope_ingest_total{protocol, domain}` — ingest rate
- `trishul_envelope_process_duration_seconds{protocol}` — transform latency
- `trishul_auth_failure_total{reason}` — auth failure rate

### NATS
- `nats_jetstream_stream_msgs{stream}` — pending messages per stream
- `nats_jetstream_consumer_lag{stream, consumer}` — consumer lag

### Storage
- `influxdb_write_latency_seconds` — InfluxDB write duration
- `victorialogs_insert_rows_total` — VictoriaLogs ingest rate

---

## Alerting Rules (Examples)

```yaml
- alert: PipelineStalled
  expr: nats_jetstream_consumer_lag{stream="FCAPS_PROCESS"} > 1000
  for: 5m
  annotations:
    summary: "Transform pipeline consumer lag > 1000 messages for 5m"

- alert: HighAuthFailureRate
  expr: rate(trishul_auth_failure_total[5m]) > 10
  for: 2m
  annotations:
    summary: "Auth failures spiking — possible brute force"
```

---

## Deliverables Checklist

- [ ] Prometheus config with scrape targets for all services
- [ ] VictoriaMetrics container added to docker-compose
- [ ] Prometheus Alertmanager + basic alert rules
- [ ] Custom metrics in core-api (envelopes, auth, pipeline latency)
- [ ] Custom metrics in each plugin (per-protocol ingest/error counters)
- [ ] Grafana dashboard JSON (or built-in Shell observability page)
- [ ] Runbook: common alerts and resolution steps
