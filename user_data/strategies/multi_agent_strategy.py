import logging
import pandas as pd
import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy
from agents.orderflow_scorer import Calculate as calc_of
from agents.orderflow_scorer import Input as OFInput
from agents.regime_scorer import Calculate as calc_regime
from agents.regime_scorer import Input as RegimeInput
from agents.technical_scorer import Calculate as calc_tech
from agents.technical_scorer import Input as TechInput
from agents.trade_gate import (
    Gate, GateConfig, Input as GateInput,
    REASON_LOW_TECH, REASON_META_MODEL, REASON_BAD_REGIME,
    REASON_LOW_CONFIDENCE, REASON_INVALID_INPUT,
)

logger = logging.getLogger(__name__)


class MultiAgentStrategy(IStrategy):
    timeframe = "15m"
    can_short = False

    minimal_roi = {
        "120": 0.01,
        "60": 0.02,
        "30": 0.04,
        "0": 0.05,
    }

    stoploss = -0.15
    trailing_stop = False
    use_custom_stoploss = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    process_only_new_candles = True
    startup_candle_count = 200

    position_adjustment_enable = True
    max_entry_position_adjustment = 3

    atr_multiplier = DecimalParameter(1.5, 3.0, default=2.0, space="sell")
    max_hold_bars = IntParameter(12, 48, default=24, space="sell")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.gate_config = GateConfig.default()
        self.trade_gate = Gate(self.gate_config)
        self._gate_stats = self._make_empty_stats()

    def _make_empty_stats(self):
        return {
            "total": 0,
            "of_available": 0,
            "of_missing": 0,
            "avg_tech_score": 0.0,
            "avg_of_score": 0.0,
            "avg_regime_score": 0.0,
            "avg_confidence": 0.0,
            "rejected_low_tech": 0,
            "rejected_meta_model": 0,
            "rejected_bad_regime": 0,
            "rejected_low_conf": 0,
            "rejected_invalid_input": 0,
            "trades": 0,
        }

    def set_freqai_targets(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        lp = self.freqai_info.get("feature_parameters", {}).get("label_period_candles", 4)
        future_return = dataframe["close"].shift(-lp) / dataframe["close"] - 1
        dataframe["&s-up_or_down"] = (future_return > 0.002).astype(str)
        return dataframe

    def feature_engineering_standard(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["adx14"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["volume_ema20"] = ta.EMA(dataframe["volume"], timeperiod=20)
        dataframe["volatility14"] = (
            dataframe["close"].pct_change().rolling(window=14).std() * 100
        )
        for col in self.freqai_info.get("feature_parameters", {}).get("feature_columns", []):
            if col in dataframe.columns:
                dataframe[f"%{col}"] = dataframe[col]
        return dataframe

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["adx14"] = ta.ADX(dataframe, timeperiod=14)

        dataframe["volume_ema20"] = ta.EMA(dataframe["volume"], timeperiod=20)

        dataframe["volatility14"] = (
            dataframe["close"].pct_change().rolling(window=14).std() * 100
        )

        # Do NOT fill orderflow columns with 0 — let NaN propagate
        # so orderflow_scorer can detect data unavailability

        if self.config.get("freqai", {}).get("enabled", False):
            dataframe = self.freqai.start(dataframe, metadata, self)
            freqai_cols = [c for c in dataframe.columns if c not in (
                "date", "open", "high", "low", "close", "volume",
                "ema20", "ema50", "ema200", "rsi14", "atr14", "adx14",
                "volume_ema20", "volatility14"
            )]
            if not hasattr(self, "_logged_cols"):
                self._logged_cols = True
                logger.info(f"FREQAI COLUMNS: {freqai_cols}")
                for c in freqai_cols:
                    try:
                        sample = dataframe[c].dropna().iloc[0] if not dataframe[c].dropna().empty else "N/A"
                        logger.info(f"  col '{c}' type={type(c)} dtype={dataframe[c].dtype} sample={sample}")
                    except Exception:
                        pass

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[:, "enter_long"] = 0

        for idx in range(self.startup_candle_count, len(dataframe)):
            row = dataframe.iloc[idx]

            tech_score = calc_tech(
                TechInput(
                    price=float(row["close"]),
                    ema20=float(row["ema20"]),
                    ema50=float(row["ema50"]),
                    ema200=float(row["ema200"]),
                    rsi14=float(row["rsi14"]),
                    atr14=float(row["atr14"]),
                    volume=float(row["volume"]),
                    vol_ema20=float(row["volume_ema20"]),
                    adx14=float(row["adx14"]),
                )
            )

            of_score = calc_of(
                OFInput(
                    funding_rate=row.get("funding_rate"),
                    oi_delta_pct=row.get("oi_delta_1_pct"),
                    ls_ratio=row.get("ls_ratio"),
                    long_liq_usd=row.get("liq_long_usd"),
                    short_liq_usd=row.get("liq_short_usd"),
                )
            )

            regime_score = calc_regime(
                RegimeInput(
                    adx14=float(row["adx14"]),
                    atr14=float(row["atr14"]),
                    price=float(row["close"]),
                    volatility=float(row["volatility14"]),
                )
            )

            ml_prob = self._get_ml_prob(row)

            gate_input = GateInput(
                technical_score=tech_score.technical_score,
                orderflow_score=of_score.orderflow_score,
                regime_score=regime_score.regime_score,
                regime_label=regime_score.regime,
                meta_model_prob=ml_prob,
                of_data_available=of_score.data_available,
            )

            decision = self.trade_gate.evaluate(gate_input)

            # ── Accumulate gate stats ─────────────────────
            self._gate_stats["total"] += 1
            self._gate_stats["avg_tech_score"] += tech_score.technical_score
            self._gate_stats["avg_of_score"] += of_score.orderflow_score
            self._gate_stats["avg_regime_score"] += regime_score.regime_score
            self._gate_stats["avg_confidence"] += decision.raw_confidence
            if of_score.data_available:
                self._gate_stats["of_available"] += 1
            else:
                self._gate_stats["of_missing"] += 1
            if decision.reason == REASON_LOW_TECH:
                self._gate_stats["rejected_low_tech"] += 1
            elif decision.reason == REASON_META_MODEL:
                self._gate_stats["rejected_meta_model"] += 1
            elif decision.reason == REASON_BAD_REGIME:
                self._gate_stats["rejected_bad_regime"] += 1
            elif decision.reason == REASON_LOW_CONFIDENCE:
                self._gate_stats["rejected_low_conf"] += 1
            elif decision.reason == REASON_INVALID_INPUT:
                self._gate_stats["rejected_invalid_input"] += 1
            if decision.decision.value != "no_trade":
                self._gate_stats["trades"] += 1

            # Log scores every 500 candles for diagnostics
            if idx % 500 == 0:
                logger.info(
                    f"BAR {idx}: tech={tech_score.technical_score:.1f} "
                    f"of={of_score.orderflow_score:.1f} "
                    f"of_avail={of_score.data_available} "
                    f"regime={regime_score.regime_score:.1f} "
                    f"label={regime_score.regime} "
                    f"ml={ml_prob:.2f} "
                    f"combined={decision.raw_confidence:.1f} "
                    f"decision={decision.decision.value} "
                    f"reason={decision.reason}"
                )

            dataframe.loc[dataframe.index[idx], "enter_long"] = (
                1 if decision.decision.value != "no_trade" else 0
            )
            dataframe.loc[dataframe.index[idx], "stake_amount"] = decision.size_multiplier
            dataframe.loc[dataframe.index[idx], "confidence"] = decision.raw_confidence
            dataframe.loc[dataframe.index[idx], "regime_label"] = regime_score.regime

        # ── Log gate stats summary after all candles ─────
        stats = self._gate_stats
        n = stats["total"] or 1
        logger.info(
            f"GATE STATS: total={n} "
            f"of_avail={stats['of_available']} "
            f"of_missing={stats['of_missing']} "
            f"avg_tech={stats['avg_tech_score']/n:.1f} "
            f"avg_of={stats['avg_of_score']/n:.1f} "
            f"avg_regime={stats['avg_regime_score']/n:.1f} "
            f"avg_conf={stats['avg_confidence']/n:.1f} "
            f"rej_low_tech={stats['rejected_low_tech']} "
            f"rej_meta={stats['rejected_meta_model']} "
            f"rej_regime={stats['rejected_bad_regime']} "
            f"rej_low_conf={stats['rejected_low_conf']} "
            f"rej_invalid={stats['rejected_invalid_input']} "
            f"trades={stats['trades']}"
        )

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[:, "exit_long"] = 0
        dataframe.loc[:, "exit_tag"] = ""

        if "True" in dataframe.columns and "do_predict" in dataframe.columns:
            ml_down = (dataframe["do_predict"] == 1) & (dataframe["True"] < 0.50)
            dataframe.loc[ml_down, "exit_long"] = 1
            dataframe.loc[ml_down, "exit_tag"] = "ml_flip_down"

        rsi_exit = (dataframe["exit_long"] == 0) & (dataframe["rsi14"] > 80)
        dataframe.loc[rsi_exit, "exit_long"] = 1
        dataframe.loc[rsi_exit, "exit_tag"] = "rsi_overbought"

        if "do_predict" in dataframe.columns:
            dp_fail = (dataframe["exit_long"] == 0) & (dataframe["do_predict"] != 1)
            dataframe.loc[dp_fail, "exit_long"] = 1
            dataframe.loc[dp_fail, "exit_tag"] = "do_predict_fail"

        return dataframe

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> bool:
        return True

    def custom_stake_amount(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_stake: float,
        min_stake: float,
        max_stake: float,
        leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return proposed_stake

        last_row = dataframe.iloc[-1]
        size_mult = last_row.get("stake_amount", 1.0)
        if not isinstance(size_mult, (int, float)):
            size_mult = 1.0

        adjusted = proposed_stake * float(size_mult)
        return max(min_stake, min(adjusted, max_stake))

    def _get_ml_prob(self, row) -> float:
        try:
            if "do_predict" in row.index and int(row["do_predict"]) == 1:
                for col in row.index:
                    col_str = str(col)
                    if col_str == "True" or col_str == "1" or col_str == "1.0":
                        val = float(row[col])
                        if 0 < val <= 1:
                            return val
                for col in row.index:
                    if col == "&s-up_or_down" or col == "do_predict":
                        continue
                    try:
                        val = float(row[col])
                        if 0 < val <= 1 and col not in ("&s-up_or_down", "do_predict"):
                            return val
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            logger.warning(f"_get_ml_prob failed for row: {e}")
        return 0.5

    def custom_stoploss(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> float | None:
        return None
