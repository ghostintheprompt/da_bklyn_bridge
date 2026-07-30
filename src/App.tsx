import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Wifi, 
  Activity, 
  AlertTriangle, 
  Smartphone, 
  Layers, 
  Terminal, 
  Clock,
  Radio,
  Signal,
  Lock,
  Eye,
  Settings
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import { format } from 'date-fns';

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

interface Stats {
  interface: string;
  mode: string;
  channel: number;
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
    night_owls: Array<{ ssid: string; bssid: string; time: string }>;
    ghosts: Array<{ ssid: string; bssid: string; time: string }>;
  };
  deauth_stats: Array<{ bssid: string; count: number; last: string }>;
  rogue_aps: Array<{ ssid: string; bssid: string; channel: number; rssi: number; crypto?: string }>;
  anomaly_model: {
    status: string;
    loaded: boolean;
    sample_count: number;
    trained_at?: string | null;
  };
}

const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) return '--:--';
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) return '--:--';
  return format(parsed, 'HH:mm');
};

const TechnicalGrid = ({ children }: { children: React.ReactNode }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-1 p-1 bg-[#1a1a1a] min-h-screen font-mono text-[#e0e0e0]">
    {children}
  </div>
);

const Widget = ({ title, icon: Icon, children, className = "" }: { title: string, icon: any, children: React.ReactNode, className?: string }) => (
  <div className={`relative overflow-hidden bg-[#121212] border border-[#333] p-4 flex flex-col ${className}`}>
    <div className="flex items-center justify-between mb-4 border-b border-[#333] pb-2">
      <div className="flex items-center gap-2">
        <Icon size={16} className="text-blue-400" />
        <h2 className="text-[10px] uppercase tracking-[0.2em] font-bold text-gray-500">{title}</h2>
      </div>
      <div className="flex gap-1">
        <div className="w-1 h-1 bg-green-500 rounded-full animate-pulse"></div>
        <div className="w-1 h-1 bg-[#333] rounded-full"></div>
      </div>
    </div>
    <div className="flex-1 overflow-auto">
      {children}
    </div>
  </div>
);

const OperationalModes = [
  { id: 'census', title: '01: Neighborhood Census', icon: Radio, desc: 'Broad spectrum AP enumeration' },
  { id: 'probes', title: '02: Behavioral Probes', icon: Smartphone, desc: 'Client travel history extraction' },
  { id: 'deauth', title: '03: Deauth Watch', icon: AlertTriangle, desc: 'Real-time spike monitoring' },
  { id: 'timelapse', title: '04: Time-Lapse', icon: Clock, desc: 'Long-term pattern analysis' },
  { id: 'audit', title: '05: Self Audit', icon: Shield, desc: 'Leak detection & rogue AP check' },
  { id: 'academy', title: '06: Academy', icon: Layers, desc: 'Exam prep & fundamentals' }
];

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [activeGame, setActiveGame] = useState('census');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/api/stats');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setStats(data);
        setHistory(prev => [...prev.slice(-20), { 
          time: format(new Date(), 'HH:mm:ss'), 
          probes: data.probes.length,
          aps: data.aps.length 
        }]);
      } catch (err) {
        console.error("Failed to fetch stats", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return (
    <div className="bg-[#0a0a0a] min-h-screen flex items-center justify-center font-mono">
      <div className="flex flex-col items-center gap-4">
        <Wifi size={48} className="text-blue-500 animate-pulse" />
        <div className="text-blue-400 text-xs tracking-widest uppercase">Initializing Sentinel...</div>
      </div>
    </div>
  );

  return (
    <div className="bg-[#1a1a1a] min-h-screen flex flex-col">
      {/* Header Bar */}
      <header className="bg-[#0a0a0a] border-b border-[#333] px-6 py-3 flex items-center justify-between z-10">
        <div className="flex items-center gap-4">
          <div className="bg-blue-600 p-2 rounded">
            <Shield size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white uppercase italic">Da Bklyn Bridge v2.0 // Alpha Stream</h1>
            <p className="text-[10px] text-blue-500/80 uppercase tracking-widest font-mono">
              [2.4/5GHz Mode Active] // <span className="text-yellow-500/80 animate-pulse">6GHz Coverage Requires AWUS036AXL Upgrade</span>
            </p>
          </div>
        </div>

        <div className="flex gap-8 text-right font-mono">
          <div>
            <div className="text-[10px] text-gray-500 uppercase font-bold">Hardware</div>
            <div className="text-xs text-blue-400 flex items-center gap-1 justify-end"><Signal size={12}/> {stats.interface}</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-500 uppercase font-bold">Status</div>
            <div className="text-xs text-yellow-400">PASSIVE_MONITOR</div>
            <div className="text-[9px] text-gray-600 uppercase">{stats.mode}</div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Nav */}
        <aside className="w-64 bg-[#0d0d0d] border-r border-[#333] hidden lg:flex flex-col p-4 gap-2">
          <div className="text-[9px] text-gray-600 uppercase tracking-widest font-bold mb-4 ml-2">Operational Modes</div>
          {OperationalModes.map((mode) => (
            <button
              key={mode.id}
              onClick={() => setActiveGame(mode.id)}
              className={`text-left p-3 rounded-lg transition-all duration-300 relative group overflow-hidden ${
                activeGame === mode.id 
                  ? 'bg-blue-600/15 border border-blue-500/40 shadow-[0_0_15px_rgba(59,130,246,0.1)]' 
                  : 'hover:bg-[#1a1a1a] border border-transparent'
              }`}
            >
              {activeGame === mode.id && (
                <motion.div 
                  layoutId="active-nav-glow"
                  className="absolute left-0 top-0 w-1 h-full bg-blue-500"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                />
              )}
              <div className="flex items-center gap-3">
                <mode.icon size={16} className={activeGame === mode.id ? 'text-blue-400' : 'text-gray-500 group-hover:text-gray-300'} />
                <div>
                  <div className={`text-[11px] font-bold uppercase transition-colors ${activeGame === mode.id ? 'text-blue-400' : 'text-gray-500 group-hover:text-gray-300'}`}>
                    {mode.title}
                  </div>
                  <div className="text-[8px] text-gray-600 uppercase tracking-tighter mt-0.5">{mode.desc}</div>
                </div>
              </div>
            </button>
          ))}
          
          <div className="mt-auto p-4 bg-blue-500/5 rounded border border-blue-500/20">
            <div className="text-[9px] text-blue-400 font-bold uppercase mb-2">Driver Status</div>
            <div className="space-y-1">
              <div className="flex justify-between text-[8px] uppercase">
                <span className="text-gray-500">Chipset</span>
                <span className="text-gray-300">RTL8812AU</span>
              </div>
              <div className="flex justify-between text-[8px] uppercase">
                <span className="text-gray-500">Monitor</span>
                <span className="text-green-500 font-bold">Enabled</span>
              </div>
              <div className="flex justify-between text-[8px] uppercase">
                <span className="text-gray-500">Kernel</span>
                <span className="text-gray-300">6.x + DKMS</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Workspace */}
        <main className="flex-1 overflow-auto bg-[#141414]">
          <TechnicalGrid>
            {/* Conditional Views based on Game */}
            {activeGame === 'census' || activeGame === 'audit' ? (
              <Widget title="Active Airspace Census" icon={Radio} className="lg:col-span-2">
                <div className="w-full overflow-x-auto">
                  <table className="w-full text-left text-[11px] border-collapse">
                    <thead>
                      <tr className="border-b border-[#222] text-gray-500 uppercase">
                        <th className="py-2 px-3 font-normal">SSID</th>
                        <th className="py-2 px-3 font-normal">BSSID</th>
                        <th className="py-2 px-3 font-normal">CH</th>
                        <th className="py-2 px-3 font-normal">RSSI</th>
                        <th className="py-2 px-3 font-normal">Vendor</th>
                        <th className="py-2 px-3 font-normal">Security</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1a1a1a]">
                      {stats.aps.map((ap, i) => (
                        <tr key={ap.bssid} className="hover:bg-[#1a1a1a] transition-colors group">
                          <td className="py-3 px-3 font-bold text-blue-400 group-hover:text-blue-300">
                             {ap.ssid === '<Hidden>' ? '░░░░░░░' : ap.ssid}
                          </td>
                          <td className="py-3 px-3 text-gray-500 font-mono tracking-tighter">{ap.bssid}</td>
                          <td className="py-3 px-3 font-mono text-green-400">{ap.channel}</td>
                          <td className="py-3 px-3">
                            <span className={`font-mono ${ap.rssi > -60 ? 'text-green-500' : 'text-gray-500'}`}>{ap.rssi}</span>
                          </td>
                          <td className="py-3 px-3 text-gray-500 text-[10px]">{ap.vendor || 'Unknown'}</td>
                          <td className="py-3 px-3 text-gray-500 italic text-[10px]">{ap.crypto}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Widget>
            ) : null}

            {activeGame === 'probes' ? (
              <Widget title="Client Behavioral Profiling" icon={Smartphone} className="lg:col-span-2">
                <div className="space-y-4">
                  <div className="p-3 bg-blue-500/5 border border-blue-500/20 text-[10px] text-blue-400">
                    ANALYSIS: Detecting device travel history via SSID leakage in broadcast probe requests.
                  </div>
                  <table className="w-full text-left text-[11px] border-collapse">
                    <thead>
                      <tr className="border-b border-[#222] text-gray-500 uppercase">
                        <th className="py-2 px-3 font-normal font-bold">Source MAC</th>
                        <th className="py-2 px-3 font-normal font-bold">Queried SSID</th>
                        <th className="py-2 px-3 font-normal font-bold">Level</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1a1a1a]">
                      {stats.probes.map((p, i) => (
                        <tr key={p.mac + i} className="hover:bg-[#000]/20">
                          <td className="py-2 px-3 font-mono text-gray-400">{p.mac}</td>
                          <td className="py-2 px-3 text-blue-400">{p.ssid}</td>
                          <td className="py-2 px-3 font-mono text-yellow-500/80">{p.rssi}dBm</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Widget>
            ) : null}

            {activeGame === 'timelapse' ? (
              <Widget title="Temporal Analysis" icon={Clock} className="lg:col-span-2">
                <div className="h-[300px] w-full p-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                      <XAxis dataKey="time" stroke="#444" fontSize={10} />
                      <YAxis stroke="#444" fontSize={10} />
                      <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }} />
                      <Line type="monotone" dataKey="probes" stroke="#3b82f6" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="aps" stroke="#10b981" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="mt-4 grid grid-cols-3 gap-2 text-[10px] text-center">
                    <div className="p-2 border border-[#333] rounded">
                      <div className="text-gray-500 uppercase">Night-Only APs</div>
                      <div className="text-blue-400 font-bold mt-1">{stats.summary.night_owl_count}</div>
                    </div>
                    <div className="p-2 border border-[#333] rounded">
                      <div className="text-gray-500 uppercase">Ghost Signals</div>
                      <div className="text-purple-400 font-bold mt-1">{stats.summary.ghost_network_count}</div>
                    </div>
                    <div className="p-2 border border-[#333] rounded">
                      <div className="text-gray-500 uppercase">Peak Air Traffic</div>
                      <div className="text-yellow-400 font-bold mt-1">
                        {history.reduce((peak, point) => point.aps + point.probes > peak.total ? { time: point.time, total: point.aps + point.probes } : peak, { time: '--:--', total: -1 }).time}
                      </div>
                    </div>
                  </div>
                </div>
              </Widget>
            ) : null}

            {activeGame === 'deauth' ? (
              <Widget title="Attack Surface Monitor" icon={AlertTriangle} className="lg:col-span-2">
                <div className={`${stats.summary.deauth_group_count ? 'bg-red-500/10 border-red-500/30' : 'bg-blue-500/5 border-blue-500/20'} border p-4 mb-4`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-2 h-2 ${stats.summary.deauth_group_count ? 'bg-red-500 animate-ping' : 'bg-blue-500'} rounded-full`} />
                    <span className={`text-[10px] ${stats.summary.deauth_group_count ? 'text-red-500' : 'text-blue-400'} font-bold uppercase tracking-widest`}>
                      {stats.summary.deauth_group_count ? 'Deauth Activity Observed' : 'No Deauth Spike In Current Window'}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-300">Passive management-frame telemetry only. Active mitigation remains gated by lab configuration.</p>
                </div>
                <div className="space-y-2">
                  {stats.deauth_stats.length ? stats.deauth_stats.map((row) => (
                    <div key={row.bssid} className="flex items-center justify-between border border-[#222] bg-[#0d0d0d] p-3 text-[10px]">
                      <span className="font-mono text-gray-400">{row.bssid}</span>
                      <span className="text-red-400 font-bold">{row.count} frames</span>
                      <span className="text-gray-600">{formatTimestamp(row.last)}</span>
                    </div>
                  )) : (
                    <div className="text-center py-16 text-gray-700 text-[10px] uppercase font-bold border-2 border-dashed border-[#222]">
                      Current deauth bucket empty
                    </div>
                  )}
                </div>
              </Widget>
            ) : null}

            {activeGame === 'audit' ? (
              <Widget title="Rogue AP Review" icon={Eye}>
                <div className="space-y-2">
                  {stats.rogue_aps.length ? stats.rogue_aps.map((ap) => (
                    <div key={ap.bssid} className="p-3 border border-red-500/30 bg-red-500/5">
                      <div className="flex items-center justify-between text-[10px] uppercase">
                        <span className="text-red-400 font-bold">{ap.ssid}</span>
                        <span className="text-gray-500">CH {ap.channel}</span>
                      </div>
                      <div className="font-mono text-[10px] text-gray-400 mt-2">{ap.bssid}</div>
                      <div className="text-[9px] text-gray-600 mt-1">{ap.crypto || 'Unknown security'} // {ap.rssi}dBm</div>
                    </div>
                  )) : (
                    <div className="text-center py-12 text-gray-700 text-[10px] uppercase font-bold border-2 border-dashed border-[#222]">
                      No rogue AP rows for watched BSSID set
                    </div>
                  )}
                </div>
              </Widget>
            ) : null}

            {activeGame === 'academy' ? (
              <Widget title="Sentinel Academy // Exam Reference" icon={Layers} className="lg:col-span-2">
                <div className="space-y-6 text-[11px] p-2">
                   <section>
                      <div className="text-blue-400 font-bold uppercase mb-2 border-b border-[#333] pb-1">01: Management Frames</div>
                      <p className="text-gray-400 leading-relaxed mb-2">Essential for Security+ & PenTest+. The Sentinel captures these in real-time:</p>
                      <ul className="list-disc list-inside space-y-1 text-gray-500">
                        <li><span className="text-gray-300">Beacons:</span> Advertised by APs to announce existence (Census Mode).</li>
                        <li><span className="text-gray-300">Probe Requests:</span> Sent by clients to find SSIDs (Probe Mode).</li>
                        <li><span className="text-gray-300">Deauth:</span> Used to terminate sessions. Spoofing these is a core wireless attack.</li>
                      </ul>
                   </section>

                   <section>
                      <div className="text-blue-400 font-bold uppercase mb-2 border-b border-[#333] pb-1">02: The 4-Way Handshake (EAPOL)</div>
                      <p className="text-gray-400 leading-relaxed mb-4">The mechanism WPA2/3 uses to derive transient keys without sending the main password over the air.</p>
                      <div className="p-3 bg-[#0d0d0d] border-l-2 border-blue-500 text-gray-500 font-mono text-[9px]">
                        Message 1: AP &rarr; Client (ANonce)<br/>
                        Message 2: Client &rarr; AP (SNonce + MIC)<br/>
                        Message 3: AP &rarr; Client (Install PTK + MIC)<br/>
                        Message 4: Client &rarr; AP (ACK)
                      </div>
                   </section>

                   <section className="bg-yellow-500/5 p-3 border border-yellow-500/20 rounded">
                      <div className="text-yellow-500 font-bold uppercase mb-1">Defense Tip: 802.11w</div>
                      <p className="text-gray-400 italic">Management Frame Protection encrypts the "Deauth" frame. Without it, your laptop is vulnerable to being kicked by anyone with an Alfa.</p>
                   </section>
                </div>
              </Widget>
            ) : null}

            {/* Common Intelligence UI */}
            <Widget title="Intelligence Feed" icon={Shield}>
              <div className="space-y-3">
                <AnimatePresence mode="popLayout">
                  {stats.alerts.map((alert, i) => (
                    <motion.div 
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`p-3 border-l text-[10px] ${
                        alert.severity === 'critical' ? 'bg-red-500/5 border-red-500/50' : 
                        alert.severity === 'warning' ? 'bg-yellow-500/5 border-yellow-500/50' : 
                        'bg-blue-500/5 border-blue-500/50'
                      }`}
                      key={alert.timestamp + i}
                    >
                      <div className="flex justify-between mb-1">
                        <span className={`font-bold ${
                          alert.severity === 'critical' ? 'text-red-400' : 'text-blue-400'
                        }`}>{alert.type}</span>
                        <span className="text-gray-500 font-mono">{formatTimestamp(alert.timestamp)}</span>
                      </div>
                      <div className="text-gray-400 leading-tight">{alert.msg}</div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                <div className="pt-4 border-t border-[#333]">
                   <button className="w-full py-2 bg-[#222] hover:bg-[#333] text-[9px] uppercase font-bold text-gray-500 rounded transition-colors flex items-center justify-center gap-2">
                     <Terminal size={12} /> View Raw Database Log
                   </button>
                </div>
              </div>
            </Widget>

            <Widget title="Telemetry Summary" icon={Activity}>
               <div className="space-y-4">
                 <div>
                   <div className="flex justify-between items-center text-[10px] mb-1 uppercase text-gray-500">
                     <span>Airspace Congestion</span>
                     <span className="text-blue-400">{Math.floor(stats.aps.length / 50 * 100)}%</span>
                   </div>
                   <div className="h-1 bg-[#222] rounded-full overflow-hidden">
                     <div className="h-full bg-blue-500" style={{ width: `${Math.floor(stats.aps.length / 50 * 100)}%` }} />
                   </div>
                 </div>
                 <div>
                   <div className="flex justify-between items-center text-[10px] mb-1 uppercase text-gray-500">
                     <span>Unencrypted AP Count</span>
                     <span className="text-red-400">{stats.aps.filter(a => a.crypto.includes('Open')).length}</span>
                   </div>
                   <div className="h-1 bg-[#222] rounded-full overflow-hidden">
                     <div className="h-full bg-red-500" style={{ width: `${Math.min(100, (stats.aps.filter(a => a.crypto.includes('Open')).length / Math.max(1, stats.aps.length)) * 100)}%` }} />
                   </div>
                 </div>
                 <div className="p-3 bg-[#0d0d0d] border border-[#222] rounded">
                   <div className="text-[9px] text-gray-600 uppercase font-bold mb-1">Anomaly Engine</div>
                    <div className="text-[11px] text-blue-400/80 italic font-medium">
                      IsolationForest model status: <span className={stats.anomaly_model.loaded ? 'text-green-500' : 'text-yellow-500'}>{stats.anomaly_model.status}</span>
                    </div>
                    <div className="text-[9px] text-gray-600 mt-1">
                      Samples: {stats.anomaly_model.sample_count || 0} // Trained: {stats.anomaly_model.trained_at || 'not yet'}
                    </div>
                 </div>
                 <div className="grid grid-cols-3 gap-2 text-center">
                   <div className="p-2 bg-[#0d0d0d] border border-[#222] rounded">
                     <div className="text-[9px] text-gray-600 uppercase">Rogue</div>
                     <div className="text-[13px] text-red-400 font-bold">{stats.summary.rogue_ap_count}</div>
                   </div>
                   <div className="p-2 bg-[#0d0d0d] border border-[#222] rounded">
                     <div className="text-[9px] text-gray-600 uppercase">Deauth</div>
                     <div className="text-[13px] text-yellow-400 font-bold">{stats.summary.deauth_group_count}</div>
                   </div>
                   <div className="p-2 bg-[#0d0d0d] border border-[#222] rounded">
                     <div className="text-[9px] text-gray-600 uppercase">RID</div>
                     <div className="text-[13px] text-blue-400 font-bold">{stats.summary.remote_id_alert_count}</div>
                   </div>
                 </div>
               </div>
            </Widget>
          </TechnicalGrid>
        </main>
      </div>

      {/* Footer Status */}
      <footer className="mt-auto bg-[#0a0a0a] border-t border-[#333] px-6 py-2 flex items-center justify-between text-[9px] uppercase tracking-[0.2em] font-mono">
        <div className="flex gap-6 items-center">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            <span className="text-gray-500">Capture Engine: {stats.mode === 'passive' ? 'Passive' : stats.mode}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
            <span className="text-gray-500">Database: sentinel.db</span>
          </div>
        </div>
        <div className="text-gray-600">
           {new Date().toISOString()} // ALPHA // MONITOR_V1
        </div>
      </footer>
    </div>
  );
}
