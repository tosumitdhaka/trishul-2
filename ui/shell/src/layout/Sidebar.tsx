import { NavLink } from 'react-router-dom';
import { usePluginsStore } from '@/store/plugins';
import type { Plugin } from '@/store/plugins';
import clsx from 'clsx';
import {
  LayoutDashboard, Puzzle, Settings, User,
  Radio, Wifi, Box, FileArchive, Webhook, FolderOpen,
  BarChart2, ScrollText, MonitorDot, Server,
} from 'lucide-react';

const PROTOCOL_ICONS: Record<string, React.ElementType> = {
  snmp:     Radio,
  ves:      Wifi,
  protobuf: Box,
  avro:     FileArchive,
  webhook:  Webhook,
  sftp:     FolderOpen,
};

const DASHBOARD_ICONS: Record<string, React.ElementType> = {
  'fm-console':   MonitorDot,
  'pm-dashboard': BarChart2,
  'log-viewer':   ScrollText,
};

function NavItem({ to, icon: Icon, label }: { to: string; icon: React.ElementType; label: string }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive
            ? 'bg-brand-500/20 text-brand-100'
            : 'text-surface-200/60 hover:text-white hover:bg-surface-200/10',
        )
      }
    >
      <Icon size={16} />
      {label}
    </NavLink>
  );
}

export default function Sidebar() {
  const plugins = usePluginsStore(s => s.plugins);

  const dashboardPlugins = plugins.filter((p: Plugin) => !p.protocols || p.protocols.length === 0);
  const protocolPlugins  = plugins.filter((p: Plugin) =>  p.protocols && p.protocols.length > 0);

  return (
    <aside className="w-56 flex-shrink-0 bg-surface-900 border-r border-surface-200/10 flex flex-col py-4 px-3">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-2 mb-6">
        <img src="/trishul-icon.svg" alt="Trishul" className="w-7 h-7 flex-shrink-0" />
        <span className="font-bold text-white tracking-tight">Trishul</span>
      </div>

      {/* Shell pages */}
      <div className="space-y-1 mb-4">
        <NavItem to="/"        icon={LayoutDashboard} label="Overview" />
        <NavItem to="/plugins" icon={Puzzle}          label="Plugins" />
      </div>

      {/* Dashboard MFEs */}
      {dashboardPlugins.length > 0 && (
        <>
          <p className="px-3 mb-1 text-xs font-semibold uppercase tracking-wider text-surface-200/40">
            Dashboards
          </p>
          <div className="space-y-1 mb-4">
            {dashboardPlugins.map((p: Plugin) => {
              const Icon  = DASHBOARD_ICONS[p.name] ?? LayoutDashboard;
              const label = p.name
                .split('-')
                .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(' ');
              return <NavItem key={p.name} to={`/${p.name}`} icon={Icon} label={label} />;
            })}
          </div>
        </>
      )}

      {/* Protocol MFEs */}
      {protocolPlugins.length > 0 && (
        <>
          <p className="px-3 mb-1 text-xs font-semibold uppercase tracking-wider text-surface-200/40">
            Protocols
          </p>
          <div className="space-y-1 mb-4">
            {protocolPlugins.map((p: Plugin) => {
              const Icon = PROTOCOL_ICONS[p.name] ?? Puzzle;
              return <NavItem key={p.name} to={`/${p.name}`} icon={Icon} label={p.name.toUpperCase()} />;
            })}
          </div>
        </>
      )}

      {/* Bottom — platform ops + user */}
      <div className="mt-auto space-y-1">
        <NavItem to="/platform" icon={Server}   label="Platform" />
        <NavItem to="/settings" icon={Settings} label="Settings" />
        <NavItem to="/profile"  icon={User}     label="Profile" />
      </div>
    </aside>
  );
}
