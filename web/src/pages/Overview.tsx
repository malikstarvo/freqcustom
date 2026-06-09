import { useEffect, useState } from "react";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { api, type Profit, type Trade, type PaperStatus } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useToast } from "@/hooks/useToast";
import {
  LayoutDashboard, TrendingUp, Activity, Zap, Shield, Clock, Brain, DollarSign,
  ArrowUpRight, ArrowDownRight, BarChart3, Server, AlertCircle
} from "lucide-react";

export default function Overview() {
  const [profit, setProfit] = useState<Profit | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [paper, setPaper] = useState<PaperStatus | null>(null);
  const [botState, setBotState] = useState<string>("unknown");
  const [lastMessage, setLastMessage] = useState<string>("");
  const { lastMessage: wsMsg, subscribe } = useWebSocket();
  const { addToast } = useToast();

  useEffect(() => {
    api.profit().then(setProfit).catch(console.error);
        api.trades(20).then((r2: { trades: Trade[] }) => setTrades(r2.trades)).catch(console.error);
    api.paperStatus().then(setPaper).catch(() => {});
    api.showConfig().then((c: { state: string }) => setBotState(c.state)).catch(console.error);
    subscribe(["ENTRY", "EXIT", "STATUS"]);
  }, [subscribe]);

  useEffect(() => {
    if (wsMsg) {
      if (wsMsg.type === "ENTRY" || wsMsg.type === "EXIT") {
        setLastMessage(`${wsMsg.type} at ${new Date().toLocaleTimeString()}`);
        addToast(wsMsg.type === "ENTRY" ? "warning" : "info", `${wsMsg.type} Signal`, `New ${wsMsg.type.toLowerCase()} signal detected`);
        api.profit().then(setProfit).catch(console.error);
    api.trades(20).then((r: { trades: Trade[] }) => setTrades(r.trades)).catch(console.error);
      }
    }
  }, [wsMsg, addToast]);

  const openTrades = trades.filter(t => t.is_open);
  const closedTrades = trades.filter(t => !t.is_open).slice(0, 5);
  const totalPnl = profit?.profit_all_percent ?? 0;
  const winrate = profit?.winrate ?? 0;

  const pnlColor = totalPnl >= 0 ? "text-profit" : "text-loss";
  const pnlIcon = totalPnl >= 0 ? <TrendingUp size={20} /> : <ArrowDownRight size={20} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <LayoutDashboard className="text-accent" />
            Overview
          </h2>
          <p className="text-sm text-text-secondary mt-1">Command center — all systems at a glance</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge label={botState} variant={botState === "running" ? "success" : "default"} />
          {lastMessage && (
            <span className="text-xs text-accent animate-pulse">{lastMessage}</span>
          )}
        </div>
      </div>

      {/* Hero KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card-bg border border-card-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-text-secondary uppercase">Total P&L</span>
            <span className={pnlColor}>{pnlIcon}</span>
          </div>
          <div className={`text-3xl font-bold ${pnlColor}`}>
            {totalPnl >= 0 ? "+" : ""}{totalPnl.toFixed(2)}%
          </div>
          <div className="text-xs text-text-secondary mt-1">
            {profit?.profit_all_coin.toFixed(4) ?? "—"} {profit?.profit_all_fiat ? `(${profit.profit_all_fiat.toFixed(2)} USD)` : ""}
          </div>
        </div>

        <div className="bg-card-bg border border-card-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-text-secondary uppercase">Win Rate</span>
            <Activity size={20} className="text-accent" />
          </div>
          <div className="text-3xl font-bold text-text-primary">
            {(winrate * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-text-secondary mt-1">
            {profit?.winning_trades ?? 0}W / {profit?.losing_trades ?? 0}L
          </div>
        </div>

        <div className="bg-card-bg border border-card-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-text-secondary uppercase">Max Drawdown</span>
            <Shield size={20} className="text-warning" />
          </div>
          <div className="text-3xl font-bold text-loss">
            {profit ? `${(profit.max_drawdown * 100).toFixed(2)}%` : "—"}
          </div>
          <div className="text-xs text-text-secondary mt-1">
            Current: {profit ? `${(profit.current_drawdown * 100).toFixed(2)}%` : "—"}
          </div>
        </div>

        <div className="bg-card-bg border border-card-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-text-secondary uppercase">Sharpe Ratio</span>
            <BarChart3 size={20} className="text-accent" />
          </div>
          <div className="text-3xl font-bold text-text-primary">
            {profit?.sharpe ? profit.sharpe.toFixed(2) : "—"}
          </div>
          <div className="text-xs text-text-secondary mt-1">
            PF: {profit?.profit_factor ? profit.profit_factor.toFixed(2) : "—"}
          </div>
        </div>
      </div>

      {/* Secondary Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Open Positions */}
        <Card title={`Open Positions (${openTrades.length})`}>
          {openTrades.length === 0 ? (
            <p className="text-sm text-text-secondary">No open positions</p>
          ) : (
            <div className="space-y-2">
              {openTrades.slice(0, 5).map(t => (
                <div key={t.trade_id} className="flex items-center justify-between p-2 bg-card-bg rounded border border-card-border/30">
                  <div className="flex items-center gap-2">
                    {t.is_short ? <ArrowDownRight size={14} className="text-loss" /> : <ArrowUpRight size={14} className="text-profit" />}
                    <span className="text-sm font-medium">{t.pair}</span>
                    <span className="text-xs text-text-secondary">@ {t.open_rate.toFixed(2)}</span>
                  </div>
                  <Badge label={t.is_short ? "SHORT" : "LONG"} variant={t.is_short ? "danger" : "success"} />
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent Closed Trades */}
        <Card title="Recent Exits">
          {closedTrades.length === 0 ? (
            <p className="text-sm text-text-secondary">No closed trades</p>
          ) : (
            <div className="space-y-2">
              {closedTrades.map(t => (
                <div key={t.trade_id} className="flex items-center justify-between p-2 bg-card-bg rounded border border-card-border/30">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{t.pair}</span>
                    <span className={`text-xs font-semibold ${(t.profit_pct ?? 0) >= 0 ? "text-profit" : "text-loss"}`}>
                      {(t.profit_pct ?? 0) >= 0 ? "+" : ""}{(t.profit_pct ?? 0).toFixed(2)}%
                    </span>
                  </div>
                  <span className="text-xs text-text-secondary">{t.exit_reason ?? "—"}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Paper + Bot Status */}
        <Card title="System Status">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Bot State</span>
              </div>
              <Badge label={botState} variant={botState === "running" ? "success" : "default"} />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Paper Equity</span>
              </div>
              <span className="text-sm font-medium">{paper ? `${paper.equity.toFixed(2)}` : "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DollarSign size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Paper P&L</span>
              </div>
              <span className={`text-sm font-medium ${paper && paper.total_pnl >= 0 ? "text-profit" : "text-loss"}`}>
                {paper ? `${paper.total_pnl >= 0 ? "+" : ""}${paper.total_pnl.toFixed(2)}` : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Paper Trades</span>
              </div>
              <span className="text-sm font-medium">{paper ? paper.day_trades : "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Active Strategy</span>
              </div>
              <span className="text-sm font-medium">{profit ? `${profit.trade_count} trades` : "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle size={14} className="text-warning" />
                <span className="text-sm text-text-secondary">Latest Signal</span>
              </div>
              <span className="text-xs text-accent">{lastMessage || "—"}</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Bottom Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Trades" value={profit?.trade_count ?? "—"} subtitle={`Closed: ${profit?.closed_trade_count ?? 0}`} />
        <StatCard label="Best Pair" value={profit?.best_pair ?? "—"} subtitle={profit ? `${profit.best_rate.toFixed(2)}%` : ""} />
        <StatCard label="Expectancy" value={profit?.expectancy ? profit.expectancy.toFixed(2) : "—"} />
        <StatCard label="SQN" value={profit?.sqn ? profit.sqn.toFixed(2) : "—"} />
        <StatCard label="Sortino" value={profit?.sortino ? profit.sortino.toFixed(2) : "—"} />
        <StatCard label="Calmar" value={profit?.calmar ? profit.calmar.toFixed(2) : "—"} />
        <StatCard label="CAGR" value={profit?.cagr ? `${(profit.cagr * 100).toFixed(1)}%` : "—"} />
        <StatCard label="Avg Duration" value={profit?.avg_duration ?? "—"} />
      </div>
    </div>
  );
}
