/**
 * Shared WebSocket hook for all MFE remotes.
 * Connects to the shell's /ws/events endpoint and filters events by protocol.
 */
import { useEffect, useRef, useState } from 'react';

export interface WsEvent {
  id:          string;
  timestamp:   string;
  domain:      string;
  protocol:    string;
  source_ne:   string;
  severity:    string | null;
  message:     string;
  envelope_id: string;
}

const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/events`;
const MAX = 100;

export function useWsEvents(filterProtocol?: string, filterDomain?: string) {
  const [events, setEvents] = useState<WsEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (ev) => {
        try {
          const e = JSON.parse(ev.data) as Record<string, unknown>;
          const domain   = e.domain   as string | undefined;
          const protocol = e.protocol as string | undefined;
          if (!domain || !['FM','PM','LOG'].includes(domain)) return;
          if (!protocol) return;
          if (filterProtocol && protocol !== filterProtocol) return;
          if (filterDomain   && domain   !== filterDomain)   return;

          const event: WsEvent = {
            id:          crypto.randomUUID(),
            timestamp:   (e.timestamp   as string) ?? new Date().toISOString(),
            domain,
            protocol,
            source_ne:   (e.source_ne   as string) ?? 'unknown',
            severity:    (e.severity    as string) ?? null,
            message:     ((e.normalized as Record<string,unknown>)?.message as string)
                         ?? (e.message  as string) ?? '',
            envelope_id: (e.id          as string) ?? '',
          };

          setEvents(prev => [event, ...prev].slice(0, MAX));
        } catch { /* ignore */ }
      };

      ws.onclose = () => setTimeout(connect, 3000);
      ws.onerror = () => ws.close();
    };
    connect();
    return () => { wsRef.current?.close(); };
  }, [filterProtocol, filterDomain]);

  return events;
}
