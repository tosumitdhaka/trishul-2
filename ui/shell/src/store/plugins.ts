import { create } from 'zustand';
import axios from 'axios';

export interface PluginMeta {
  name:       string;
  version:    string;
  domains:    string[];
  protocols:  string[];
  health:     'healthy' | 'degraded' | 'unknown';
  remote_url?: string;   // set in Phase 5 when MFE remotes exist
  exposed?:    string;   // Module Federation exposed module, e.g. "./SNMPModule"
}

interface PluginsState {
  plugins:   PluginMeta[];
  loaded:    boolean;
  fetch:     () => Promise<void>;
}

export const usePluginsStore = create<PluginsState>((set) => ({
  plugins: [],
  loaded:  false,

  fetch: async () => {
    try {
      const res = await axios.get('/api/v1/plugins/registry');
      set({ plugins: res.data.plugins ?? [], loaded: true });
    } catch {
      // graceful degradation — shell still works without registry
      set({ loaded: true });
    }
  },
}));
