import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { SearchInput } from "@/components/ui/search-input";
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
  const [lastCheck, setLastCheck] = useState<string>("—");

  const checkData = async () => {
    setLoading(true);
    setQualityData([]);
    try {
      const wl = await api.whitelist();
      setWhitelist(wl);
      const items: DataQualityItem[] = [];
      const pairs = wl.whitelist.slice(0, 20); // Limit to avoid too many API calls
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
            lastCandle: "—",
            candleCount: 0,
            dataStart: "—",
            dataStop: "—",
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
    fresh: { color: "text-[--color-profit]", bg: "bg-green-950/50", border: "border-green-500/30", icon: <CheckCircle size={14} /> },
    stale: { color: "text-[--color-warning]", bg: "bg-yellow-950/50", border: "border-yellow-500/30", icon: <AlertTriangle size={14} /> },
    missing: { color: "text-[--color-loss]", bg: "bg-red-950/50", border: "border-red-500/30", icon: <AlertTriangle size={14} /> },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Database className="text-[--color-accent]" /> Data Quality
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[--color-text-secondary]">Last check: {lastCheck}</span>
          <button
            onClick={checkData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 bg-[--color-accent] hover:bg-[--color-accent-hover] text-[#0f1119] rounded-lg text-xs font-semibold disabled:opacity-50"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Check
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-[--color-card-bg] border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 text-[--color-profit] mb-1">
            <CheckCircle size={16} />
            <span className="text-xs uppercase font-medium">Fresh</span>
          </div>
          <div className="text-2xl font-bold">{freshCount}</div>
          <div className="text-xs text-[--color-text-secondary]">{(freshCount / total * 100).toFixed(0)}% coverage</div>
        </div>
        <div className="bg-[--color-card-bg] border border-yellow-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 text-[--color-warning] mb-1">
            <AlertTriangle size={16} />
            <span className="text-xs uppercase font-medium">Stale</span>
          </div>
          <div className="text-2xl font-bold">{staleCount}</div>
          <div className="text-xs text-[--color-text-secondary]">{(staleCount / total * 100).toFixed(0)}% coverage</div>
        </div>
        <div className="bg-[--color-card-bg] border border-red-500/30 rounded-lg p-4">
          <div className="flex items-center gap-2 text-[--color-loss] mb-1">
            <AlertTriangle size={16} />
            <span className="text-xs uppercase font-medium">Missing</span>
          </div>
          <div className="text-2xl font-bold">{missingCount}</div>
          <div className="text-xs text-[--color-text-secondary]">{(missingCount / total * 100).toFixed(0)}% coverage</div>
        </div>
      </div>

      {/* Coverage Bar */}
      <Card title="Coverage Overview">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[--color-text-secondary]">Overall data quality</span>
            <span className="font-medium">{freshCount}/{qualityData.length} pairs fresh</span>
          </div>
          <div className="w-full h-3 bg-[--color-card-border] rounded-full overflow-hidden flex">
            <div className="h-full bg-[--color-profit]" style={{ width: `${(freshCount / total) * 100}%` }} />
            <div className="h-full bg-[--color-warning]" style={{ width: `${(staleCount / total) * 100}%` }} />
            <div className="h-full bg-[--color-loss]" style={{ width: `${(missingCount / total) * 100}%` }} />
          </div>
          <div className="flex items-center gap-4 text-xs text-[--color-text-secondary]">
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[--color-profit]" /> Fresh</div>
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[--color-warning]" /> Stale</div>
            <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[--color-loss]" /> Missing</div>
          </div>
        </div>
      </Card>

      {/* Controls */}
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium ${
                timeframe === tf
                  ? "bg-[--color-accent] text-[#0f1119]"
                  : "bg-[--color-card-bg] border border-[--color-card-border] text-[--color-text-secondary]"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
        <SearchInput value={search} onChange={setSearch} placeholder="Search pair..." className="max-w-xs" />
      </div>

      {/* Data Quality Table */}
      <Card title={`Pair Data Quality (${filtered.length} shown)`}>
        <div className="overflow-auto max-h-[60vh]">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-[--color-card-bg]">
              <tr className="text-left text-[--color-text-secondary] border-b border-[--color-card-border]">
                <th className="pb-2 pr-4">Pair</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Last Candle</th>
                <th className="pb-2 pr-4">Age</th>
                <th className="pb-2 pr-4">Candles</th>
                <th className="pb-2">Range</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((d) => {
                const cfg = statusConfig[d.status];
                return (
                  <tr key={d.pair} className={`border-b border-[--color-card-border]/30 ${cfg.bg}`}>
                    <td className="py-2 pr-4 font-medium">{d.pair}</td>
                    <td className="py-2 pr-4">
                      <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${cfg.border} ${cfg.color}`}>
                        {cfg.icon}
                        {d.status.toUpperCase()}
                      </div>
                    </td>
                    <td className="py-2 pr-4 text-[--color-text-secondary]">{d.lastCandle}</td>
                    <td className="py-2 pr-4">
                      {d.ageHours === Infinity ? "—" : (
                        <span className={d.ageHours > 6 ? "text-[--color-warning]" : "text-[--color-profit]"}>
                          {d.ageHours > 24 ? `${(d.ageHours / 24).toFixed(1)}d` : `${d.ageHours.toFixed(1)}h`}
                        </span>
                      )}
                    </td>
                    <td className="py-2 pr-4">{d.candleCount}</td>
                    <td className="py-2 text-xs text-[--color-text-secondary]">{d.dataStart} → {d.dataStop}</td>
                  </tr>
                );
              })}
              {filtered.length === 0 && !loading && (
                <tr><td colSpan={6} className="py-8 text-center text-[--color-text-secondary]">No data</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
