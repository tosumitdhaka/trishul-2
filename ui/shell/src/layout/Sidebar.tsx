import { NavLink, useLocation } from 'react-router-dom';
import { usePluginsStore } from '@/store/plugins';
import clsx from 'clsx';
import {
  LayoutDashboard, Puzzle, Settings, User,
  Radio, Wifi, Box, FileArchive, Webhook, FolderOpen,
} from 'lucide-react';

const PROTOCOL_ICONS: Record<string, React.ElementType> = {
  snmp:     Radio,
  ves:      Wifi,
  protobuf: Box,
  avro:     FileArchive,
  webhook:  Webhook,
  sftp:     FolderOpen,
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

  return (
    <aside className="w-56 flex-shrink-0 bg-surface-900 border-r border-surface-200/10 flex flex-col py-4 px-3">
      {/* Logo */}
      <div className="flex items-center gap-2 px-2 mb-6">
        <span className="text-2xl">🔱</span>
        <span className="font-bold text-white tracking-tight">Trishul</span>
      </div>

      {/* Shell pages */}
      <div className="space-y-1 mb-4">
        <NavItem to="/"        icon={LayoutDashboard} label="Dashboard" />
        <NavItem to="/plugins" icon={Puzzle}          label="Plugins" />
      </div>

      {/* Divider + Plugin nav */}
      {plugins.length > 0 && (
        <>
          <p className="px-3 mb-1 text-xs font-semibold uppercase tracking-wider text-surface-200/40">
            Protocols
          </p>
          <div className="space-y-1 mb-4">
            {plugins.map(p => {
              const Icon = PROTOCOL_ICONS[p.name] ?? Puzzle;
              return <NavItem key={p.name} to={`/${p.name}`} icon={Icon} label={p.name.toUpperCase()} />;
            })}
          </div>
        </>
      )}

      {/* Bottom */}
      <div className="mt-auto space-y-1">
        <NavItem to="/settings" icon={Settings} label="Settings" />
        <NavItem to="/profile"  icon={User}     label="Profile" />
      </div>
    </aside>
  );
}
