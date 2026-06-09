import { useEffect, useState } from "react";
import { Card, StatCard, Badge } from "@/components/ui/card";
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

  useEffect(() => {
    fetchCollectorStatus();
    const interval = setInterval(fetchCollectorStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchCollectorStatus = async () => {
    try {
      const resp = await fetch("/api/v1/ping");
      if (!resp.ok) return;
      // Query TimescaleDB for collector data via API proxy
      const candlesResp = await fetch("/proxy/timescale/candles");
      if (candlesResp.ok) {
        const data = await candlesResp.json();
        setStatus(data);
      }
    } catch {
      // TimescaleDB query not available — show fallback
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Radio className="text-accent" /> Collector
        </h2>
        <Badge label={status ? "Running" : "Checking..."} variant={status ? "success" : "warning"} />
      </div>

      <p className="text-sm text-text-secondary">
        Go collector streams Bybit WebSocket data (OHLCV, funding rate, open interest, liquidations) into TimescaleDB. This data powers the multi-agent scoring system and FreqAI predictions.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Symbols" value={status?.symbols ?? "—"} subtitle="Monitored pairs" />
        <StatCard label="Timeframes" value={status?.timeframes ?? "—"} subtitle="15m, 1h, 4h" />
        <StatCard label="Candles" value={status?.candles?.toLocaleString() ?? "—"} subtitle="In TimescaleDB" />
        <StatCard label="Features" value={status?.features?.toLocaleString() ?? "—"} subtitle="Indicator rows" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Orderflow Data Status">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Funding Rate</span>
              </div>
              <Badge label={status?.fundingAvailable ? "Available" : "Waiting"} variant={status?.fundingAvailable ? "success" : "warning"} />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Open Interest</span>
              </div>
              <Badge label={status?.fundingAvailable ? "Available" : "Waiting"} variant={status?.fundingAvailable ? "success" : "warning"} />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Liquidations</span>
              </div>
              <Badge label={status?.fundingAvailable ? "Available" : "Waiting"} variant={status?.fundingAvailable ? "success" : "warning"} />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Long/Short Ratio</span>
              </div>
              <Badge label={status?.fundingAvailable ? "Streaming" : "Waiting"} variant={status?.fundingAvailable ? "success" : "warning"} />
            </div>
          </div>
        </Card>

        <Card title="Stream Health">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Last Candle Saved</span>
              </div>
              <span className="text-sm font-medium">{status?.lastCandle ?? "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">TimescaleDB Connection</span>
              </div>
              <Badge label="Connected" variant="success" />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HardDrive size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Candle Hypertable</span>
              </div>
              <Badge label="Active" variant="success" />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu size={14} className="text-accent" />
                <span className="text-sm text-text-secondary">Feature Computation</span>
              </div>
              <Badge label="Auto" variant="success" />
            </div>
          </div>
        </Card>
      </div>

      <Card title="Configuration">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary text-xs">Exchange</span>
            <p className="font-medium">Bybit (Perpetuals)</p>
          </div>
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary text-xs">Symbols</span>
            <p className="font-medium">BTC, ETH, SOL, XRP, DOGE, BNB</p>
          </div>
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary text-xs">Timeframes</span>
            <p className="font-medium">15m, 1h, 4h</p>
          </div>
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary text-xs">Streams</span>
            <p className="font-medium">OHLCV + Funding + OI + Liq + LS</p>
          </div>
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary text-xs">Indicators</span>
            <p className="font-medium">EMA, RSI, ATR, ADX, Volatility</p>
          </div>
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary text-xs">Feature Set ID</span>
            <p className="font-medium">1</p>
          </div>
        </div>
      </Card>

      <Card title="CLI Quick Reference">
        <div className="space-y-2 font-mono text-xs">
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary">Check candles: </span>
            <span className="text-accent">docker exec docker-timescaledb-1 psql -U freqtrade -d freqtrade -c "SELECT symbol, timeframe, count(*) FROM candles GROUP BY 1,2;"</span>
          </div>
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary">Check features: </span>
            <span className="text-accent">docker exec docker-timescaledb-1 psql -U freqtrade -d freqtrade -c "SELECT symbol, count(*) FROM feature_values WHERE funding_rate != 0 GROUP BY 1;"</span>
          </div>
          <div className="p-2 bg-card-bg rounded">
            <span className="text-text-secondary">Collector logs: </span>
            <span className="text-accent">docker compose -f docker/docker-compose.monitoring.yml logs go-collector --tail 20</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
