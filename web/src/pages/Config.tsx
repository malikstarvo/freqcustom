import { useEffect, useState } from "react";
import { Card, Badge } from "@/components/ui/card";
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
      // Refresh config
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
      <div className="space-y-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Settings className="text-accent" /> Configuration
        </h2>
        <p className="text-sm text-text-secondary">Loading configuration...</p>
      </div>
    );
  }

  const Section = ({ title, icon, children }: {
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
  }) => (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-text-secondary uppercase tracking-wide">
        {icon}
        {title}
      </div>
      <div className="space-y-2">
        {children}
      </div>
    </div>
  );

  const Row = ({ label, value, highlight = false }: { label: string; value: string | number; highlight?: boolean }) => (
    <div className="flex items-center justify-between py-1.5 px-3 bg-card-bg rounded border border-card-border/30">
      <span className="text-xs text-text-secondary">{label}</span>
      <span className={`text-sm font-medium ${highlight ? "text-accent" : "text-text-primary"}`}>
        {value}
      </span>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Settings className="text-accent" /> Configuration
        </h2>
        <div className="flex items-center gap-3">
          <Badge label={config.state} variant={config.state === "running" ? "success" : "default"} />
          <Badge label={config.dry_run ? "Dry Run" : "Live"} variant={config.dry_run ? "warning" : "danger"} />
          <button
            onClick={handleReload}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 bg-accent hover:bg-accent-hover text-[#0f1119] rounded-lg text-xs font-semibold disabled:opacity-50"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Reload
          </button>
        </div>
      </div>

      {reloadStatus && (
        <div className={`p-3 rounded-lg text-sm ${
          reloadStatus === "reloaded" ? "bg-green-950/50 text-green-400 border border-green-500/30" : "bg-red-950/50 text-red-400 border border-red-500/30"
        }`}>
          {reloadStatus}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Bot Info */}
        <Card>
          <Section title="Bot Info" icon={<Server size={14} />}>
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

        {/* Exchange */}
        <Card>
          <Section title="Exchange" icon={<Globe size={14} />}>
            <Row label="Exchange" value={config.exchange} />
            <Row label="Stake Currency" value={config.stake_currency} />
            <Row label="Stake Amount" value={config.stake_amount} />
            <Row label="Available Capital" value={config.available_capital ?? "—"} />
            <Row label="Max Open Trades" value={config.max_open_trades} />
            <Row label="Position Adjustment" value={config.position_adjustment_enable ? "Enabled" : "Disabled"} />
            <Row label="Max Entry Adjustments" value={config.max_entry_position_adjustment} />
          </Section>
        </Card>

        {/* Strategy */}
        <Card>
          <Section title="Strategy" icon={<Zap size={14} />}>
            <Row label="Strategy" value={config.strategy ?? "—"} highlight />
            <Row label="Timeframe" value={config.timeframe ?? "—"} />
            <Row label="TF (ms)" value={config.timeframe_ms} />
            <Row label="Force Entry" value={config.force_entry_enable ? "Enabled" : "Disabled"} />
            <Row label="Custom Stoploss" value={config.use_custom_stoploss ? "Yes" : "No"} />
          </Section>
        </Card>

        {/* Risk */}
        <Card>
          <Section title="Risk Management" icon={<Shield size={14} />}>
            <Row label="Stoploss" value={config.stoploss !== null ? `${(config.stoploss * 100).toFixed(1)}%` : "—"} />
            <Row label="Stoploss on Exchange" value={config.stoploss_on_exchange ? "Yes" : "No"} />
            <Row label="Trailing Stop" value={config.trailing_stop ? "Enabled" : "Disabled"} />
            <Row label="Trailing Positive" value={config.trailing_stop_positive !== null ? `${(config.trailing_stop_positive * 100).toFixed(1)}%` : "—"} />
            <Row label="Trailing Offset" value={config.trailing_stop_positive_offset !== null ? `${(config.trailing_stop_positive_offset * 100).toFixed(1)}%` : "—"} />
            <Row label="Only Offset Reached" value={config.trailing_only_offset_is_reached ? "Yes" : "No"} />
          </Section>
        </Card>

        {/* ROI & Pricing */}
        <Card>
          <Section title="ROI & Pricing" icon={<TrendingUp size={14} />}>
            <Row label="Minimal ROI" value={JSON.stringify(config.minimal_roi)} />
            <Row label="Entry Pricing" value={JSON.stringify(config.entry_pricing)} />
            <Row label="Exit Pricing" value={JSON.stringify(config.exit_pricing)} />
          </Section>
        </Card>

        {/* FreqAI */}
        <Card>
          <Section title="FreqAI" icon={<Brain size={14} />}>
            <Row label="Margin Mode" value={config.margin_mode} />
            <Row label="Unfilled Timeout" value={config.unfilledtimeout ? JSON.stringify(config.unfilledtimeout) : "—"} />
            <Row label="Order Types" value={config.order_types ? JSON.stringify(config.order_types) : "—"} />
            <Row label="Strategy Version" value={config.strategy_version ?? "—"} />
          </Section>
        </Card>
      </div>

      {/* Raw JSON toggle */}
      <Card title="Raw Configuration">
        <pre className="text-xs font-mono overflow-auto max-h-[50vh] bg-card-bg p-4 rounded border border-card-border text-text-secondary">
          {JSON.stringify(config, null, 2)}
        </pre>
      </Card>
    </div>
  );
}
