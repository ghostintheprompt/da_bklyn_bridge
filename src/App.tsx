import React, {useEffect, useMemo, useState} from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Command,
  Copy,
  Database,
  Eye,
  Layers,
  PlugZap,
  Radio,
  Router,
  Shield,
  Signal,
  Smartphone,
  Terminal,
  Wifi,
  XCircle,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {AnimatePresence, motion} from 'motion/react';
import {format} from 'date-fns';

interface AP {
  bssid: string;
  ssid: string;
  channel: number;
  rssi: number;
  crypto: string;
  vendor?: string;
  lastSeen: string;
}

interface Probe {
  mac: string;
  ssid: string;
  rssi: number;
  timestamp: string;
}

interface Alert {
  type: string;
  msg: string;
  severity: 'info' | 'warning' | 'critical';
  timestamp: string;
}

interface HardwareStatus {
  interface_present: boolean;
  interface: string;
  mode: string;
  monitor_mode: boolean;
  driver: string;
  chipset_hint: string;
  usb_hints: string[];
  platform: string;
  apple_silicon_vm: boolean;
  doctor: string;
}

interface Stats {
  interface: string;
  mode: string;
  channel: number;
  hardware?: HardwareStatus;
  summary: {
    ap_count: number;
    probe_count: number;
    alert_count: number;
    active_alert_count: number;
    rogue_ap_count: number;
    deauth_group_count: number;
    night_owl_count: number;
    ghost_network_count: number;
    remote_id_alert_count: number;
  };
  aps: AP[];
  probes: Probe[];
  alerts: Alert[];
  timelapse: {
    night_owls: Array<{ssid: string; bssid: string; time: string}>;
    ghosts: Array<{ssid: string; bssid: string; time: string}>;
  };
  deauth_stats: Array<{bssid: string; count: number; last: string}>;
  rogue_aps: Array<{ssid: string; bssid: string; channel: number; rssi: number; crypto?: string}>;
  anomaly_model: {
    status: string;
    loaded: boolean;
    sample_count: number;
    trained_at?: string | null;
  };
}

interface HistoryPoint {
  time: string;
  probes: number;
  aps: number;
  alerts: number;
}

const API_BASE = (import.meta.env.VITE_SENTINEL_API_BASE || '').replace(/\/$/, '');

const fallbackHardware = (iface = 'wlan0'): HardwareStatus => ({
  interface_present: false,
  interface: iface,
  mode: 'unknown',
  monitor_mode: false,
  driver: 'unknown',
  chipset_hint: 'unknown',
  usb_hints: [],
  platform: 'unknown',
  apple_silicon_vm: false,
  doctor: 'scripts/alfa_doctor.sh',
});

const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) return '--:--';
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) return '--:--';
  return format(parsed, 'HH:mm');
};

const signalGrade = (rssi: number) => {
  if (rssi >= -55) return 'Hot';
  if (rssi >= -70) return 'Usable';
  return 'Faint';
};

const cx = (...classes: Array<string | false | null | undefined>) => classes.filter(Boolean).join(' ');

const StatusDot = ({state}: {state: 'good' | 'warn' | 'bad' | 'idle'}) => (
  <span
    className={cx(
      'h-2 w-2 rounded-full',
      state === 'good' && 'bg-emerald-400 shadow-[0_0_16px_rgba(52,211,153,0.75)]',
      state === 'warn' && 'bg-yellow-300 shadow-[0_0_16px_rgba(253,224,71,0.65)]',
      state === 'bad' && 'bg-red-400 shadow-[0_0_16px_rgba(248,113,113,0.65)]',
      state === 'idle' && 'bg-zinc-600',
    )}
  />
);

const Widget = ({
  title,
  icon: Icon,
  children,
  className = '',
  accent = 'cyan',
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  className?: string;
  accent?: 'cyan' | 'amber' | 'green' | 'red' | 'violet';
}) => {
  const accentClass = {
    cyan: 'text-cyan-300 border-cyan-400/35',
    amber: 'text-yellow-300 border-yellow-300/35',
    green: 'text-emerald-300 border-emerald-400/35',
    red: 'text-red-300 border-red-400/35',
    violet: 'text-violet-300 border-violet-400/35',
  }[accent];

  return (
    <section className={cx('relative overflow-hidden border border-zinc-800 bg-[#11110f] p-4 shadow-[0_18px_60px_rgba(0,0,0,0.28)]', className)}>
      <div className="mb-4 flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <span className={cx('grid h-7 w-7 place-items-center border bg-black/35', accentClass)}>
            <Icon size={15} />
          </span>
          <h2 className="text-[10px] font-black uppercase tracking-[0.18em] text-zinc-400">{title}</h2>
        </div>
        <div className="h-px w-14 bg-gradient-to-r from-transparent via-yellow-300/70 to-transparent" />
      </div>
      {children}
    </section>
  );
};

const CommandCard = ({
  label,
  command,
  copied,
  onCopy,
}: {
  label: string;
  command: string;
  copied: boolean;
  onCopy: (command: string, label: string) => void;
}) => (
  <button
    type="button"
    title={`Copy ${label}`}
    onClick={() => onCopy(command, label)}
    className="group flex min-h-[64px] w-full items-center justify-between gap-3 border border-zinc-800 bg-black/35 p-3 text-left transition hover:border-yellow-300/60 hover:bg-yellow-300/5"
  >
    <div className="min-w-0">
      <div className="text-[9px] font-black uppercase tracking-[0.16em] text-yellow-300">{label}</div>
      <code className="mt-1 block truncate text-[11px] text-zinc-300">{command}</code>
    </div>
    {copied ? <CheckCircle2 className="shrink-0 text-emerald-300" size={18} /> : <Copy className="shrink-0 text-zinc-500 group-hover:text-yellow-300" size={18} />}
  </button>
);

const EmptyState = ({label}: {label: string}) => (
  <div className="grid min-h-[150px] place-items-center border border-dashed border-zinc-800 bg-black/20 text-center text-[10px] font-bold uppercase tracking-[0.16em] text-zinc-600">
    {label}
  </div>
);

const OperationalModes = [
  {id: 'launch', title: '00: Launch Deck', icon: PlugZap, desc: 'Apple Silicon VM, Alfa, API readiness'},
  {id: 'census', title: '01: Air Census', icon: Radio, desc: 'AP enumeration and signal map'},
  {id: 'probes', title: '02: Probe Watch', icon: Smartphone, desc: 'Client probe telemetry'},
  {id: 'deauth', title: '03: Deauth Watch', icon: AlertTriangle, desc: 'Passive spike detection'},
  {id: 'timelapse', title: '04: Time-Lapse', icon: Clock, desc: 'Pattern drift over time'},
  {id: 'audit', title: '05: Self Audit', icon: Shield, desc: 'Rogue AP and scope review'},
  {id: 'academy', title: '06: Academy', icon: Layers, desc: 'Exam-linked field notes'},
];

const OfflineStart = ({error}: {error: string | null}) => {
  const [copied, setCopied] = useState('');
  const copyCommand = async (command: string, label: string) => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(label);
      window.setTimeout(() => setCopied(''), 1600);
    } catch {
      setCopied('');
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0b09] font-mono text-zinc-100">
      <div className="mx-auto grid min-h-screen max-w-6xl content-center gap-4 px-4 py-8">
        <div className="border border-zinc-800 bg-[#11110f] p-5">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-yellow-300">
                <StatusDot state="warn" /> Da Bklyn Bridge
              </div>
              <h1 className="text-3xl font-black uppercase text-white md:text-5xl">Bridge Deck Offline</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-400">
                Start the local API or point the Mac dashboard at the Linux VM. Capture stays passive by default; hardware work happens inside Linux.
              </p>
            </div>
            <div className="border border-red-400/30 bg-red-500/10 p-3 text-[11px] text-red-200">
              {error || 'Waiting for /api/stats'}
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Widget title="Mac Browser + VM API" icon={Router} accent="amber">
            <div className="space-y-2">
              <CommandCard label="VM API" command="bash scripts/run_api.sh --host-vm" copied={copied === 'VM API'} onCopy={copyCommand} />
              <CommandCard label="Mac Frontend" command="SENTINEL_PROXY_TARGET=http://<VM_IP>:5000 npm run dev" copied={copied === 'Mac Frontend'} onCopy={copyCommand} />
              <CommandCard label="Direct API Base" command="VITE_SENTINEL_API_BASE=http://<VM_IP>:5000 npm run dev" copied={copied === 'Direct API Base'} onCopy={copyCommand} />
            </div>
          </Widget>

          <Widget title="Alfa Readiness" icon={PlugZap} accent="green">
            <div className="space-y-2">
              <CommandCard label="VM Bootstrap" command="bash scripts/apple_silicon_vm_bootstrap.sh --rtl8812au --with-aircrack" copied={copied === 'VM Bootstrap'} onCopy={copyCommand} />
              <CommandCard label="Doctor" command="bash scripts/alfa_doctor.sh" copied={copied === 'Doctor'} onCopy={copyCommand} />
              <CommandCard label="Passive Capture" command="bash scripts/run_passive.sh --interface wlan0 --lab-insecure" copied={copied === 'Passive Capture'} onCopy={copyCommand} />
            </div>
          </Widget>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [activeGame, setActiveGame] = useState('launch');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [copied, setCopied] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const now = new Date();
        setStats(data);
        setLastUpdated(now);
        setConnectionError(null);
        setHistory((prev) => [
          ...prev.slice(-23),
          {
            time: format(now, 'HH:mm:ss'),
            probes: data.probes.length,
            aps: data.aps.length,
            alerts: data.summary.active_alert_count,
          },
        ]);
      } catch (err) {
        setConnectionError(err instanceof Error ? err.message : 'API unavailable');
      }
    };

    fetchData();
    const interval = window.setInterval(fetchData, 3000);
    return () => window.clearInterval(interval);
  }, []);

  const copyCommand = async (command: string, label: string) => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(label);
      window.setTimeout(() => setCopied(''), 1600);
    } catch {
      setCopied('');
    }
  };

  if (!stats) return <OfflineStart error={connectionError} />;

  const hardware = stats.hardware ?? fallbackHardware(stats.interface);
  const monitorLabel = hardware.monitor_mode ? 'Enabled' : hardware.mode === 'unknown' ? 'Unknown' : hardware.mode;
  const readiness = [
    {label: 'API', ok: !connectionError, detail: lastUpdated ? format(lastUpdated, 'HH:mm:ss') : 'waiting'},
    {label: 'USB', ok: hardware.usb_hints.length > 0, detail: hardware.usb_hints.length ? 'adapter seen' : 'check passthrough'},
    {label: 'Iface', ok: hardware.interface_present, detail: hardware.interface || 'unknown'},
    {label: 'Monitor', ok: hardware.monitor_mode, detail: monitorLabel},
  ];
  const openApCount = stats.aps.filter((ap) => ap.crypto.includes('Open')).length;
  const congestion = Math.min(100, Math.floor((stats.aps.length / 50) * 100));
  const activeSeverity = stats.alerts.some((alert) => alert.severity === 'critical') ? 'critical' : stats.alerts.some((alert) => alert.severity === 'warning') ? 'warning' : 'info';

  const topAp = useMemo(() => [...stats.aps].sort((a, b) => b.rssi - a.rssi)[0], [stats.aps]);

  return (
    <div className="min-h-screen bg-[#0b0b09] font-mono text-zinc-100">
      <header className="border-b border-zinc-800 bg-[#10100e] px-4 py-3 md:px-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="grid h-12 w-12 place-items-center border border-yellow-300/45 bg-yellow-300 text-black">
              <Shield size={25} strokeWidth={2.6} />
            </div>
            <div>
              <div className="text-[10px] font-black uppercase tracking-[0.24em] text-yellow-300">Ghostintheprompt Field Console</div>
              <h1 className="text-xl font-black uppercase text-white md:text-2xl">Da Bklyn Bridge v2.1</h1>
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-zinc-500">
                Passive-first wireless evidence // Brooklyn edge // Apple Silicon aware
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-right md:grid-cols-4">
            {readiness.map((item) => (
              <div key={item.label} className="min-w-[120px] border border-zinc-800 bg-black/30 px-3 py-2">
                <div className="flex items-center justify-end gap-2 text-[9px] font-black uppercase tracking-[0.16em] text-zinc-500">
                  <StatusDot state={item.ok ? 'good' : 'warn'} /> {item.label}
                </div>
                <div className={cx('mt-1 truncate text-xs font-bold uppercase', item.ok ? 'text-emerald-300' : 'text-yellow-300')}>{item.detail}</div>
              </div>
            ))}
          </div>
        </div>
      </header>

      <div className="flex min-h-[calc(100vh-76px)]">
        <aside className="hidden w-72 shrink-0 border-r border-zinc-800 bg-[#0f0f0d] p-4 lg:flex lg:flex-col">
          <div className="mb-4 text-[9px] font-black uppercase tracking-[0.22em] text-zinc-600">Bridge Modes</div>
          <div className="space-y-2">
            {OperationalModes.map((mode) => (
              <button
                key={mode.id}
                type="button"
                title={mode.title}
                onClick={() => setActiveGame(mode.id)}
                className={cx(
                  'relative flex min-h-[58px] w-full items-center gap-3 border p-3 text-left transition',
                  activeGame === mode.id
                    ? 'border-yellow-300/55 bg-yellow-300/[0.08] text-yellow-200'
                    : 'border-transparent text-zinc-500 hover:border-zinc-700 hover:bg-black/30 hover:text-zinc-200',
                )}
              >
                {activeGame === mode.id && <motion.div layoutId="nav-stripe" className="absolute left-0 top-0 h-full w-1 bg-yellow-300" />}
                <mode.icon size={17} className={activeGame === mode.id ? 'text-yellow-300' : 'text-zinc-600'} />
                <div className="min-w-0">
                  <div className="truncate text-[11px] font-black uppercase">{mode.title}</div>
                  <div className="mt-0.5 text-[9px] text-zinc-600">{mode.desc}</div>
                </div>
              </button>
            ))}
          </div>

          <div className="mt-auto border border-zinc-800 bg-black/25 p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-[9px] font-black uppercase tracking-[0.18em] text-yellow-300">Hardware Stack</div>
              {hardware.monitor_mode ? <CheckCircle2 size={15} className="text-emerald-300" /> : <XCircle size={15} className="text-yellow-300" />}
            </div>
            <div className="space-y-2 text-[10px] uppercase">
              <div className="flex justify-between gap-3">
                <span className="text-zinc-600">Chipset</span>
                <span className="max-w-[150px] truncate text-right text-zinc-300" title={hardware.chipset_hint}>{hardware.chipset_hint}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-zinc-600">Driver</span>
                <span className="text-zinc-300">{hardware.driver}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-zinc-600">Platform</span>
                <span className="max-w-[150px] truncate text-right text-zinc-300" title={hardware.platform}>{hardware.platform}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-zinc-600">Mode</span>
                <span className={hardware.monitor_mode ? 'text-emerald-300' : 'text-yellow-300'}>{monitorLabel}</span>
              </div>
            </div>
          </div>
        </aside>

        <main className="flex-1 overflow-auto bg-[radial-gradient(circle_at_top_left,rgba(250,204,21,0.08),transparent_32%),linear-gradient(180deg,#151512,#0b0b09)] p-2 md:p-4">
          <div className="grid grid-cols-1 gap-2 xl:grid-cols-3">
            {activeGame === 'launch' && (
              <>
                <Widget title="Launch Deck" icon={PlugZap} accent="amber" className="xl:col-span-2">
                  <div className="grid gap-3 md:grid-cols-2">
                    {readiness.map((item) => (
                      <div key={item.label} className="border border-zinc-800 bg-black/35 p-4">
                        <div className="mb-3 flex items-center justify-between">
                          <div className="text-[10px] font-black uppercase tracking-[0.16em] text-zinc-500">{item.label}</div>
                          <StatusDot state={item.ok ? 'good' : 'warn'} />
                        </div>
                        <div className={cx('text-lg font-black uppercase', item.ok ? 'text-emerald-300' : 'text-yellow-300')}>{item.ok ? 'Ready' : 'Needs Check'}</div>
                        <div className="mt-1 text-[11px] text-zinc-500">{item.detail}</div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 border border-zinc-800 bg-[#090907] p-4">
                    <div className="mb-3 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.18em] text-yellow-300">
                      <Command size={14} /> Fast Lane Commands
                    </div>
                    <div className="grid gap-2 md:grid-cols-2">
                      <CommandCard label="Doctor" command="bash scripts/alfa_doctor.sh" copied={copied === 'Doctor'} onCopy={copyCommand} />
                      <CommandCard label="Bootstrap ACH" command="bash scripts/apple_silicon_vm_bootstrap.sh --rtl8812au --with-aircrack" copied={copied === 'Bootstrap ACH'} onCopy={copyCommand} />
                      <CommandCard label="Passive Capture" command="bash scripts/run_passive.sh --interface wlan0" copied={copied === 'Passive Capture'} onCopy={copyCommand} />
                      <CommandCard label="VM API" command="bash scripts/run_api.sh --host-vm" copied={copied === 'VM API'} onCopy={copyCommand} />
                    </div>
                  </div>
                </Widget>

                <Widget title="USB Street Sheet" icon={PlugZap} accent="green">
                  {hardware.usb_hints.length ? (
                    <div className="space-y-2">
                      {hardware.usb_hints.map((hint) => (
                        <div key={hint} className="border border-emerald-400/20 bg-emerald-400/5 p-3 text-[10px] leading-5 text-emerald-100">{hint}</div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState label="No Alfa USB hint from the VM yet" />
                  )}
                </Widget>
              </>
            )}

            {(activeGame === 'census' || activeGame === 'audit') && (
              <Widget title="Airspace Census" icon={Radio} accent="cyan" className="xl:col-span-2">
                {stats.aps.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[760px] border-collapse text-left text-[11px]">
                      <thead>
                        <tr className="border-b border-zinc-800 text-[9px] uppercase tracking-[0.16em] text-zinc-600">
                          <th className="px-3 py-2 font-black">SSID</th>
                          <th className="px-3 py-2 font-black">BSSID</th>
                          <th className="px-3 py-2 font-black">CH</th>
                          <th className="px-3 py-2 font-black">RSSI</th>
                          <th className="px-3 py-2 font-black">Grade</th>
                          <th className="px-3 py-2 font-black">Vendor</th>
                          <th className="px-3 py-2 font-black">Security</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900">
                        {stats.aps.map((ap) => (
                          <tr key={ap.bssid} className="transition hover:bg-yellow-300/5">
                            <td className="px-3 py-3 font-black text-cyan-200">{ap.ssid === '<Hidden>' ? 'hidden' : ap.ssid}</td>
                            <td className="px-3 py-3 text-zinc-500">{ap.bssid}</td>
                            <td className="px-3 py-3 text-emerald-300">{ap.channel}</td>
                            <td className="px-3 py-3 text-yellow-300">{ap.rssi}</td>
                            <td className="px-3 py-3 text-zinc-400">{signalGrade(ap.rssi)}</td>
                            <td className="px-3 py-3 text-zinc-500">{ap.vendor || 'Unknown'}</td>
                            <td className="px-3 py-3 text-zinc-500">{ap.crypto}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyState label="No AP rows yet" />
                )}
              </Widget>
            )}

            {activeGame === 'probes' && (
              <Widget title="Probe Watch" icon={Smartphone} accent="cyan" className="xl:col-span-2">
                {stats.probes.length ? (
                  <div className="space-y-2">
                    {stats.probes.map((probe, index) => (
                      <div key={`${probe.mac}-${probe.timestamp}-${index}`} className="grid gap-2 border border-zinc-800 bg-black/30 p-3 text-[11px] md:grid-cols-[1.2fr_1fr_auto]">
                        <span className="text-zinc-400">{probe.mac}</span>
                        <span className="font-bold text-cyan-200">{probe.ssid}</span>
                        <span className="text-yellow-300">{probe.rssi} dBm</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState label="No probe rows yet" />
                )}
              </Widget>
            )}

            {activeGame === 'deauth' && (
              <Widget title="Deauth Watch" icon={AlertTriangle} accent={stats.summary.deauth_group_count ? 'red' : 'green'} className="xl:col-span-2">
                <div className={cx('mb-4 border p-4', stats.summary.deauth_group_count ? 'border-red-400/35 bg-red-500/10' : 'border-emerald-400/25 bg-emerald-400/5')}>
                  <div className="mb-1 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.16em]">
                    <StatusDot state={stats.summary.deauth_group_count ? 'bad' : 'good'} />
                    <span className={stats.summary.deauth_group_count ? 'text-red-300' : 'text-emerald-300'}>
                      {stats.summary.deauth_group_count ? 'Management-frame abuse observed' : 'Current window clean'}
                    </span>
                  </div>
                  <p className="text-[11px] leading-5 text-zinc-400">Passive telemetry only. Active mitigation stays locked unless written lab scope and config gates are present.</p>
                </div>
                {stats.deauth_stats.length ? (
                  <div className="space-y-2">
                    {stats.deauth_stats.map((row) => (
                      <div key={row.bssid} className="grid grid-cols-[1fr_auto_auto] items-center gap-3 border border-zinc-800 bg-black/35 p-3 text-[11px]">
                        <span className="text-zinc-400">{row.bssid}</span>
                        <span className="font-black text-red-300">{row.count} frames</span>
                        <span className="text-zinc-600">{formatTimestamp(row.last)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState label="No deauth bucket rows" />
                )}
              </Widget>
            )}

            {activeGame === 'timelapse' && (
              <Widget title="Time-Lapse" icon={Clock} accent="violet" className="xl:col-span-2">
                <div className="h-[320px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="time" stroke="#71717a" fontSize={10} />
                      <YAxis stroke="#71717a" fontSize={10} />
                      <Tooltip contentStyle={{backgroundColor: '#11110f', border: '1px solid #3f3f46', borderRadius: 0}} />
                      <Line type="monotone" dataKey="probes" stroke="#22d3ee" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="aps" stroke="#facc15" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="alerts" stroke="#f87171" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </Widget>
            )}

            {activeGame === 'audit' && (
              <Widget title="Rogue AP Review" icon={Eye} accent={stats.rogue_aps.length ? 'red' : 'green'}>
                {stats.rogue_aps.length ? (
                  <div className="space-y-2">
                    {stats.rogue_aps.map((ap) => (
                      <div key={ap.bssid} className="border border-red-400/30 bg-red-500/10 p-3">
                        <div className="flex items-center justify-between gap-2 text-[10px] uppercase">
                          <span className="font-black text-red-200">{ap.ssid}</span>
                          <span className="text-zinc-500">CH {ap.channel}</span>
                        </div>
                        <div className="mt-2 text-[10px] text-zinc-400">{ap.bssid}</div>
                        <div className="mt-1 text-[9px] text-zinc-600">{ap.crypto || 'Unknown security'} // {ap.rssi} dBm</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState label="No rogue AP rows for watched scope" />
                )}
              </Widget>
            )}

            {activeGame === 'academy' && (
              <Widget title="Academy Field Notes" icon={Layers} accent="amber" className="xl:col-span-2">
                <div className="grid gap-3 md:grid-cols-3">
                  {[
                    ['Management Frames', 'Beacons, probes, and deauth frames explain most of what this dashboard sees.'],
                    ['EAPOL', 'Handshake frames are evidence events here, not cracking workflow instructions.'],
                    ['802.11w', 'Protected Management Frames reduce spoofed deauth risk and should be part of the defensive story.'],
                  ].map(([title, body]) => (
                    <div key={title} className="border border-zinc-800 bg-black/30 p-4">
                      <div className="mb-2 text-[10px] font-black uppercase tracking-[0.16em] text-yellow-300">{title}</div>
                      <p className="text-[11px] leading-5 text-zinc-400">{body}</p>
                    </div>
                  ))}
                </div>
              </Widget>
            )}

            <Widget title="Intelligence Feed" icon={Shield} accent={activeSeverity === 'critical' ? 'red' : activeSeverity === 'warning' ? 'amber' : 'green'}>
              <div className="space-y-3">
                <AnimatePresence mode="popLayout">
                  {stats.alerts.length ? stats.alerts.map((alert, index) => (
                    <motion.div
                      key={`${alert.timestamp}-${alert.type}-${index}`}
                      initial={{opacity: 0, y: 8}}
                      animate={{opacity: 1, y: 0}}
                      className={cx(
                        'border-l-2 bg-black/30 p-3 text-[10px]',
                        alert.severity === 'critical' && 'border-red-400',
                        alert.severity === 'warning' && 'border-yellow-300',
                        alert.severity === 'info' && 'border-cyan-300',
                      )}
                    >
                      <div className="mb-1 flex justify-between gap-3">
                        <span className={cx('font-black uppercase', alert.severity === 'critical' ? 'text-red-300' : alert.severity === 'warning' ? 'text-yellow-300' : 'text-cyan-300')}>{alert.type}</span>
                        <span className="text-zinc-600">{formatTimestamp(alert.timestamp)}</span>
                      </div>
                      <div className="leading-5 text-zinc-400">{alert.msg}</div>
                    </motion.div>
                  )) : (
                    <EmptyState label="No alert rows yet" />
                  )}
                </AnimatePresence>
              </div>
            </Widget>

            <Widget title="Telemetry Summary" icon={Activity} accent="cyan">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  {[
                    ['APs', stats.summary.ap_count, 'text-cyan-300'],
                    ['Probes', stats.summary.probe_count, 'text-yellow-300'],
                    ['Rogue', stats.summary.rogue_ap_count, 'text-red-300'],
                    ['RID', stats.summary.remote_id_alert_count, 'text-emerald-300'],
                  ].map(([label, value, color]) => (
                    <div key={label as string} className="border border-zinc-800 bg-black/30 p-3">
                      <div className="text-[9px] font-black uppercase tracking-[0.16em] text-zinc-600">{label}</div>
                      <div className={cx('mt-1 text-2xl font-black', color as string)}>{value}</div>
                    </div>
                  ))}
                </div>

                <div>
                  <div className="mb-1 flex justify-between text-[10px] uppercase text-zinc-500">
                    <span>Airspace Congestion</span>
                    <span className="text-yellow-300">{congestion}%</span>
                  </div>
                  <div className="h-1.5 overflow-hidden bg-zinc-900">
                    <div className="h-full bg-yellow-300" style={{width: `${congestion}%`}} />
                  </div>
                </div>

                <div>
                  <div className="mb-1 flex justify-between text-[10px] uppercase text-zinc-500">
                    <span>Open AP Count</span>
                    <span className="text-red-300">{openApCount}</span>
                  </div>
                  <div className="h-1.5 overflow-hidden bg-zinc-900">
                    <div className="h-full bg-red-400" style={{width: `${Math.min(100, (openApCount / Math.max(1, stats.aps.length)) * 100)}%`}} />
                  </div>
                </div>

                <div className="border border-zinc-800 bg-black/30 p-3">
                  <div className="text-[9px] font-black uppercase tracking-[0.16em] text-zinc-600">Anomaly Engine</div>
                  <div className="mt-2 text-[11px] text-zinc-400">
                    IsolationForest: <span className={stats.anomaly_model.loaded ? 'text-emerald-300' : 'text-yellow-300'}>{stats.anomaly_model.status}</span>
                  </div>
                  <div className="mt-1 text-[9px] text-zinc-600">
                    Samples {stats.anomaly_model.sample_count || 0} // Trained {stats.anomaly_model.trained_at || 'not yet'}
                  </div>
                </div>

                <div className="h-[92px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={history}>
                      <defs>
                        <linearGradient id="bridgePulse" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#facc15" stopOpacity={0.45} />
                          <stop offset="95%" stopColor="#facc15" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <Area type="monotone" dataKey="aps" stroke="#facc15" fill="url(#bridgePulse)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </Widget>

            <Widget title="Top Signal" icon={Signal} accent="amber">
              {topAp ? (
                <div className="space-y-3">
                  <div className="text-3xl font-black uppercase text-white">{topAp.ssid === '<Hidden>' ? 'hidden' : topAp.ssid}</div>
                  <div className="grid grid-cols-2 gap-2 text-[10px] uppercase">
                    <div className="border border-zinc-800 bg-black/30 p-3">
                      <div className="text-zinc-600">RSSI</div>
                      <div className="mt-1 text-lg font-black text-yellow-300">{topAp.rssi}</div>
                    </div>
                    <div className="border border-zinc-800 bg-black/30 p-3">
                      <div className="text-zinc-600">Channel</div>
                      <div className="mt-1 text-lg font-black text-cyan-300">{topAp.channel}</div>
                    </div>
                  </div>
                  <div className="break-all text-[10px] leading-5 text-zinc-500">{topAp.bssid}</div>
                </div>
              ) : (
                <EmptyState label="No top signal yet" />
              )}
            </Widget>
          </div>
        </main>
      </div>

      <footer className="border-t border-zinc-800 bg-[#10100e] px-4 py-2 text-[9px] font-bold uppercase tracking-[0.18em] text-zinc-600 md:px-6">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap gap-4">
            <span className="flex items-center gap-2"><StatusDot state="good" /> Capture {stats.mode === 'passive' ? 'Passive' : stats.mode}</span>
            <span className="flex items-center gap-2"><Database size={12} /> sentinel.db</span>
            <span className="flex items-center gap-2"><Terminal size={12} /> {hardware.doctor}</span>
          </div>
          <div>{lastUpdated ? `Updated ${format(lastUpdated, 'HH:mm:ss')}` : 'Waiting'}</div>
        </div>
      </footer>
    </div>
  );
}
