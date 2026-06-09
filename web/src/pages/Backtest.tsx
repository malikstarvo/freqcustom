import { useEffect, useState, useCallback, useRef } from "react";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Empty } from "@/components/ui/empty";
import { cn } from "@/lib/utils";
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
    if (status?.running) return <AlertCircle className="size-4 text-warning" aria-hidden="true" />;
    if (status?.status === "ended") return <CheckCircle className="size-4 text-profit" aria-hidden="true" />;
    if (status?.status === "error") return <XCircle className="size-4 text-loss" aria-hidden="true" />;
    return null;
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <BarChart3 className="size-5 text-primary" aria-hidden="true" /> Backtest
        </h2>
        {status?.running && (
          <Badge label="Running" variant="warning" />
        )}
      </div>

      <Card title="Backtest Runner">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground uppercase">Strategy</label>
            <select
              className="w-full px-3 py-2 bg-muted/30 border border-border/50 rounded-lg text-sm focus:outline-none focus:border-primary"
              value={form.strategy}
              onChange={(e) => setForm({ ...form, strategy: e.target.value })}
            >
              <option value="">Select strategy\u2026</option>
              {strategies.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground uppercase">Timeframe</label>
            <select
              className="w-full px-3 py-2 bg-muted/30 border border-border/50 rounded-lg text-sm focus:outline-none focus:border-primary"
              value={form.timeframe}
              onChange={(e) => setForm({ ...form, timeframe: e.target.value })}
            >
              {TIMEFRAMES.map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground uppercase" htmlFor="timerange">Timerange</label>
            <Input
              id="timerange"
              type="text"
              value={form.timerange}
              onChange={(e) => setForm({ ...form, timerange: e.target.value })}
              className="w-full"
              placeholder="YYYYMMDD-YYYYMMDD"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground uppercase" htmlFor="max_open_trades">Max Trades</label>
            <Input
              id="max_open_trades"
              type="text"
              value={form.max_open_trades}
              onChange={(e) => setForm({ ...form, max_open_trades: e.target.value })}
              className="w-full"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground uppercase" htmlFor="stake_amount">Stake Amount</label>
            <Input
              id="stake_amount"
              type="text"
              value={form.stake_amount}
              onChange={(e) => setForm({ ...form, stake_amount: e.target.value })}
              className="w-full"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground uppercase" htmlFor="dry_run_wallet">Dry Wallet</label>
            <Input
              id="dry_run_wallet"
              type="number"
              value={form.dry_run_wallet}
              onChange={(e) => setForm({ ...form, dry_run_wallet: Number(e.target.value) })}
              className="w-full"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground uppercase" htmlFor="freqaimodel">FreqAI Model</label>
            <Input
              id="freqaimodel"
              type="text"
              value={form.freqaimodel}
              onChange={(e) => setForm({ ...form, freqaimodel: e.target.value })}
              className="w-full"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="protections"
              type="checkbox"
              checked={form.enable_protections}
              onChange={(e) => setForm({ ...form, enable_protections: e.target.checked })}
              className="size-4 rounded border-border/50 bg-muted/30 text-primary"
            />
            <label htmlFor="protections" className="text-sm text-muted-foreground">Enable protections</label>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-4">
          <Button
            onClick={startBacktest}
            disabled={!form.strategy || loading}
            variant="default"
          >
            <Play aria-hidden="true" /> {loading ? "Running\u2026" : "Run Backtest"}
          </Button>
          <Button
            onClick={resetBacktest}
            variant="outline"
          >
            <RotateCcw aria-hidden="true" /> Reset
          </Button>
        </div>

        {error && (
          <Alert variant="destructive" className="mt-3">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {status?.running && (
          <div className="mt-4 flex flex-col gap-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{status.status_msg}</span>
              <span className="text-primary font-mono">{(status.progress * 100).toFixed(0)}%</span>
            </div>
            <Progress value={status.progress * 100} />
          </div>
        )}
      </Card>

      {result && resultData && (
        <Card title="Results">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <StatCard label="Win Rate" value={winrate !== undefined ? `${(winrate * 100).toFixed(1)}%` : "\u2014"} />
            <StatCard label="Profit Factor" value={profitFactor !== undefined ? profitFactor.toFixed(2) : "\u2014"} />
            <StatCard label="Sharpe" value={sharpe !== undefined ? sharpe.toFixed(2) : "\u2014"} />
            <StatCard label="Drawdown" value={drawdown !== undefined ? `${(drawdown * 100).toFixed(2)}%` : "\u2014"} />
            <StatCard label="Trades" value={totalTrades ?? "\u2014"} />
            <StatCard label="Return" value={returnPct !== undefined ? `${returnPct.toFixed(2)}%` : "\u2014"}
              trend={returnPct !== undefined && returnPct >= 0 ? `+${returnPct.toFixed(2)}%` : returnPct !== undefined ? `${returnPct.toFixed(2)}%` : ""} />
          </div>

          <h4 className="text-sm font-semibold text-muted-foreground mb-2">Trade Log</h4>
          {tradeList.length === 0 ? (
            <Empty title="No Trades" />
          ) : (
            <div className="overflow-auto max-h-[40vh] border border-border/50 rounded-lg">
              <table className="w-full text-xs">
                <thead className="bg-muted/30 sticky top-0">
                  <tr>
                    <th className="px-3 py-2.5 text-left text-muted-foreground font-medium">Pair</th>
                    <th className="px-3 py-2.5 text-left text-muted-foreground font-medium">Dir</th>
                    <th className="px-3 py-2.5 text-right text-muted-foreground font-medium">Entry</th>
                    <th className="px-3 py-2.5 text-right text-muted-foreground font-medium">Exit</th>
                    <th className="px-3 py-2.5 text-right text-muted-foreground font-medium">P&amp;L%</th>
                    <th className="px-3 py-2.5 text-right text-muted-foreground font-medium">Bars</th>
                    <th className="px-3 py-2.5 text-left text-muted-foreground font-medium">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {tradeList.slice(0, 50).map((t, i) => (
                    <tr key={i} className="hover:bg-muted/30 motion-safe:transition-colors">
                      <td className="px-3 py-2.5 font-bold">{t["pair"] as string}</td>
                      <td className="px-3 py-2.5">{(t["is_short"] as boolean) ? "Short" : "Long"}</td>
                      <td className="px-3 py-2.5 text-right font-mono">{(t["open_rate"] as number)?.toFixed(4)}</td>
                      <td className="px-3 py-2.5 text-right font-mono">{(t["close_rate"] as number)?.toFixed(4) ?? "\u2014"}</td>
                      <td className={cn("px-3 py-2.5 text-right font-mono font-bold", ((t["profit_pct"] as number) ?? (t["profit_ratio"] as number) ?? 0) >= 0 ? "text-profit" : "text-loss")}>
                        {((t["profit_pct"] as number) ?? (t["profit_ratio"] as number) ?? 0).toFixed(2)}%
                      </td>
                      <td className="px-3 py-2.5 text-right font-mono">{t["trade_duration"] as number ?? t["duration"] as number ?? "\u2014"}</td>
                      <td className="px-3 py-2.5 text-muted-foreground">{t["exit_reason"] as string ?? t["sell_reason"] as string ?? "\u2014"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      <Card title="Recent Backtests">
        {history.length === 0 ? (
          <Empty title="No Backtest History" />
        ) : (
          <div className="flex flex-col gap-2">
            {history.map((h) => (
              <div key={h.filename} className="flex items-center justify-between p-3 bg-muted/30 border border-border/50 rounded-lg hover:bg-muted/50 motion-safe:transition-colors">
                <div className="flex items-center gap-3">
                  <FileText className="size-4 text-muted-foreground" aria-hidden="true" />
                  <div>
                    <div className="text-sm font-bold">{h.filename}</div>
                    <div className="text-xs text-muted-foreground">{h.strategy} \u00b7 {h.timeframe ?? "\u2014"}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => loadHistoryResult(h)}
                    variant="default"
                    size="sm"
                  >
                    View
                  </Button>
                  <Button
                    onClick={() => deleteHistory(h.filename)}
                    variant="destructive"
                    size="icon-sm"
                    aria-label="Delete"
                  >
                    <Trash2 aria-hidden="true" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
