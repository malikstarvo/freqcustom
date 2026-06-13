import math
from dataclasses import dataclass, field


@dataclass
class Input:
    funding_rate: float | None = None


@dataclass
class Components:
    funding_score: float = 0.0


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


def _all_none(*values: float | None) -> bool:
    return all(v is None for v in values)


def Calculate(input: Input) -> Score:
    if not _valid(input.funding_rate):
        return Score(
            orderflow_score=0.0,
            data_available=False,
            components=Components(),
        )

    funding_score = _calc_funding_score(input.funding_rate)
    total = funding_score
    if total > 100:
        total = 100
    if total < 0:
        total = 0

    return Score(
        orderflow_score=total,
        data_available=True,
        components=Components(
            funding_score=funding_score,
        ),
    )
