import { X } from 'lucide-react';
import { useEventsStore, LiveEvent, Severity } from '@/store/events';
import { formatDistanceToNow } from 'date-fns';
import clsx from 'clsx';

const SEV_CLASS: Record<string, string> = {
  CRITICAL: 'badge-critical',
  MAJOR:    'badge-major',
  MINOR:    'badge-minor',
  WARNING:  'badge-info',
  CLEARED:  'badge-cleared',
  NORMAL:   'badge-cleared',
};

const SEV_ICON: Record<string, string> = {
  CRITICAL: '🔴',
  MAJOR:    '🟠',
  MINOR:    '🟡',
  WARNING:  '🔵',
  CLEARED:  '🟢',
  NORMAL:   '🟢',
};

function EventRow({ ev }: { ev: LiveEvent }) {
  const sev  = ev.severity ?? 'NORMAL';
  const ago  = formatDistanceToNow(new Date(ev.timestamp), { addSuffix: true });
  return (
    <div className="px-4 py-3 border-b border-surface-200/10 hover:bg-surface-200/5">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-xs text-surface-200/50">{ago}</span>
        <span className={clsx('text-xs font-medium', SEV_CLASS[sev] ?? 'badge-info')}>
          {SEV_ICON[sev]} {sev}
        </span>
      </div>
      <p className="text-sm font-medium text-white truncate">{ev.source_ne}</p>
      <p className="text-xs text-surface-200/50 truncate">{ev.message || ev.envelope_id}</p>
    </div>
  );
}

export default function NotificationPanel({ onClose }: { onClose: () => void }) {
  const events = useEventsStore(s => s.events).filter(e => e.domain === 'FM');
  const clear  = useEventsStore(s => s.clear);

  return (
    <aside className="w-80 flex-shrink-0 bg-surface-900 border-l border-surface-200/10
                      flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-200/10">
        <span className="font-semibold text-sm">Live Alerts</span>
        <div className="flex items-center gap-2">
          <button onClick={clear} className="text-xs text-surface-200/50 hover:text-white">Clear</button>
          <button onClick={onClose} className="p-1 hover:bg-surface-200/10 rounded"><X size={14} /></button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {events.length === 0
          ? <p className="p-4 text-sm text-surface-200/40 text-center">No alerts yet</p>
          : events.map(ev => <EventRow key={ev.id} ev={ev} />)
        }
      </div>
    </aside>
  );
}
