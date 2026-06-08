import math

from .correlation import EdgeStore
from .types import EdgeFilter, FeatureInfo, LabelHorizon


class RegimeResult:
    def __init__(self, regime: str = "", corr: float = 0.0,
                 samples: int = 0) -> None:
        self.regime = regime
        self.corr = corr
        self.samples = samples


def run_regime(
    store: EdgeStore, flt: EdgeFilter, feature: FeatureInfo,
    horizon: LabelHorizon,
) -> list[RegimeResult]:
    rows = store.regime_correlations(
        feature.col, horizon.col,
        flt.symbol, flt.timeframe, flt.feature_set_id,
    )
    results = []
    for r in rows:
        results.append(RegimeResult(
            regime=r["regime"], corr=r["corr"], samples=r["samples"],
        ))
    return results


def regime_consistency(regimes: list[RegimeResult]) -> float:
    if len(regimes) == 0:
        return 0.0

    corrs = [r.corr for r in regimes if not math.isnan(r.corr)]
    if len(corrs) < 2:
        return 1.0

    max_c = max(corrs)
    min_c = min(corrs)
    return 1.0 - (max_c - min_c)
