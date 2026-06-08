class ComponentScore:
    def __init__(self, feature_name: str = "", quantile_pf: float = 0.0,
                 quantile_wr_delta: float = 0.0, rolling_stability: float = 0.0,
                 regime_consistency_val: float = 0.0,
                 avg_abs_correlation: float = 0.0,
                 composite_score: float = 0.0) -> None:
        self.feature_name = feature_name
        self.quantile_pf = quantile_pf
        self.quantile_wr_delta = quantile_wr_delta
        self.rolling_stability = rolling_stability
        self.regime_consistency_val = regime_consistency_val
        self.avg_abs_correlation = avg_abs_correlation
        self.composite_score = composite_score


def compute_ranking(scores: list[ComponentScore]) -> list[ComponentScore]:
    if not scores:
        return []

    ranked = [ComponentScore(
        feature_name=s.feature_name,
        quantile_pf=s.quantile_pf,
        quantile_wr_delta=s.quantile_wr_delta,
        rolling_stability=s.rolling_stability,
        regime_consistency_val=s.regime_consistency_val,
        avg_abs_correlation=s.avg_abs_correlation,
    ) for s in scores]

    def _ranks(getter) -> list[int]:
        vals = [getter(s) for s in ranked]
        order = sorted(range(len(vals)), key=lambda i: vals[i], reverse=True)
        out = [0] * len(vals)
        for rank, idx in enumerate(order):
            out[idx] = rank + 1
        return out

    pf_ranks = _ranks(lambda s: s.quantile_pf)
    wr_ranks = _ranks(lambda s: s.quantile_wr_delta)
    stability_ranks = _ranks(lambda s: s.rolling_stability)
    regime_ranks = _ranks(lambda s: s.regime_consistency_val)
    corr_ranks = _ranks(lambda s: s.avg_abs_correlation)

    n = len(ranked)
    if n <= 1:
        for s in ranked:
            s.composite_score = 1.0
        return ranked

    for i in range(n):
        pf_score = 1.0 - (pf_ranks[i] - 1) / (n - 1)
        wr_score = 1.0 - (wr_ranks[i] - 1) / (n - 1)
        stability_score = 1.0 - (stability_ranks[i] - 1) / (n - 1)
        regime_score = 1.0 - (regime_ranks[i] - 1) / (n - 1)
        corr_score = 1.0 - (corr_ranks[i] - 1) / (n - 1)

        ranked[i].composite_score = (
            0.40 * pf_score + 0.25 * wr_score + 0.15 * stability_score
            + 0.10 * regime_score + 0.10 * corr_score
        )

    ranked.sort(key=lambda s: s.composite_score, reverse=True)
    return ranked
