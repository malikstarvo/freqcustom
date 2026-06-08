from .correlation import EdgeStore
from .types import EdgeFilter, FeatureInfo, LabelHorizon


def run_quantile(
    store: EdgeStore, flt: EdgeFilter, feature: FeatureInfo,
    horizon: LabelHorizon, n_buckets: int,
) -> list[dict]:
    buckets = store.quantiles(
        feature.col, horizon.col,
        flt.symbol, flt.timeframe, flt.feature_set_id, n_buckets,
    )
    return buckets if buckets else []
