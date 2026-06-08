from freqtrade.optimize.edge_study.decay import analyze_decay, DecayResult


def almost_equal(a: float, b: float, tolerance: float = 0.001) -> bool:
    return abs(a - b) <= tolerance


class TestDecayAnalysis:

    def test_empty_input(self):
        result = analyze_decay([])
        assert result.peak_corr == 0.0
        assert result.avg_corr == 0.0
        assert result.decay_rate == 0.0
        assert result.persistence == 0.0

    def test_single_value(self):
        result = analyze_decay([0.5])
        assert almost_equal(result.peak_corr, 0.5)
        assert almost_equal(result.avg_corr, 0.5)
        assert result.decay_rate == 0.0
        assert almost_equal(result.persistence, 0.5)

    def test_decaying_correlations(self):
        corrs = [0.8, 0.6, 0.4, 0.2]
        result = analyze_decay(corrs)
        assert almost_equal(result.peak_corr, 0.8)
        assert almost_equal(result.avg_corr, 0.5)
        assert almost_equal(result.decay_rate, 0.2)
        assert almost_equal(result.persistence, 0.2)

    def test_mixed_signs(self):
        corrs = [0.3, -0.1, 0.2, -0.05]
        result = analyze_decay(corrs)
        assert almost_equal(result.peak_corr, 0.3)
        # abs values: 0.3, 0.1, 0.2, 0.05 -> avg = 0.1625
        assert almost_equal(result.avg_corr, 0.1625)
        # decay from 0.3 to 0.05 over 3 steps
        assert almost_equal(result.decay_rate, 0.08333, 0.01)
        assert almost_equal(result.persistence, 0.05)

    def test_increasing_correlations(self):
        corrs = [0.1, 0.3, 0.5, 0.7]
        result = analyze_decay(corrs)
        assert almost_equal(result.peak_corr, 0.7)
        assert almost_equal(result.avg_corr, 0.4)
        assert result.decay_rate < 0  # negative decay (strengthening)
        assert almost_equal(result.persistence, 0.1)
