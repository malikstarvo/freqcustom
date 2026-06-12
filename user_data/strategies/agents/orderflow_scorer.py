import math
from dataclasses import dataclass, field


@dataclass
class Input:
    funding_rate: float | None = None
    oi_delta_pct: float | None = None
    ls_ratio: float | None = None
    long_liq_usd: float | None = None
    short_liq_usd: float | None = None


@dataclass
class Components:
    funding_score: float = 0.0
    oi_score: float = 0.0
    ls_score: float = 0.0
    liq_score: float = 0.0


@dataclass
class Score:
    orderflow_score: float = 0.0
    data_available: bool = False
    components: Components = field(default_factory=Components)


def _valid(v: float | None) -> bool:
    if v is None:
        return False
    return not (math.isnan(v) or math.isinf(v))


def _calc_funding_score(funding_rate: float) -> float:
    bps = funding_rate * 10000

    if bps <= 0:
        score = 10 + bps * 3
        if score < 0:
            score = 0
        return score
    elif bps < 2:
        return 10 + bps * 5
    elif bps < 5:
        score = 20 - (bps - 2) * 3.33
        if score < 10:
            score = 10
        return score
    else:
        score = 10 - (bps - 5) * 2
        if score < 0:
            score = 0
        return score


def _calc_oi_score(oi_delta_pct: float) -> float:
    score = 15 + oi_delta_pct * 10
    if score > 25:
        score = 25
    if score < 0:
        score = 0
    return score


def _calc_ls_score(ls_ratio: float) -> float:
    if ls_ratio <= 0:
        return 10.0

    if ls_ratio >= 1.0 and ls_ratio <= 1.3:
        return 12 + (ls_ratio - 1.0) / 0.3 * 6
    elif ls_ratio > 1.3 and ls_ratio <= 2.0:
        score = 18 - (ls_ratio - 1.3) / 0.7 * 8
        if score < 10:
            score = 10
        return score
    elif ls_ratio > 2.0:
        score = 10 - (ls_ratio - 2.0) * 8
        if score < 2:
            score = 2
        return score
    else:
        score = 12 - (1.0 - ls_ratio) * 20
        if score < 0:
            score = 0
        return score


def _calc_liq_score(long_liq: float, short_liq: float) -> float:
    total_liq = long_liq + short_liq
    if total_liq <= 0:
        return 12.5

    imbalance = (short_liq - long_liq) / total_liq
    norm = total_liq / 50_000_000
    if norm > 1:
        norm = 1
    if norm < 0:
        norm = 0

    direction = imbalance * norm * 8
    magnitude = norm * 4.5

    score = 12.5 - direction + magnitude
    if score > 25:
        score = 25
    if score < 0:
        score = 0
    return score


def _all_none(*values: float | None) -> bool:
    return all(v is None for v in values)


def Calculate(input: Input) -> Score:
    # Check if ALL orderflow data is unavailable (None/NaN)
    if _all_none(input.funding_rate, input.oi_delta_pct, input.ls_ratio,
                 input.long_liq_usd, input.short_liq_usd):
        return Score(
            orderflow_score=0.0,
            data_available=False,
            components=Components(),
        )

    # Partial data: some fields available, others default to 0
    funding_rate = input.funding_rate if _valid(input.funding_rate) else 0.0
    oi_delta_pct = input.oi_delta_pct if _valid(input.oi_delta_pct) else 0.0
    ls_ratio = input.ls_ratio if _valid(input.ls_ratio) else 1.0
    long_liq = input.long_liq_usd if _valid(input.long_liq_usd) else 0.0
    short_liq = input.short_liq_usd if _valid(input.short_liq_usd) else 0.0

    funding_score = _calc_funding_score(funding_rate)
    oi_score = _calc_oi_score(oi_delta_pct)
    ls_score = _calc_ls_score(ls_ratio)
    liq_score = _calc_liq_score(long_liq, short_liq)

    total = funding_score + oi_score + ls_score + liq_score
    if total > 100:
        total = 100
    if total < 0:
        total = 0

    return Score(
        orderflow_score=total,
        data_available=True,
        components=Components(
            funding_score=funding_score,
            oi_score=oi_score,
            ls_score=ls_score,
            liq_score=liq_score,
        ),
    )
