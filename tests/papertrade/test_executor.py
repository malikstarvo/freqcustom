from freqtrade.papertrade.executor import (
    calc_position_size,
    decide_direction,
    simulate_entry,
    simulate_exit,
)


def almost_equal(a: float, b: float, tolerance: float = 0.0001) -> bool:
    return abs(a - b) <= tolerance


class TestSimulateEntry:

    def test_long_entry(self):
        result = simulate_entry(ref_price=50000, size=100, direction="long",
                                slippage=0.0005, commission=0.00055)
        assert almost_equal(result["fill_price"], 50025.0)
        assert almost_equal(result["commission"], 0.055)
        assert result["slippage_pct"] >= 0.0005

    def test_short_entry(self):
        result = simulate_entry(ref_price=50000, size=100, direction="short",
                                slippage=0.0005, commission=0.00055)
        assert almost_equal(result["fill_price"], 49975.0)
        assert almost_equal(result["commission"], 0.055)

    def test_volume_premium(self):
        result = simulate_entry(ref_price=100, size=50000, direction="long",
                                slippage=0.001, commission=0.001,
                                candle_volume=100000)
        assert result["slippage_pct"] > 0.001

    def test_zero_volume_no_premium(self):
        result = simulate_entry(ref_price=100, size=10, direction="long",
                                slippage=0.001, commission=0.001,
                                candle_volume=0)
        assert almost_equal(result["slippage_pct"], 0.001)


class TestSimulateExit:

    def test_long_exit(self):
        result = simulate_exit(ref_price=50000, size=100, direction="long",
                               slippage=0.0005, commission=0.00055)
        assert almost_equal(result["fill_price"], 49975.0)
        assert almost_equal(result["commission"], 0.055)

    def test_short_exit(self):
        result = simulate_exit(ref_price=50000, size=100, direction="short",
                               slippage=0.0005, commission=0.00055)
        assert almost_equal(result["fill_price"], 50025.0)
        assert almost_equal(result["commission"], 0.055)


class TestCalcPositionSize:

    def test_standard_calc(self):
        size = calc_position_size(
            equity=10000, entry_price=50000, atr=1000,
            atr_multiplier=2.0, risk_pct=1.0,
        )
        expected = 10000 * 0.01 / (1000 * 2.0)
        assert almost_equal(size, expected)

    def test_zero_atr(self):
        size = calc_position_size(equity=10000, entry_price=50000, atr=0,
                                  atr_multiplier=2.0, risk_pct=1.0)
        assert size == 0.0

    def test_zero_equity(self):
        size = calc_position_size(equity=0, entry_price=50000, atr=1000,
                                  atr_multiplier=2.0, risk_pct=1.0)
        assert size == 0.0

    def test_small_risk(self):
        size = calc_position_size(
            equity=5000, entry_price=20000, atr=500,
            atr_multiplier=1.5, risk_pct=0.5,
        )
        expected = 5000 * 0.005 / (500 * 1.5)
        assert almost_equal(size, expected)


class TestDecideDirection:

    def test_long_signal(self):
        assert decide_direction(70, 60, 40) == "long"
        assert decide_direction(60, 60, 40) == "long"

    def test_short_signal(self):
        assert decide_direction(30, 60, 40) == "short"
        assert decide_direction(40, 60, 40) == "short"

    def test_no_trade(self):
        assert decide_direction(50, 60, 40) == "no_trade"
