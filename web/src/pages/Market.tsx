import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Card, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Empty } from "@/components/ui/empty";
import { Spinner } from "@/components/ui/spinner";
import { SearchInput } from "@/components/ui/search-input";
import { api, type MarketResponse, type WhitelistResponse, type PairHistory, type MarketModel } from "@/lib/api";
import { Globe, TrendingUp, CandlestickChart } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ComposedChart, Bar
} from "recharts";

export default function Market() {
  const [markets, setMarkets] = useState<MarketResponse | null>(null);
  const [whitelist, setWhitelist] = useState<WhitelistResponse | null>(null);
  const [search, setSearch] = useState("");
  const [selectedPair, setSelectedPair] = useState<string>("");
  const [candles, setCandles] = useState<PairHistory | null>(null);
  const [timeframe, setTimeframe] = useState("1h");
  const [loadingCandles, setLoadingCandles] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.markets().then(setMarkets),
      api.whitelist().then(setWhitelist),
    ]).catch(console.error).finally(() => setLoading(false));
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
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <Globe className="size-5 text-primary" aria-hidden="true" /> Market
        </h2>
        <div className="flex items-center gap-2">
          <Badge label={`${marketEntries.length} markets`} variant="default" />
          <Badge label={`${whitelist?.length ?? 0} whitelisted`} variant="success" />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Market List */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <Card title="Market List">
            {loading ? (
              <div className="flex items-center justify-center h-40 text-sm text-muted-foreground">Loading markets…</div>
            ) : (
            <>
            <div className="mb-3">
              <SearchInput value={search} onChange={setSearch} placeholder="Search symbol, base, quote…" />
            </div>
            <div className="overflow-auto max-h-[60vh]">
              <table className="w-full text-sm min-w-[600px]">
                <thead className="sticky top-0 bg-muted/30">
                  <tr className="text-left text-muted-foreground border-b border-border/50">
                    <th className="pb-2 pr-4 pl-3">Symbol</th>
                    <th className="pb-2 pr-4">Base</th>
                    <th className="pb-2 pr-4">Quote</th>
                    <th className="pb-2 pr-4">Spot</th>
                    <th className="pb-2 pr-4">Swap</th>
                    <th className="pb-2 pr-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(([symbol, m]) => (
                    <tr
                      key={symbol}
                      className={cn(
                        "cursor-pointer hover:bg-muted/30 motion-safe:transition-colors",
                        selectedPair === symbol ? "bg-primary/10" : ""
                      )}
                      onClick={() => setSelectedPair(symbol)}
                      tabIndex={0}
                      role="button"
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelectedPair(symbol); } }}
                    >
                      <td className="py-2.5 pl-3 pr-4 rounded-l-lg font-medium">{symbol}</td>
                      <td className="py-2.5 pr-4 text-muted-foreground">{m.base}</td>
                      <td className="py-2.5 pr-4 text-muted-foreground">{m.quote}</td>
                      <td className="py-2.5 pr-4">
                        <Badge label={m.spot ? "Yes" : "No"} variant={m.spot ? "success" : "default"} />
                      </td>
                      <td className="py-2.5 pr-4">
                        <Badge label={m.swap ? "Yes" : "No"} variant={m.swap ? "success" : "default"} />
                      </td>
                      <td className="py-2.5 pr-3 rounded-r-lg">
                        <Badge label={isWhitelisted(symbol) ? "Active" : "Inactive"} variant={isWhitelisted(symbol) ? "success" : "default"} />
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8">
                        <Empty icon={Globe} title="No markets match your search" />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            </>
          )}
          </Card>
        </div>

        {/* Candle Preview */}
        <div className="flex flex-col gap-4">
          <Card title="Candle Preview">
            {selectedPair ? (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{selectedPair}</span>
                  <div className="flex flex-wrap gap-1">
                    {TIMEFRAMES.map(tf => (
                      <Button
                        key={tf}
                        variant={timeframe === tf ? "default" : "ghost"}
                        size="sm"
                        onClick={() => setTimeframe(tf)}
                      >
                        {tf}
                      </Button>
                    ))}
                  </div>
                </div>

                {loadingCandles ? (
                  <div className="flex items-center justify-center h-40 text-sm text-muted-foreground gap-2">
                    <Spinner /> Loading…
                  </div>
                ) : candles ? (
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>Data: {candles.data_start} &rarr; {candles.data_stop}</span>
                      <span>{candles.length} candles</span>
                    </div>
                <div className="h-48 sm:h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={candles.data.slice(-50).map((row: Array<number | string | null>) => {
                        const dateIdx = candles.columns.indexOf("date");
                        const openIdx = candles.columns.indexOf("open");
                        const highIdx = candles.columns.indexOf("high");
                        const lowIdx = candles.columns.indexOf("low");
                        const closeIdx = candles.columns.indexOf("close");
                        const volIdx = candles.columns.indexOf("volume");
                        return {
                          date: dateIdx >= 0 ? String(row[dateIdx] ?? "").slice(5, 16) : "",
                          open: openIdx >= 0 ? Number(row[openIdx]) : 0,
                          high: highIdx >= 0 ? Number(row[highIdx]) : 0,
                          low: lowIdx >= 0 ? Number(row[lowIdx]) : 0,
                          close: closeIdx >= 0 ? Number(row[closeIdx]) : 0,
                          volume: volIdx >= 0 ? Number(row[volIdx]) : 0,
                        };
                      })}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3e" />
                        <XAxis dataKey="date" stroke="#888a9e" fontSize={9} tickLine={false} />
                        <YAxis stroke="#888a9e" fontSize={9} tickLine={false} domain={["auto", "auto"]} />
                        <Tooltip contentStyle={{ background: "#1a1d2e", border: "1px solid #2a2d3e", borderRadius: 8, fontSize: 11 }} />
                        <Area type="monotone" dataKey="close" stroke="#00d4ff" fill="#00d4ff20" strokeWidth={1.5} />
                        <Bar dataKey="volume" fill="#00d4ff15" yAxisId={1} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <TrendingUp className="size-3" aria-hidden="true" />
                      <span>Signals: {candles.enter_long_signals} long / {candles.enter_short_signals} short entries</span>
                    </div>
                  </div>
                ) : (
                  <Empty icon={CandlestickChart} title="No candle data available" />
                )}
              </div>
            ) : (
              <Empty icon={CandlestickChart} title="Select a market to view candles" />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
