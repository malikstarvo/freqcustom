import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { api, type Health, type SysInfo } from "@/lib/api";
import { Server, Cpu, MemoryStick, Activity, Power, Square, RotateCw, Clock } from "lucide-react";

export default function System() {
  const [health, setHealth] = useState<Health | null>(null);
  const [sysinfo, setSysinfo] = useState<SysInfo | null>(null);
  const [botState, setBotState] = useState<string>("unknown");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [grafanaUrl, setGrafanaUrl] = useState("");
  const [prometheusUrl, setPrometheusUrl] = useState("");

  useEffect(() => {
    setGrafanaUrl(window.location.origin.replace(":3000", ":3001"));
    setPrometheusUrl(window.location.origin.replace(":3000", ":9090"));
  }, []);

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

  const uptime = health && health.bot_start_ts
    ? (() => {
        const diff = Date.now() - health.bot_start_ts! * 1000;
        const days = Math.floor(diff / 86400000);
        const hours = Math.floor((diff % 86400000) / 3600000);
        const mins = Math.floor((diff % 3600000) / 60000);
        return `${days}d ${hours}h ${mins}m`;
      })()
    : "\u2014";

  const lastProcess = health && health.last_process_ts
    ? new Date(health.last_process_ts! * 1000).toLocaleString()
    : "\u2014";

  const cpuCores = sysinfo?.cpu_load.map((c: { pct: number }) => c.pct) ?? [];
  const cpuAvg = sysinfo?.cpu_avg ?? 0;
  const ramPct = sysinfo?.ram_pct ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <Server className="size-5 text-primary" aria-hidden="true" /> System
        </h2>
        <div className="flex items-center gap-2">
          <Badge label={botState} variant={botState === "running" ? "success" : "default"} />
        </div>
      </div>

      {/* State Control */}
      <div className="flex items-center gap-3">
        <Button
          onClick={handleStart}
          disabled={loading || botState === "running"}
        >
          <Power data-icon="inline-start" aria-hidden="true" /> Start
        </Button>
        <Button
          onClick={handleStop}
          disabled={loading || botState !== "running"}
          variant="destructive"
        >
          <Square data-icon="inline-start" aria-hidden="true" /> Stop
        </Button>
        <Button
          onClick={fetchData}
          disabled={loading}
          variant="outline"
        >
          <RotateCw data-icon="inline-start" aria-hidden="true" className={loading ? "animate-spin" : ""} /> Refresh
        </Button>
      </div>

      {message && (
        <Alert variant={message.includes("started") || message.includes("stopped") ? "success" : "destructive"}>
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Uptime"
          value={uptime}
          icon={<Clock size={14} />}
        />
        <StatCard
          label="Bot Started"
          value={health && health.bot_start_ts ? new Date(health.bot_start_ts! * 1000).toLocaleDateString() : "\u2014"}
          icon={<Power size={14} />}
        />
        <StatCard
          label="Last Process"
          value={lastProcess}
          icon={<RotateCw size={14} />}
        />
        <StatCard
          label="CPU Cores"
          value={sysinfo?.cpu_count ?? "\u2014"}
          icon={<Cpu size={14} />}
        />
      </div>

      {/* CPU & RAM */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* CPU */}
        <Card title="CPU Load">
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu size={16} className="text-primary" aria-hidden="true" />
                <span className="text-sm font-medium">Average</span>
              </div>
              <span className="text-sm font-bold font-mono">{cpuAvg.toFixed(1)}%</span>
            </div>
            <Progress value={cpuAvg} />
            <div className="grid grid-cols-4 gap-2 mt-2">
              {cpuCores.slice(0, 8).map((pct: number, i: number) => (
                <div key={i} className="flex flex-col gap-1 rounded-lg py-1 px-2 hover:bg-muted/30 motion-safe:transition-colors">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Core {i + 1}</span>
                    <span className="font-mono">{pct.toFixed(0)}%</span>
                  </div>
                  <Progress value={pct} />
                </div>
              ))}
              {cpuCores.length === 0 && (
                <p className="text-sm text-muted-foreground col-span-4">\u2014</p>
              )}
            </div>
          </div>
        </Card>

        {/* RAM */}
        <Card title="Memory">
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MemoryStick size={16} className="text-primary" aria-hidden="true" />
                <span className="text-sm font-medium">RAM Usage</span>
              </div>
              <span className="text-sm font-bold font-mono">{ramPct.toFixed(1)}%</span>
            </div>
            <Progress value={ramPct} />
            <div className="mt-4 flex flex-col gap-2">
              <div className="flex items-center gap-2 text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
                <Activity size={14} className="text-muted-foreground shrink-0" aria-hidden="true" />
                <span className="text-muted-foreground">Load avg (1m):</span>
                <span className="font-mono font-medium">{sysinfo?.cpu_load_avg?.["1m"]?.toFixed(2) ?? "\u2014"}</span>
              </div>
              <div className="flex items-center gap-2 text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
                <Activity size={14} className="text-muted-foreground shrink-0" aria-hidden="true" />
                <span className="text-muted-foreground">Load avg (5m):</span>
                <span className="font-mono font-medium">{sysinfo?.cpu_load_avg?.["5m"]?.toFixed(2) ?? "\u2014"}</span>
              </div>
              <div className="flex items-center gap-2 text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
                <Activity size={14} className="text-muted-foreground shrink-0" aria-hidden="true" />
                <span className="text-muted-foreground">Load avg (15m):</span>
                <span className="font-mono font-medium">{sysinfo?.cpu_load_avg?.["15m"]?.toFixed(2) ?? "\u2014"}</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Health Details */}
      <Card title="Health Details">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div className="rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
            <span className="text-muted-foreground text-xs block">Last Process Timestamp</span>
            <span className="font-mono font-medium">{health?.last_process_ts ?? "\u2014"}</span>
          </div>
          <div className="rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
            <span className="text-muted-foreground text-xs block">Bot Start Timestamp</span>
            <span className="font-mono font-medium">{health?.bot_start_ts ?? "\u2014"}</span>
          </div>
          <div className="rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
            <span className="text-muted-foreground text-xs block">Bot Startup</span>
            <span className="font-medium">{health?.bot_startup ? new Date(health.bot_startup).toLocaleString() : "\u2014"}</span>
          </div>
          <div className="rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
            <span className="text-muted-foreground text-xs block">CPU Load Average</span>
            <span className="font-mono font-medium">{sysinfo?.cpu_avg?.toFixed(1) ?? "\u2014"}%</span>
          </div>
          <div className="rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
            <span className="text-muted-foreground text-xs block">Logical CPUs</span>
            <span className="font-mono font-medium">{sysinfo?.cpu_count ?? "\u2014"}</span>
          </div>
          <div className="rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
            <span className="text-muted-foreground text-xs block">RAM %</span>
            <span className="font-mono font-medium">{sysinfo?.ram_pct?.toFixed(1) ?? "\u2014"}%</span>
          </div>
        </div>
      </Card>

      {/* Monitoring Hub */}
      <Card title="Monitoring Hub">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a href={grafanaUrl} target="_blank" rel="noopener noreferrer"
            className="rounded-lg border border-border/50 p-4 hover:bg-muted/30 motion-safe:transition-colors hover:border-primary/30">
            <div className="flex items-center gap-2 mb-2">
              <span className="size-2 rounded-full bg-profit" />
              <span className="text-sm font-medium">Grafana</span>
            </div>
            <p className="text-xs text-muted-foreground">Pre-built dashboards with 9 panels: equity curve, trade profit distribution, agent scores, ML predictions, and more.</p>
          </a>
          <a href={prometheusUrl} target="_blank" rel="noopener noreferrer"
            className="rounded-lg border border-border/50 p-4 hover:bg-muted/30 motion-safe:transition-colors hover:border-primary/30">
            <div className="flex items-center gap-2 mb-2">
              <span className="size-2 rounded-full bg-warning" />
              <span className="text-sm font-medium">Prometheus</span>
            </div>
            <p className="text-xs text-muted-foreground">Metrics collection from Freqtrade API. Scrapes /metrics every 15s. Query via PromQL.</p>
          </a>
          <Link href="/collector" className="rounded-lg border border-border/50 p-4 hover:bg-muted/30 motion-safe:transition-colors hover:border-primary/30">
            <div className="flex items-center gap-2 mb-2">
              <span className="size-2 rounded-full bg-primary animate-pulse" />
              <span className="text-sm font-medium">Collector</span>
            </div>
            <p className="text-xs text-muted-foreground">Go collector streams Bybit data (OHLCV, funding, OI, liquidations) into TimescaleDB.</p>
          </Link>
        </div>
        <div className="mt-3 flex gap-2">
          <span className="text-xs text-muted-foreground">
            Prometheus metrics: <code className="text-primary text-xs font-mono">freqtrade:8080/metrics</code>
          </span>
        </div>
      </Card>
    </div>
  );
}
