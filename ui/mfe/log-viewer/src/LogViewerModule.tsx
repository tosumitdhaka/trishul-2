import { useState, useMemo } from 'react';
import { Search } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useWsEvents } from './useWsEvents';

const DOMAIN_COLOR: Record<string,string> = {
  FM:  'text-red-400',
  PM:  'text-blue-400',
  LOG: 'text-white/40',
};

const PROTO_COLORS = ['#3b5bdb','#e03131','#f76707','#2f9e44','#f59f00','#74c0fc','#9775fa'];
const protoColor = (p: string) => PROTO_COLORS[p.charCodeAt(0) % PROTO_COLORS.length];

export default function LogViewerModule() {
  const allEvents  = useWsEvents();
  const [query, setQuery]   = useState('');
  const [domain, setDomain] = useState('ALL');
  const [proto, setProto]   = useState('ALL');

  const protocols = useMemo(() => ['ALL', ...Array.from(new Set(allEvents.map(e => e.protocol)))], [allEvents]);

  const filtered = useMemo(() => allEvents.filter(e => {
    if (domain !== 'ALL' && e.domain   !== domain) return false;
    if (proto  !== 'ALL' && e.protocol !== proto)  return false;
    if (query) {
      const q = query.toLowerCase();
      if (!e.message.toLowerCase().includes(q) &&
          !e.source_ne.toLowerCase().includes(q) &&
          !e.protocol.toLowerCase().includes(q)) return false;
    }
    return true;
  }), [allEvents, query, domain, proto]);

  return (
    <div className="space-y-4 text-white">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Log Viewer</h2>
        <span className="text-white/30 text-xs">{filtered.length} / {allEvents.length} events</span>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex-1 min-w-48 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
          <input type="text" value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search source, message, protocol…"
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5
                       text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <select value={domain} onChange={e => setDomain(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none">
          {['ALL','FM','PM','LOG'].map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={proto} onChange={e => setProto(e.target.value)}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none">
          {protocols.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {/* Log stream */}
      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
        <div className="font-mono text-xs divide-y divide-white/5 max-h-[520px] overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="px-4 py-8 text-center text-white/20">
              {allEvents.length === 0 ? 'Waiting for events via WebSocket…' : 'No events match current filters.'}
            </div>
          ) : filtered.map(ev => (
            <div key={ev.id} className="flex items-start gap-3 px-4 py-2 hover:bg-white/5">
              <span className="text-white/25 flex-shrink-0 w-20">
                {new Date(ev.timestamp).toLocaleTimeString()}
              </span>
              <span className={`flex-shrink-0 w-10 font-semibold ${DOMAIN_COLOR[ev.domain] ?? 'text-white/40'}`}>
                {ev.domain}
              </span>
              <span className="flex-shrink-0 w-16 truncate" style={{ color: protoColor(ev.protocol) }}>
                {ev.protocol}
              </span>
              <span className="text-white/50 flex-shrink-0 w-24 truncate">{ev.source_ne}</span>
              <span className="text-white/70 flex-1">{ev.message || ev.envelope_id}</span>
              {ev.severity && (
                <span className="flex-shrink-0 text-white/40">{ev.severity}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
