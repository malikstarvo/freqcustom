import { useEffect, useState } from "react";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { Empty } from "@/components/ui/empty";
import { api, type Profit, type Trade, type PaperStatus } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useToast } from "@/hooks/useToast";
import {
  LayoutDashboard, TrendingUp, Activity, Zap, Shield, Clock, Brain, DollarSign,
  ArrowUpRight, ArrowDownRight, ArrowRightLeft, BarChart3, Server, AlertCircle
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
  const pnlTrend = totalPnl >= 0 ? `+${totalPnl.toFixed(2)}%` : `${totalPnl.toFixed(2)}%`;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2.5">
            <LayoutDashboard className="text-primary size-5" aria-hidden="true" />
            Overview
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">Command center — all systems at a glance</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge label={botState} variant={botState === "running" ? "success" : "default"} />
          {lastMessage && (
            <span className="text-xs text-primary motion-safe:animate-pulse" aria-live="polite">{lastMessage}</span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total P&L"
          value={`${totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}%`}
          subtitle={`${profit?.profit_all_coin.toFixed(4) ?? "—"} ${profit?.profit_all_fiat ? `(${profit.profit_all_fiat.toFixed(2)} USD)` : ""}`}
          trend={profit ? pnlTrend : undefined}
          icon={totalPnl >= 0 ? <TrendingUp size={18} className="text-profit" aria-hidden="true" /> : <ArrowDownRight size={18} className="text-loss" aria-hidden="true" />}
        />
        <StatCard
          label="Win Rate"
          value={profit ? `${(winrate * 100).toFixed(1)}%` : "—"}
          subtitle={profit ? `${profit.winning_trades ?? 0}W / ${profit.losing_trades ?? 0}L` : ""}
          icon={<Activity size={18} className="text-primary" aria-hidden="true" />}
        />
        <StatCard
          label="Max Drawdown"
          value={profit ? `${(profit.max_drawdown * 100).toFixed(2)}%` : "—"}
          subtitle={profit ? `Current: ${(profit.current_drawdown * 100).toFixed(2)}%` : ""}
          icon={<Shield size={18} className="text-warning" aria-hidden="true" />}
        />
        <StatCard
          label="Sharpe Ratio"
          value={profit?.sharpe ? profit.sharpe.toFixed(2) : "—"}
          subtitle={profit?.profit_factor ? `PF: ${profit.profit_factor.toFixed(2)}` : ""}
          icon={<BarChart3 size={18} className="text-primary" aria-hidden="true" />}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <Card title={`Open Positions (${openTrades.length})`}>
          {openTrades.length === 0 ? (
            <Empty icon={TrendingUp} title="No Open Positions" />
          ) : (
            <div className="flex flex-col gap-1.5">
              {openTrades.slice(0, 5).map(t => (
                <div key={t.trade_id} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-muted/30 transition-colors">
                  <div className="flex items-center gap-2.5 min-w-0">
                    {t.is_short
                      ? <ArrowDownRight size={15} className="text-loss shrink-0" aria-hidden="true" />
                      : <ArrowUpRight size={15} className="text-profit shrink-0" aria-hidden="true" />}
                    <span className="text-sm font-medium truncate">{t.pair}</span>
                    <span className="text-xs text-muted-foreground shrink-0">@ {t.open_rate.toFixed(2)}</span>
                  </div>
                  <Badge label={t.is_short ? "SHORT" : "LONG"} variant={t.is_short ? "danger" : "success"} />
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Recent Exits">
          {closedTrades.length === 0 ? (
            <Empty icon={ArrowRightLeft} title="No Closed Trades" />
          ) : (
            <div className="flex flex-col gap-1.5">
              {closedTrades.map(t => (
                <div key={t.trade_id} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-muted/30 transition-colors">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="text-sm font-medium truncate">{t.pair}</span>
                    <span className={cn("text-xs font-semibold shrink-0", (t.profit_pct ?? 0) >= 0 ? "text-profit" : "text-loss")}>
                      {(t.profit_pct ?? 0) >= 0 ? "+" : ""}{(t.profit_pct ?? 0).toFixed(2)}%
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0 ml-2">{t.exit_reason ?? "—"}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="System Status">
          <div className="flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server size={14} className="text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Bot State</span>
              </div>
              <Badge label={botState} variant={botState === "running" ? "success" : "default"} />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap size={14} className="text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Paper Equity</span>
              </div>
              <span className="text-sm font-mono font-medium">{paper ? `$${paper.equity.toFixed(2)}` : "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DollarSign size={14} className="text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Paper P&L</span>
              </div>
              <span className={cn("text-sm font-mono font-medium", paper && paper.total_pnl >= 0 ? "text-profit" : "text-loss")}>
                {paper ? `${paper.total_pnl >= 0 ? "+" : ""}$${paper.total_pnl.toFixed(2)}` : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock size={14} className="text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Paper Trades</span>
              </div>
              <span className="text-sm font-mono font-medium">{paper ? paper.day_trades : "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain size={14} className="text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Active Strategy</span>
              </div>
              <span className="text-sm font-mono font-medium">{profit ? `${profit.trade_count} trades` : "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle size={14} className="text-warning" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Latest Signal</span>
              </div>
              <span className="text-xs text-primary font-medium truncate max-w-[140px]">{lastMessage || "—"}</span>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
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
