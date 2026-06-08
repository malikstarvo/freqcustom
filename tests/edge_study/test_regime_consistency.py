import math

from freqtrade.optimize.edge_study.regime_analysis import RegimeResult, regime_consistency


def almost_equal(a: float, b: float, tolerance: float = 0.001) -> bool:
    return abs(a - b) <= tolerance


class TestRegimeConsistency:

    def test_empty_input(self):
        assert regime_consistency([]) == 0.0

    def test_single_regime(self):
        regimes = [RegimeResult(regime="trending", corr=0.5, samples=100)]
        assert almost_equal(regime_consistency(regimes), 1.0)

    def test_identical_correlations(self):
        regimes = [
            RegimeResult(regime="trending_low", corr=0.4, samples=50),
            RegimeResult(regime="trending_high", corr=0.4, samples=50),
        ]
        assert almost_equal(regime_consistency(regimes), 1.0)

    def test_divergent_correlations(self):
        regimes = [
            RegimeResult(regime="trending_low", corr=0.6, samples=50),
            RegimeResult(regime="ranging_high", corr=0.1, samples=50),
        ]
        consistency = regime_consistency(regimes)
        assert almost_equal(consistency, 0.5)

    def test_nan_correlation_filtered(self):
        regimes = [
            RegimeResult(regime="trending_low", corr=0.5, samples=50),
            RegimeResult(regime="ranging", corr=math.nan, samples=0),
            RegimeResult(regime="trending_high", corr=0.4, samples=50),
        ]
        consistency = regime_consistency(regimes)
        assert almost_equal(consistency, 0.9)

    def test_three_regimes(self):
        regimes = [
            RegimeResult(regime="a", corr=0.8, samples=30),
            RegimeResult(regime="b", corr=0.5, samples=40),
            RegimeResult(regime="c", corr=0.3, samples=30),
        ]
        consistency = regime_consistency(regimes)
        assert almost_equal(consistency, 0.5)
