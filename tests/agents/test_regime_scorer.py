import math

from user_data.strategies.agents.regime_scorer import (
    Calculate,
    Input,
    _valid,
)


def almost_equal(a: float, b: float, tolerance: float = 1.0) -> bool:
    return abs(a - b) <= tolerance


class TestRegimeScorer:

    def test_strong_trend_active_vol(self):
        input = Input(adx14=40, atr14=1250, price=50000, volatility=1.5)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 85, 1.0), \
            f"Expected ~85, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "trending_high_vol", \
            f"Expected trending_high_vol, got {score.regime}"

    def test_strong_trend_low_vol(self):
        input = Input(adx14=40, atr14=400, price=50000, volatility=0.6)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 62, 1.0), \
            f"Expected ~62, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "trending_low_vol", \
            f"Expected trending_low_vol, got {score.regime}"

    def test_moderate_trend_active_vol(self):
        input = Input(adx14=30, atr14=1500, price=50000, volatility=2.0)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 75, 1.0), \
            f"Expected ~75, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "trending_high_vol", \
            f"Expected trending_high_vol, got {score.regime}"

    def test_weak_trend_low_vol(self):
        input = Input(adx14=22, atr14=500, price=50000, volatility=0.7)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 22, 1.0), \
            f"Expected ~22, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "ranging_low_vol", \
            f"Expected ranging_low_vol, got {score.regime}"

    def test_dead_flat(self):
        input = Input(adx14=15, atr14=150, price=50000, volatility=0.2)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 5, 1.0), \
            f"Expected ~5, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "ranging_low_vol", \
            f"Expected ranging_low_vol, got {score.regime}"

    def test_choppy_high_vol(self):
        input = Input(adx14=18, atr14=1750, price=50000, volatility=2.5)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 42, 1.0), \
            f"Expected ~42, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "ranging_high_vol", \
            f"Expected ranging_high_vol, got {score.regime}"

    def test_strong_trend_extreme_vol(self):
        input = Input(adx14=40, atr14=3000, price=50000, volatility=4.0)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 68, 1.0), \
            f"Expected ~68, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "trending_low_vol", \
            f"Expected trending_low_vol, got {score.regime}"

    def test_trend_boundary_low_vol(self):
        input = Input(adx14=25, atr14=700, price=50000, volatility=0.9)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 39, 1.0), \
            f"Expected ~39, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "trending_low_vol", \
            f"Expected trending_low_vol, got {score.regime}"

    def test_strong_trend_moderate_high_vol(self):
        input = Input(adx14=35, atr14=1000, price=50000, volatility=1.2)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 80, 1.0), \
            f"Expected ~80, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "trending_high_vol", \
            f"Expected trending_high_vol, got {score.regime}"

    def test_nan_guard_all_invalid(self):
        input = Input(adx14=math.nan, atr14=math.nan, price=math.nan, volatility=math.nan)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 50, 1.0), \
            f"Expected ~50, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "unknown", \
            f"Expected unknown, got {score.regime}"

    def test_partial_nan_adx_only(self):
        input = Input(adx14=math.nan, atr14=1000, price=50000, volatility=1.5)
        score = Calculate(input)
        assert almost_equal(score.regime_score, 57, 1.0), \
            f"Expected ~57, got {score.regime_score}. Comp: {score.components}"
        assert score.regime == "unknown", \
            f"Expected unknown, got {score.regime}"


class TestComponentsSum:

    def test_strong_trend_high_vol_sum(self):
        input = Input(40, 1250, 50000, 1.5)
        score = Calculate(input)
        s = score.components
        total = s.trend_score + s.vol_score
        assert almost_equal(total, score.regime_score, 1.5), \
            f"Sum {total} != score {score.regime_score}"

    def test_dead_flat_sum(self):
        input = Input(15, 150, 50000, 0.2)
        score = Calculate(input)
        s = score.components
        total = s.trend_score + s.vol_score
        assert almost_equal(total, score.regime_score, 1.5)

    def test_choppy_high_vol_sum(self):
        input = Input(18, 1750, 50000, 2.5)
        score = Calculate(input)
        s = score.components
        total = s.trend_score + s.vol_score
        assert almost_equal(total, score.regime_score, 1.5)

    def test_nan_all_sum(self):
        input = Input(math.nan, math.nan, math.nan, math.nan)
        score = Calculate(input)
        s = score.components
        total = s.trend_score + s.vol_score
        assert almost_equal(total, score.regime_score, 1.5)


class TestBounds:

    def test_max_trend_max_vol(self):
        input = Input(adx14=100, atr14=1750, price=50000, volatility=2.0)
        score = Calculate(input)
        assert score.regime_score <= 100, \
            f"Score exceeds 100: {score.regime_score}"
        assert score.components.trend_score <= 50, \
            f"Trend exceeds 50: {score.components.trend_score}"

    def test_negative_values_no_crash(self):
        input = Input(adx14=-5, atr14=-100, price=50000, volatility=-0.1)
        score = Calculate(input)
        assert score.regime_score >= 0, \
            f"Score should not be negative: {score.regime_score}"


class TestValid:

    def test_valid_number(self):
        assert _valid(42.0) is True

    def test_valid_zero(self):
        assert _valid(0.0) is True

    def test_valid_nan(self):
        assert _valid(math.nan) is False

    def test_valid_pos_inf(self):
        assert _valid(math.inf) is False
