import { useEffect, useState } from "react";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { api, type Health, type SysInfo } from "@/lib/api";
import { Server, Cpu, MemoryStick, Activity, Power, Square, RotateCw, Clock, Zap } from "lucide-react";

export default function System() {
  const [health, setHealth] = useState<Health | null>(null);
  const [sysinfo, setSysinfo] = useState<SysInfo | null>(null);
  const [botState, setBotState] = useState<string>("unknown");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const h = await api.health();
      setHealth(h);
      const s = await api.sysinfo();
      setSysinfo(s);
      const cfg = await api.showConfig();
      setBotState(cfg.state);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const resp = await api.start();
      setMessage(`Bot ${resp.status}`);
      await fetchData();
    } catch (e: any) {
      setMessage(e.message || "Failed to start");
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const resp = await api.stop();
      setMessage(`Bot ${resp.status}`);
      await fetchData();
    } catch (e: any) {
      setMessage(e.message || "Failed to stop");
    } finally {
      setLoading(false);
    }
  };

  const uptime = health?.bot_start_ts
    ? (() => {
        const diff = Date.now() - health.bot_start_ts * 1000;
        const days = Math.floor(diff / 86400000);
        const hours = Math.floor((diff % 86400000) / 3600000);
        const mins = Math.floor((diff % 3600000) / 60000);
        return `${days}d ${hours}h ${mins}m`;
      })()
    : "—";

  const lastProcess = health?.last_process_ts
    ? new Date(health.last_process_ts * 1000).toLocaleString()
    : "—";

  const cpuCores = sysinfo?.cpu_load.map((c: { pct: number }) => c.pct) ?? [];
  const cpuAvg = sysinfo?.cpu_avg ?? 0;
  const ramPct = sysinfo?.ram_pct ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Server className="text-[--color-accent]" /> System
        </h2>
        <div className="flex items-center gap-2">
          <Badge label={botState} variant={botState === "running" ? "success" : "default"} />
        </div>
      </div>

      {/* State Control */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleStart}
          disabled={loading || botState === "running"}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Power size={14} /> Start
        </button>
        <button
          onClick={handleStop}
          disabled={loading || botState !== "running"}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Square size={14} /> Stop
        </button>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 border border-[--color-card-border] hover:bg-[--color-card-border]/30 rounded-lg text-sm text-[--color-text-secondary]"
        >
          <RotateCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {message && (
        <div className={`p-3 rounded-lg text-sm ${
          message.includes("started") || message.includes("stopped")
            ? "bg-green-950/50 text-green-400 border border-green-500/30"
            : "bg-red-950/50 text-red-400 border border-red-500/30"
        }`}>
          {message}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Uptime" value={uptime} />
        <StatCard label="Bot Started" value={health ? new Date(health.bot_start_ts * 1000).toLocaleDateString() : "—"} />
        <StatCard label="Last Process" value={lastProcess} />
        <StatCard label="CPU Cores" value={sysinfo?.cpu_count ?? "—"} />
      </div>

      {/* CPU & RAM */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* CPU */}
        <Card title="CPU Load">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu size={16} className="text-[--color-accent]" />
                <span className="text-sm font-medium">Average</span>
              </div>
              <span className="text-sm font-bold">{cpuAvg.toFixed(1)}%</span>
            </div>
            <Progress value={cpuAvg} />
            <div className="grid grid-cols-4 gap-2 mt-2">
              {cpuCores.slice(0, 8).map((pct: number, i: number) => (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-xs text-[--color-text-secondary]">
                    <span>Core {i + 1}</span>
                    <span>{pct.toFixed(0)}%</span>
                  </div>
                  <Progress value={pct} />
                </div>
              ))}
              {cpuCores.length === 0 && (
                <p className="text-sm text-[--color-text-secondary] col-span-4">No CPU data available</p>
              )}
            </div>
          </div>
        </Card>

        {/* RAM */}
        <Card title="Memory">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MemoryStick size={16} className="text-[--color-accent]" />
                <span className="text-sm font-medium">RAM Usage</span>
              </div>
              <span className="text-sm font-bold">{ramPct.toFixed(1)}%</span>
            </div>
            <Progress value={ramPct} />
            <div className="mt-4 space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Activity size={14} className="text-[--color-text-secondary]" />
                <span className="text-[--color-text-secondary]">Load avg (1m):</span>
                <span className="font-medium">{sysinfo?.cpu_load_avg?.["1m"]?.toFixed(2) ?? "—"}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Activity size={14} className="text-[--color-text-secondary]" />
                <span className="text-[--color-text-secondary]">Load avg (5m):</span>
                <span className="font-medium">{sysinfo?.cpu_load_avg?.["5m"]?.toFixed(2) ?? "—"}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Activity size={14} className="text-[--color-text-secondary]" />
                <span className="text-[--color-text-secondary]">Load avg (15m):</span>
                <span className="font-medium">{sysinfo?.cpu_load_avg?.["15m"]?.toFixed(2) ?? "—"}</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Health Details */}
      <Card title="Health Details">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-[--color-text-secondary] text-xs block">Last Process Timestamp</span>
            <span className="font-medium">{health?.last_process_ts ?? "—"}</span>
          </div>
          <div>
            <span className="text-[--color-text-secondary] text-xs block">Bot Start Timestamp</span>
            <span className="font-medium">{health?.bot_start_ts ?? "—"}</span>
          </div>
          <div>
            <span className="text-[--color-text-secondary] text-xs block">Bot Startup</span>
            <span className="font-medium">{health?.bot_startup ? new Date(health.bot_startup).toLocaleString() : "—"}</span>
          </div>
          <div>
            <span className="text-[--color-text-secondary] text-xs block">CPU Load Average</span>
            <span className="font-medium">{sysinfo?.cpu_avg.toFixed(1) ?? "—"}%</span>
          </div>
          <div>
            <span className="text-[--color-text-secondary] text-xs block">Logical CPUs</span>
            <span className="font-medium">{sysinfo?.cpu_count ?? "—"}</span>
          </div>
          <div>
            <span className="text-[--color-text-secondary] text-xs block">RAM %</span>
            <span className="font-medium">{sysinfo?.ram_pct.toFixed(1) ?? "—"}%</span>
          </div>
        </div>
      </Card>

      {/* Prometheus Link */}
      <Card title="Monitoring">
        <div className="flex items-center gap-3">
          <Zap size={16} className="text-[--color-accent]" />
          <span className="text-sm text-[--color-text-secondary]">
            Prometheus metrics are available at <code className="text-[--color-accent] text-xs">/metrics</code> on the bot API port.
          </span>
        </div>
        <div className="mt-3 flex gap-2">
          <a
            href="http://localhost:9090"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 bg-[--color-accent]/10 hover:bg-[--color-accent]/20 text-[--color-accent] rounded text-xs font-medium"
          >
            Prometheus
          </a>
          <a
            href="http://localhost:3000"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 bg-[--color-accent]/10 hover:bg-[--color-accent]/20 text-[--color-accent] rounded text-xs font-medium"
          >
            Grafana
          </a>
        </div>
      </Card>
    </div>
  );
}
