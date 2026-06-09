import { useEffect, useState, useCallback } from "react";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { api, PaperStatus, PaperTrade } from "@/lib/api";
import { downloadCSV } from "@/lib/export";
import { useToast } from "@/hooks/useToast";
import { DollarSign, TrendingUp, TrendingDown, Clock, BarChart3, Download } from "lucide-react";

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
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <DollarSign className="text-accent" />
            Paper Trading
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            {status ? `${status.state} · ${status.bar_count} bars · ${Math.floor(status.uptime_sec / 60)}m uptime` : "Loading..."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-3 py-1.5 bg-card-bg border border-card-border hover:border-accent rounded-lg text-xs text-text-secondary transition-colors"
          >
            <Download size={14} /> Export CSV
          </button>
          {topupMsg && (
            <span className="text-xs text-profit bg-profit/10 px-3 py-1 rounded-full">
              {topupMsg}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4">
        <StatCard label="Equity" value={status ? `$${status.equity.toFixed(0)}` : "—"} />
        <StatCard label="Balance" value={status ? `$${status.balance.toFixed(0)}` : "—"} />
        <StatCard
          label="Day P&L"
          value={status ? `$${status.day_pnl.toFixed(2)}` : "—"}
          trend={status ? `${((status.day_pnl / (status.balance - status.day_pnl)) * 100).toFixed(2)}%` : ""}
        />
        <StatCard label="Total P&L" value={status ? `$${status.total_pnl.toFixed(2)}` : "—"} />
        <StatCard label="Day Trades" value={status?.day_trades ?? "—"} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card title="Open Position">
          {pos ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {pos.direction === "long" ? (
                    <TrendingUp size={20} className="text-profit" />
                  ) : (
                    <TrendingDown size={20} className="text-loss" />
                  )}
                  <span className="font-bold text-lg">{pos.symbol}</span>
                  <Badge label={pos.direction.toUpperCase()} variant={pos.direction === "long" ? "success" : "danger"} />
                </div>
                <span className="text-sm text-text-secondary">
                  Entry: ${pos.entry_price.toFixed(2)} &middot; Size: {pos.quantity.toFixed(4)}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>
                  <span className="text-text-secondary">Stop Price</span>
                  <p className="font-mono">${pos.stop_price.toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Entry Fee</span>
                  <p className="font-mono">${pos.entry_fee.toFixed(4)}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Opened</span>
                  <p className="font-mono text-xs">{new Date(pos.open_ts).toLocaleString()}</p>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-text-secondary flex items-center gap-1">
                    <Clock size={12} /> Held: {pos.bars_held} bars
                  </span>
                  <span className="text-text-secondary">Max: {maxBars}</span>
                </div>
                <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
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
            <p className="text-sm text-text-secondary py-4 text-center">No open position</p>
          )}
        </Card>

        <Card title="Top-Up Balance">
          <div className="space-y-3">
            <p className="text-xs text-text-secondary">
              Add simulated capital. Drawdown baseline adjusts proportionally.
            </p>
            <div className="flex gap-2">
              <input
                type="number"
                min="1"
                step="100"
                value={topupAmount}
                onChange={(e) => setTopupAmount(e.target.value)}
                placeholder="Amount in USD"
                className="flex-1 bg-gray-800 border border-card-border rounded px-3 py-2 text-sm text-white placeholder-gray-500 outline-none focus:border-accent"
                onKeyDown={(e) => e.key === "Enter" && handleTopUp()}
              />
              <button
                onClick={handleTopUp}
                className="px-4 py-2 bg-accent text-black font-medium text-sm rounded hover:bg-accent-hover transition-colors"
              >
                Top Up
              </button>
            </div>
            {topupHistory.length > 0 && (
              <div className="mt-3">
                <span className="text-xs text-text-secondary">Recent top-ups:</span>
                <div className="mt-1 space-y-1">
                  {topupHistory.slice(0, 5).map((t, i) => (
                    <div key={i} className="flex justify-between text-xs bg-gray-800/50 rounded px-2 py-1">
                      <span className="text-text-secondary">
                        {new Date(t.ts).toLocaleDateString()}
                      </span>
                      <span className="text-profit">+${t.amount.toFixed(0)}</span>
                      <span className="text-text-secondary">
                        ${t.balance_before.toFixed(0)} → ${t.balance_after.toFixed(0)}
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
          <p className="text-sm text-text-secondary py-4 text-center">No trades yet</p>
        ) : (
          <div className="overflow-auto max-h-80">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-secondary border-b border-card-border">
                  <th className="pb-2 pr-4">Symbol</th>
                  <th className="pb-2 pr-4">Direction</th>
                  <th className="pb-2 pr-4">Entry</th>
                  <th className="pb-2 pr-4">Exit</th>
                  <th className="pb-2 pr-4">Size</th>
                  <th className="pb-2 pr-4">P&L</th>
                  <th className="pb-2 pr-4">Return</th>
                  <th className="pb-2 pr-4">Bars</th>
                  <th className="pb-2">Reason</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t: PaperTrade, i: number) => (
                  <tr key={i} className="border-b border-card-border/30 hover:bg-gray-800/50">
                    <td className="py-2 pr-4 font-medium">{t.symbol}</td>
                    <td className="py-2 pr-4">
                      <Badge label={t.direction.toUpperCase()} variant={t.direction === "long" ? "success" : "danger"} />
                    </td>
                    <td className="py-2 pr-4 font-mono text-xs">${t.entry_price.toFixed(2)}</td>
                    <td className="py-2 pr-4 font-mono text-xs">${t.exit_price.toFixed(2)}</td>
                    <td className="py-2 pr-4">{t.size.toFixed(4)}</td>
                    <td className={`py-2 pr-4 ${t.net_pnl >= 0 ? "text-profit" : "text-loss"}`}>
                      ${t.net_pnl.toFixed(2)}
                    </td>
                    <td className={`py-2 pr-4 ${t.return_pct >= 0 ? "text-profit" : "text-loss"}`}>
                      {(t.return_pct * 100).toFixed(2)}%
                    </td>
                    <td className="py-2 pr-4 text-text-secondary">{t.holding_bars}</td>
                    <td className="py-2">
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
