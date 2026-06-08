import math

from .correlation import EdgeStore
from .types import EdgeFilter, FeatureInfo, LabelHorizon


class RollingSummary:
    def __init__(self, window: int = 0, mean: float = 0.0,
                 std: float = 0.0, stability: float = 0.0) -> None:
        self.window = window
        self.mean = mean
        self.std = std
        self.stability = stability


def run_rolling(
    store: EdgeStore, flt: EdgeFilter, feature: FeatureInfo,
    horizon: LabelHorizon, windows: list[int],
) -> list[RollingSummary]:
    summaries: list[RollingSummary] = []

    for w in windows:
        points = store.rolling_correlation(
            feature.col, horizon.col,
            flt.symbol, flt.timeframe, flt.feature_set_id, w,
        )

        corr_sum = 0.0
        corr_sq_sum = 0.0
        n = 0
        overall_sign = 0.0

        for p in points:
            c = p["corr"]
            if math.isnan(c):
                continue
            corr_sum += c
            corr_sq_sum += c * c
            n += 1
            overall_sign += c

        if n == 0:
            summaries.append(RollingSummary(window=w))
            continue

        mean = corr_sum / n
        variance = corr_sq_sum / n - mean * mean
        if variance < 0:
            variance = 0.0
        std = math.sqrt(variance)

        same_sign_count = 0
        for p in points:
            c = p["corr"]
            if math.isnan(c):
                continue
            if (c >= 0 and overall_sign >= 0) or (c < 0 and overall_sign < 0):
                same_sign_count += 1

        stability = same_sign_count / n

        summaries.append(RollingSummary(
            window=w, mean=mean, std=std, stability=stability,
        ))

    return summaries
