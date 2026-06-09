import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
import { api, Trade } from "@/lib/api";
import { downloadCSV } from "@/lib/export";
import { useToast } from "@/hooks/useToast";
import { ArrowRightLeft, Download } from "lucide-react";

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const { addToast } = useToast();

  useEffect(() => {
    api.trades(200).then((r: { trades: Trade[] }) => setTrades(r.trades)).catch(console.error);
  }, []);

  const handleExport = () => {
    const headers = ["ID", "Pair", "Side", "Amount", "Entry", "Exit", "Profit%", "Status", "Open Date", "Close Date", "Exit Reason"];
    const rows = trades.map(t => [
      t.trade_id,
      t.pair,
      t.is_short ? "SHORT" : "LONG",
      t.amount.toFixed(4),
      t.open_rate.toFixed(4),
      t.close_rate?.toFixed(4) ?? "",
      (t.profit_pct ?? 0).toFixed(2),
      t.is_open ? "OPEN" : "CLOSED",
      t.open_date,
      t.close_date ?? "",
      t.exit_reason ?? "",
    ]);
    downloadCSV("trades.csv", headers, rows);
    addToast("success", "Export complete", `${trades.length} trades exported to CSV`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <ArrowRightLeft className="text-accent" /> Trade History
        </h2>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-3 py-1.5 bg-card-bg border border-card-border hover:border-accent rounded-lg text-xs text-text-secondary transition-colors"
        >
          <Download size={14} /> Export CSV
        </button>
      </div>
      <Card title={`All Trades (${trades.length})`}>
        <div className="overflow-auto max-h-[70vh]">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-text-secondary border-b border-card-border">
                <th className="pb-2 pr-4">ID</th><th className="pb-2 pr-4">Pair</th>
                <th className="pb-2 pr-4">Side</th><th className="pb-2 pr-4">Amount</th>
                <th className="pb-2 pr-4">Entry</th><th className="pb-2 pr-4">Exit</th>
                <th className="pb-2 pr-4">P&L</th><th className="pb-2 pr-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {trades.map(t => (
                <tr key={t.trade_id} className="border-b border-card-border/50 hover:bg-gray-800/50">
                  <td className="py-2 pr-4">{t.trade_id}</td>
                  <td className="py-2 pr-4 font-medium">{t.pair}</td>
                  <td className="py-2 pr-4"><Badge label={t.is_short ? "SHORT" : "LONG"} variant={t.is_short ? "danger" : "success"} /></td>
                  <td className="py-2 pr-4">{t.amount.toFixed(4)}</td>
                  <td className="py-2 pr-4">{t.open_rate.toFixed(4)}</td>
                  <td className="py-2 pr-4">{t.close_rate?.toFixed(4) ?? "—"}</td>
                  <td className={`py-2 pr-4 ${(t.profit_pct ?? 0) >= 0 ? "text-profit" : "text-loss"}`}>{(t.profit_pct ?? 0).toFixed(2)}%</td>
                  <td className="py-2"><Badge label={t.is_open ? "OPEN" : "CLOSED"} variant={t.is_open ? "warning" : "default"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
