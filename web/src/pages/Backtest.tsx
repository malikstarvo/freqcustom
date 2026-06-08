import { useEffect, useState, useCallback, useRef } from "react";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { api, type BacktestStatus, type BacktestHistoryEntry, type StrategyListResponse } from "@/lib/api";
import { BarChart3, Play, Trash2, RotateCcw, FileText, CheckCircle, XCircle, AlertCircle } from "lucide-react";

const TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"];

export default function Backtest() {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [form, setForm] = useState({
    strategy: "",
    timeframe: "15m",
    timerange: "20260101-20260501",
    max_open_trades: "3",
    stake_amount: "100",
    enable_protections: false,
    dry_run_wallet: 1000,
    freqaimodel: "XGBoostGridSearchModel",
  });
  const [status, setStatus] = useState<BacktestStatus | null>(null);
  const [history, setHistory] = useState<BacktestHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [selectedResult, setSelectedResult] = useState<BacktestStatus | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const s = await api.backtest();
      setStatus(s);
      if (s.running === false && s.status !== "not_started") {
        // Backtest finished or errored
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          setLoading(false);
        }
        if (s.status === "ended") {
          fetchHistory();
        }
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  const fetchHistory = async () => {
    try {
      const h = await api.backtestHistory();
      setHistory(h);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    api.strategies().then((r: StrategyListResponse) => setStrategies(r.strategies)).catch(console.error);
    fetchStatus();
    fetchHistory();
  }, []);

  useEffect(() => {
    return () => { if (pollIntervalRef.current) clearInterval(pollIntervalRef.current); };
  }, []);

  const startBacktest = async () => {
    setError(null);
    setLoading(true);
    setSelectedResult(null);
    try {
      await api.backtestStart({
        strategy: form.strategy,
        timeframe: form.timeframe,
        timerange: form.timerange,
        max_open_trades: form.max_open_trades,
        stake_amount: form.stake_amount,
        enable_protections: form.enable_protections,
        dry_run_wallet: form.dry_run_wallet,
        freqaimodel: form.freqaimodel,
      });
      const interval = setInterval(fetchStatus, 2000);
      pollIntervalRef.current = interval;
    } catch (e: any) {
      setError(e.message || "Failed to start backtest");
      setLoading(false);
    }
  };

  const resetBacktest = async () => {
    await api.backtestDelete();
    setStatus(null);
    setSelectedResult(null);
  };

  const deleteHistory = async (file: string) => {
    await api.backtestHistoryDelete(file);
    fetchHistory();
  };

  const loadHistoryResult = async (entry: BacktestHistoryEntry) => {
    try {
      const result = await api.backtestHistoryResult(entry.filename, entry.strategy);
      setSelectedResult(result);
    } catch (e) {
      console.error(e);
    }
  };

  const result = selectedResult || (status?.status === "ended" ? status : null);
  const resultData = result?.backtest_result as Record<string, unknown> | null;
  const strategyResult = resultData?.strategy as Record<string, unknown> | null;
  const summary = strategyResult?.[form.strategy || Object.keys(strategyResult || {})[0] || ""] as Record<string, unknown> | null;
  const stats = summary as Record<string, unknown> | null;

  const winrate = stats?.["winrate"] as number | undefined;
  const profitFactor = stats?.["profit_factor"] as number | undefined;
  const sharpe = stats?.["sharpe"] as number | undefined;
  const drawdown = stats?.["max_drawdown"] as number | undefined;
  const totalTrades = stats?.["total_trades"] as number | undefined;
  const returnPct = stats?.["profit_pct"] as number | undefined;
  const tradeList = (stats?.["trades"] as Array<Record<string, unknown>>) || [];

  const statusIcon = () => {
    if (status?.running) return <AlertCircle size={16} className="text-[--color-warning]" />;
    if (status?.status === "ended") return <CheckCircle size={16} className="text-[--color-profit]" />;
    if (status?.status === "error") return <XCircle size={16} className="text-[--color-loss]" />;
    return null;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <BarChart3 className="text-[--color-accent]" /> Backtest
        </h2>
        {status?.running && (
          <Badge label="Running" variant="warning" />
        )}
      </div>

      {/* Runner Form */}
      <Card title="Backtest Runner">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="space-y-1">
            <label className="text-xs text-[--color-text-secondary] uppercase">Strategy</label>
            <select
              className="w-full px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:border-[--color-accent]"
              value={form.strategy}
              onChange={(e) => setForm({ ...form, strategy: e.target.value })}
            >
              <option value="">Select strategy...</option>
              {strategies.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[--color-text-secondary] uppercase">Timeframe</label>
            <select
              className="w-full px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:border-[--color-accent]"
              value={form.timeframe}
              onChange={(e) => setForm({ ...form, timeframe: e.target.value })}
            >
              {TIMEFRAMES.map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[--color-text-secondary] uppercase">Timerange</label>
            <input
              type="text"
              value={form.timerange}
              onChange={(e) => setForm({ ...form, timerange: e.target.value })}
              className="w-full px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:border-[--color-accent]"
              placeholder="YYYYMMDD-YYYYMMDD"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[--color-text-secondary] uppercase">Max Trades</label>
            <input
              type="text"
              value={form.max_open_trades}
              onChange={(e) => setForm({ ...form, max_open_trades: e.target.value })}
              className="w-full px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:border-[--color-accent]"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[--color-text-secondary] uppercase">Stake Amount</label>
            <input
              type="text"
              value={form.stake_amount}
              onChange={(e) => setForm({ ...form, stake_amount: e.target.value })}
              className="w-full px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:border-[--color-accent]"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[--color-text-secondary] uppercase">Dry Wallet</label>
            <input
              type="number"
              value={form.dry_run_wallet}
              onChange={(e) => setForm({ ...form, dry_run_wallet: Number(e.target.value) })}
              className="w-full px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:border-[--color-accent]"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-[--color-text-secondary] uppercase">FreqAI Model</label>
            <input
              type="text"
              value={form.freqaimodel}
              onChange={(e) => setForm({ ...form, freqaimodel: e.target.value })}
              className="w-full px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:border-[--color-accent]"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="protections"
              type="checkbox"
              checked={form.enable_protections}
              onChange={(e) => setForm({ ...form, enable_protections: e.target.checked })}
              className="w-4 h-4 rounded border-[--color-card-border] bg-[--color-card-bg] text-[--color-accent]"
            />
            <label htmlFor="protections" className="text-sm text-[--color-text-secondary]">Enable protections</label>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={startBacktest}
            disabled={!form.strategy || loading}
            className="flex items-center gap-2 px-4 py-2 bg-[--color-accent] hover:bg-[--color-accent-hover] text-[#0f1119] rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play size={14} /> {loading ? "Running..." : "Run Backtest"}
          </button>
          <button
            onClick={resetBacktest}
            className="flex items-center gap-2 px-4 py-2 border border-[--color-card-border] hover:bg-[--color-card-border]/30 rounded-lg text-sm text-[--color-text-secondary]"
          >
            <RotateCcw size={14} /> Reset
          </button>
        </div>

        {error && (
          <div className="mt-3 p-3 bg-red-950/50 border border-red-500/30 rounded-lg text-sm text-red-400">
            {error}
          </div>
        )}

        {status?.running && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-[--color-text-secondary]">{status.status_msg}</span>
              <span className="text-[--color-accent]">{(status.progress * 100).toFixed(0)}%</span>
            </div>
            <Progress value={status.progress * 100} />
          </div>
        )}
      </Card>

      {/* Results */}
      {(result && resultData) && (
        <Card title="Results">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <StatCard label="Win Rate" value={winrate !== undefined ? `${(winrate * 100).toFixed(1)}%` : "—"} />
            <StatCard label="Profit Factor" value={profitFactor !== undefined ? profitFactor.toFixed(2) : "—"} />
            <StatCard label="Sharpe" value={sharpe !== undefined ? sharpe.toFixed(2) : "—"} />
            <StatCard label="Drawdown" value={drawdown !== undefined ? `${(drawdown * 100).toFixed(2)}%` : "—"} />
            <StatCard label="Trades" value={totalTrades ?? "—"} />
            <StatCard label="Return" value={returnPct !== undefined ? `${returnPct.toFixed(2)}%` : "—"}
              trend={returnPct !== undefined && returnPct >= 0 ? `+${returnPct.toFixed(2)}%` : returnPct !== undefined ? `${returnPct.toFixed(2)}%` : ""} />
          </div>

          <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-2">Trade Log</h4>
          <div className="overflow-auto max-h-[40vh] border border-[--color-card-border] rounded-lg">
            <table className="w-full text-xs">
              <thead className="bg-[--color-card-bg] sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-left text-[--color-text-secondary] font-medium">Pair</th>
                  <th className="px-3 py-2 text-left text-[--color-text-secondary] font-medium">Dir</th>
                  <th className="px-3 py-2 text-right text-[--color-text-secondary] font-medium">Entry</th>
                  <th className="px-3 py-2 text-right text-[--color-text-secondary] font-medium">Exit</th>
                  <th className="px-3 py-2 text-right text-[--color-text-secondary] font-medium">P&L%</th>
                  <th className="px-3 py-2 text-right text-[--color-text-secondary] font-medium">Bars</th>
                  <th className="px-3 py-2 text-left text-[--color-text-secondary] font-medium">Reason</th>
                </tr>
              </thead>
              <tbody>
                {tradeList.slice(0, 50).map((t, i) => (
                  <tr key={i} className="border-t border-[--color-card-border]/30">
                    <td className="px-3 py-1.5 font-medium">{t["pair"] as string}</td>
                    <td className="px-3 py-1.5">{(t["is_short"] as boolean) ? "Short" : "Long"}</td>
                    <td className="px-3 py-1.5 text-right">{(t["open_rate"] as number)?.toFixed(4)}</td>
                    <td className="px-3 py-1.5 text-right">{(t["close_rate"] as number)?.toFixed(4) ?? "—"}</td>
                    <td className={`px-3 py-1.5 text-right font-medium ${((t["profit_pct"] as number) ?? (t["profit_ratio"] as number) ?? 0) >= 0 ? "text-[--color-profit]" : "text-[--color-loss]"}`}>
                      {((t["profit_pct"] as number) ?? (t["profit_ratio"] as number) ?? 0).toFixed(2)}%
                    </td>
                    <td className="px-3 py-1.5 text-right">{t["trade_duration"] as number ?? t["duration"] as number ?? "—"}</td>
                    <td className="px-3 py-1.5 text-[--color-text-secondary]">{t["exit_reason"] as string ?? t["sell_reason"] as string ?? "—"}</td>
                  </tr>
                ))}
                {tradeList.length === 0 && (
                  <tr><td colSpan={7} className="px-3 py-4 text-center text-[--color-text-secondary]">No trades</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* History */}
      <Card title="Recent Backtests">
        {history.length === 0 ? (
          <p className="text-sm text-[--color-text-secondary]">No backtest history found.</p>
        ) : (
          <div className="space-y-2">
            {history.map((h) => (
              <div key={h.filename} className="flex items-center justify-between p-3 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg hover:border-[--color-accent]/50 transition-colors">
                <div className="flex items-center gap-3">
                  <FileText size={16} className="text-[--color-text-secondary]" />
                  <div>
                    <div className="text-sm font-medium">{h.filename}</div>
                    <div className="text-xs text-[--color-text-secondary]">{h.strategy} · {h.timeframe ?? "—"}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => loadHistoryResult(h)}
                    className="px-3 py-1 text-xs bg-[--color-accent]/10 hover:bg-[--color-accent]/20 text-[--color-accent] rounded"
                  >
                    View
                  </button>
                  <button
                    onClick={() => deleteHistory(h.filename)}
                    className="px-3 py-1 text-xs bg-red-500/10 hover:bg-red-500/20 text-[--color-loss] rounded"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
