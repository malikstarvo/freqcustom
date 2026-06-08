from freqtrade.optimize.edge_study.ranking import ComponentScore, compute_ranking


def almost_equal(a: float, b: float, tolerance: float = 0.001) -> bool:
    return abs(a - b) <= tolerance


class TestRanking:

    def test_empty_input(self):
        result = compute_ranking([])
        assert result == []

    def test_single_feature(self):
        scores = [
            ComponentScore(
                feature_name="rsi14", quantile_pf=1.5,
                quantile_wr_delta=0.1, rolling_stability=0.8,
                regime_consistency_val=0.7, avg_abs_correlation=0.3,
            ),
        ]
        result = compute_ranking(scores)
        assert len(result) == 1
        assert result[0].feature_name == "rsi14"
        assert almost_equal(result[0].composite_score, 1.0)

    def test_ranking_order(self):
        scores = [
            ComponentScore(
                feature_name="weak", quantile_pf=0.8,
                quantile_wr_delta=0.02, rolling_stability=0.3,
                regime_consistency_val=0.2, avg_abs_correlation=0.05,
            ),
            ComponentScore(
                feature_name="strong", quantile_pf=2.0,
                quantile_wr_delta=0.15, rolling_stability=0.9,
                regime_consistency_val=0.85, avg_abs_correlation=0.6,
            ),
            ComponentScore(
                feature_name="medium", quantile_pf=1.2,
                quantile_wr_delta=0.08, rolling_stability=0.6,
                regime_consistency_val=0.5, avg_abs_correlation=0.2,
            ),
        ]
        result = compute_ranking(scores)
        assert len(result) == 3
        assert result[0].feature_name == "strong"
        assert result[0].composite_score > result[1].composite_score
        assert result[1].composite_score > result[2].composite_score
        assert result[2].feature_name == "weak"

    def test_composite_score_in_range(self):
        scores = [
            ComponentScore(
                feature_name="f1", quantile_pf=1.5,
                quantile_wr_delta=0.1, rolling_stability=0.8,
                regime_consistency_val=0.7, avg_abs_correlation=0.3,
            ),
        ]
        result = compute_ranking(scores)
        assert 0 <= result[0].composite_score <= 1.0

    def test_ties_stable_ordinal_ranking(self):
        scores = [
            ComponentScore(
                feature_name="a", quantile_pf=1.0,
                quantile_wr_delta=0.1, rolling_stability=0.5,
                regime_consistency_val=0.5, avg_abs_correlation=0.2,
            ),
            ComponentScore(
                feature_name="b", quantile_pf=1.0,
                quantile_wr_delta=0.1, rolling_stability=0.5,
                regime_consistency_val=0.5, avg_abs_correlation=0.2,
            ),
        ]
        result = compute_ranking(scores)
        assert len(result) == 2
        assert result[0].composite_score > result[1].composite_score
