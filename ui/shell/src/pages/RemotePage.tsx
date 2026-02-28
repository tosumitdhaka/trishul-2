import { useParams } from 'react-router-dom';
import { usePluginsStore } from '@/store/plugins';
import { Suspense, useEffect, useState } from 'react';

/**
 * Loads a Vite Module Federation remote.
 *
 * @originjs/vite-plugin-federation@1.3.x with target:'esnext' emits pure ESM:
 *
 *   export const get  = (module) => moduleMap[module]?.();
 *   export const init = (shareScope) => { ... };
 *
 * Correct consumption: dynamic import() the remoteEntry URL, then call
 * init(shareScope) and get(exposedModule) directly from its exports.
 * No window[name], no __federation_method_* helpers needed.
 */
async function loadRemoteModule(
  remoteUrl: string,
  exposedModule: string,
): Promise<{ default: React.ComponentType }> {
  // Dynamic import of the remoteEntry.js as an ES module.
  // @vite-ignore suppresses the Vite static-analysis warning on runtime URLs.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const remote: any = await import(/* @vite-ignore */ remoteUrl);

  if (typeof remote.get !== 'function') {
    throw new Error(
      `remoteEntry.js at ${remoteUrl} does not export a get() function.\n` +
      `Exports found: ${Object.keys(remote).join(', ') || '(none)'}`,
    );
  }

  // init() shares the host's module instances (React singleton etc.)
  // Pass an empty scope if the host hasn't set one up — MFE will use its own bundled copies.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const shareScope = (window as any).__federation_shared_scope__ ?? {};
  if (typeof remote.init === 'function') {
    try { await remote.init(shareScope); } catch { /* already initialised */ }
  }

  // get() returns a factory function for the exposed module
  const factory = await remote.get(exposedModule);
  if (typeof factory !== 'function') {
    throw new Error(`remote.get('${exposedModule}') did not return a factory. Got: ${typeof factory}`);
  }

  return factory();
}

export default function RemotePage() {
  const { pluginName } = useParams<{ pluginName: string }>();
  const plugins = usePluginsStore(s => s.plugins);
  const plugin  = plugins.find(p => p.name === pluginName);

  const [RemoteComp, setRemoteComp] = useState<React.ComponentType | null>(null);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    if (!plugin?.remote_url || !plugin?.exposed) return;
    setError(null);
    setRemoteComp(null);
    loadRemoteModule(plugin.remote_url, plugin.exposed)
      .then(mod => {
        const Comp = mod.default ?? (mod as any);
        setRemoteComp(() => Comp);
      })
      .catch(e => setError(String(e)));
  }, [plugin?.remote_url, plugin?.exposed]);

  if (!plugin) {
    return (
      <div className="card text-center py-12">
        <p className="text-surface-200/40 text-sm">
          Plugin <code className="font-mono">{pluginName}</code> not found in registry.
        </p>
      </div>
    );
  }

  if (RemoteComp) {
    return (
      <Suspense fallback={<div className="card animate-pulse h-64" />}>
        <RemoteComp />
      </Suspense>
    );
  }

  if (error) {
    return (
      <div className="card border border-severity-critical/30 space-y-3 p-4">
        <p className="text-severity-critical text-sm font-semibold">⚠ Failed to load MFE remote</p>
        <pre className="text-surface-200/50 text-xs font-mono whitespace-pre-wrap break-all bg-black/30 rounded p-3">{error}</pre>
        <div className="text-surface-200/30 text-xs space-y-1">
          <p>URL: <code className="font-mono text-white/50">{plugin.remote_url}</code></p>
          <p>Exposed: <code className="font-mono text-white/50">{plugin.exposed}</code></p>
        </div>
        <button
          onClick={() => setError(null)}
          className="text-xs bg-white/5 hover:bg-white/10 border border-white/10 rounded px-3 py-1.5 transition-colors"
        >
          ↺ Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold capitalize">{plugin.name} Plugin</h1>
        <span className="badge-cleared">v{plugin.version}</span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs text-surface-200/50 uppercase tracking-wider mb-1">FCAPS Domains</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {plugin.domains?.map(d => <span key={d} className="badge-info">{d}</span>)}
          </div>
        </div>
        <div className="card">
          <p className="text-xs text-surface-200/50 uppercase tracking-wider mb-1">Protocols</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {plugin.protocols?.map(p => <span key={p} className="badge-info font-mono">{p}</span>)}
          </div>
        </div>
        <div className="card">
          <p className="text-xs text-surface-200/50 uppercase tracking-wider mb-1">Remote</p>
          <p className="text-white/40 font-mono text-xs mt-2 break-all">{plugin.remote_url}</p>
        </div>
      </div>
      <div className="card">
        <div className="flex items-center gap-3 py-1">
          <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          <p className="text-xs text-surface-200/40">
            Loading <code className="font-mono text-white/50">{plugin.remote_url}</code>…
          </p>
        </div>
      </div>
    </div>
  );
}
