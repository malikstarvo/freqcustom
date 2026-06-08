import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { api, Balance as BalanceType } from "@/lib/api";
import { Wallet } from "lucide-react";

export default function Balance() {
  const [balance, setBalance] = useState<BalanceType | null>(null);

  useEffect(() => {
    api.balance().then(setBalance).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold flex items-center gap-2">
        <Wallet className="text-[--color-accent]" /> Balance
      </h2>

      {balance && (
        <div className="grid grid-cols-3 gap-4">
          <Card>
            <span className="text-xs text-[--color-text-secondary] uppercase">Total Value</span>
            <p className="text-2xl font-bold">{balance.total.toFixed(2)} {balance.symbol}</p>
          </Card>
        </div>
      )}

      <Card title="Currencies">
        <div className="overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[--color-text-secondary] border-b border-[--color-card-border]">
                <th className="pb-2 pr-4">Currency</th><th className="pb-2 pr-4">Free</th>
                <th className="pb-2 pr-4">Used</th><th className="pb-2 pr-4">Balance</th>
              </tr>
            </thead>
            <tbody>
              {balance?.currencies?.map((c: { currency: string; free: number; used: number; balance: number }) => (
                <tr key={c.currency} className="border-b border-[--color-card-border]/50">
                  <td className="py-2 pr-4 font-medium">{c.currency}</td>
                  <td className="py-2 pr-4">{c.free.toFixed(4)}</td>
                  <td className="py-2 pr-4">{c.used.toFixed(4)}</td>
                  <td className="py-2 pr-4">{c.balance.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
