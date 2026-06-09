import { useEffect, useState } from "react";
import { Card, StatCard, Badge } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Activity, Database, Radio, Clock, HardDrive, Cpu } from "lucide-react";

type CollectorStatus = {
  symbols: number;
  timeframes: number;
  candles: number;
  features: number;
  lastCandle: string;
  fundingAvailable: boolean;
  uptime: string;
};

export default function Collector() {
  const [status, setStatus] = useState<CollectorStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCollectorStatus();
    const interval = setInterval(fetchCollectorStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchCollectorStatus = async () => {
    try {
      const resp = await fetch("/api/v1/ping");
      if (!resp.ok) {
        setError("API ping failed");
        return;
      }
      const candlesResp = await fetch("/proxy/timescale/candles");
      if (candlesResp.ok) {
        const data = await candlesResp.json();
        setStatus(data);
        setError(null);
      } else {
        setError("TimescaleDB query unavailable \u2014 collector may not be running");
      }
    } catch {
      setError("Cannot reach collector API \u2014 check Docker services");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <Radio className="size-5 text-primary" aria-hidden="true" /> Collector
        </h2>
        <Badge label={status ? "Running" : "Checking\u2026"} variant={status ? "success" : "warning"} />
      </div>

      <p className="text-sm text-muted-foreground">
        Go collector streams Bybit WebSocket data (OHLCV, funding rate, open interest, liquidations) into TimescaleDB. This data powers the multi-agent scoring system and FreqAI predictions.
      </p>

      {loading && (
        <div className="flex items-center justify-center h-40 text-sm text-muted-foreground">
          Connecting to collector\u2026
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!loading && !error && (
      <>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Symbols" value={status?.symbols ?? "\u2014"} subtitle="Monitored pairs" />
        <StatCard label="Timeframes" value={status?.timeframes ?? "\u2014"} subtitle="15m, 1h, 4h" />
        <StatCard label="Candles" value={status?.candles?.toLocaleString() ?? "\u2014"} subtitle="In TimescaleDB" />
        <StatCard label="Features" value={status?.features?.toLocaleString() ?? "\u2014"} subtitle="Indicator rows" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Orderflow Data Status">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 motion-safe:transition-colors">
              <div className="flex items-center gap-2">
                <Activity className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Funding Rate</span>
              </div>
              <Badge label={status?.fundingAvailable ? "Available" : "Waiting"} variant={status?.fundingAvailable ? "success" : "warning"} />
            </div>
            <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 motion-safe:transition-colors">
              <div className="flex items-center gap-2">
                <Activity className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Open Interest</span>
              </div>
              <Badge label={status?.fundingAvailable ? "Available" : "Waiting"} variant={status?.fundingAvailable ? "success" : "warning"} />
            </div>
            <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 motion-safe:transition-colors">
              <div className="flex items-center gap-2">
                <Activity className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Liquidations</span>
              </div>
              <Badge label={status?.fundingAvailable ? "Available" : "Waiting"} variant={status?.fundingAvailable ? "success" : "warning"} />
            </div>
            <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 motion-safe:transition-colors">
              <div className="flex items-center gap-2">
                <Activity className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Long/Short Ratio</span>
              </div>
              <Badge label={status?.fundingAvailable ? "Streaming" : "Waiting"} variant={status?.fundingAvailable ? "success" : "warning"} />
            </div>
          </div>
        </Card>

        <Card title="Stream Health">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 motion-safe:transition-colors">
              <div className="flex items-center gap-2">
                <Clock className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Last Candle Saved</span>
              </div>
              <span className="text-sm font-bold">{status?.lastCandle ?? "\u2014"}</span>
            </div>
            <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 motion-safe:transition-colors">
              <div className="flex items-center gap-2">
                <Database className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">TimescaleDB Connection</span>
              </div>
              <Badge label="Connected" variant="success" />
            </div>
            <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 motion-safe:transition-colors">
              <div className="flex items-center gap-2">
                <HardDrive className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Candle Hypertable</span>
              </div>
              <Badge label="Active" variant="success" />
            </div>
            <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 motion-safe:transition-colors">
              <div className="flex items-center gap-2">
                <Cpu className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Feature Computation</span>
              </div>
              <Badge label="Auto" variant="success" />
            </div>
          </div>
        </Card>
      </div>

      <Card title="Configuration">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground text-xs">Exchange</span>
            <p className="font-bold">Bybit (Perpetuals)</p>
          </div>
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground text-xs">Symbols</span>
            <p className="font-bold">BTC, ETH, SOL, XRP, DOGE, BNB</p>
          </div>
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground text-xs">Timeframes</span>
            <p className="font-bold">15m, 1h, 4h</p>
          </div>
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground text-xs">Streams</span>
            <p className="font-bold">OHLCV + Funding + OI + Liq + LS</p>
          </div>
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground text-xs">Indicators</span>
            <p className="font-bold">EMA, RSI, ATR, ADX, Volatility</p>
          </div>
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground text-xs">Feature Set ID</span>
            <p className="font-bold">1</p>
          </div>
        </div>
      </Card>

      <Card title="CLI Quick Reference">
        <div className="flex flex-col gap-2 font-mono text-xs">
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground">Check candles: </span>
            <span className="text-primary">docker exec docker-timescaledb-1 psql -U freqtrade -d freqtrade -c "SELECT symbol, timeframe, count(*) FROM candles GROUP BY 1,2;"</span>
          </div>
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground">Check features: </span>
            <span className="text-primary">docker exec docker-timescaledb-1 psql -U freqtrade -d freqtrade -c "SELECT symbol, count(*) FROM feature_values WHERE funding_rate != 0 GROUP BY 1;"</span>
          </div>
          <div className="p-2 bg-muted/30 rounded">
            <span className="text-muted-foreground">Collector logs: </span>
            <span className="text-primary">docker compose -f docker/docker-compose.monitoring.yml logs go-collector --tail 20</span>
          </div>
        </div>
      </Card>
      </>
      )}
    </div>
  );
}
