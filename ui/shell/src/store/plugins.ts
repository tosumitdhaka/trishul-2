import { create } from 'zustand';
import axios from 'axios';

export interface Plugin {
  name:             string;
  version:          string;
  domains:          string[];
  protocols?:       string[];
  remote_url?:      string;
  exposed?:         string;
  federation_name?: string;  // exact window[key] Vite registers the MFE container under
  health?:          string;
  [key: string]:    unknown;
}

interface PluginsState {
  plugins:  Plugin[];
  loading:  boolean;
  error:    string | null;
  fetch:    () => Promise<void>;   // keep original name — ShellLayout + PluginsPage use s.fetch
}

export const usePluginsStore = create<PluginsState>((set) => ({
  plugins: [],
  loading: false,
  error:   null,

  fetch: async () => {
    set({ loading: true, error: null });
    try {
      const res = await axios.get<{ plugins: Plugin[] }>('/api/v1/plugins/registry');
      set({ plugins: res.data.plugins, loading: false });
    } catch (e: unknown) {
      set({ error: (e as Error).message, loading: false });
    }
  },
}));
