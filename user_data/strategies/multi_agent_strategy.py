
import pandas as pd
import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy
from user_data.strategies.agents.orderflow_scorer import Calculate as calc_of
from user_data.strategies.agents.orderflow_scorer import Input as OFInput
from user_data.strategies.agents.regime_scorer import Calculate as calc_regime
from user_data.strategies.agents.regime_scorer import Input as RegimeInput
from user_data.strategies.agents.technical_scorer import Calculate as calc_tech
from user_data.strategies.agents.technical_scorer import Input as TechInput
from user_data.strategies.agents.trade_gate import Gate, GateConfig, GateInput


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

        of_columns = [
            "funding_rate", "oi_delta_1_pct", "ls_ratio",
            "liq_long_usd", "liq_short_usd",
        ]
        for col in of_columns:
            if col not in dataframe.columns:
                dataframe[col] = 0.0

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
                    funding_rate=float(row.get("funding_rate", 0)),
                    oi_delta_pct=float(row.get("oi_delta_1_pct", 0)),
                    ls_ratio=float(row.get("ls_ratio", 0)),
                    long_liq_usd=float(row.get("liq_long_usd", 0)),
                    short_liq_usd=float(row.get("liq_short_usd", 0)),
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
            )

            decision = self.trade_gate.evaluate(gate_input)

            dataframe.at[dataframe.index[idx], "enter_long"] = (
                1 if decision.decision.value != "no_trade" else 0
            )
            dataframe.at[dataframe.index[idx], "stake_amount"] = decision.size_multiplier
            dataframe.at[dataframe.index[idx], "confidence"] = decision.raw_confidence
            dataframe.at[dataframe.index[idx], "regime_label"] = regime_score.regime

        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[:, "exit_long"] = 0

        for idx in range(self.startup_candle_count + 1, len(dataframe)):
            row = dataframe.iloc[idx]

            stop_price = row["close"] - (self.atr_multiplier.value * row["atr14"])
            prev_low = dataframe.iloc[idx - 1]["low"]
            if prev_low <= stop_price:
                dataframe.at[dataframe.index[idx], "exit_long"] = 1
                continue

            bars_since_entry = idx - self.startup_candle_count
            if bars_since_entry >= self.max_hold_bars.value:
                dataframe.at[dataframe.index[idx], "exit_long"] = 1
                continue

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
        if self.trade_gate.state().value != "idle":
            return False
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
        if self.dp.runmode.value in ("live", "dry_run"):
            return 1.0
        return 1.0
