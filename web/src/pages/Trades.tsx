import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Empty } from "@/components/ui/empty";
import { api, Trade } from "@/lib/api";
import { cn } from "@/lib/utils";
import { downloadCSV } from "@/lib/export";
import { useToast } from "@/hooks/useToast";
import { ArrowRightLeft, Download } from "lucide-react";

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  useEffect(() => {
    api.trades(200).then((r: { trades: Trade[] }) => setTrades(r.trades)).catch(console.error).finally(() => setLoading(false));
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
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <ArrowRightLeft className="size-5 text-primary" aria-hidden="true" /> Trade History
        </h2>
        <Button onClick={handleExport} variant="outline">
          <Download data-icon="inline-start" aria-hidden="true" /> Export CSV
        </Button>
      </div>
      <Card title={`All Trades (${trades.length})`}>
        {loading ? (
          <div className="flex items-center justify-center h-40 text-sm text-muted-foreground">Loading trades&hellip;</div>
        ) : (
          <div className="overflow-auto max-h-[70vh]">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="bg-muted/30 text-left text-muted-foreground">
                  <th className="py-2.5 px-3 font-medium">ID</th>
                  <th className="py-2.5 px-3 font-medium">Pair</th>
                  <th className="py-2.5 px-3 font-medium">Side</th>
                  <th className="py-2.5 px-3 font-medium">Amount</th>
                  <th className="py-2.5 px-3 font-medium">Entry</th>
                  <th className="py-2.5 px-3 font-medium">Exit</th>
                  <th className="py-2.5 px-3 font-medium">P&amp;L</th>
                  <th className="py-2.5 px-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {trades.map(t => (
                  <tr key={t.trade_id} className="hover:bg-muted/30 motion-safe:transition-colors">
                    <td className="py-2.5 px-3 font-mono">{t.trade_id}</td>
                    <td className="py-2.5 px-3 font-bold">{t.pair}</td>
                    <td className="py-2.5 px-3"><Badge label={t.is_short ? "SHORT" : "LONG"} variant={t.is_short ? "danger" : "success"} /></td>
                    <td className="py-2.5 px-3 font-mono">{t.amount.toFixed(4)}</td>
                    <td className="py-2.5 px-3 font-mono">{t.open_rate.toFixed(4)}</td>
                    <td className="py-2.5 px-3 font-mono">{t.close_rate?.toFixed(4) ?? "\u2014"}</td>
                    <td className={cn("py-2.5 px-3 font-mono font-bold", (t.profit_pct ?? 0) >= 0 ? "text-profit" : "text-loss")}>{(t.profit_pct ?? 0).toFixed(2)}%</td>
                    <td className="py-2.5 px-3"><Badge label={t.is_open ? "OPEN" : "CLOSED"} variant={t.is_open ? "warning" : "default"} /></td>
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
