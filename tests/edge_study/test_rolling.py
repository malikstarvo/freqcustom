from freqtrade.optimize.edge_study.rolling import RollingSummary, run_rolling


class MockEdgeStore:
    def __init__(self) -> None:
        pass

    def rolling_correlation(self, feature_col, label_col, symbol,
                            timeframe, feature_set_id, window):
        if window == 50:
            return [
                {"corr": 0.3, "ts": None}, {"corr": 0.4, "ts": None},
                {"corr": 0.35, "ts": None}, {"corr": 0.5, "ts": None},
                {"corr": 0.45, "ts": None},
            ]
        elif window == 100:
            return [
                {"corr": 0.35, "ts": None}, {"corr": 0.38, "ts": None},
                {"corr": 0.42, "ts": None},
            ]
        else:
            return []


def almost_equal(a: float, b: float, tolerance: float = 0.01) -> bool:
    return abs(a - b) <= tolerance


class TestRollingAnalysis:

    def test_rolling_with_data(self):
        from freqtrade.optimize.edge_study.types import EdgeFilter, FeatureInfo, LabelHorizon

        store = MockEdgeStore()
        flt = EdgeFilter(symbol="BTCUSDT", timeframe="15m", feature_set_id=1)
        feature = FeatureInfo(name="rsi14", col="rsi14")
        horizon = LabelHorizon(name="future_return_4", col="future_return_4")

        summaries = run_rolling(store, flt, feature, horizon, [50, 100])
        assert len(summaries) == 2

        s50 = summaries[0]
        assert s50.window == 50
        assert s50.stability > 0
        assert s50.mean > 0

        s100 = summaries[1]
        assert s100.window == 100
        assert s100.stability > 0

    def test_empty_window(self):
        from freqtrade.optimize.edge_study.types import EdgeFilter, FeatureInfo, LabelHorizon

        store = MockEdgeStore()
        flt = EdgeFilter()
        feature = FeatureInfo(name="rsi", col="rsi")
        horizon = LabelHorizon(name="fr4", col="fr4")

        summaries = run_rolling(store, flt, feature, horizon, [200])
        assert len(summaries) == 1
        assert summaries[0].window == 200
        assert summaries[0].mean == 0.0
        assert summaries[0].stability == 0.0
