import { useEffect, useState } from "react";
import { Card, StatCard } from "@/components/ui/card";
import { Sparkline } from "@/components/ui/sparkline";
import { api, type Profit, type PerformanceEntry, type DailyResponse } from "@/lib/api";
import { downloadCSV } from "@/lib/export";
import { useToast } from "@/hooks/useToast";
import { useWebSocket } from "@/hooks/useWebSocket";
import { BarChart3, Activity, TrendingUp, Clock, DollarSign, Shield, Zap, Download } from "lucide-react";
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
  const [lastTrade, setLastTrade] = useState<string>("—");
  const [lastSignal, setLastSignal] = useState<string>("—");
  const [uptime, setUptime] = useState<string>("—");
  const [equityData, setEquityData] = useState<ChartPoint[]>([]);
  const [dailyPnlData, setDailyPnlData] = useState<{ label: string; pnl: number }[]>([]);
  const { lastMessage, subscribe } = useWebSocket();
  const { addToast } = useToast();

  const handleExport = () => {
    if (!daily) return;
    const headers = ["Date", "Abs Profit", "Rel Profit %", "Starting Balance", "Trade Count"];
    const rows = daily.data.map(d => [d.date, d.abs_profit.toFixed(2), d.rel_profit.toFixed(2), d.starting_balance.toFixed(2), d.trade_count]);
    downloadCSV("daily_pnl.csv", headers, rows);
    addToast("success", "Export complete", `${daily.data.length} daily records exported`);
  };

  useEffect(() => {
    api.profit().then(setProfit).catch(console.error);
    api.performance().then(setPerf).catch(console.error);
    api.daily(30).then(setDaily).catch(console.error);
    subscribe(["ENTRY", "EXIT", "STATUS"]);
  }, [subscribe]);

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
      setDailyPnlData(daily.data.map(d => ({
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <BarChart3 className="text-[--color-accent]" />
            Dashboard
          </h2>
          <p className="text-sm text-[--color-text-secondary] mt-1">Real-time trading overview</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-3 py-1.5 bg-[--color-card-bg] border border-[--color-card-border] hover:border-[--color-accent] rounded-lg text-xs text-[--color-text-secondary] transition-colors"
          >
            <Download size={14} /> Export CSV
          </button>
          <div className="text-xs text-[--color-text-secondary] flex items-center gap-1">
            <Clock size={12} />
            {uptime}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          label="Total P&L"
          value={profit ? `${totalPnl.toFixed(2)}%` : "—"}
          subtitle={profit ? `${profit.profit_all_coin.toFixed(4)}` : ""}
          trend={totalPnl >= 0 ? `+${totalPnl.toFixed(2)}%` : `${totalPnl.toFixed(2)}%`}
        />
        <StatCard
          label="Closed P&L"
          value={profit ? `${closedPnl.toFixed(2)}%` : "—"}
          trend={closedPnl >= 0 ? `+${closedPnl.toFixed(2)}%` : `${closedPnl.toFixed(2)}%`}
        />
        <StatCard
          label="Win Rate"
          value={profit ? `${(winrate * 100).toFixed(1)}%` : "—"}
          subtitle={`${profit?.winning_trades ?? 0}W / ${profit?.losing_trades ?? 0}L`}
        />
        <StatCard
          label="Trades"
          value={tradeCount}
          subtitle={`Best: ${profit?.best_pair ?? "—"}`}
        />
        <StatCard
          label="Max Drawdown"
          value={profit ? `${(maxDrawdown * 100).toFixed(2)}%` : "—"}
          trend={profitFactor ? `PF: ${profitFactor.toFixed(2)}` : ""}
        />
        <StatCard
          label="Sharpe"
          value={sharpe ? sharpe.toFixed(2) : "—"}
          subtitle={expectancy ? `Exp: ${expectancy.toFixed(2)}` : ""}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Equity Curve */}
        <Card title="Equity Curve" className="min-h-[300px]">
          {equityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
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
                  formatter={(val: number) => [`${val.toFixed(2)}`, "Equity"]}
                />
                <Area type="monotone" dataKey="equity" stroke={pnlColor} strokeWidth={2} fill="url(#equityGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[260px] text-sm text-[--color-text-secondary]">
              No equity data available
            </div>
          )}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <DollarSign size={14} className="text-[--color-accent]" />
              <span className="text-xs text-[--color-text-secondary]">Starting: {daily?.data[0]?.starting_balance.toFixed(2) ?? "—"}</span>
            </div>
            <Sparkline data={equitySparkline} color={pnlColor} />
          </div>
        </Card>

        {/* Daily P&L */}
        <Card title="Daily P&L %" className="min-h-[300px]">
          {dailyPnlData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
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
                  formatter={(val: number) => [`${val.toFixed(2)}%`, "Daily P&L"]}
                />
                <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
                  {dailyPnlData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? "#00ff88" : "#ff4466"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[260px] text-sm text-[--color-text-secondary]">
              No daily P&L data available
            </div>
          )}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-[--color-accent]" />
              <span className="text-xs text-[--color-text-secondary]">
                {daily?.data.reduce((s, d) => s + d.trade_count, 0) ?? 0} trades over {daily?.data.length ?? 0} days
              </span>
            </div>
            <Sparkline data={pnlSparkline} color="#00d4ff" />
          </div>
        </Card>
      </div>

      {/* Secondary Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Recent Activity */}
        <Card title="Recent Activity">
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <Zap size={16} className="text-[--color-accent]" />
              <span>Last entry signal: <span className="text-[--color-accent] font-medium">{lastSignal}</span></span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Activity size={16} className="text-[--color-profit]" />
              <span>Last trade exit: <span className="text-[--color-profit] font-medium">{lastTrade}</span></span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Shield size={16} className="text-[--color-warning]" />
              <span>Current drawdown: <span className={profit && profit.current_drawdown < 0 ? "text-[--color-loss]" : "text-[--color-text-secondary]"}>
                {profit ? `${(profit.current_drawdown * 100).toFixed(2)}%` : "—"}
              </span></span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <TrendingUp size={16} className="text-[--color-text-secondary]" />
              <span>Expectancy ratio: <span className="text-[--color-text-secondary]">{profit ? `${profit.expectancy_ratio?.toFixed(3) ?? "—"}` : "—"}</span></span>
            </div>
          </div>
        </Card>

        {/* Top Pairs */}
        <Card title="Top Pairs by P&L">
          <div className="space-y-2">
            {perf.slice(0, 6).map((p) => (
              <div key={p.pair} className="flex items-center justify-between text-sm">
                <span className="font-medium">{p.pair}</span>
                <div className="flex items-center gap-3">
                  <span className="text-[--color-text-secondary] text-xs">{p.count} trades</span>
                  <span className={`font-semibold ${p.profit_pct >= 0 ? "text-[--color-profit]" : "text-[--color-loss]"}`}>
                    {p.profit_pct >= 0 ? "+" : ""}{p.profit_pct.toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
            {perf.length === 0 && (
              <p className="text-sm text-[--color-text-secondary]">No performance data yet</p>
            )}
          </div>
        </Card>

        {/* Quick Stats */}
        <Card title="Key Metrics">
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-[--color-text-secondary]">Profit Factor</span>
              <span className="font-semibold">{profitFactor ? profitFactor.toFixed(2) : "—"}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-[--color-text-secondary]">Sortino</span>
              <span className="font-semibold">{profit?.sortino ? profit.sortino.toFixed(2) : "—"}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-[--color-text-secondary]">Calmar</span>
              <span className="font-semibold">{profit?.calmar ? profit.calmar.toFixed(2) : "—"}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-[--color-text-secondary]">SQN</span>
              <span className="font-semibold">{profit?.sqn ? profit.sqn.toFixed(2) : "—"}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-[--color-text-secondary]">Avg Duration</span>
              <span className="font-semibold">{profit?.avg_duration ?? "—"}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-[--color-text-secondary]">CAGR</span>
              <span className="font-semibold">{profit?.cagr ? `${(profit.cagr * 100).toFixed(1)}%` : "—"}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
