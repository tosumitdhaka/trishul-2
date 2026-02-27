import { useEventsStore, LiveEvent } from '@/store/events';

const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/events`;
const RECONNECT_DELAY_MS = 3_000;
const MAX_RECONNECT     = 10;

let ws:           WebSocket | null = null;
let reconnects    = 0;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

function connect() {
  if (ws && ws.readyState < WebSocket.CLOSING) return;

  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    reconnects = 0;
    console.info('[WS] connected to', WS_URL);
  };

  ws.onmessage = (ev) => {
    try {
      const envelope = JSON.parse(ev.data) as Record<string, unknown>;
      const event: LiveEvent = {
        id:          crypto.randomUUID(),
        timestamp:   (envelope.timestamp as string) ?? new Date().toISOString(),
        domain:      (envelope.domain   as string) ?? 'LOG',
        protocol:    (envelope.protocol as string) ?? 'unknown',
        source_ne:   (envelope.source_ne as string) ?? '—',
        severity:    (envelope.severity as LiveEvent['severity']) ?? null,
        message:     ((envelope.normalized as Record<string,unknown>)?.message as string)
                     ?? (envelope.message as string)
                     ?? '',
        envelope_id: (envelope.id as string) ?? '',
      };
      useEventsStore.getState().push(event);
    } catch { /* malformed message, ignore */ }
  };

  ws.onerror = () => ws?.close();

  ws.onclose = () => {
    if (reconnects < MAX_RECONNECT) {
      reconnects++;
      const delay = RECONNECT_DELAY_MS * Math.min(reconnects, 4);
      reconnectTimer = setTimeout(connect, delay);
    }
  };
}

export function startWebSocket() {
  connect();
}

export function stopWebSocket() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  ws?.close();
  ws = null;
}
