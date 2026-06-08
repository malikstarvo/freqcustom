import math

from user_data.strategies.agents.technical_scorer import (
    Calculate,
    Input,
    _valid,
)


def almost_equal(a: float, b: float, tolerance: float = 1.0) -> bool:
    return abs(a - b) <= tolerance


class TestTechnicalScorer:

    def test_bullish_perfect(self):
        input = Input(
            price=50000, ema20=49500, ema50=48500, ema200=47000,
            rsi14=55, atr14=1250, volume=1500000, vol_ema20=1000000, adx14=30,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 89, 1.0), \
            f"Expected ~89, got {score.technical_score}. Components: {score.components}"

    def test_bearish_kuat(self):
        input = Input(
            price=45000, ema20=47000, ema50=48000, ema200=49000,
            rsi14=25, atr14=1800, volume=500000, vol_ema20=1000000, adx14=15,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 25, 1.0), \
            f"Expected ~25, got {score.technical_score}. Components: {score.components}"

    def test_pullback_in_uptrend(self):
        input = Input(
            price=48000, ema20=49000, ema50=48500, ema200=47000,
            rsi14=42, atr14=900, volume=1000000, vol_ema20=1000000, adx14=22,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 62, 1.0), \
            f"Expected ~62, got {score.technical_score}. Components: {score.components}"

    def test_overbought(self):
        input = Input(
            price=52000, ema20=50000, ema50=49000, ema200=48000,
            rsi14=82, atr14=1560, volume=2000000, vol_ema20=1000000, adx14=35,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 79, 1.0), \
            f"Expected ~79, got {score.technical_score}. Components: {score.components}"

    def test_zero_volume(self):
        input = Input(
            price=50000, ema20=49500, ema50=49000, ema200=48500,
            rsi14=50, atr14=1000, volume=0, vol_ema20=1000000, adx14=28,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 76, 1.0), \
            f"Expected ~76, got {score.technical_score}. Components: {score.components}"

    def test_flat_market(self):
        input = Input(
            price=50000, ema20=50000, ema50=50000, ema200=50000,
            rsi14=50, atr14=250, volume=1000000, vol_ema20=1000000, adx14=18,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 35, 1.0), \
            f"Expected ~35, got {score.technical_score}. Components: {score.components}"

    def test_rsi_extreme_oversold(self):
        input = Input(
            price=50000, ema20=48000, ema50=46000, ema200=44000,
            rsi14=0, atr14=1100, volume=1200000, vol_ema20=1000000, adx14=20,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 62, 1.0), \
            f"Expected ~62, got {score.technical_score}. Components: {score.components}"

    def test_all_zero_inputs(self):
        input = Input(
            price=0, ema20=0, ema50=0, ema200=0,
            rsi14=0, atr14=0, volume=0, vol_ema20=0, adx14=0,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 5, 1.0), \
            f"Expected ~5, got {score.technical_score}. Components: {score.components}"

    def test_high_volatility(self):
        input = Input(
            price=50000, ema20=48500, ema50=47500, ema200=46500,
            rsi14=60, atr14=3000, volume=2500000, vol_ema20=1000000, adx14=32,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 89, 1.0), \
            f"Expected ~89, got {score.technical_score}. Components: {score.components}"

    def test_bearish_oversold(self):
        input = Input(
            price=45000, ema20=46000, ema50=47000, ema200=48000,
            rsi14=28, atr14=1350, volume=1800000, vol_ema20=1000000, adx14=25,
        )
        score = Calculate(input)
        assert almost_equal(score.technical_score, 44, 1.0), \
            f"Expected ~44, got {score.technical_score}. Components: {score.components}"

    def test_nan_price(self):
        input = Input(
            price=math.nan, ema20=49500, ema50=48500, ema200=47000,
            rsi14=55, atr14=1250, volume=1500000, vol_ema20=1000000, adx14=30,
        )
        score = Calculate(input)
        assert score.technical_score == 0.0, \
            f"Expected 0 for NaN price, got {score.technical_score}"

    def test_inf_price(self):
        input = Input(
            price=math.inf, ema20=49500, ema50=48500, ema200=47000,
            rsi14=55, atr14=1250, volume=1500000, vol_ema20=1000000, adx14=30,
        )
        score = Calculate(input)
        assert score.technical_score == 0.0, \
            f"Expected 0 for Inf price, got {score.technical_score}"


class TestComponentsSum:

    def test_bullish_sum(self):
        input = Input(50000, 49500, 48500, 47000, 55, 1250, 1500000, 1000000, 30)
        score = Calculate(input)
        s = score.components
        total = s.trend + s.momentum + s.volume + s.volatility + s.adx_bonus
        assert almost_equal(total, score.technical_score, 1.5), \
            f"Sum {total} != score {score.technical_score}"

    def test_bearish_sum(self):
        input = Input(45000, 47000, 48000, 49000, 25, 1800, 500000, 1000000, 15)
        score = Calculate(input)
        s = score.components
        total = s.trend + s.momentum + s.volume + s.volatility + s.adx_bonus
        assert almost_equal(total, score.technical_score, 1.5)

    def test_flat_sum(self):
        input = Input(50000, 50000, 50000, 50000, 50, 250, 1000000, 1000000, 18)
        score = Calculate(input)
        s = score.components
        total = s.trend + s.momentum + s.volume + s.volatility + s.adx_bonus
        assert almost_equal(total, score.technical_score, 1.5)

    def test_high_vol_sum(self):
        input = Input(50000, 48500, 47500, 46500, 60, 3000, 2500000, 1000000, 32)
        score = Calculate(input)
        s = score.components
        total = s.trend + s.momentum + s.volume + s.volatility + s.adx_bonus
        assert almost_equal(total, score.technical_score, 1.5)

    def test_nan_guard(self):
        input = Input()
        score = Calculate(input)
        s = score.components
        total = s.trend + s.momentum + s.volume + s.volatility + s.adx_bonus
        assert almost_equal(total, score.technical_score, 1.5)


class TestValid:

    def test_valid_number(self):
        assert _valid(42.0) is True

    def test_valid_zero(self):
        assert _valid(0.0) is True

    def test_valid_nan(self):
        assert _valid(math.nan) is False

    def test_valid_pos_inf(self):
        assert _valid(math.inf) is False

    def test_valid_neg_inf(self):
        assert _valid(-math.inf) is False
