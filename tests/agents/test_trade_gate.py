import math

from user_data.strategies.agents.trade_gate import (
    Decision,
    Gate,
    GateConfig,
    GateState,
    Input,
)


def almost_equal(a: float, b: float, tolerance: float = 0.01) -> bool:
    return abs(a - b) <= tolerance


class TestDecisions:

    def test_full_size_high_confidence_ideal_regime(self):
        g = Gate()
        input = Input(
            technical_score=85, orderflow_score=82, regime_score=80,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.FULL_SIZE, \
            f"Expected FULL_SIZE, got {out.decision}. Reason: {out.reason}"
        assert 1.0 <= out.size_multiplier <= 1.0

    def test_normal_size_moderate_confidence(self):
        g = Gate()
        input = Input(
            technical_score=75, orderflow_score=70, regime_score=65,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.NORMAL_SIZE, \
            f"Expected NORMAL_SIZE, got {out.decision}"
        assert 0.5 <= out.size_multiplier <= 0.5

    def test_small_size_trending_high_vol_override(self):
        g = Gate()
        input = Input(
            technical_score=65, orderflow_score=60, regime_score=55,
            regime_label="trending_high_vol", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.SMALL_SIZE, \
            f"Expected SMALL_SIZE, got {out.decision}"
        assert 0.18 <= out.size_multiplier <= 0.19

    def test_full_base_ranging_high_vol_cuts_to_25pct(self):
        g = Gate()
        input = Input(
            technical_score=85, orderflow_score=80, regime_score=75,
            regime_label="ranging_high_vol", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.FULL_SIZE, \
            f"Expected FULL_SIZE (base), got {out.decision}"
        assert 0.25 <= out.size_multiplier <= 0.25

    def test_regime_blacklist_ranging_low_vol(self):
        g = Gate()
        input = Input(
            technical_score=90, orderflow_score=85, regime_score=40,
            regime_label="ranging_low_vol", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"Expected NO_TRADE, got {out.decision}"
        assert out.reason == "regime: ranging_low_vol", \
            f"Expected regime reason, got {out.reason}"

    def test_small_size_borderline_confidence(self):
        g = Gate()
        input = Input(
            technical_score=55, orderflow_score=60, regime_score=70,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.SMALL_SIZE, \
            f"Expected SMALL_SIZE, got {out.decision}"
        assert 0.25 <= out.size_multiplier <= 0.25

    def test_no_trade_low_confidence(self):
        g = Gate()
        input = Input(
            technical_score=40, orderflow_score=30, regime_score=50,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"Expected NO_TRADE, got {out.decision}"
        assert "low confidence" in out.reason, \
            f"Expected low confidence reason, got {out.reason}"

    def test_no_trade_ml_below_threshold(self):
        g = Gate()
        input = Input(
            technical_score=85, orderflow_score=80, regime_score=75,
            regime_label="trending_low_vol", meta_model_prob=0.40,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"Expected NO_TRADE, got {out.decision}"
        assert "ML below threshold" in out.reason, \
            f"Expected ML threshold reason, got {out.reason}"

    def test_no_trade_nan_scores(self):
        g = Gate()
        input = Input(
            technical_score=math.nan, orderflow_score=80, regime_score=75,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"Expected NO_TRADE, got {out.decision}"
        assert "NaN" in out.reason, \
            f"Expected NaN reason, got {out.reason}"

    def test_no_trade_cooldown_active(self):
        g = Gate()
        input = Input(
            technical_score=85, orderflow_score=82, regime_score=80,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )
        g.on_trade_closed()
        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"Expected NO_TRADE, got {out.decision}"
        assert out.reason == "cooldown: 2 bars remaining", \
            f"Expected cooldown reason, got {out.reason}"

    def test_no_trade_regime_unknown(self):
        g = Gate()
        input = Input(
            technical_score=85, orderflow_score=80, regime_score=75,
            regime_label="unknown", meta_model_prob=1.0,
        )
        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"Expected NO_TRADE, got {out.decision}"
        assert out.reason == "regime: unknown", \
            f"Expected unknown regime reason, got {out.reason}"


class TestRawConfidence:

    def test_raw_confidence_rejected_trade(self):
        g = Gate()
        out = g.evaluate(Input(
            technical_score=90, orderflow_score=85, regime_score=40,
            regime_label="ranging_low_vol", meta_model_prob=1.0,
        ))
        assert almost_equal(out.raw_confidence, 78.0, 0.1), \
            f"Expected raw_confidence ~78.0, got {out.raw_confidence}"

    def test_raw_confidence_accepted_trade(self):
        g = Gate()
        out = g.evaluate(Input(
            technical_score=85, orderflow_score=82, regime_score=80,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        ))
        assert almost_equal(out.raw_confidence, 82.8, 0.1), \
            f"Expected raw_confidence ~82.8, got {out.raw_confidence}"


class TestCooldownStateMachine:

    def test_full_lifecycle(self):
        g = Gate(GateConfig(
            cooldown_bars=2, max_trades_per_day=5, drawdown_limit=-0.05,
            starting_capital=10_000, meta_model_threshold=0.45,
            tech_weight=0.40, of_weight=0.40, regime_weight=0.20,
        ))

        input = Input(
            technical_score=85, orderflow_score=82, regime_score=80,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )

        out = g.evaluate(input)
        assert out.decision == Decision.FULL_SIZE, \
            f"Initial eval should pass, got {out.decision}"

        g.on_trade_placed()
        g.on_trade_closed()

        g.on_bar()
        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"During cooldown should be NoTrade, got {out.decision}"
        assert out.reason == "cooldown: 1 bars remaining", \
            f"Expected 'cooldown: 1 bars remaining', got {out.reason}"

        g.on_bar()
        assert g.state() == GateState.IDLE, \
            f"After cooldown state should be IDLE, got {g.state()}"

        out = g.evaluate(input)
        assert out.decision == Decision.FULL_SIZE, \
            f"After cooldown should allow trade, got {out.decision}"


class TestMaxTradesPerDay:

    def test_limit_then_reset(self):
        g = Gate(GateConfig(
            cooldown_bars=0, max_trades_per_day=3, drawdown_limit=-0.05,
            starting_capital=10_000, meta_model_threshold=0.45,
            tech_weight=0.40, of_weight=0.40, regime_weight=0.20,
        ))

        input = Input(
            technical_score=85, orderflow_score=82, regime_score=80,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )

        for i in range(3):
            out = g.evaluate(input)
            assert out.decision == Decision.FULL_SIZE, \
                f"Trade {i+1}: expected FullSize, got {out.decision}"
            g.on_trade_placed()
            g.on_trade_closed()
            g.on_bar()

        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"4th trade should be blocked, got {out.decision}"
        assert out.reason == "max trades per day reached: 3", \
            f"Expected max trades reason, got {out.reason}"

        g.reset_day("2026-06-07", 0)
        out = g.evaluate(input)
        assert out.decision == Decision.FULL_SIZE, \
            f"After reset should allow trade, got {out.decision}"


class TestDailyDrawdownStop:

    def test_drawdown_stops_then_resets(self):
        g = Gate(GateConfig(
            cooldown_bars=0, max_trades_per_day=5, drawdown_limit=-0.05,
            starting_capital=10_000, meta_model_threshold=0.45,
            tech_weight=0.40, of_weight=0.40, regime_weight=0.20,
        ))

        input = Input(
            technical_score=85, orderflow_score=82, regime_score=80,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        )

        g.update_pnl(-300)
        g.update_pnl(-200)
        g.update_pnl(-100)
        g.update_pnl(-200)

        assert g.state() == GateState.STOPPED, \
            f"After drawdown state should be STOPPED, got {g.state()}"

        out = g.evaluate(input)
        assert out.decision == Decision.NO_TRADE, \
            f"During drawdown expected NoTrade, got {out.decision}"
        assert out.reason == "daily drawdown limit hit", \
            f"Expected drawdown reason, got {out.reason}"

        reset = g.reset_day("2026-06-07", 0)
        assert reset is True, "ResetDay should return True when resuming from stopped"
        assert g.state() == GateState.IDLE, \
            f"After reset state should be IDLE, got {g.state()}"

        out = g.evaluate(input)
        assert out.decision == Decision.FULL_SIZE, \
            f"After day reset should allow trade, got {out.decision}"


class TestRegimeUnknown:

    def test_unknown_regime_rejected(self):
        g = Gate()
        out = g.evaluate(Input(
            technical_score=85, orderflow_score=82, regime_score=80,
            regime_label="unknown", meta_model_prob=1.0,
        ))
        assert out.decision == Decision.NO_TRADE, \
            f"Unknown regime: expected NoTrade, got {out.decision}"


class TestBoundaries:

    def test_confidence_60_small_size(self):
        g = Gate()
        out = g.evaluate(Input(
            technical_score=60, orderflow_score=60, regime_score=60,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        ))
        assert out.decision == Decision.SMALL_SIZE, \
            f"Conf=60: expected SMALL_SIZE, got {out.decision}"

    def test_confidence_70_normal_size(self):
        g = Gate()
        out = g.evaluate(Input(
            technical_score=70, orderflow_score=70, regime_score=70,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        ))
        assert out.decision == Decision.NORMAL_SIZE, \
            f"Conf=70: expected NORMAL_SIZE, got {out.decision}"

    def test_confidence_80_full_size(self):
        g = Gate()
        out = g.evaluate(Input(
            technical_score=80, orderflow_score=80, regime_score=80,
            regime_label="trending_low_vol", meta_model_prob=1.0,
        ))
        assert out.decision == Decision.FULL_SIZE, \
            f"Conf=80: expected FULL_SIZE, got {out.decision}"

    def test_ml_prob_exactly_45_passes(self):
        g = Gate()
        out = g.evaluate(Input(
            technical_score=85, orderflow_score=82, regime_score=80,
            regime_label="trending_low_vol", meta_model_prob=0.45,
        ))
        assert out.decision == Decision.FULL_SIZE, \
            f"ML prob=0.45: should pass threshold, got {out.decision}"
