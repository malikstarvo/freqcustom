import { useEffect, useState } from "react";
import { Card, StatCard } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Empty } from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { api, type StrategyListResponse, type FreqAIModelListResponse } from "@/lib/api";
import { cn } from "@/lib/utils";
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
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <Sparkles className="size-5 text-primary" aria-hidden="true" /> Features
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{strategies.length} strategies</span>
          <span className="text-xs text-muted-foreground">{freqaimodels.length} models</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Strategy Registry">
          <div className="flex flex-col gap-2">
            {strategies.map((s) => (
              <Button
                key={s}
                onClick={() => setSelectedStrategy(s)}
                variant={selectedStrategy === s ? "default" : "outline"}
                className="w-full justify-start text-left"
                size="sm"
              >
                <div className="flex items-center gap-2">
                  <Zap data-icon="inline-start" aria-hidden="true" />
                  <span className="font-bold">{s}</span>
                </div>
              </Button>
            ))}
            {strategies.length === 0 && (
              <Empty icon={Zap} title="No Strategies" description="No strategies found" />
            )}
          </div>
        </Card>

        <Card title="FreqAI Model Registry">
          <div className="flex flex-col gap-2">
            {freqaimodels.map((m) => (
              <div key={m} className="flex items-center gap-2 px-3 py-2.5 bg-muted/30 rounded-lg border border-border/50 text-sm hover:bg-muted/30 motion-safe:transition-colors">
                <Brain className="size-4 text-primary" aria-hidden="true" />
                <span className="font-bold">{m}</span>
              </div>
            ))}
            {freqaimodels.length === 0 && (
              <Empty icon={Brain} title="No FreqAI Models" description="No FreqAI models found" />
            )}
          </div>
        </Card>
      </div>

      {selectedStrategy && (
        <Card title={`Strategy Parameters: ${selectedStrategy}`}>
          {loading ? (
            <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
              <Cpu className="size-4 animate-spin mr-2" aria-hidden="true" /> Loading strategy details\u2026
            </div>
          ) : strategyDetails ? (
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="Strategy" value={strategyDetails.strategy as string} />
                <StatCard label="Timeframe" value={strategyDetails.timeframe as string ?? "\u2014"} />
                <StatCard label="Parameters" value={params?.length ?? 0} />
                <StatCard label="Code Length" value={`${(strategyDetails.code as string)?.length ?? 0} chars`} />
              </div>

              <div className="border border-border/50 rounded-lg overflow-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/30 sticky top-0">
                    <tr>
                      <th className="px-3 py-2.5 text-left text-muted-foreground font-medium">Parameter</th>
                      <th className="px-3 py-2.5 text-left text-muted-foreground font-medium">Type</th>
                      <th className="px-3 py-2.5 text-left text-muted-foreground font-medium">Value</th>
                      <th className="px-3 py-2.5 text-left text-muted-foreground font-medium">Range</th>
                      <th className="px-3 py-2.5 text-left text-muted-foreground font-medium">Optimizable</th>
                    </tr>
                  </thead>
                  <tbody>
                    {params?.map((p, i) => (
                      <tr key={i} className="hover:bg-muted/30 motion-safe:transition-colors">
                        <td className="px-3 py-2.5 font-bold">{p.name}</td>
                        <td className="px-3 py-2.5 text-muted-foreground">{p.param_type}</td>
                        <td className="px-3 py-2.5 text-primary font-bold">
                          {typeof p.value === "number" ? p.value.toFixed(p.decimals ?? 4) : String(p.value)}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {p.low !== undefined && p.high !== undefined ? `[${p.low}, ${p.high}]` : "\u2014"}
                        </td>
                        <td className="px-3 py-2.5">
                          <span className={cn("text-xs px-2 py-0.5 rounded-md", p.opt_range ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground")}>
                            {p.opt_range ? "Yes" : "No"}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {(!params || params.length === 0) && (
                      <tr><td colSpan={5} className="px-3 py-4 text-center text-muted-foreground">No parameters</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Failed to load strategy details</p>
          )}
        </Card>
      )}

      <Card title="Edge Study">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <BookOpen className="size-4" aria-hidden="true" />
            <span>Edge study analyzes feature correlations and predictive power for each symbol/timeframe combination.</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm font-bold">Correlation Analysis</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Measures feature-to-target correlations across multiple timeframes.
              </p>
            </div>
            <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm font-bold">Feature Ranking</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Ranks features by predictive power using mutual information and correlation.
              </p>
            </div>
            <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
              <div className="flex items-center gap-2 mb-2">
                <Settings className="size-4 text-primary" aria-hidden="true" />
                <span className="text-sm font-bold">Label Engineering</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Configures forward-looking labels with horizon and barrier settings.
              </p>
            </div>
          </div>
          <div className="p-3 bg-primary/5 rounded-lg border border-primary/20 text-sm">
            <span className="text-primary font-bold">CLI Command: </span>
            <code className="text-muted-foreground font-mono">freqtrade edge-study --symbol BTC/USDT --timeframe 1h --output edge_study_results</code>
          </div>
        </div>
      </Card>
    </div>
  );
}
