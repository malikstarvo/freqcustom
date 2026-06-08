import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
import { SearchInput } from "@/components/ui/search-input";
import { api, type MarketResponse, type WhitelistResponse, type PairHistory, type MarketModel } from "@/lib/api";
import { Globe, TrendingUp, Activity, CandlestickChart } from "lucide-react";

export default function Market() {
  const [markets, setMarkets] = useState<MarketResponse | null>(null);
  const [whitelist, setWhitelist] = useState<WhitelistResponse | null>(null);
  const [search, setSearch] = useState("");
  const [selectedPair, setSelectedPair] = useState<string>("");
  const [candles, setCandles] = useState<PairHistory | null>(null);
  const [timeframe, setTimeframe] = useState("1h");
  const [loadingCandles, setLoadingCandles] = useState(false);

  useEffect(() => {
    api.markets().then(setMarkets).catch(console.error);
    api.whitelist().then(setWhitelist).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedPair) {
      setLoadingCandles(true);
      api.pairCandles(selectedPair, timeframe, 50)
        .then(setCandles)
        .catch(console.error)
        .finally(() => setLoadingCandles(false));
    }
  }, [selectedPair, timeframe]);

  const marketEntries = markets?.markets
    ? Object.entries(markets.markets)
    : [];

  const filtered = (marketEntries as Array<[string, MarketModel]>).filter(([symbol, m]) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      symbol.toLowerCase().includes(s) ||
      m.base.toLowerCase().includes(s) ||
      m.quote.toLowerCase().includes(s)
    );
  });

  const isWhitelisted = (symbol: string) => whitelist?.whitelist.includes(symbol) ?? false;

  const TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Globe className="text-[--color-accent]" /> Market
        </h2>
        <div className="flex items-center gap-2">
          <Badge label={`${marketEntries.length} markets`} variant="default" />
          <Badge label={`${whitelist?.length ?? 0} whitelisted`} variant="success" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Market List */}
        <div className="lg:col-span-2 space-y-4">
          <Card title="Market List">
            <div className="mb-3">
              <SearchInput value={search} onChange={setSearch} placeholder="Search symbol, base, quote..." />
            </div>
            <div className="overflow-auto max-h-[60vh]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-[--color-card-bg]">
                  <tr className="text-left text-[--color-text-secondary] border-b border-[--color-card-border]">
                    <th className="pb-2 pr-4">Symbol</th>
                    <th className="pb-2 pr-4">Base</th>
                    <th className="pb-2 pr-4">Quote</th>
                    <th className="pb-2 pr-4">Spot</th>
                    <th className="pb-2 pr-4">Swap</th>
                    <th className="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(([symbol, m]) => (
                    <tr
                      key={symbol}
                      className={`border-b border-[--color-card-border]/30 cursor-pointer transition-colors ${
                        selectedPair === symbol ? "bg-[--color-accent]/10" : "hover:bg-gray-800/50"
                      }`}
                      onClick={() => setSelectedPair(symbol)}
                    >
                      <td className="py-2 pr-4 font-medium">{symbol}</td>
                      <td className="py-2 pr-4 text-[--color-text-secondary]">{m.base}</td>
                      <td className="py-2 pr-4 text-[--color-text-secondary]">{m.quote}</td>
                      <td className="py-2 pr-4">
                        <Badge label={m.spot ? "Yes" : "No"} variant={m.spot ? "success" : "default"} />
                      </td>
                      <td className="py-2 pr-4">
                        <Badge label={m.swap ? "Yes" : "No"} variant={m.swap ? "success" : "default"} />
                      </td>
                      <td className="py-2">
                        <Badge label={isWhitelisted(symbol) ? "Active" : "Inactive"} variant={isWhitelisted(symbol) ? "success" : "default"} />
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-[--color-text-secondary]">
                        No markets match your search
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Candle Preview */}
        <div className="space-y-4">
          <Card title="Candle Preview">
            {selectedPair ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{selectedPair}</span>
                  <div className="flex gap-1">
                    {TIMEFRAMES.map(tf => (
                      <button
                        key={tf}
                        onClick={() => setTimeframe(tf)}
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          timeframe === tf
                            ? "bg-[--color-accent] text-[#0f1119]"
                            : "bg-[--color-card-bg] border border-[--color-card-border] text-[--color-text-secondary]"
                        }`}
                      >
                        {tf}
                      </button>
                    ))}
                  </div>
                </div>

                {loadingCandles ? (
                  <div className="flex items-center justify-center h-40 text-sm text-[--color-text-secondary]">
                    <Activity size={16} className="animate-spin mr-2" /> Loading...
                  </div>
                ) : candles ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-[--color-text-secondary]">
                      <span>Data: {candles.data_start} → {candles.data_stop}</span>
                      <span>{candles.length} candles</span>
                    </div>
                    <div className="overflow-auto max-h-60 border border-[--color-card-border] rounded">
                      <table className="w-full text-xs">
                        <thead className="sticky top-0 bg-[--color-card-bg]">
                          <tr className="text-left text-[--color-text-secondary]">
                             {candles.columns.slice(0, 6).map((c: string, i: number) => (
                              <th key={i} className="px-2 py-1 border-b border-[--color-card-border]">{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                           {candles.data.slice(-10).map((row: Array<number | string | null>, i: number) => (
                            <tr key={i} className="border-b border-[--color-card-border]/30">
                              {row.slice(0, 6).map((cell: number | string | null, j: number) => (
                                <td key={j} className="px-2 py-1 font-mono">
                                  {typeof cell === "number" ? cell.toFixed(4) : String(cell)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-[--color-text-secondary]">
                      <TrendingUp size={12} />
                      <span>Signals: {candles.enter_long_signals} long / {candles.enter_short_signals} short entries</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-[--color-text-secondary]">No candle data available</div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-40 text-sm text-[--color-text-secondary]">
                <CandlestickChart size={24} className="mb-2 opacity-50" />
                Select a market to view candles
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
