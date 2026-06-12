import math
import threading
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    NO_TRADE = "no_trade"
    SMALL_SIZE = "small_size"
    NORMAL_SIZE = "normal_size"
    FULL_SIZE = "full_size"


class GateState(str, Enum):
    IDLE = "idle"
    COOLDOWN = "cooldown"
    STOPPED = "stopped"


@dataclass
class GateConfig:
    cooldown_bars: int = 2
    max_trades_per_day: int = 5
    drawdown_limit: float = -0.05
    starting_capital: float = 10_000.0
    meta_model_threshold: float = 0.45
    min_tech_score: float = 55.0
    tech_weight_default: float = 0.65
    of_weight_default: float = 0.15
    regime_weight_default: float = 0.20
    tech_weight_no_of: float = 0.80
    of_weight_no_of: float = 0.00
    regime_weight_no_of: float = 0.20

    @staticmethod
    def default() -> "GateConfig":
        return GateConfig()


@dataclass
class Input:
    technical_score: float = 0.0
    orderflow_score: float = 0.0
    regime_score: float = 0.0
    regime_label: str = "unknown"
    meta_model_prob: float = 0.0
    of_data_available: bool = False


@dataclass
class Output:
    decision: Decision = Decision.NO_TRADE
    size_multiplier: float = 0.0
    raw_confidence: float = 0.0
    final_confidence: float = 0.0
    reason: str = ""


# ── Rejection reason constants ───────────────────────
REASON_INVALID_INPUT = "invalid_input"
REASON_LOW_TECH = "low_tech_score"
REASON_META_MODEL = "meta_model_below_threshold"
REASON_BAD_REGIME = "bad_regime"
REASON_STOPPED = "daily_drawdown_limit"
REASON_MAX_TRADES = "max_trades_per_day"
REASON_COOLDOWN = "cooldown"
REASON_LOW_CONFIDENCE = "low_confidence"
REASON_OK = ""


def _valid(v: float) -> bool:
    return not (math.isnan(v) or math.isinf(v))


def _size_from_confidence(conf: float) -> float:
    if conf >= 80:
        return 1.00
    elif conf >= 65:
        return 0.50
    elif conf >= 50:
        return 0.25
    else:
        return 0.0


def _decision_from_size(size: float) -> Decision:
    if size >= 1.00:
        return Decision.FULL_SIZE
    elif size >= 0.50:
        return Decision.NORMAL_SIZE
    elif size > 0:
        return Decision.SMALL_SIZE
    else:
        return Decision.NO_TRADE


def _apply_regime_override(size: float, label: str) -> float:
    if size <= 0:
        return 0.0

    if label == "trending_low_vol":
        return size * 1.00
    elif label == "trending_high_vol":
        return size * 0.75
    elif label == "ranging_high_vol":
        return size * 0.50
    elif label == "ranging_low_vol":
        return size * 0.25
    else:
        return 0.0


class Gate:
    def __init__(self, config: GateConfig | None = None) -> None:
        self._mu = threading.Lock()
        self.cfg = config if config is not None else GateConfig.default()
        self._state: GateState = GateState.IDLE
        self._cooldown_bars_remaining: int = 0
        self._trade_count: int = 0
        self._day_pnl: float = 0.0
        self._current_day: str = ""

    def evaluate(self, input: Input) -> Output:
        if (
            not _valid(input.technical_score)
            or not _valid(input.regime_score)
        ):
            return self._no_trade(0.0, REASON_INVALID_INPUT)

        # ── Dynamic weighting: OF unavailable? reassign weight ──
        if input.of_data_available:
            tech_w = self.cfg.tech_weight_default
            of_w = self.cfg.of_weight_default
            regime_w = self.cfg.regime_weight_default
            of_val = input.orderflow_score if _valid(input.orderflow_score) else 0.0
        else:
            tech_w = self.cfg.tech_weight_no_of
            of_w = self.cfg.of_weight_no_of
            regime_w = self.cfg.regime_weight_no_of
            of_val = 0.0

        raw_conf = (
            input.technical_score * tech_w
            + of_val * of_w
            + input.regime_score * regime_w
        )

        if raw_conf > 100:
            raw_conf = 100
        if raw_conf < 0:
            raw_conf = 0

        # ── MIN_TECH_SCORE guard ──────────────────────────
        if input.technical_score < self.cfg.min_tech_score:
            return self._no_trade(
                raw_conf,
                REASON_LOW_TECH,
            )

        # ── Meta-model threshold ──────────────────────────
        if input.meta_model_prob < self.cfg.meta_model_threshold:
            return self._no_trade(
                raw_conf,
                REASON_META_MODEL,
            )

        # ── Regime filter ─────────────────────────────────
        if input.regime_label == "unknown":
            return self._no_trade(raw_conf, REASON_BAD_REGIME)

        # ── State machine ─────────────────────────────────
        with self._mu:
            if self._state == GateState.STOPPED:
                return self._no_trade(raw_conf, REASON_STOPPED)

            if self._trade_count >= self.cfg.max_trades_per_day:
                return self._no_trade(
                    raw_conf,
                    REASON_MAX_TRADES,
                )

            if self._state == GateState.COOLDOWN:
                return self._no_trade(
                    raw_conf,
                    REASON_COOLDOWN,
                )

            base_size = _size_from_confidence(raw_conf)
            if base_size == 0:
                return self._no_trade(
                    raw_conf,
                    REASON_LOW_CONFIDENCE,
                )

            final_size = _apply_regime_override(base_size, input.regime_label)
            decision = _decision_from_size(final_size)

            return Output(
                decision=decision,
                size_multiplier=final_size,
                raw_confidence=raw_conf,
                final_confidence=raw_conf,
                reason=REASON_OK,
            )

    def on_trade_placed(self) -> None:
        with self._mu:
            self._trade_count += 1

    def on_trade_closed(self) -> None:
        with self._mu:
            self._state = GateState.COOLDOWN
            self._cooldown_bars_remaining = self.cfg.cooldown_bars

    def on_bar(self) -> None:
        with self._mu:
            if self._state == GateState.COOLDOWN:
                self._cooldown_bars_remaining -= 1
                if self._cooldown_bars_remaining <= 0:
                    self._state = GateState.IDLE

    def update_pnl(self, pnl: float) -> None:
        with self._mu:
            self._day_pnl += pnl
            dd_pct = self._day_pnl / self.cfg.starting_capital
            if dd_pct <= self.cfg.drawdown_limit:
                self._state = GateState.STOPPED

    def reset_day(self, new_day: str, starting_pnl: float = 0.0) -> bool:
        with self._mu:
            self._trade_count = 0
            self._day_pnl = starting_pnl
            self._current_day = new_day
            if self._state == GateState.STOPPED:
                self._state = GateState.IDLE
                return True
            return False

    def state(self) -> GateState:
        with self._mu:
            return self._state

    def trade_count(self) -> int:
        with self._mu:
            return self._trade_count

    def _no_trade(self, raw_conf: float, reason: str) -> Output:
        return Output(
            decision=Decision.NO_TRADE,
            size_multiplier=0.0,
            raw_confidence=raw_conf,
            final_confidence=raw_conf,
            reason=reason,
        )
