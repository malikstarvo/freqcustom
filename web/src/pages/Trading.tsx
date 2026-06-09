import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
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

  useEffect(() => {
    api.trades(100).then((r: { trades: Trade[] }) => setTrades(r.trades)).catch(console.error);
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
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold flex items-center gap-2">
          <TrendingUp className="text-[--color-accent]" />
          Trading Terminal
        </h2>
        <p className="text-sm text-[--color-text-secondary] mt-1">
          {openTrades.length} open &middot; {closedTrades.length} closed
        </p>
      </div>

      <Card title={`Open Positions (${openTrades.length})`}>
        {openTrades.length === 0 ? (
          <p className="text-sm text-[--color-text-secondary]">No open positions</p>
        ) : (
          <div className="space-y-3">
            {openTrades.map(t => (
              <div key={t.trade_id} className="flex items-center justify-between py-2 border-b border-[--color-card-border] last:border-0">
                <div className="flex items-center gap-3">
                  {t.is_short ? <ArrowDownRight size={16} className="text-[--color-loss]" /> : <ArrowUpRight size={16} className="text-[--color-profit]" />}
                  <div>
                    <span className="font-medium">{t.pair}</span>
                    <span className="text-xs text-[--color-text-secondary] ml-2">
                      @ {t.open_rate.toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <Badge label={t.is_short ? "SHORT" : "LONG"} variant={t.is_short ? "danger" : "success"} />
                  <span>{t.amount.toFixed(4)}</span>
                  <span className="text-[--color-text-secondary]">{(t.stake_amount).toFixed(2)} USDT</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Manual Actions">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="space-y-2">
            <div className="text-xs text-[--color-text-secondary] uppercase">Force Entry</div>
            <div className="flex gap-2">
              <input
                type="text" value={forcePair} onChange={(e) => setForcePair(e.target.value)}
                placeholder="BTC/USDT:USDT" className="flex-1 px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm focus:outline-none focus:border-[--color-accent]"
              />
              <input
                type="number" value={forcePrice} onChange={(e) => setForcePrice(e.target.value)}
                placeholder="Price (opt)" className="w-28 px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm focus:outline-none focus:border-[--color-accent]"
              />
              <button
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
                className="flex items-center gap-1 px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-semibold disabled:opacity-50"
              >
                <Zap size={12} /> Entry
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-[--color-text-secondary] uppercase">Force Exit</div>
            <div className="flex gap-2">
              <input
                type="number" value={forceExitId} onChange={(e) => setForceExitId(e.target.value)}
                placeholder="Trade ID" className="flex-1 px-3 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm focus:outline-none focus:border-[--color-accent]"
              />
              <button
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
                className="flex items-center gap-1 px-3 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-semibold disabled:opacity-50"
              >
                <XCircle size={12} /> Exit
              </button>
            </div>
          </div>
        </div>
      </Card>

      <Card title={`Trade History (${closedTrades.length})`}>
        <div className="overflow-auto max-h-96">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[--color-text-secondary] border-b border-[--color-card-border]">
                <th className="pb-2 pr-4">Pair</th>
                <th className="pb-2 pr-4">Direction</th>
                <th className="pb-2 pr-4">Entry</th>
                <th className="pb-2 pr-4">Exit</th>
                <th className="pb-2 pr-4">P&L</th>
                <th className="pb-2 pr-4">Exit Reason</th>
                <th className="pb-2">Closed</th>
              </tr>
            </thead>
            <tbody>
              {closedTrades.slice(0, 50).map(t => (
                <tr key={t.trade_id} className="border-b border-[--color-card-border]/50">
                  <td className="py-2 pr-4 font-medium">{t.pair}</td>
                  <td className="py-2 pr-4">
                    <Badge label={t.is_short ? "SHORT" : "LONG"} variant={t.is_short ? "danger" : "success"} />
                  </td>
                  <td className="py-2 pr-4">{t.open_rate.toFixed(4)}</td>
                  <td className="py-2 pr-4">{t.close_rate?.toFixed(4) ?? "—"}</td>
                  <td className={`py-2 pr-4 ${(t.profit_pct ?? 0) >= 0 ? "text-[--color-profit]" : "text-[--color-loss]"}`}>
                    {(t.profit_pct ?? 0).toFixed(2)}%
                  </td>
                  <td className="py-2 pr-4 text-xs text-[--color-text-secondary]">{t.exit_reason ?? "—"}</td>
                  <td className="py-2 text-xs text-[--color-text-secondary]">{t.close_date ? new Date(t.close_date).toLocaleDateString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
