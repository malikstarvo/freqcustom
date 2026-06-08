import math
from dataclasses import dataclass, field


@dataclass
class Input:
    adx14: float = 0.0
    atr14: float = 0.0
    price: float = 0.0
    volatility: float = 0.0


@dataclass
class Components:
    trend_score: float = 0.0
    vol_score: float = 0.0


@dataclass
class Score:
    regime_score: float = 0.0
    regime: str = "unknown"
    components: Components = field(default_factory=Components)


def _valid(v: float) -> bool:
    return not (math.isnan(v) or math.isinf(v))


def _calc_trend_score(adx: float) -> float:
    if not _valid(adx):
        return 25.0
    if adx < 20:
        return 0.0
    if adx >= 35:
        return 50.0
    return (adx - 20) / 15 * 50


def _calc_vol_from_atr(atr: float, price: float) -> float:
    if not _valid(atr) or not _valid(price) or price <= 0 or atr <= 0:
        return 25.0

    atr_pct = atr / price * 100

    if atr_pct < 0.5:
        return 5.0
    elif atr_pct < 1.5:
        return 5 + (atr_pct - 0.5) / 1.0 * 20
    elif atr_pct < 3.0:
        return 25 + (atr_pct - 1.5) / 1.5 * 20
    elif atr_pct < 5.0:
        return 45 - (atr_pct - 3.0) / 2.0 * 20
    else:
        return 15.0


def _calc_vol_from_feature(vol: float) -> float:
    if not _valid(vol) or vol <= 0:
        return 25.0

    if vol < 0.3:
        return 5.0
    elif vol < 1.0:
        return 5 + (vol - 0.3) / 0.7 * 20
    elif vol < 2.5:
        return 25 + (vol - 1.0) / 1.5 * 20
    elif vol < 4.0:
        return 45 - (vol - 2.5) / 1.5 * 15
    else:
        return 20.0


def _classify_regime(adx: float, vol_score: float) -> str:
    if not _valid(adx):
        return "unknown"

    is_trending = adx >= 25
    is_high_vol = vol_score >= 25

    if is_trending and is_high_vol:
        return "trending_high_vol"
    elif is_trending and not is_high_vol:
        return "trending_low_vol"
    elif not is_trending and is_high_vol:
        return "ranging_high_vol"
    else:
        return "ranging_low_vol"


def Calculate(input: Input) -> Score:
    if (
        not _valid(input.adx14)
        and not _valid(input.atr14)
        and not _valid(input.price)
        and not _valid(input.volatility)
    ):
        return Score(
            regime_score=50.0,
            regime="unknown",
            components=Components(trend_score=25.0, vol_score=25.0),
        )

    trend_score = _calc_trend_score(input.adx14)

    atr_vol_score = _calc_vol_from_atr(input.atr14, input.price)
    feature_vol_score = _calc_vol_from_feature(input.volatility)

    vol_score = (atr_vol_score + feature_vol_score) / 2

    total = trend_score + vol_score
    if total > 100:
        total = 100
    if total < 0:
        total = 0

    regime = _classify_regime(input.adx14, vol_score)

    return Score(
        regime_score=total,
        regime=regime,
        components=Components(trend_score=trend_score, vol_score=vol_score),
    )
