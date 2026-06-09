import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Empty } from "@/components/ui/empty";
import { cn } from "@/lib/utils";
import { api, type ShowConfig } from "@/lib/api";
import { Settings, RefreshCw, Globe, Shield, Zap, Server, Brain, TrendingUp } from "lucide-react";

export default function Config() {
  const [config, setConfig] = useState<ShowConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [reloadStatus, setReloadStatus] = useState<string | null>(null);

  useEffect(() => {
    api.showConfig().then(setConfig).catch(console.error);
  }, []);

  const handleReload = async () => {
    setLoading(true);
    setReloadStatus(null);
    try {
      const resp = await api.reloadConfig();
      setReloadStatus(resp.status);
      const updated = await api.showConfig();
      setConfig(updated);
    } catch (e: any) {
      setReloadStatus(e.message || "Failed to reload");
    } finally {
      setLoading(false);
    }
  };

  if (!config) {
    return (
      <div className="flex flex-col gap-6">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <Settings className="size-5 text-primary" aria-hidden="true" /> Configuration
        </h2>
        <Empty title="Loading" description="Loading configuration\u2026" />
      </div>
    );
  }

  const Section = ({ title, icon, children }: {
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
  }) => (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
        {icon}
        {title}
      </div>
      <div className="flex flex-col gap-2">
        {children}
      </div>
    </div>
  );

  const Row = ({ label, value, highlight = false }: { label: string; value: string | number; highlight?: boolean }) => (
    <div className="flex items-center justify-between py-1.5 px-3 bg-muted/30 rounded border border-border/50">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={cn("text-sm font-bold", highlight ? "text-primary" : "")}>
        {value}
      </span>
    </div>
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <Settings className="size-5 text-primary" aria-hidden="true" /> Configuration
        </h2>
        <div className="flex items-center gap-3">
          <Badge label={config.state} variant={config.state === "running" ? "success" : "default"} />
          <Badge label={config.dry_run ? "Dry Run" : "Live"} variant={config.dry_run ? "warning" : "danger"} />
          <Button
            onClick={handleReload}
            disabled={loading}
            variant="default"
            size="sm"
          >
            <RefreshCw aria-hidden="true" className={loading ? "animate-spin" : ""} /> Reload
          </Button>
        </div>
      </div>

      {reloadStatus && (
        <Alert variant={reloadStatus === "reloaded" ? "success" : "destructive"}>
          <AlertDescription>{reloadStatus}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <Section title="Bot Info" icon={<Server className="size-4" aria-hidden="true" />}>
            <Row label="Name" value={config.bot_name} />
            <Row label="Version" value={config.version} />
            <Row label="API Version" value={config.api_version} />
            <Row label="State" value={config.state} highlight />
            <Row label="Run Mode" value={config.runmode} />
            <Row label="Trading Mode" value={config.trading_mode} />
            <Row label="Short Allowed" value={config.short_allowed ? "Yes" : "No"} />
            <Row label="Demo Trading" value={config.demo_trading ? "Yes" : "No"} />
          </Section>
        </Card>

        <Card>
          <Section title="Exchange" icon={<Globe className="size-4" aria-hidden="true" />}>
            <Row label="Exchange" value={config.exchange} />
            <Row label="Stake Currency" value={config.stake_currency} />
            <Row label="Stake Amount" value={config.stake_amount} />
            <Row label="Available Capital" value={config.available_capital ?? "\u2014"} />
            <Row label="Max Open Trades" value={config.max_open_trades} />
            <Row label="Position Adjustment" value={config.position_adjustment_enable ? "Enabled" : "Disabled"} />
            <Row label="Max Entry Adjustments" value={config.max_entry_position_adjustment} />
          </Section>
        </Card>

        <Card>
          <Section title="Strategy" icon={<Zap className="size-4" aria-hidden="true" />}>
            <Row label="Strategy" value={config.strategy ?? "\u2014"} highlight />
            <Row label="Timeframe" value={config.timeframe ?? "\u2014"} />
            <Row label="TF (ms)" value={config.timeframe_ms} />
            <Row label="Force Entry" value={config.force_entry_enable ? "Enabled" : "Disabled"} />
            <Row label="Custom Stoploss" value={config.use_custom_stoploss ? "Yes" : "No"} />
          </Section>
        </Card>

        <Card>
          <Section title="Risk Management" icon={<Shield className="size-4" aria-hidden="true" />}>
            <Row label="Stoploss" value={config.stoploss !== null ? `${(config.stoploss * 100).toFixed(1)}%` : "\u2014"} />
            <Row label="Stoploss on Exchange" value={config.stoploss_on_exchange ? "Yes" : "No"} />
            <Row label="Trailing Stop" value={config.trailing_stop ? "Enabled" : "Disabled"} />
            <Row label="Trailing Positive" value={config.trailing_stop_positive !== null ? `${(config.trailing_stop_positive * 100).toFixed(1)}%` : "\u2014"} />
            <Row label="Trailing Offset" value={config.trailing_stop_positive_offset !== null ? `${(config.trailing_stop_positive_offset * 100).toFixed(1)}%` : "\u2014"} />
            <Row label="Only Offset Reached" value={config.trailing_only_offset_is_reached ? "Yes" : "No"} />
          </Section>
        </Card>

        <Card>
          <Section title="ROI &amp; Pricing" icon={<TrendingUp className="size-4" aria-hidden="true" />}>
            <Row label="Minimal ROI" value={JSON.stringify(config.minimal_roi)} />
            <Row label="Entry Pricing" value={JSON.stringify(config.entry_pricing)} />
            <Row label="Exit Pricing" value={JSON.stringify(config.exit_pricing)} />
          </Section>
        </Card>

        <Card>
          <Section title="FreqAI" icon={<Brain className="size-4" aria-hidden="true" />}>
            <Row label="Margin Mode" value={config.margin_mode} />
            <Row label="Unfilled Timeout" value={config.unfilledtimeout ? JSON.stringify(config.unfilledtimeout) : "\u2014"} />
            <Row label="Order Types" value={config.order_types ? JSON.stringify(config.order_types) : "\u2014"} />
            <Row label="Strategy Version" value={config.strategy_version ?? "\u2014"} />
          </Section>
        </Card>
      </div>

      <Card title="Raw Configuration">
        <pre className="text-xs font-mono overflow-auto max-h-[50vh] bg-muted/30 p-4 rounded border border-border/50 text-muted-foreground">
          {JSON.stringify(config, null, 2)}
        </pre>
      </Card>
    </div>
  );
}
