import { useParams } from 'react-router-dom';
import { usePluginsStore } from '@/store/plugins';
import { Suspense, useEffect, useState } from 'react';

/**
 * Loads a Vite Module Federation remote using dynamic import().
 *
 * @originjs/vite-plugin-federation@1.3.x with target:'esnext' emits
 * standard ES module exports from remoteEntry.js — NOT window[name].
 * The correct way to consume it is:
 *
 *   const mod = await import(/* @vite-ignore *\/ remoteUrl);
 *   await mod.__federation_method_setRemote(name, { ... });
 *   const component = await mod.__federation_method_getRemote(name, exposedModule);
 *
 * This bypasses window[name] entirely and works with ESM output.
 */
async function loadRemoteModule(
  federationName: string,
  remoteUrl: string,
  exposedModule: string,
): Promise<{ default: React.ComponentType }> {
  // Dynamically import the remoteEntry.js as an ES module
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const remoteEntry: any = await import(/* @vite-ignore */ remoteUrl);

  // @originjs/vite-plugin-federation exposes helper methods on the module:
  // __federation_method_setRemote  — registers the remote with its name + getter
  // __federation_method_getRemote  — fetches the exposed module from it
  // __federation_method_unwrapDefault — unwraps the default export correctly
  const {
    __federation_method_setRemote: setRemote,
    __federation_method_getRemote: getRemote,
    __federation_method_unwrapDefault: unwrapDefault,
  } = remoteEntry;

  if (!setRemote || !getRemote) {
    throw new Error(
      `remoteEntry.js from ${remoteUrl} does not export __federation_method_setRemote / __federation_method_getRemote.\n` +
      `Ensure @originjs/vite-plugin-federation is installed in the MFE and vite build succeeded.`,
    );
  }

  // Register the remote so getRemote knows where to load chunks from
  await setRemote(federationName, {
    url: () => Promise.resolve(remoteUrl),
    format: 'esm',
    from: 'vite',
  });

  // Load the exposed module (e.g. './WebhookModule')
  const mod = await getRemote(federationName, exposedModule);
  return unwrapDefault ? unwrapDefault(mod, true) : mod;
}

export default function RemotePage() {
  const { pluginName } = useParams<{ pluginName: string }>();
  const plugins = usePluginsStore(s => s.plugins);
  const plugin  = plugins.find(p => p.name === pluginName);

  const [RemoteComp, setRemoteComp] = useState<React.ComponentType | null>(null);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    if (!plugin?.remote_url || !plugin?.exposed || !plugin?.federation_name) return;
    setError(null);
    setRemoteComp(null);
    loadRemoteModule(plugin.federation_name, plugin.remote_url, plugin.exposed)
      .then(mod => setRemoteComp(() => mod.default ?? (mod as any)))
      .catch(e  => setError(String(e)));
  }, [plugin?.federation_name, plugin?.remote_url, plugin?.exposed]);

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
          <p>Container: <code className="font-mono text-white/50">{plugin.federation_name}</code></p>
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
            Loading <code className="font-mono text-white/50">{plugin.federation_name}</code>…
          </p>
        </div>
      </div>
    </div>
  );
}
