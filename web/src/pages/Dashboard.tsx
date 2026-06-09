import { useEffect, useState } from "react";
import { Card, StatCard } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Empty } from "@/components/ui/empty";
import { Spinner } from "@/components/ui/spinner";
import { Sparkline } from "@/components/ui/sparkline";
import { api, type Profit, type PerformanceEntry, type DailyResponse } from "@/lib/api";
import { downloadCSV } from "@/lib/export";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/useToast";
import { useWebSocket } from "@/hooks/useWebSocket";
import { BarChart3, Activity, TrendingUp, TrendingDown, Target, Clock, DollarSign, Shield, Zap, Download } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from "recharts";

interface ChartPoint {
  label: string;
  value: number;
  equity: number;
  pnl: number;
}

export default function Dashboard() {
  const [profit, setProfit] = useState<Profit | null>(null);
  const [perf, setPerf] = useState<PerformanceEntry[]>([]);
  const [daily, setDaily] = useState<DailyResponse | null>(null);
  const [lastTrade, setLastTrade] = useState<string>("\u2014");
  const [lastSignal, setLastSignal] = useState<string>("\u2014");
  const [uptime, setUptime] = useState<string>("\u2014");
  const [equityData, setEquityData] = useState<ChartPoint[]>([]);
  const [dailyPnlData, setDailyPnlData] = useState<{ label: string; pnl: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const { lastMessage, subscribe } = useWebSocket();
  const { addToast } = useToast();

  const handleExport = () => {
    if (!daily) return;
    const headers = ["Date", "Abs Profit", "Rel Profit %", "Starting Balance", "Trade Count"];
    const rows = daily.data.map((d: { date: string; abs_profit: number; rel_profit: number; starting_balance: number; trade_count: number }) => [d.date, d.abs_profit.toFixed(2), d.rel_profit.toFixed(2), d.starting_balance.toFixed(2), d.trade_count]);
    downloadCSV("daily_pnl.csv", headers, rows);
    addToast("success", "Export complete", `${daily.data.length} daily records exported`);
  };

  useEffect(() => {
    Promise.all([
      api.profit().then(setProfit),
      api.performance().then(setPerf),
      api.daily(30).then(setDaily),
    ]).catch(console.error).finally(() => setLoading(false));
    subscribe(["ENTRY", "EXIT", "STATUS"]);
  }, [subscribe]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 sm:h-80 gap-4">
        <Spinner className="text-primary" />
        <span className="text-sm text-muted-foreground">Loading dashboard\u2026</span>
      </div>
    );
  }

  useEffect(() => {
    if (daily && daily.data.length > 0) {
      const equityPoints: ChartPoint[] = [];
      let runningBalance = daily.data[0].starting_balance;
      for (const d of daily.data) {
        runningBalance += d.abs_profit;
        equityPoints.push({
          label: d.date.slice(5),
          value: runningBalance,
          equity: runningBalance,
          pnl: d.abs_profit,
        });
      }
      setEquityData(equityPoints);
      setDailyPnlData(daily.data.map((d: { date: string; rel_profit: number }) => ({
        label: d.date.slice(5),
        pnl: d.rel_profit,
      })));
    }
  }, [daily]);

  useEffect(() => {
    if (profit && profit.bot_start_timestamp) {
      const start = profit.bot_start_timestamp * 1000;
      const now = Date.now();
      const diff = now - start;
      const days = Math.floor(diff / 86400000);
      const hours = Math.floor((diff % 86400000) / 3600000);
      const mins = Math.floor((diff % 3600000) / 60000);
      setUptime(`${days}d ${hours}h ${mins}m`);
    }
  }, [profit]);

  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === "EXIT") {
        setLastTrade(new Date().toLocaleTimeString());
        api.profit().then(setProfit).catch(console.error);
      }
      if (lastMessage.type === "ENTRY") {
        setLastSignal(new Date().toLocaleTimeString());
      }
    }
  }, [lastMessage]);

  const totalPnl = profit?.profit_all_percent ?? 0;
  const closedPnl = profit?.profit_closed_percent ?? 0;
  const winrate = profit?.winrate ?? 0;
  const tradeCount = profit?.trade_count ?? 0;
  const maxDrawdown = profit?.max_drawdown ?? 0;
  const profitFactor = profit?.profit_factor ?? 0;
  const sharpe = profit?.sharpe ?? 0;
  const expectancy = profit?.expectancy ?? 0;

  const equitySparkline = equityData.map(d => d.equity);
  const pnlSparkline = dailyPnlData.map(d => d.pnl);

  const pnlColor = totalPnl >= 0 ? "#00ff88" : "#ff4466";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2.5">
            <BarChart3 className="size-5 text-primary" aria-hidden="true" />
            Dashboard
          </h2>
          <p className="text-sm text-muted-foreground mt-1">Real-time trading overview</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download aria-hidden="true" /> Export CSV
          </Button>
          <div className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock size={12} aria-hidden="true" />
            <span className="font-mono">{uptime}</span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          label="Total P&L"
          value={profit ? `${totalPnl.toFixed(2)}%` : "\u2014"}
          subtitle={profit ? `${profit.profit_all_coin.toFixed(4)}` : ""}
          trend={totalPnl >= 0 ? `+${totalPnl.toFixed(2)}%` : `${totalPnl.toFixed(2)}%`}
          icon={<DollarSign size={14} />}
        />
        <StatCard
          label="Closed P&L"
          value={profit ? `${closedPnl.toFixed(2)}%` : "\u2014"}
          trend={closedPnl >= 0 ? `+${closedPnl.toFixed(2)}%` : `${closedPnl.toFixed(2)}%`}
          icon={<TrendingUp size={14} />}
        />
        <StatCard
          label="Win Rate"
          value={profit ? `${(winrate * 100).toFixed(1)}%` : "\u2014"}
          subtitle={`${profit?.winning_trades ?? 0}W / ${profit?.losing_trades ?? 0}L`}
          icon={<Target size={14} />}
        />
        <StatCard
          label="Trades"
          value={tradeCount}
          subtitle={`Best: ${profit?.best_pair ?? "\u2014"}`}
          icon={<Activity size={14} />}
        />
        <StatCard
          label="Max Drawdown"
          value={profit ? `${(maxDrawdown * 100).toFixed(2)}%` : "\u2014"}
          trend={profitFactor ? `PF: ${profitFactor.toFixed(2)}` : ""}
          icon={<TrendingDown size={14} />}
        />
        <StatCard
          label="Sharpe"
          value={sharpe ? sharpe.toFixed(2) : "\u2014"}
          subtitle={expectancy ? `Exp: ${expectancy.toFixed(2)}` : ""}
          icon={<Zap size={14} />}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Equity Curve */}
        <Card title="Equity Curve">
          {equityData.length > 0 ? (
            <div className="h-64 sm:h-72 xl:h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={equityData}>
                  <defs>
                    <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={pnlColor} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={pnlColor} stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" />
                  <XAxis dataKey="label" stroke="#888a9e" fontSize={11} tickLine={false} />
                  <YAxis stroke="#888a9e" fontSize={11} tickLine={false} domain={["auto", "auto"]} />
                  <Tooltip
                    contentStyle={{
                      background: "#1a1d2e",
                      border: "1px solid #2a2d3e",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    labelStyle={{ color: "#e4e6f0" }}
                    itemStyle={{ color: pnlColor }}
                    formatter={(_val: unknown) => [String(_val), "Equity"]}
                  />
                  <Area type="monotone" dataKey="equity" stroke={pnlColor} strokeWidth={2} fill="url(#equityGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty icon={BarChart3} title="No equity data available" />
          )}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <DollarSign size={14} className="text-primary" aria-hidden="true" />
              <span className="text-xs text-muted-foreground">Starting: {" "}
                <span className="font-mono">{daily?.data[0]?.starting_balance.toFixed(2) ?? "\u2014"}</span>
              </span>
            </div>
            <Sparkline data={equitySparkline} color={pnlColor} />
          </div>
        </Card>

        {/* Daily P&L */}
        <Card title="Daily P&L %">
          {dailyPnlData.length > 0 ? (
            <div className="h-64 sm:h-72 xl:h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dailyPnlData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" />
                  <XAxis dataKey="label" stroke="#888a9e" fontSize={11} tickLine={false} />
                  <YAxis stroke="#888a9e" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      background: "#1a1d2e",
                      border: "1px solid #2a2d3e",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(_val: unknown) => [`${String(_val)}%`, "Daily P&L"]}
                  />
                  <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
                    {dailyPnlData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? "#00ff88" : "#ff4466"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty icon={BarChart3} title="No daily P&L data available" />
          )}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-primary" aria-hidden="true" />
              <span className="text-xs text-muted-foreground">
                {daily?.data.reduce((s: number, d: { trade_count: number }) => s + d.trade_count, 0) ?? 0} trades over {daily?.data.length ?? 0} days
              </span>
            </div>
            <Sparkline data={pnlSparkline} color="#00d4ff" />
          </div>
        </Card>
      </div>

      {/* Secondary Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {/* Recent Activity */}
        <Card title="Recent Activity">
          <div className="flex flex-col gap-1" aria-live="polite">
            <div className="flex items-center gap-3 text-sm rounded-lg py-2 px-3">
              <Zap size={16} className="text-primary shrink-0" aria-hidden="true" />
              <span className="text-muted-foreground">Last entry signal:</span>
              <span className="text-primary font-mono font-medium">{lastSignal}</span>
            </div>
            <div className="flex items-center gap-3 text-sm rounded-lg py-2 px-3">
              <Activity size={16} className="text-profit shrink-0" aria-hidden="true" />
              <span className="text-muted-foreground">Last trade exit:</span>
              <span className="text-profit font-mono font-medium">{lastTrade}</span>
            </div>
            <div className="flex items-center gap-3 text-sm rounded-lg py-2 px-3">
              <Shield size={16} className="text-warning shrink-0" aria-hidden="true" />
              <span className="text-muted-foreground">Current drawdown:</span>
              <span className={cn("font-mono font-medium", profit && profit.current_drawdown < 0 ? "text-loss" : "text-muted-foreground")}>
                {profit ? `${(profit.current_drawdown * 100).toFixed(2)}%` : "\u2014"}
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm rounded-lg py-2 px-3">
              <TrendingUp size={16} className="text-muted-foreground shrink-0" aria-hidden="true" />
              <span className="text-muted-foreground">Expectancy ratio:</span>
              <span className="font-mono font-medium">{profit ? `${profit.expectancy_ratio?.toFixed(3) ?? "\u2014"}` : "\u2014"}</span>
            </div>
          </div>
        </Card>

        {/* Top Pairs */}
        <Card title="Top Pairs by P&L">
          <div className="flex flex-col gap-1">
            {perf.slice(0, 6).map((p) => (
              <div key={p.pair} className="flex items-center justify-between text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
                <span className="font-medium">{p.pair}</span>
                <div className="flex items-center gap-3">
                  <span className="text-muted-foreground text-xs font-mono">{p.count} trades</span>
                  <span className={cn("font-bold font-mono", p.profit_pct >= 0 ? "text-profit" : "text-loss")}>
                    {p.profit_pct >= 0 ? "+" : ""}{p.profit_pct.toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
            {perf.length === 0 && (
              <Empty icon={BarChart3} title="No performance data yet" />
            )}
          </div>
        </Card>

        {/* Quick Stats */}
        <Card title="Key Metrics">
          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-center text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
              <span className="text-muted-foreground">Profit Factor</span>
              <span className="font-bold font-mono">{profitFactor ? profitFactor.toFixed(2) : "\u2014"}</span>
            </div>
            <div className="flex justify-between items-center text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
              <span className="text-muted-foreground">Sortino</span>
              <span className="font-bold font-mono">{profit?.sortino ? profit.sortino.toFixed(2) : "\u2014"}</span>
            </div>
            <div className="flex justify-between items-center text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
              <span className="text-muted-foreground">Calmar</span>
              <span className="font-bold font-mono">{profit?.calmar ? profit.calmar.toFixed(2) : "\u2014"}</span>
            </div>
            <div className="flex justify-between items-center text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
              <span className="text-muted-foreground">SQN</span>
              <span className="font-bold font-mono">{profit?.sqn ? profit.sqn.toFixed(2) : "\u2014"}</span>
            </div>
            <div className="flex justify-between items-center text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
              <span className="text-muted-foreground">Avg Duration</span>
              <span className="font-bold font-mono">{profit?.avg_duration ?? "\u2014"}</span>
            </div>
            <div className="flex justify-between items-center text-sm rounded-lg py-2 px-3 hover:bg-muted/30 motion-safe:transition-colors">
              <span className="text-muted-foreground">CAGR</span>
              <span className="font-bold font-mono">{profit?.cagr ? `${(profit.cagr * 100).toFixed(1)}%` : "\u2014"}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
