import { useEffect, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Empty } from "@/components/ui/empty";
import { api, PaperStatus, PaperTrade } from "@/lib/api";
import { downloadCSV } from "@/lib/export";
import { useToast } from "@/hooks/useToast";
import { DollarSign, TrendingUp, TrendingDown, Clock, BarChart3, Download, Wallet, PiggyBank, CalendarDays, Percent } from "lucide-react";

export default function Paper() {
  const [status, setStatus] = useState<PaperStatus | null>(null);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [topupAmount, setTopupAmount] = useState<string>("");
  const [topupMsg, setTopupMsg] = useState<string>("");
  const [topupHistory, setTopupHistory] = useState<Array<{
    ts: string; amount: number; balance_before: number; balance_after: number;
  }>>([]);
  const { addToast } = useToast();

  const refresh = useCallback(() => {
    api.paperStatus().then(setStatus).catch(() => {});
    api.paperTrades(50).then(setTrades).catch(() => {});
    api.paperAccount(100).then((snaps: Array<{ ts: string; balance: number; equity: number; unrealized_pnl: number; day_pnl: number; day_trades: number }>) => {
      const tops: typeof topupHistory = [];
      let prev = 0;
      for (const s of snaps) {
        if (s.balance > prev + 50) {
          tops.push({
            ts: s.ts,
            amount: s.balance - prev,
            balance_before: prev,
            balance_after: s.balance,
          });
        }
        prev = s.balance;
      }
      setTopupHistory(tops.slice(-10).reverse());
    }).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 10_000);
    return () => clearInterval(timer);
  }, [refresh]);

  const handleTopUp = async () => {
    const amount = parseFloat(topupAmount);
    if (!amount || amount <= 0) return;
    try {
      const res = await api.paperTopUp(amount);
      setTopupMsg(`Top-up successful: $${res.old_balance.toFixed(0)} → $${res.new_balance.toFixed(0)} (+$${res.amount})`);
      addToast("success", "Top-up successful", `$${res.amount} added to paper balance`);
      setTopupAmount("");
      setTimeout(refresh, 500);
    } catch {
      setTopupMsg("Top-up failed. Is the paper trader running?");
      addToast("error", "Top-up failed", "Is the paper trader running?");
    }
  };

  const handleExport = () => {
    const headers = ["ID", "Symbol", "Direction", "Entry", "Exit", "Size", "P&L", "Return%", "Bars", "Reason", "Entry Time", "Exit Time"];
    const rows = trades.map((t, i) => [
      i + 1,
      t.symbol,
      t.direction,
      t.entry_price.toFixed(2),
      t.exit_price.toFixed(2),
      t.size.toFixed(4),
      t.net_pnl.toFixed(2),
      (t.return_pct * 100).toFixed(2),
      t.holding_bars,
      t.exit_reason,
      t.entry_ts,
      t.exit_ts,
    ]);
    downloadCSV("paper_trades.csv", headers, rows);
    addToast("success", "Export complete", `${trades.length} paper trades exported to CSV`);
  };

  const pos = status?.position;
  const maxBars = 24;
  const barPct = pos ? Math.min((pos.bars_held / maxBars) * 100, 100) : 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2.5">
            <DollarSign className="size-5 text-primary" aria-hidden="true" />
            Paper Trading
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            {status ? `${status.state} · ${status.bar_count} bars · ${Math.floor(status.uptime_sec / 60)}m uptime` : "Loading…"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download aria-hidden="true" /> Export CSV
          </Button>
          {topupMsg && (
            <span className="text-xs text-profit bg-profit/10 px-3 py-1 rounded-md">
              {topupMsg}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
        <StatCard label="Equity" value={status ? `$${status.equity.toFixed(0)}` : "—"} icon={<Wallet className="size-4 text-muted-foreground" />} />
        <StatCard label="Balance" value={status ? `$${status.balance.toFixed(0)}` : "—"} icon={<PiggyBank className="size-4 text-muted-foreground" />} />
        <StatCard
          label="Day P&L"
          value={status ? `$${status.day_pnl.toFixed(2)}` : "—"}
          trend={status ? `${((status.day_pnl / (status.balance - status.day_pnl)) * 100).toFixed(2)}%` : ""}
          icon={<CalendarDays className="size-4 text-muted-foreground" />}
        />
        <StatCard label="Total P&L" value={status ? `$${status.total_pnl.toFixed(2)}` : "—"} icon={<TrendingUp className="size-4 text-muted-foreground" />} />
        <StatCard label="Day Trades" value={status?.day_trades ?? "—"} icon={<BarChart3 className="size-4 text-muted-foreground" />} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Open Position">
          {pos ? (
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {pos.direction === "long" ? (
                    <TrendingUp className="size-5 text-profit" aria-hidden="true" />
                  ) : (
                    <TrendingDown className="size-5 text-loss" aria-hidden="true" />
                  )}
                  <span className="font-bold text-lg">{pos.symbol}</span>
                  <Badge label={pos.direction.toUpperCase()} variant={pos.direction === "long" ? "success" : "danger"} />
                </div>
                <span className="text-sm text-muted-foreground">
                  Entry: ${pos.entry_price.toFixed(2)} &middot; Size: {pos.quantity.toFixed(4)}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Stop Price</span>
                  <p className="font-mono">${pos.stop_price.toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Entry Fee</span>
                  <p className="font-mono">${pos.entry_fee.toFixed(4)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Opened</span>
                  <p className="font-mono text-xs">{new Date(pos.open_ts).toLocaleString()}</p>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground flex items-center gap-1">
                    <Clock className="size-3" aria-hidden="true" /> Held: {pos.bars_held} bars
                  </span>
                  <span className="text-muted-foreground">Max: {maxBars}</span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${barPct}%`,
                      background: barPct > 75 ? "var(--color-loss)" : barPct > 50 ? "var(--color-warning)" : "var(--color-profit)",
                    }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <Empty icon={TrendingUp} title="No open position" />
          )}
        </Card>

        <Card title="Top-Up Balance">
          <div className="flex flex-col gap-3">
            <p className="text-xs text-muted-foreground">
              Add simulated capital. Drawdown baseline adjusts proportionally.
            </p>
            <div className="flex gap-2">
              <Input
                type="number"
                min="1"
                step="100"
                value={topupAmount}
                onChange={(e) => setTopupAmount(e.target.value)}
                placeholder="Amount in USD"
                className="flex-1"
                onKeyDown={(e) => e.key === "Enter" && handleTopUp()}
              />
              <Button onClick={handleTopUp}>
                Top Up
              </Button>
            </div>
            {topupHistory.length > 0 && (
              <div className="mt-3">
                <span className="text-xs text-muted-foreground">Recent top-ups:</span>
                <div className="mt-1 flex flex-col gap-1">
                  {topupHistory.slice(0, 5).map((t, i) => (
                    <div key={i} className="flex justify-between text-xs bg-muted/30 rounded-md px-2 py-1">
                      <span className="text-muted-foreground">
                        {new Date(t.ts).toLocaleDateString()}
                      </span>
                      <span className="text-profit font-mono">+${t.amount.toFixed(0)}</span>
                      <span className="text-muted-foreground font-mono">
                        ${t.balance_before.toFixed(0)} &rarr; ${t.balance_after.toFixed(0)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card title="Trade History">
        {trades.length === 0 ? (
          <Empty icon={BarChart3} title="No trades yet" />
        ) : (
          <div className="overflow-auto max-h-80">
            <table className="w-full text-sm min-w-[720px]">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border/50">
                  <th className="pb-2 pr-4 pl-3">Symbol</th>
                  <th className="pb-2 pr-4">Direction</th>
                  <th className="pb-2 pr-4">Entry</th>
                  <th className="pb-2 pr-4">Exit</th>
                  <th className="pb-2 pr-4">Size</th>
                  <th className="pb-2 pr-4">P&amp;L</th>
                  <th className="pb-2 pr-4">Return</th>
                  <th className="pb-2 pr-4">Bars</th>
                  <th className="pb-2 pr-3">Reason</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t: PaperTrade, i: number) => (
                  <tr key={i} className="hover:bg-muted/30 motion-safe:transition-colors">
                    <td className="py-2.5 pl-3 pr-4 rounded-l-lg font-medium">{t.symbol}</td>
                    <td className="py-2.5 pr-4">
                      <Badge label={t.direction.toUpperCase()} variant={t.direction === "long" ? "success" : "danger"} />
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-xs">${t.entry_price.toFixed(2)}</td>
                    <td className="py-2.5 pr-4 font-mono text-xs">${t.exit_price.toFixed(2)}</td>
                    <td className="py-2.5 pr-4 font-mono">{t.size.toFixed(4)}</td>
                    <td className={cn("py-2.5 pr-4 font-mono", t.net_pnl >= 0 ? "text-profit" : "text-loss")}>
                      ${t.net_pnl.toFixed(2)}
                    </td>
                    <td className={cn("py-2.5 pr-4 font-mono", t.return_pct >= 0 ? "text-profit" : "text-loss")}>
                      {(t.return_pct * 100).toFixed(2)}%
                    </td>
                    <td className="py-2.5 pr-4 text-muted-foreground">{t.holding_bars}</td>
                    <td className="py-2.5 pr-3 rounded-r-lg">
                      <Badge label={t.exit_reason} variant={
                        t.exit_reason === "stop_loss" ? "danger" :
                        t.exit_reason === "max_hold" ? "warning" : "default"
                      } />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
