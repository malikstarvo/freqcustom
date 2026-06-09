import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Empty } from "@/components/ui/empty";
import { cn } from "@/lib/utils";
import { api, Trade } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useToast } from "@/hooks/useToast";
import { ArrowUpRight, ArrowDownRight, TrendingUp, Clock, Zap, XCircle } from "lucide-react";

export default function Trading() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const { lastMessage, subscribe } = useWebSocket();
  const { addToast } = useToast();
  const [forcePair, setForcePair] = useState("");
  const [forcePrice, setForcePrice] = useState("");
  const [forceExitId, setForceExitId] = useState("");
  const [acting, setActing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.trades(100).then((r: { trades: Trade[] }) => setTrades(r.trades)).catch(console.error).finally(() => setLoading(false));
    subscribe(["ENTRY", "ENTRY_FILL", "EXIT", "EXIT_FILL", "STATUS"]);
  }, [subscribe]);

  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === "ENTRY_FILL") {
        addToast("success", "Entry Fill", "New position opened");
        api.trades(100).then((r: { trades: Trade[] }) => setTrades(r.trades)).catch(console.error);
      } else if (lastMessage.type === "EXIT_FILL") {
        addToast("info", "Exit Fill", "Position closed");
        api.trades(100).then((r: { trades: Trade[] }) => setTrades(r.trades)).catch(console.error);
      } else if (lastMessage.type === "ENTRY") {
        addToast("warning", "Entry Signal", "New entry signal detected");
      }
    }
  }, [lastMessage, addToast]);

  const openTrades = trades.filter(t => t.is_open);
  const closedTrades = trades.filter(t => !t.is_open);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <TrendingUp className="size-5 text-primary" aria-hidden="true" />
          Trading Terminal
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {openTrades.length} open &middot; {closedTrades.length} closed
        </p>
      </div>

      <Card title={`Open Positions (${openTrades.length})`}>
        {loading ? (
          <div className="flex items-center justify-center h-20 text-sm text-muted-foreground">Loading positions…</div>
        ) : openTrades.length === 0 ? (
          <Empty icon={TrendingUp} title="No Open Positions" />
        ) : (
          <div className="flex flex-col gap-2">
            {openTrades.map(t => (
              <div key={t.trade_id} className="flex items-center justify-between rounded-lg py-2.5 px-3 hover:bg-muted/30 motion-safe:transition-colors">
                <div className="flex items-center gap-3">
                  {t.is_short ? <ArrowDownRight className="size-4 text-loss" aria-hidden="true" /> : <ArrowUpRight className="size-4 text-profit" aria-hidden="true" />}
                  <div>
                    <span className="font-medium">{t.pair}</span>
                    <span className="text-xs text-muted-foreground ml-2">
                      @ {t.open_rate.toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <Badge label={t.is_short ? "SHORT" : "LONG"} variant={t.is_short ? "danger" : "success"} />
                  <span className="font-mono">{t.amount.toFixed(4)}</span>
                  <span className="text-muted-foreground font-mono">{(t.stake_amount).toFixed(2)} USDT</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Manual Actions">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <div className="text-xs text-muted-foreground uppercase">Force Entry</div>
            <div className="flex flex-wrap sm:flex-nowrap gap-2">
              <Input
                type="text" value={forcePair} onChange={(e) => setForcePair(e.target.value)}
                placeholder="BTC/USDT:USDT"
              />
              <Input
                type="number" value={forcePrice} onChange={(e) => setForcePrice(e.target.value)}
                placeholder="Price (opt)" className="w-24 sm:w-28"
              />
              <Button
                onClick={async () => {
                  setActing(true);
                  try {
                    await api.forceEnter(forcePair, forcePrice ? Number(forcePrice) : undefined);
                    addToast("success", "Force Entry", `${forcePair} entry triggered`);
                    setForcePair(""); setForcePrice("");
                  } catch (e: any) { addToast("error", "Failed", e.message); }
                  setActing(false);
                }}
                disabled={!forcePair || acting}
                size="sm"
              >
                <Zap data-icon="inline-start" aria-hidden="true" /> Entry
              </Button>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <div className="text-xs text-muted-foreground uppercase">Force Exit</div>
            <div className="flex flex-wrap sm:flex-nowrap gap-2">
              <Input
                type="number" value={forceExitId} onChange={(e) => setForceExitId(e.target.value)}
                placeholder="Trade ID"
              />
              <Button
                onClick={async () => {
                  setActing(true);
                  try {
                    await api.forceExit(Number(forceExitId));
                    addToast("info", "Force Exit", `Trade #${forceExitId} exit triggered`);
                    setForceExitId("");
                  } catch (e: any) { addToast("error", "Failed", e.message); }
                  setActing(false);
                }}
                disabled={!forceExitId || acting}
                variant="destructive"
                size="sm"
              >
                <XCircle data-icon="inline-start" aria-hidden="true" /> Exit
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <Card title={`Trade History (${closedTrades.length})`}>
        <div className="overflow-auto max-h-96 sm:max-h-[32rem]">
          <table className="w-full text-sm min-w-[600px]">
            <thead>
              <tr className="text-left text-muted-foreground border-b border-border/50">
                <th className="pb-2 pr-4">Pair</th>
                <th className="pb-2 pr-4">Direction</th>
                <th className="pb-2 pr-4">Entry</th>
                <th className="pb-2 pr-4">Exit</th>
                <th className="pb-2 pr-4">P&amp;L</th>
                <th className="pb-2 pr-4">Exit Reason</th>
                <th className="pb-2">Closed</th>
              </tr>
            </thead>
            <tbody>
              {closedTrades.slice(0, 50).map(t => (
                <tr key={t.trade_id} className="hover:bg-muted/30 motion-safe:transition-colors">
                  <td className="py-2.5 pl-3 pr-4 rounded-l-lg font-medium">{t.pair}</td>
                  <td className="py-2.5 pr-4">
                    <Badge label={t.is_short ? "SHORT" : "LONG"} variant={t.is_short ? "danger" : "success"} />
                  </td>
                  <td className="py-2.5 pr-4 font-mono">{t.open_rate.toFixed(4)}</td>
                  <td className="py-2.5 pr-4 font-mono">{t.close_rate?.toFixed(4) ?? "—"}</td>
                  <td className={cn("py-2.5 pr-4 font-mono", (t.profit_pct ?? 0) >= 0 ? "text-profit" : "text-loss")}>
                    {(t.profit_pct ?? 0).toFixed(2)}%
                  </td>
                  <td className="py-2.5 pr-4 text-xs text-muted-foreground">{t.exit_reason ?? "—"}</td>
                  <td className="py-2.5 pr-3 rounded-r-lg text-xs text-muted-foreground font-mono">{t.close_date ? new Date(t.close_date).toLocaleDateString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
