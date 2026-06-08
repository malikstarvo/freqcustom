
from user_data.strategies.agents import (
    Decision,
    Gate,
    GateInput,
    OrderFlowInput,
    RegimeInput,
    TechnicalInput,
    calculate_orderflow,
    calculate_regime,
    calculate_technical,
)


def almost_equal(a: float, b: float, tolerance: float = 1.0) -> bool:
    return abs(a - b) <= tolerance


class TestMultiAgentIntegration:

    def test_valid_signal_passes_all_agents_and_gate(self):
        tech = calculate_technical(TechnicalInput(
            price=50000, ema20=49500, ema50=48500, ema200=47000,
            rsi14=55, atr14=1250, volume=1500000, vol_ema20=1000000, adx14=30,
        ))
        assert tech.technical_score >= 80, f"Tech score too low: {tech.technical_score}"

        of = calculate_orderflow(OrderFlowInput(
            funding_rate=0.00002, oi_delta_pct=0.5, ls_ratio=1.2,
            long_liq_usd=1_000_000, short_liq_usd=500_000,
        ))
        assert of.orderflow_score >= 50, f"OF score too low: {of.orderflow_score}"

        regime = calculate_regime(RegimeInput(
            adx14=40, atr14=1250, price=50000, volatility=1.5,
        ))
        assert regime.regime_score >= 80, f"Regime score too low: {regime.regime_score}"
        assert regime.regime == "trending_high_vol", \
            f"Wrong regime: {regime.regime}"

        gate = Gate()
        decision = gate.evaluate(GateInput(
            technical_score=tech.technical_score,
            orderflow_score=of.orderflow_score,
            regime_score=regime.regime_score,
            regime_label=regime.regime,
            meta_model_prob=1.0,
        ))
        assert decision.decision != Decision.NO_TRADE, \
            f"Gate blocked valid signal: {decision.reason}"
        assert decision.size_multiplier > 0, "Size multiplier should be positive"

    def test_bearish_signal_blocked(self):
        tech = calculate_technical(TechnicalInput(
            price=45000, ema20=47000, ema50=48000, ema200=49000,
            rsi14=25, atr14=1800, volume=500000, vol_ema20=1000000, adx14=15,
        ))
        assert tech.technical_score < 40, f"Tech score should be low: {tech.technical_score}"

        of = calculate_orderflow(OrderFlowInput(
            funding_rate=-0.00003, oi_delta_pct=-0.8, ls_ratio=0.7,
            long_liq_usd=200_000, short_liq_usd=1_000_000,
        ))
        assert of.orderflow_score < 45, f"OF score should be low: {of.orderflow_score}"

        regime = calculate_regime(RegimeInput(
            adx14=18, atr14=1750, price=50000, volatility=2.5,
        ))
        assert regime.regime == "ranging_high_vol", \
            f"Wrong regime: {regime.regime}"

        gate = Gate()
        decision = gate.evaluate(GateInput(
            technical_score=tech.technical_score,
            orderflow_score=of.orderflow_score,
            regime_score=regime.regime_score,
            regime_label=regime.regime,
            meta_model_prob=1.0,
        ))
        assert decision.decision == Decision.NO_TRADE or decision.size_multiplier <= 0.25, \
            f"Bearish should be blocked or small: {decision.decision}, size={decision.size_multiplier}"

    def test_ranging_low_vol_always_blocked(self):
        """No matter how good tech and OF scores are, ranging_low_vol must block."""
        regime = calculate_regime(RegimeInput(
            adx14=15, atr14=150, price=50000, volatility=0.2,
        ))
        assert regime.regime == "ranging_low_vol", \
            f"Expected ranging_low_vol, got {regime.regime}"

        gate = Gate()
        decision = gate.evaluate(GateInput(
            technical_score=95,
            orderflow_score=90,
            regime_score=30,
            regime_label=regime.regime,
            meta_model_prob=1.0,
        ))
        assert decision.decision == Decision.NO_TRADE, \
            f"ranging_low_vol MUST block even with high scores. Got: {decision.decision}"
        assert decision.reason == "regime: ranging_low_vol", \
            f"Expected regime reason, got: {decision.reason}"

    def test_ml_threshold_gate_blocks(self):
        gate = Gate()
        decision = gate.evaluate(GateInput(
            technical_score=85,
            orderflow_score=80,
            regime_score=75,
            regime_label="trending_low_vol",
            meta_model_prob=0.30,
        ))
        assert decision.decision == Decision.NO_TRADE, \
            f"ML below 0.45 should block. Got: {decision.decision}"
        assert "ML below threshold: 0.30" == decision.reason, \
            f"Wrong reason: {decision.reason}"

    def test_all_scores_within_0_100_range(self):
        tech = calculate_technical(TechnicalInput(
            price=50000, ema20=49500, ema50=48500, ema200=47000,
            rsi14=55, atr14=1250, volume=1500000, vol_ema20=1000000, adx14=30,
        ))
        assert 0 <= tech.technical_score <= 100, \
            f"Tech score out of range: {tech.technical_score}"

        of = calculate_orderflow(OrderFlowInput(
            funding_rate=0.00002, oi_delta_pct=0.5, ls_ratio=1.2,
            long_liq_usd=1_000_000, short_liq_usd=500_000,
        ))
        assert 0 <= of.orderflow_score <= 100, \
            f"OF score out of range: {of.orderflow_score}"

        regime = calculate_regime(RegimeInput(
            adx14=40, atr14=1250, price=50000, volatility=1.5,
        ))
        assert 0 <= regime.regime_score <= 100, \
            f"Regime score out of range: {regime.regime_score}"
