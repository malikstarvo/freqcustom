import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { api, Balance as BalanceType } from "@/lib/api";
import { Wallet } from "lucide-react";

export default function Balance() {
  const [balance, setBalance] = useState<BalanceType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.balance().then(setBalance).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col gap-6">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <Wallet className="size-5 text-primary" aria-hidden="true" /> Balance
        </h2>
        <div className="flex items-center justify-center h-40 sm:h-48">
          <Spinner className="text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold flex items-center gap-2.5">
        <Wallet className="size-5 text-primary" aria-hidden="true" /> Balance
      </h2>

      {balance && (
        <div className="max-w-sm">
          <Card>
            <span className="text-xs text-muted-foreground uppercase">Total Value</span>
            <p className="text-2xl font-bold font-mono">{balance.total.toFixed(2)} {balance.symbol}</p>
          </Card>
        </div>
      )}

      <Card title="Currencies">
        <div className="overflow-auto">
          <table className="w-full text-sm min-w-[360px]">
            <thead>
              <tr className="bg-muted/30 text-left text-muted-foreground">
                <th className="py-2.5 px-3 font-medium">Currency</th>
                <th className="py-2.5 px-3 font-medium">Free</th>
                <th className="py-2.5 px-3 font-medium">Used</th>
                <th className="py-2.5 px-3 font-medium">Balance</th>
              </tr>
            </thead>
            <tbody>
              {balance?.currencies?.map((c: { currency: string; free: number; used: number; balance: number }) => (
                <tr key={c.currency} className="hover:bg-muted/30 motion-safe:transition-colors">
                  <td className="py-2.5 px-3 font-bold">{c.currency}</td>
                  <td className="py-2.5 px-3 font-mono">{c.free.toFixed(4)}</td>
                  <td className="py-2.5 px-3 font-mono">{c.used.toFixed(4)}</td>
                  <td className="py-2.5 px-3 font-mono font-bold">{c.balance.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
