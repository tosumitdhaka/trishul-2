import { create } from 'zustand';

export type Severity = 'CRITICAL' | 'MAJOR' | 'MINOR' | 'WARNING' | 'CLEARED' | 'NORMAL';

export interface LiveEvent {
  id:         string;
  timestamp:  string;
  domain:     string;   // FM | PM | LOG
  protocol:   string;   // snmp | ves | ...
  source_ne:  string;
  severity:   Severity | null;
  message:    string;
  envelope_id: string;
}

const MAX_EVENTS = 200;

interface EventsState {
  events:      LiveEvent[];
  unread:      number;
  paused:      boolean;
  push:        (e: LiveEvent) => void;
  markRead:    () => void;
  setPaused:   (p: boolean) => void;
  clear:       () => void;
}

export const useEventsStore = create<EventsState>((set) => ({
  events:  [],
  unread:  0,
  paused:  false,

  push: (e) => set((s) => {
    if (s.paused) return s;
    const events = [e, ...s.events].slice(0, MAX_EVENTS);
    return { events, unread: s.unread + 1 };
  }),

  markRead:  () => set({ unread: 0 }),
  setPaused: (paused) => set({ paused }),
  clear:     () => set({ events: [], unread: 0 }),
}));
