import math
from dataclasses import dataclass, field


@dataclass
class Input:
    price: float = 0.0
    ema20: float = 0.0
    ema50: float = 0.0
    ema200: float = 0.0
    rsi14: float = 0.0
    atr14: float = 0.0
    volume: float = 0.0
    vol_ema20: float = 0.0
    adx14: float = 0.0


@dataclass
class Components:
    trend: float = 0.0
    momentum: float = 0.0
    volume: float = 0.0
    volatility: float = 0.0
    adx_bonus: float = 0.0


@dataclass
class Score:
    technical_score: float = 0.0
    components: Components = field(default_factory=Components)


def _valid(v: float) -> bool:
    return not (math.isnan(v) or math.isinf(v))


def _calc_trend(input: Input) -> float:
    if not _valid(input.ema20) or not _valid(input.ema50) or not _valid(input.ema200):
        return 0.0

    price, e20, e50, e200 = input.price, input.ema20, input.ema50, input.ema200

    if price > e20 and e20 > e50 and e50 > e200:
        base = 30.0
    elif price > e20 and e20 > e50:
        base = 25.0
    elif price > e20:
        base = 20.0
    elif price < e20 and e20 > e50 and e50 > e200:
        base = 20.0
    elif price > e50:
        base = 15.0
    elif price > e200:
        base = 10.0
    else:
        base = 0.0

    if e20 > e50 and e50 > e200:
        alignment = 5.0
    else:
        alignment = 0.0

    result = base + alignment
    if result > 35:
        result = 35
    return result


def _calc_momentum(rsi: float) -> float:
    if not _valid(rsi):
        return 0.0

    if rsi >= 45 and rsi <= 65:
        return 22 + ((rsi - 45) / 20) * 8
    elif rsi >= 30 and rsi < 45:
        return 15 + ((rsi - 30) / 15) * 7
    elif rsi > 65 and rsi <= 75:
        return 22 - ((rsi - 65) / 10) * 7
    elif rsi > 75:
        val = 15 - ((rsi - 75) / 25) * 15
        if val < 0:
            val = 0
        return val
    elif rsi >= 0 and rsi < 30:
        return 5 + (rsi / 30) * 10
    else:
        return 0.0


def _calc_volume(volume: float, vol_ema20: float) -> float:
    if not _valid(volume) or not _valid(vol_ema20) or vol_ema20 <= 0:
        return 0.0

    ratio = volume / vol_ema20
    score = math.log1p(ratio) * 12
    if score > 20:
        score = 20
    if score < 0:
        score = 0
    return score


def _calc_volatility(atr: float, price: float) -> float:
    if not _valid(atr) or not _valid(price) or price <= 0 or atr <= 0:
        return 0.0

    atr_pct = atr / price * 100

    if atr_pct < 1.0:
        return 3.0
    elif atr_pct < 2.0:
        return 5.0
    elif atr_pct < 3.5:
        return 10.0
    elif atr_pct < 5.0:
        return 7.0
    else:
        return 4.0


def _calc_adx_bonus(adx: float) -> float:
    if not _valid(adx) or adx <= 0:
        return 0.0

    if adx >= 35:
        return 10.0
    elif adx >= 25:
        return 7.0
    elif adx >= 20:
        return 3.0
    else:
        return 0.0


def Calculate(input: Input) -> Score:
    if not _valid(input.price):
        return Score()

    trend = _calc_trend(input)
    momentum = _calc_momentum(input.rsi14)
    volume = _calc_volume(input.volume, input.vol_ema20)
    volatility = _calc_volatility(input.atr14, input.price)
    adx_bonus = _calc_adx_bonus(input.adx14)

    total = trend + momentum + volume + volatility + adx_bonus
    if total > 100:
        total = 100
    if total < 0:
        total = 0

    return Score(
        technical_score=total,
        components=Components(
            trend=trend,
            momentum=momentum,
            volume=volume,
            volatility=volatility,
            adx_bonus=adx_bonus,
        ),
    )
