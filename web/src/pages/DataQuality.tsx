import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Empty } from "@/components/ui/empty";
import { SearchInput } from "@/components/ui/search-input";
import { cn } from "@/lib/utils";
import { api, type WhitelistResponse, type PairHistory } from "@/lib/api";
import { Database, Clock, AlertTriangle, CheckCircle, RefreshCw } from "lucide-react";

type DataQualityItem = {
  pair: string;
  timeframe: string;
  lastCandle: string;
  candleCount: number;
  dataStart: string;
  dataStop: string;
  ageHours: number;
  status: "fresh" | "stale" | "missing";
};

const TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"];

export default function DataQuality() {
  const [whitelist, setWhitelist] = useState<WhitelistResponse | null>(null);
  const [qualityData, setQualityData] = useState<DataQualityItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [timeframe, setTimeframe] = useState("1h");
  const [lastCheck, setLastCheck] = useState<string>("\u2014");

  const checkData = async () => {
    setLoading(true);
    setQualityData([]);
    try {
      const wl = await api.whitelist();
      setWhitelist(wl);
      const items: DataQualityItem[] = [];
      const pairs = wl.whitelist.slice(0, 20);
      for (const pair of pairs) {
        try {
          const hist = await api.pairCandles(pair, timeframe, 1);
          const lastTs = hist.data_stop_ts;
          const now = Date.now() / 1000;
          const ageHours = (now - lastTs) / 3600;
          let status: "fresh" | "stale" | "missing" = "fresh";
          if (ageHours > 48) status = "missing";
          else if (ageHours > 6) status = "stale";
          items.push({
            pair,
            timeframe,
            lastCandle: hist.data_stop,
            candleCount: hist.length,
            dataStart: hist.data_start,
            dataStop: hist.data_stop,
            ageHours,
            status,
          });
        } catch {
          items.push({
            pair,
            timeframe,
            lastCandle: "\u2014",
            candleCount: 0,
            dataStart: "\u2014",
            dataStop: "\u2014",
            ageHours: Infinity,
            status: "missing",
          });
        }
      }
      setQualityData(items);
      setLastCheck(new Date().toLocaleTimeString());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkData();
  }, [timeframe]);

  const filtered = qualityData.filter(d => {
    if (!search) return true;
    return d.pair.toLowerCase().includes(search.toLowerCase());
  });

  const freshCount = qualityData.filter(d => d.status === "fresh").length;
  const staleCount = qualityData.filter(d => d.status === "stale").length;
  const missingCount = qualityData.filter(d => d.status === "missing").length;
  const total = qualityData.length || 1;

  const statusConfig = {
    fresh: { color: "text-profit", bg: "bg-profit/10", border: "border-profit/25", icon: <CheckCircle className="size-3.5" /> },
    stale: { color: "text-warning", bg: "bg-warning/10", border: "border-warning/25", icon: <AlertTriangle className="size-3.5" /> },
    missing: { color: "text-loss", bg: "bg-loss/10", border: "border-loss/25", icon: <AlertTriangle className="size-3.5" /> },
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <Database className="size-5 text-primary" aria-hidden="true" /> Data Quality
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Last check: {lastCheck}</span>
          <Button
            onClick={checkData}
            disabled={loading}
            variant="default"
            size="sm"
          >
            <RefreshCw aria-hidden="true" className={loading ? "animate-spin" : ""} /> Check
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-muted/30 border border-profit/25 rounded-lg p-4">
          <div className="flex items-center gap-2 text-profit mb-1">
            <CheckCircle className="size-4" aria-hidden="true" />
            <span className="text-xs uppercase font-bold">Fresh</span>
          </div>
          <div className="text-2xl font-bold font-mono">{freshCount}</div>
          <div className="text-xs text-muted-foreground">{(freshCount / total * 100).toFixed(0)}% coverage</div>
        </div>
        <div className="bg-muted/30 border border-warning/25 rounded-lg p-4">
          <div className="flex items-center gap-2 text-warning mb-1">
            <AlertTriangle className="size-4" aria-hidden="true" />
            <span className="text-xs uppercase font-bold">Stale</span>
          </div>
          <div className="text-2xl font-bold font-mono">{staleCount}</div>
          <div className="text-xs text-muted-foreground">{(staleCount / total * 100).toFixed(0)}% coverage</div>
        </div>
        <div className="bg-muted/30 border border-loss/25 rounded-lg p-4">
          <div className="flex items-center gap-2 text-loss mb-1">
            <AlertTriangle className="size-4" aria-hidden="true" />
            <span className="text-xs uppercase font-bold">Missing</span>
          </div>
          <div className="text-2xl font-bold font-mono">{missingCount}</div>
          <div className="text-xs text-muted-foreground">{(missingCount / total * 100).toFixed(0)}% coverage</div>
        </div>
      </div>

      <Card title="Coverage Overview">
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Overall data quality</span>
            <span className="font-bold">{freshCount}/{qualityData.length} pairs fresh</span>
          </div>
          <div className="w-full h-3 bg-muted rounded-full overflow-hidden flex">
            <div className="h-full bg-profit" style={{ width: `${(freshCount / total) * 100}%` }} />
            <div className="h-full bg-warning" style={{ width: `${(staleCount / total) * 100}%` }} />
            <div className="h-full bg-loss" style={{ width: `${(missingCount / total) * 100}%` }} />
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1"><div className="size-2 rounded-full bg-profit" /> Fresh</div>
            <div className="flex items-center gap-1"><div className="size-2 rounded-full bg-warning" /> Stale</div>
            <div className="flex items-center gap-1"><div className="size-2 rounded-full bg-loss" /> Missing</div>
          </div>
        </div>
      </Card>

      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          {TIMEFRAMES.map(tf => (
            <Button
              key={tf}
              onClick={() => setTimeframe(tf)}
              variant={timeframe === tf ? "default" : "outline"}
              size="sm"
            >
              {tf}
            </Button>
          ))}
        </div>
        <SearchInput value={search} onChange={setSearch} placeholder="Search pair\u2026" className="max-w-xs" />
      </div>

      <Card title={`Pair Data Quality (${filtered.length} shown)`}>
        {filtered.length === 0 && !loading ? (
          <Empty title="No Data" />
        ) : (
          <div className="overflow-auto max-h-[60vh]">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 sticky top-0">
                <tr>
                  <th className="py-2.5 px-3 text-left text-muted-foreground font-medium">Pair</th>
                  <th className="py-2.5 px-3 text-left text-muted-foreground font-medium">Status</th>
                  <th className="py-2.5 px-3 text-left text-muted-foreground font-medium">Last Candle</th>
                  <th className="py-2.5 px-3 text-left text-muted-foreground font-medium">Age</th>
                  <th className="py-2.5 px-3 text-left text-muted-foreground font-medium">Candles</th>
                  <th className="py-2.5 px-3 text-left text-muted-foreground font-medium">Range</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => {
                  const cfg = statusConfig[d.status];
                  return (
                    <tr key={d.pair} className="hover:bg-muted/30 motion-safe:transition-colors">
                      <td className="py-2.5 px-3 font-bold">{d.pair}</td>
                      <td className="py-2.5 px-3">
                        <div className={cn("flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border w-fit", cfg.border, cfg.color)}>
                          {cfg.icon}
                          {d.status.toUpperCase()}
                        </div>
                      </td>
                      <td className="py-2.5 px-3 text-muted-foreground font-mono">{d.lastCandle}</td>
                      <td className="py-2.5 px-3 font-mono">
                        {d.ageHours === Infinity ? "\u2014" : (
                          <span className={d.ageHours > 6 ? "text-warning" : "text-profit"}>
                            {d.ageHours > 24 ? `${(d.ageHours / 24).toFixed(1)}d` : `${d.ageHours.toFixed(1)}h`}
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono">{d.candleCount}</td>
                      <td className="py-2.5 px-3 text-xs text-muted-foreground font-mono">{d.dataStart} \u2192 {d.dataStop}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
