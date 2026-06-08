import { useEffect, useState } from "react";
import { Card, StatCard } from "@/components/ui/card";
import { Brain, BarChart3, TrendingUp, Cpu } from "lucide-react";

type FeatureImportance = {
  feature: string;
  importance: number;
};

type ModelStatus = {
  model: string;
  identifier: string;
  last_trained: string;
  train_period_days: number;
  features: string[];
  feature_count: number;
  cv_auc_mean: number;
  cv_auc_std: number;
  best_params: Record<string, number | string>;
};

const MOCK_FEATURES: FeatureImportance[] = [
  { feature: "adx14", importance: 0.185 },
  { feature: "rsi14", importance: 0.152 },
  { feature: "volatility14", importance: 0.131 },
  { feature: "volume_ema20", importance: 0.118 },
  { feature: "funding_rate", importance: 0.098 },
  { feature: "oi_delta_1_pct", importance: 0.082 },
  { feature: "ema50", importance: 0.064 },
  { feature: "atr14", importance: 0.052 },
  { feature: "ls_ratio", importance: 0.041 },
  { feature: "ema200", importance: 0.035 },
  { feature: "liq_long_usd", importance: 0.021 },
  { feature: "liq_short_usd", importance: 0.012 },
  { feature: "ema20", importance: 0.009 },
];

const MOCK_STATUS: ModelStatus = {
  model: "XGBoostGridSearchModel",
  identifier: "multi_agent_v1",
  last_trained: new Date().toISOString(),
  train_period_days: 90,
  features: MOCK_FEATURES.map(f => f.feature),
  feature_count: 13,
  cv_auc_mean: 0.723,
  cv_auc_std: 0.031,
  best_params: {
    max_depth: 5,
    learning_rate: 0.05,
    n_estimators: 500,
    subsample: 0.8,
    colsample_bytree: 0.8,
  },
};

export default function ModelPage() {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [features, setFeatures] = useState<FeatureImportance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const resp = await fetch("/api/v1/freqai/model_status");
        if (resp.ok) {
          const data = await resp.json();
          setStatus(data);
          return;
        }
      } catch {}

      try {
        const resp = await fetch("/api/v1/freqai/feature_importance");
        if (resp.ok) {
          const data = await resp.json();
          setFeatures(data);
        }
      } catch {
        setFeatures(MOCK_FEATURES);
        setStatus(MOCK_STATUS);
      }
      setLoading(false);
    };

    load();
  }, []);

  const displayStatus = status || MOCK_STATUS;
  const displayFeatures = features.length > 0 ? features : MOCK_FEATURES;
  const maxImp = Math.max(...displayFeatures.map(f => f.importance), 0.01);

  const barColor = (rank: number) => {
    if (rank <= 3) return "var(--color-profit)";
    if (rank <= 6) return "var(--color-accent)";
    return "var(--color-text-secondary)";
  };

  const aucColor = (displayStatus.cv_auc_mean >= 0.70 ? "var(--color-profit)" :
                    displayStatus.cv_auc_mean >= 0.60 ? "var(--color-warning)" : "var(--color-loss)");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Brain className="text-[--color-accent]" />
          Model Monitor
        </h2>
        <p className="text-sm text-[--color-text-secondary] mt-1">
          {displayStatus.identifier} &middot; {displayStatus.model}
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Model"
          value={displayStatus.model.replace("Model", "").replace("XGBoost", "XGB")}
          subtitle={`ID: ${displayStatus.identifier}`}
        />
        <StatCard
          label="CV AUC (Mean)"
          value={displayStatus.cv_auc_mean.toFixed(3)}
          subtitle={`±${displayStatus.cv_auc_std.toFixed(3)}`}
        />
        <StatCard
          label="Features"
          value={displayStatus.feature_count}
          subtitle={displayStatus.train_period_days ? `${displayStatus.train_period_days}d training` : ""}
        />
        <StatCard
          label="Last Trained"
          value={displayStatus.last_trained ? new Date(displayStatus.last_trained).toLocaleDateString() : "—"}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card title="Feature Importance">
          <div className="space-y-2">
            {displayFeatures.map((f, i) => (
              <div key={f.feature}>
                <div className="flex justify-between text-xs mb-0.5">
                  <span className="text-[--color-text-secondary]">{f.feature}</span>
                  <span className="font-mono">{(f.importance * 100).toFixed(1)}%</span>
                </div>
                <div className="bar">
                  <div
                    className="bar-fill"
                    style={{
                      width: `${(f.importance / maxImp) * 100}%`,
                      background: barColor(i),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <style>{`
            .bar { height: 6px; background: #2a2d3e; border-radius: 3px; overflow: hidden; margin-bottom: 4px; }
            .bar-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
          `}</style>
        </Card>

        <Card title="AUC Score">
          <div className="flex flex-col items-center justify-center py-6">
            <div className="relative w-40 h-40">
              <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                <circle cx="50" cy="50" r="42" fill="none" stroke="#2a2d3e" strokeWidth="8" />
                <circle
                  cx="50" cy="50" r="42" fill="none"
                  stroke={aucColor}
                  strokeWidth="8"
                  strokeDasharray={`${displayStatus.cv_auc_mean * 2.64} ${264 - displayStatus.cv_auc_mean * 2.64}`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold" style={{ color: aucColor }}>
                  {displayStatus.cv_auc_mean.toFixed(3)}
                </span>
                <span className="text-xs text-[--color-text-secondary] mt-0.5">ROC-AUC</span>
              </div>
            </div>
            <p className="text-xs text-[--color-text-secondary] mt-2">
              Threshold for trade gate: &ge; 0.45 → PASS
            </p>
          </div>
        </Card>
      </div>

      <Card title="Grid Search Best Parameters">
        <div className="grid grid-cols-4 gap-4">
          {Object.entries(displayStatus.best_params).map(([key, val]) => (
            <div key={key} className="bg-gray-800/50 rounded-lg p-3">
              <div className="text-xs text-[--color-text-secondary] uppercase mb-1">{key}</div>
              <div className="text-lg font-mono font-bold text-[--color-accent]">
                {typeof val === "number" && val < 1 ? val.toFixed(2) : val}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Training Pipeline">
        <div className="space-y-3">
          <div className="flex items-center gap-4 py-2 border-b border-[--color-card-border]">
            <span className="w-8 h-8 rounded-full bg-[--color-profit]/20 text-[--color-profit] flex items-center justify-center text-sm font-bold">1</span>
            <div>
              <span className="font-medium">Edge Study</span>
              <p className="text-xs text-[--color-text-secondary]">Rank 13 features by predictive power (pearson, quantile PF, stability)</p>
            </div>
            <span className="ml-auto text-xs text-[--color-text-secondary]">freqtrade edge-study</span>
          </div>
          <div className="flex items-center gap-4 py-2 border-b border-[--color-card-border]">
            <span className="w-8 h-8 rounded-full bg-[--color-accent]/20 text-[--color-accent] flex items-center justify-center text-sm font-bold">2</span>
            <div>
              <span className="font-medium">Grid Search Training</span>
              <p className="text-xs text-[--color-text-secondary]">5 param grid × 3-fold CV = 15 fits per iteration. Best AUC selected.</p>
            </div>
            <span className="ml-auto text-xs text-[--color-text-secondary]">GridSearchCV</span>
          </div>
          <div className="flex items-center gap-4 py-2">
            <span className="w-8 h-8 rounded-full bg-[--color-warning]/20 text-[--color-warning] flex items-center justify-center text-sm font-bold">3</span>
            <div>
              <span className="font-medium">Trade Gate</span>
              <p className="text-xs text-[--color-text-secondary]">ML probability ≥ 0.45 required for trade execution</p>
            </div>
            <span className="ml-auto text-xs text-[--color-text-secondary]">MetaModelProb</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
