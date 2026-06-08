import logging
from typing import Any

from .correlation import EdgeStore
from .decay import analyze_decay
from .quantile import run_quantile
from .ranking import ComponentScore, compute_ranking
from .regime_analysis import regime_consistency, run_regime
from .rolling import run_rolling
from .types import EdgeFilter, FeatureInfo, MetricResult, StudyConfig


logger = logging.getLogger(__name__)


class Study:
    def __init__(self, store: EdgeStore, cfg: StudyConfig) -> None:
        self.store = store
        self.cfg = cfg
        self.all_results: list[MetricResult] = []

    def run_all(self) -> None:
        count = self.store.count_features(self.cfg.feature_set_id)
        if count == 0:
            raise ValueError(
                f"feature_values is empty for feature_set_id={self.cfg.feature_set_id}"
            )

        for sym in self.cfg.symbols:
            for tf in self.cfg.timeframes:
                flt = EdgeFilter(
                    symbol=sym, timeframe=tf,
                    feature_set_id=self.cfg.feature_set_id,
                )
                logger.info(f"Running edge study: {sym} {tf}")
                self._run_for_filter(flt)

    def _run_for_filter(self, flt: EdgeFilter) -> None:
        feature_scores: list[ComponentScore] = []

        for feature in self.cfg.features:
            feature_scores.append(self._analyze_feature(flt, feature))

        ranked = compute_ranking(feature_scores)

        for i, fs in enumerate(ranked):
            self._add_result(
                fs.feature_name, "", "composite_score", fs.composite_score, 0,
                {"rank": i + 1, "symbol": flt.symbol, "timeframe": flt.timeframe},
            )
            logger.info(f"  Rank {i+1}: {fs.feature_name} (score={fs.composite_score:.3f})")

    def _analyze_feature(self, flt: EdgeFilter, feature: FeatureInfo) -> ComponentScore:
        cs = ComponentScore(feature_name=feature.name)

        horizon_corrs: list[float] = []
        stability_sum = 0.0
        stability_count = 0

        for h in self.cfg.label_horizons:
            p, sp, samples = self.store.correlation(
                feature.col, h.col,
                flt.symbol, flt.timeframe, flt.feature_set_id,
            )

            self._add_result(
                feature.name, h.name, "pearson", p, samples,
                {"symbol": flt.symbol, "timeframe": flt.timeframe},
            )
            self._add_result(
                feature.name, h.name, "spearman", sp, samples,
                {"symbol": flt.symbol, "timeframe": flt.timeframe},
            )

            avg_corr = (abs(p) + abs(sp)) / 2
            horizon_corrs.append(avg_corr)

            buckets = run_quantile(
                self.store, flt, feature, h, self.cfg.quantile_n_buckets,
            )
            if len(buckets) > 0:
                top = buckets[-1]
                bottom = buckets[0]

                self._add_result(
                    feature.name, h.name, "q_top_pf",
                    top["profit_factor"], top["trades"],
                )
                self._add_result(
                    feature.name, h.name, "q_top_wr",
                    top["win_rate"], top["trades"],
                )
                self._add_result(
                    feature.name, h.name, "q_bottom_pf",
                    bottom["profit_factor"], bottom["trades"],
                )
                self._add_result(
                    feature.name, h.name, "q_bottom_wr",
                    bottom["win_rate"], bottom["trades"],
                )

                if top["profit_factor"] > cs.quantile_pf:
                    cs.quantile_pf = top["profit_factor"]
                wr_delta = top["win_rate"] - bottom["win_rate"]
                if wr_delta > cs.quantile_wr_delta:
                    cs.quantile_wr_delta = wr_delta

            summaries = run_rolling(
                self.store, flt, feature, h, self.cfg.rolling_windows,
            )
            for rs in summaries:
                self._add_result(
                    feature.name, h.name, f"rolling_mean_{rs.window}",
                    rs.mean, 0,
                )
                self._add_result(
                    feature.name, h.name, f"rolling_std_{rs.window}",
                    rs.std, 0,
                )
                self._add_result(
                    feature.name, h.name, f"rolling_stability_{rs.window}",
                    rs.stability, 0,
                )
                stability_sum += rs.stability
                stability_count += 1

            regimes = run_regime(self.store, flt, feature, h)
            for r in regimes:
                self._add_result(
                    feature.name, h.name,
                    f"regime_{r.regime}", r.corr, r.samples,
                )
            rc = regime_consistency(regimes)
            if rc > cs.regime_consistency_val:
                cs.regime_consistency_val = rc

        if stability_count > 0:
            cs.rolling_stability = stability_sum / stability_count

        total_abs = sum(horizon_corrs)
        if len(horizon_corrs) > 0:
            cs.avg_abs_correlation = total_abs / len(horizon_corrs)

        decay = analyze_decay(horizon_corrs)
        self._add_result(feature.name, "", "decay_peak", decay.peak_corr, 0)
        self._add_result(feature.name, "", "decay_avg", decay.avg_corr, 0)
        self._add_result(feature.name, "", "decay_rate", decay.decay_rate, 0)
        self._add_result(feature.name, "", "decay_persistence", decay.persistence, 0)

        return cs

    def _add_result(self, feature_name: str, label_horizon: str,
                    metric_name: str, value: float, samples: int,
                    meta: dict[str, Any] | None = None) -> None:
        if meta is None:
            meta = {}
        self.all_results.append(MetricResult(
            feature_name=feature_name,
            label_horizon=label_horizon,
            metric_name=metric_name,
            metric_value=value,
            samples=samples,
            metadata=meta,
        ))

    def get_results(self) -> list[MetricResult]:
        return self.all_results

    def top_features(self, n: int = 5) -> list[str]:
        unique: dict[str, float] = {}
        for r in self.all_results:
            if r.metric_name == "composite_score":
                existing = unique.get(r.feature_name, -1.0)
                if r.metric_value > existing:
                    unique[r.feature_name] = r.metric_value

        pairs = sorted(unique.items(), key=lambda x: x[1], reverse=True)
        return [p[0] for p in pairs[:n]]
