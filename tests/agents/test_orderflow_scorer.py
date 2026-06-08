import math

from user_data.strategies.agents.orderflow_scorer import (
    Calculate,
    Input,
    _valid,
)


def almost_equal(a: float, b: float, tolerance: float = 1.0) -> bool:
    return abs(a - b) <= tolerance


class TestOrderFlowScorer:

    def test_bullish_confluence(self):
        input = Input(
            funding_rate=0.00002, oi_delta_pct=0.5, ls_ratio=1.2,
            long_liq_usd=1_000_000, short_liq_usd=500_000,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 60, 1.0), \
            f"Expected ~60, got {score.orderflow_score}. Comp: {score.components}"

    def test_bearish_confluence(self):
        input = Input(
            funding_rate=-0.00003, oi_delta_pct=-0.8, ls_ratio=0.7,
            long_liq_usd=200_000, short_liq_usd=1_000_000,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 35, 1.0), \
            f"Expected ~35, got {score.orderflow_score}. Comp: {score.components}"

    def test_short_squeeze_top(self):
        input = Input(
            funding_rate=0.00008, oi_delta_pct=1.0, ls_ratio=1.8,
            long_liq_usd=500_000, short_liq_usd=10_000_000,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 63, 1.0), \
            f"Expected ~63, got {score.orderflow_score}. Comp: {score.components}"

    def test_long_capitulation(self):
        input = Input(
            funding_rate=0.00001, oi_delta_pct=0.2, ls_ratio=1.05,
            long_liq_usd=5_000_000, short_liq_usd=500_000,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 54, 1.0), \
            f"Expected ~54, got {score.orderflow_score}. Comp: {score.components}"

    def test_extreme_bearish(self):
        input = Input(
            funding_rate=-0.00010, oi_delta_pct=-1.5, ls_ratio=0.4,
            long_liq_usd=10_000_000, short_liq_usd=300_000,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 22, 1.0), \
            f"Expected ~22, got {score.orderflow_score}. Comp: {score.components}"

    def test_blowoff_top(self):
        input = Input(
            funding_rate=0.00015, oi_delta_pct=2.0, ls_ratio=2.5,
            long_liq_usd=20_000_000, short_liq_usd=1_000_000,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 66, 1.0), \
            f"Expected ~66, got {score.orderflow_score}. Comp: {score.components}"

    def test_neutral_no_activity(self):
        input = Input(
            funding_rate=0, oi_delta_pct=0, ls_ratio=1.0,
            long_liq_usd=0, short_liq_usd=0,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 50, 1.0), \
            f"Expected ~50, got {score.orderflow_score}. Comp: {score.components}"

    def test_mixed_signals(self):
        input = Input(
            funding_rate=0.00005, oi_delta_pct=-0.3, ls_ratio=1.4,
            long_liq_usd=100_000, short_liq_usd=100_000,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 54, 1.0), \
            f"Expected ~54, got {score.orderflow_score}. Comp: {score.components}"

    def test_long_wipeout(self):
        input = Input(
            funding_rate=0.00002, oi_delta_pct=0.3, ls_ratio=1.1,
            long_liq_usd=50_000_000, short_liq_usd=500_000,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 68, 1.0), \
            f"Expected ~68, got {score.orderflow_score}. Comp: {score.components}"

    def test_nan_guard_missing_data(self):
        input = Input(
            funding_rate=math.nan, oi_delta_pct=math.nan, ls_ratio=math.nan,
            long_liq_usd=math.nan, short_liq_usd=math.nan,
        )
        score = Calculate(input)
        assert almost_equal(score.orderflow_score, 45, 1.0), \
            f"Expected ~45, got {score.orderflow_score}. Comp: {score.components}"


class TestComponentsSum:

    def test_bullish_sum(self):
        input = Input(0.00002, 0.5, 1.2, 1_000_000, 500_000)
        score = Calculate(input)
        s = score.components
        total = s.funding_score + s.oi_score + s.ls_score + s.liq_score
        assert almost_equal(total, score.orderflow_score, 1.5), \
            f"Sum {total} != score {score.orderflow_score}"

    def test_bearish_sum(self):
        input = Input(-0.00003, -0.8, 0.7, 200_000, 1_000_000)
        score = Calculate(input)
        s = score.components
        total = s.funding_score + s.oi_score + s.ls_score + s.liq_score
        assert almost_equal(total, score.orderflow_score, 1.5)

    def test_neutral_sum(self):
        input = Input(0, 0, 1.0, 0, 0)
        score = Calculate(input)
        s = score.components
        total = s.funding_score + s.oi_score + s.ls_score + s.liq_score
        assert almost_equal(total, score.orderflow_score, 1.5)

    def test_nan_sum(self):
        input = Input(math.nan, math.nan, math.nan, math.nan, math.nan)
        score = Calculate(input)
        s = score.components
        total = s.funding_score + s.oi_score + s.ls_score + s.liq_score
        assert almost_equal(total, score.orderflow_score, 1.5)


class TestBounds:

    def test_extreme_bull(self):
        input = Input(
            funding_rate=0.0001, oi_delta_pct=5.0, ls_ratio=1.15,
            long_liq_usd=500_000_000, short_liq_usd=0,
        )
        score = Calculate(input)
        assert score.orderflow_score > 50, \
            f"Extreme bull should score high, got {score.orderflow_score}"
        assert score.orderflow_score <= 100, \
            f"Score should not exceed 100, got {score.orderflow_score}"

    def test_extreme_bear(self):
        input = Input(
            funding_rate=-0.001, oi_delta_pct=-10.0, ls_ratio=0.01,
            long_liq_usd=0, short_liq_usd=500_000_000,
        )
        score = Calculate(input)
        assert score.orderflow_score < 20, \
            f"Extreme bear should score low, got {score.orderflow_score}"


class TestValid:

    def test_valid_number(self):
        assert _valid(42.0) is True

    def test_valid_zero(self):
        assert _valid(0.0) is True

    def test_valid_nan(self):
        assert _valid(math.nan) is False

    def test_valid_pos_inf(self):
        assert _valid(math.inf) is False
