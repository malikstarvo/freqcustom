"""
Slippage simulation, position sizing, and direction decision.

Ported 1:1 from internal/papertrade/executor.go
"""


def simulate_entry(ref_price: float, size: float, direction: str,
                   slippage: float, commission: float, candle_volume: float = 0) -> dict:
    s = slippage
    if candle_volume > 0 and size > candle_volume * 0.01:
        ratio = size / (candle_volume * 0.01)
        s += slippage * min(ratio, 2.0)

    if direction == "long":
        fill_price = ref_price * (1 + s)
    elif direction == "short":
        fill_price = ref_price * (1 - s)
    else:
        fill_price = ref_price

    return {
        "fill_price": fill_price,
        "slippage_pct": s,
        "commission": size * commission,
    }


def simulate_exit(ref_price: float, size: float, direction: str,
                  slippage: float, commission: float) -> dict:
    if direction == "long":
        fill_price = ref_price * (1 - slippage)
    elif direction == "short":
        fill_price = ref_price * (1 + slippage)
    else:
        fill_price = ref_price

    return {
        "fill_price": fill_price,
        "slippage_pct": slippage,
        "commission": size * commission,
    }


def calc_position_size(equity: float, entry_price: float, atr: float,
                       atr_multiplier: float, risk_pct: float) -> float:
    if atr <= 0 or equity <= 0 or entry_price <= 0:
        return 0.0

    stop_distance = atr * atr_multiplier
    if stop_distance <= 0:
        return 0.0

    size = equity * (risk_pct / 100.0) / stop_distance
    if size <= 0:
        return 0.0

    return size


def decide_direction(tech_score: float, long_threshold: float, short_threshold: float) -> str:
    if tech_score >= long_threshold:
        return "long"
    if tech_score <= short_threshold:
        return "short"
    return "no_trade"
