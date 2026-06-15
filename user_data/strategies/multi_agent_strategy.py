import json
import logging
import math
import os
from datetime import datetime, timezone

import pandas as pd
import talib.abstract as ta

from freqtrade.persistence import Trade
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
    can_short = True

    minimal_roi = {
        "120": 0.0025,
        "60": 0.005,
        "30": 0.01,
        "0": 0.02,
    }

    stoploss = -0.08
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True
    use_custom_stoploss = True
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
        data_dir = config.get("user_data_dir", "user_data")
        self._entry_log_path = os.path.join(data_dir, "trade_logs", "entry_logs.jsonl")
        os.makedirs(os.path.dirname(self._entry_log_path), exist_ok=True)
        self._entry_cache: dict[str, list[dict]] = {}
        self._custom_data_done: set[int] = set()

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
        dataframe["&-s_close"] = future_return
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

        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bb["upperband"]
        dataframe["bb_lower"] = bb["lowerband"]
        dataframe["bb_width"] = (bb["upperband"] - bb["lowerband"]) / bb["middleband"]
        dataframe["bb_pct"] = (dataframe["close"] - bb["lowerband"]) / (bb["upperband"] - bb["lowerband"])

        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macd_signal"] = macd["macdsignal"]
        dataframe["macd_hist"] = macd["macdhist"]

        dataframe["obv"] = ta.OBV(dataframe["close"], dataframe["volume"])
        dataframe["williams_r"] = ta.WILLR(dataframe)

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
        dataframe["ema_short"] = ta.EMA(dataframe, timeperiod=9)

        dataframe["volume_ema20"] = ta.EMA(dataframe["volume"], timeperiod=20)

        dataframe["volatility14"] = (
            dataframe["close"].pct_change().rolling(window=14).std() * 100
        )

        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bb["upperband"]
        dataframe["bb_lower"] = bb["lowerband"]
        dataframe["bb_width"] = (bb["upperband"] - bb["lowerband"]) / bb["middleband"]
        dataframe["bb_pct"] = (dataframe["close"] - bb["lowerband"]) / (bb["upperband"] - bb["lowerband"])

        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macd_signal"] = macd["macdsignal"]
        dataframe["macd_hist"] = macd["macdhist"]

        dataframe["obv"] = ta.OBV(dataframe["close"], dataframe["volume"])
        dataframe["williams_r"] = ta.WILLR(dataframe)

        # Do NOT fill orderflow columns with 0 — let NaN propagate
        # so orderflow_scorer can detect data unavailability

        if self.config.get("freqai", {}).get("enabled", False):
            dataframe = self.freqai.start(dataframe, metadata, self)

        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[:, "enter_long"] = 0
        dataframe.loc[:, "enter_short"] = 0

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

            # LONG evaluation
            long_gate = GateInput(
                technical_score=tech_score.technical_score,
                orderflow_score=of_score.orderflow_score,
                regime_score=regime_score.regime_score,
                regime_label=regime_score.regime,
                meta_model_prob=ml_prob,
                of_data_available=of_score.data_available,
            )
            long_decision = self.trade_gate.evaluate(long_gate)

            # SHORT evaluation (inverse ML prob)
            short_ml = 1 - ml_prob
            short_gate = GateInput(
                technical_score=tech_score.technical_score,
                orderflow_score=of_score.orderflow_score,
                regime_score=regime_score.regime_score,
                regime_label=regime_score.regime,
                meta_model_prob=short_ml,
                of_data_available=of_score.data_available,
            )
            short_decision = self.trade_gate.evaluate(short_gate)

            # Choose direction: LONG > SHORT > no trade
            if long_decision.decision.value != "no_trade":
                chosen = long_decision
                is_long = True
            elif short_decision.decision.value != "no_trade":
                chosen = short_decision
                is_long = False
            else:
                chosen = None
                is_long = True

            # ── Accumulate gate stats ─────────────────────
            self._gate_stats["total"] += 1
            self._gate_stats["avg_tech_score"] += tech_score.technical_score
            self._gate_stats["avg_of_score"] += of_score.orderflow_score
            self._gate_stats["avg_regime_score"] += regime_score.regime_score
            if chosen:
                self._gate_stats["avg_confidence"] += chosen.raw_confidence
                self._gate_stats["trades"] += 1
            if of_score.data_available:
                self._gate_stats["of_available"] += 1
            else:
                self._gate_stats["of_missing"] += 1
            if chosen:
                if chosen.reason == REASON_LOW_TECH:
                    self._gate_stats["rejected_low_tech"] += 1
                elif chosen.reason == REASON_META_MODEL:
                    self._gate_stats["rejected_meta_model"] += 1
                elif chosen.reason == REASON_BAD_REGIME:
                    self._gate_stats["rejected_bad_regime"] += 1
                elif chosen.reason == REASON_LOW_CONFIDENCE:
                    self._gate_stats["rejected_low_conf"] += 1
                elif chosen.reason == REASON_INVALID_INPUT:
                    self._gate_stats["rejected_invalid_input"] += 1

            # Log scores every 500 candles for diagnostics
            if idx % 500 == 0:
                logger.info(
                    f"BAR {idx}: tech={tech_score.technical_score:.1f} "
                    f"of={of_score.orderflow_score:.1f} "
                    f"of_avail={of_score.data_available} "
                    f"regime={regime_score.regime_score:.1f} "
                    f"label={regime_score.regime} "
                    f"ml={ml_prob:.2f} "
                    f"combined={chosen.raw_confidence if chosen else 0:.1f} "
                    f"direction={'LONG' if chosen and is_long else 'SHORT' if chosen else 'NONE'} "
                    f"decision={chosen.decision.value if chosen else 'no_trade'} "
                    f"reason={chosen.reason if chosen else 'no_signal'}"
                )

            dataframe.loc[dataframe.index[idx], "enter_long"] = (
                1 if chosen and is_long else 0
            )
            dataframe.loc[dataframe.index[idx], "enter_short"] = (
                1 if chosen and not is_long else 0
            )
            dataframe.loc[dataframe.index[idx], "stake_amount"] = (
                chosen.size_multiplier if chosen else 1.0
            )
            dataframe.loc[dataframe.index[idx], "confidence"] = (
                chosen.raw_confidence if chosen else 0.0
            )
            dataframe.loc[dataframe.index[idx], "regime_label"] = regime_score.regime
            dataframe.loc[dataframe.index[idx], "tech_score"] = tech_score.technical_score
            dataframe.loc[dataframe.index[idx], "of_score"] = of_score.orderflow_score
            dataframe.loc[dataframe.index[idx], "regime_score"] = regime_score.regime_score
            dataframe.loc[dataframe.index[idx], "ml_prob_val"] = ml_prob
            dataframe.loc[dataframe.index[idx], "decision_value"] = (
                chosen.decision.value if chosen else "no_trade"
            )
            dataframe.loc[dataframe.index[idx], "decision_reason"] = (
                chosen.reason if chosen else "no_signal"
            )
            dataframe.loc[dataframe.index[idx], "of_available"] = int(of_score.data_available)

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
        dataframe.loc[:, "exit_short"] = 0

        # ── LONG exits ────────────────────────────────────

        # Exit 1: RSI overbought + price di bawah EMA20 (bearish divergence)
        dataframe.loc[
            (dataframe["rsi14"] > 75)
            & (dataframe["close"] < dataframe["ema20"]),
            "exit_long",
        ] = 1

        # Exit 2: ML probability drop (< 0.3) + volume spike
        dataframe.loc[
            (dataframe["ml_prob_val"].notna())
            & (dataframe["ml_prob_val"] < 0.3)
            & (dataframe["volume"] > dataframe["volume_ema20"] * 1.5),
            "exit_long",
        ] = 1

        # ── SHORT exits ───────────────────────────────────

        # Exit 1: RSI oversold + price di atas EMA20 (bullish reversal — cover short)
        dataframe.loc[
            (dataframe["rsi14"] < 25)
            & (dataframe["close"] > dataframe["ema20"]),
            "exit_short",
        ] = 1

        # Exit 2: ML prob flips up (> 0.6) — model now predicts up
        dataframe.loc[
            (dataframe["ml_prob_val"].notna())
            & (dataframe["ml_prob_val"] > 0.6)
            & (dataframe["volume"] > dataframe["volume_ema20"] * 1.5),
            "exit_short",
        ] = 1

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
        try:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and not dataframe.empty:
                row = dataframe.iloc[-1]
                entry = {
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "pair": pair,
                    "price": rate,
                    "amount": amount,
                    "indicators": {
                        "ema20": float(row.get("ema20", 0)),
                        "ema50": float(row.get("ema50", 0)),
                        "ema200": float(row.get("ema200", 0)),
                        "rsi14": float(row.get("rsi14", 0)),
                        "atr14": float(row.get("atr14", 0)),
                        "adx14": float(row.get("adx14", 0)),
                        "volume_ema20": float(row.get("volume_ema20", 0)),
                        "volatility14": float(row.get("volatility14", 0)),
                    },
                    "gate": {
                        "tech_score": float(row.get("tech_score", 0)),
                        "of_score": float(row.get("of_score", 0)),
                        "regime_score": float(row.get("regime_score", 0)),
                        "ml_prob": float(row.get("ml_prob_val", 0.5)),
                        "confidence": float(row.get("confidence", 0)),
                        "regime_label": str(row.get("regime_label", "")),
                        "decision_value": str(row.get("decision_value", "")),
                        "decision_reason": str(row.get("decision_reason", "")),
                        "size_multiplier": float(row.get("stake_amount", 0)),
                        "of_available": bool(row.get("of_available", False)),
                    },
                    "freqai": {
                        "prediction": float(row.get("&-s_close", 0.0)),
                        "probability": float(self._get_ml_prob(row)),
                        "do_predict": int(row.get("do_predict", 0)),
                    },
                }
                with open(self._entry_log_path, "a") as f:
                    f.write(json.dumps(entry) + "\n")
                self._entry_cache.setdefault(pair, []).append(entry)
        except Exception as e:
            logger.warning(f"Failed to log entry data for {pair}: {e}")
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
                pred = row.get("&-s_close", None)
                if pred is not None and not pd.isna(pred):
                    return 1.0 / (1.0 + math.exp(-float(pred)))
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
        if trade.id not in self._custom_data_done and pair in self._entry_cache:
            pending_list = self._entry_cache.get(pair)
            if pending_list:
                try:
                    trade.custom_data = pending_list.pop(0)
                    Trade.session.commit()
                    self._custom_data_done.add(trade.id)
                except Exception as e:
                    logger.warning(f"Failed to save custom_data for {pair}: {e}")
                if not pending_list:
                    try:
                        del self._entry_cache[pair]
                    except KeyError:
                        pass
        if trade.is_short:
            open_days = (current_time - trade.open_date_utc).days
            if open_days >= 4:
                return 0.04
            if open_days >= 2:
                return 0.08
            return None
        open_days = (current_time - trade.open_date_utc).days
        if open_days >= 4:
            return -0.04
        if open_days >= 2:
            return -0.08
        return None

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> str | bool | None:
        open_hours = (current_time - trade.open_date_utc).total_seconds() / 3600
        if open_hours > 48:
            return "time_based_max_hold"
        return None
