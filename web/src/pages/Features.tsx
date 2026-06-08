import { useEffect, useState } from "react";
import { Card, StatCard } from "@/components/ui/card";
import { api, type StrategyListResponse, type FreqAIModelListResponse } from "@/lib/api";
import { Brain, Cpu, Zap, Settings, BarChart3, TrendingUp, BookOpen, Sparkles } from "lucide-react";

export default function Features() {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [freqaimodels, setFreqaimodels] = useState<string[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>("");
  const [strategyDetails, setStrategyDetails] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.strategies().then((r: StrategyListResponse) => {
      setStrategies(r.strategies);
      if (r.strategies.length > 0) setSelectedStrategy(r.strategies[0]);
    }).catch(console.error);
    api.freqaimodels().then((r: FreqAIModelListResponse) => setFreqaimodels(r.freqaimodels)).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      setLoading(true);
      fetch(`/api/v1/strategy/${selectedStrategy}`)
        .then(r => r.json())
        .then(d => setStrategyDetails(d))
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [selectedStrategy]);

  const params = strategyDetails?.params as Array<{
    param_type: string;
    name: string;
    value: number | string | boolean;
    low?: number;
    high?: number;
    decimals?: number;
    opt_range?: Array<unknown>;
  }> | undefined;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Sparkles className="text-[--color-accent]" /> Features
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[--color-text-secondary]">{strategies.length} strategies</span>
          <span className="text-xs text-[--color-text-secondary]">{freqaimodels.length} models</span>
        </div>
      </div>

      {/* Strategy + Model Registry */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Strategy Registry">
          <div className="space-y-2">
            {strategies.map((s) => (
              <button
                key={s}
                onClick={() => setSelectedStrategy(s)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedStrategy === s
                    ? "bg-[--color-accent]/10 text-[--color-accent] border border-[--color-accent]/30"
                    : "bg-[--color-card-bg] border border-[--color-card-border] text-[--color-text-primary] hover:border-[--color-accent]/30"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Zap size={14} />
                  <span className="font-medium">{s}</span>
                </div>
              </button>
            ))}
            {strategies.length === 0 && (
              <p className="text-sm text-[--color-text-secondary]">No strategies found</p>
            )}
          </div>
        </Card>

        <Card title="FreqAI Model Registry">
          <div className="space-y-2">
            {freqaimodels.map((m) => (
              <div key={m} className="flex items-center gap-2 px-3 py-2 bg-[--color-card-bg] rounded-lg border border-[--color-card-border] text-sm">
                <Brain size={14} className="text-[--color-accent]" />
                <span className="font-medium">{m}</span>
              </div>
            ))}
            {freqaimodels.length === 0 && (
              <p className="text-sm text-[--color-text-secondary]">No FreqAI models found</p>
            )}
          </div>
        </Card>
      </div>

      {/* Strategy Parameters */}
      {selectedStrategy && (
        <Card title={`Strategy Parameters: ${selectedStrategy}`}>
          {loading ? (
            <div className="flex items-center justify-center py-8 text-sm text-[--color-text-secondary]">
              <Cpu size={16} className="animate-spin mr-2" /> Loading strategy details...
            </div>
          ) : strategyDetails ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard label="Strategy" value={strategyDetails.strategy as string} />
                <StatCard label="Timeframe" value={strategyDetails.timeframe as string ?? "—"} />
                <StatCard label="Parameters" value={params?.length ?? 0} />
                <StatCard label="Code Length" value={`${(strategyDetails.code as string)?.length ?? 0} chars`} />
              </div>

              <div className="border border-[--color-card-border] rounded-lg overflow-auto">
                <table className="w-full text-sm">
                  <thead className="bg-[--color-card-bg] sticky top-0">
                    <tr className="text-left text-[--color-text-secondary] border-b border-[--color-card-border]">
                      <th className="px-3 py-2">Parameter</th>
                      <th className="px-3 py-2">Type</th>
                      <th className="px-3 py-2">Value</th>
                      <th className="px-3 py-2">Range</th>
                      <th className="px-3 py-2">Optimizable</th>
                    </tr>
                  </thead>
                  <tbody>
                    {params?.map((p, i) => (
                      <tr key={i} className="border-b border-[--color-card-border]/30">
                        <td className="px-3 py-2 font-medium">{p.name}</td>
                        <td className="px-3 py-2 text-[--color-text-secondary]">{p.param_type}</td>
                        <td className="px-3 py-2 text-[--color-accent] font-medium">
                          {typeof p.value === "number" ? p.value.toFixed(p.decimals ?? 4) : String(p.value)}
                        </td>
                        <td className="px-3 py-2 text-[--color-text-secondary]">
                          {p.low !== undefined && p.high !== undefined ? `[${p.low}, ${p.high}]` : "—"}
                        </td>
                        <td className="px-3 py-2">
                          <span className={`text-xs px-2 py-0.5 rounded ${p.opt_range ? "bg-[--color-accent]/10 text-[--color-accent]" : "bg-gray-800 text-gray-400"}`}>
                            {p.opt_range ? "Yes" : "No"}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {(!params || params.length === 0) && (
                      <tr><td colSpan={5} className="px-3 py-4 text-center text-[--color-text-secondary]">No parameters</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="text-sm text-[--color-text-secondary]">Failed to load strategy details</p>
          )}
        </Card>
      )}

      {/* Edge Study Section */}
      <Card title="Edge Study">
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-[--color-text-secondary]">
            <BookOpen size={14} />
            <span>Edge study analyzes feature correlations and predictive power for each symbol/timeframe combination.</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-4 bg-[--color-card-bg] rounded-lg border border-[--color-card-border]">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 size={16} className="text-[--color-accent]" />
                <span className="text-sm font-medium">Correlation Analysis</span>
              </div>
              <p className="text-xs text-[--color-text-secondary]">
                Measures feature-to-target correlations across multiple timeframes.
              </p>
            </div>
            <div className="p-4 bg-[--color-card-bg] rounded-lg border border-[--color-card-border]">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={16} className="text-[--color-accent]" />
                <span className="text-sm font-medium">Feature Ranking</span>
              </div>
              <p className="text-xs text-[--color-text-secondary]">
                Ranks features by predictive power using mutual information and correlation.
              </p>
            </div>
            <div className="p-4 bg-[--color-card-bg] rounded-lg border border-[--color-card-border]">
              <div className="flex items-center gap-2 mb-2">
                <Settings size={16} className="text-[--color-accent]" />
                <span className="text-sm font-medium">Label Engineering</span>
              </div>
              <p className="text-xs text-[--color-text-secondary]">
                Configures forward-looking labels with horizon and barrier settings.
              </p>
            </div>
          </div>
          <div className="p-3 bg-[--color-accent]/5 rounded-lg border border-[--color-accent]/20 text-sm">
            <span className="text-[--color-accent] font-medium">CLI Command: </span>
            <code className="text-[--color-text-secondary]">freqtrade edge-study --symbol BTC/USDT --timeframe 1h --output edge_study_results</code>
          </div>
        </div>
      </Card>
    </div>
  );
}
