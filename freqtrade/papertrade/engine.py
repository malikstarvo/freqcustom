import json
import logging
import sys
import time as time_mod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.pool

from freqtrade.papertrade.executor import (
    calc_position_size,
    decide_direction,
    simulate_entry,
    simulate_exit,
)
from freqtrade.papertrade.store import PaperStore

logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    "symbol": "BTCUSDT",
    "timeframe": "15m",
    "initial_capital": 10_000.0,
    "commission": 0.00055,
    "slippage": 0.0005,
    "atr_multiplier": 2.0,
    "holding_bars": 24,
    "poll_interval_sec": 60,
    "risk_per_trade_pct": 1.0,
    "max_daily_drawdown_pct": 5.0,
    "max_total_drawdown_pct": 15.0,
    "long_threshold": 60.0,
    "short_threshold": 40.0,
    "ml_api_url": "",
}


class PaperEngine:

    def __init__(self, config: dict, store: PaperStore,
                 feature_pool: psycopg2.pool.ThreadedConnectionPool) -> None:
        self.cfg = {**DEFAULT_CONFIG, **config}

        strategies_dir = Path(self.cfg.get(
            "user_data_dir", Path.cwd() / "user_data",
        )) / "strategies"
        if str(strategies_dir) not in sys.path:
            sys.path.insert(0, str(strategies_dir))

        from agents.trade_gate import Gate, GateConfig  # noqa: E501

        self.store = store
        self._feature_pool = feature_pool

        gate_cfg = GateConfig.default()
        gate_cfg.starting_capital = self.cfg["initial_capital"]
        self.gate = Gate(gate_cfg)

        self.state: str = "running"
        self.position: Optional[dict] = None
        self._last_bar_ts: Optional[datetime] = None
        self._equity: float = self.cfg["initial_capital"]
        self._balance: float = self.cfg["initial_capital"]
        self._total_pnl: float = 0.0
        self._day_pnl: float = 0.0
        self._day_trades: int = 0
        self._current_day: str = ""
        self._bar_count: int = 0
        self._start_time: float = time_mod.time()
        self._feature_set_id: int = int(config.get("feature_set_id", 1))

    def top_up(self, amount: float) -> dict:
        old = self._balance
        self._balance += amount
        self._equity += amount
        self.gate.cfg.starting_capital += amount

        self.store.insert_top_up(
            amount=amount,
            balance_before=old,
            balance_after=self._balance,
            ts=datetime.now(timezone.utc),
        )

        logger.info(f"[PaperEngine] TOP-UP: +${amount:.0f} balance=${old:.0f}→${self._balance:.0f}")
        return {
            "old_balance": old,
            "new_balance": self._balance,
            "amount": amount,
        }

    def get_state(self) -> dict:
        return {
            "state": self.state,
            "equity": self._equity,
            "balance": self._balance,
            "total_pnl": self._total_pnl,
            "day_pnl": self._day_pnl,
            "day_trades": self._day_trades,
            "bar_count": self._bar_count,
            "uptime_sec": time_mod.time() - self._start_time,
            "position": self.position,
        }

    def recover(self) -> None:
        pos = self.store.load_open_position(
            self.cfg["symbol"], self.cfg["timeframe"],
        )
        if pos:
            self.position = pos
            logger.info(f"[PaperEngine] Recovered position #{pos['id']} "
                        f"{pos['direction']} entry={pos['entry_price']:.2f} "
                        f"stop={pos['stop_price']:.2f} bars={pos['bars_held']}")

        total_pnl = self.store.load_total_pnl()
        self._total_pnl = total_pnl
        self._balance = self.cfg["initial_capital"] + total_pnl
        self._equity = self._balance

        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        day_pnl, day_trades = self.store.load_daily_stats(day)
        self._day_pnl = day_pnl
        self._day_trades = day_trades
        self._current_day = day

        logger.info(f"[PaperEngine] Recovery: balance={self._balance:.0f} "
                    f"totalPnL={total_pnl:.0f} dayPnL={day_pnl:.0f} "
                    f"dayTrades={day_trades} hasPosition={pos is not None}")

    def _load_candle(self) -> Optional[dict]:
        with self._feature_pool.getconn() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT time, symbol, timeframe, open, high, low, close, volume
                        FROM candles
                        WHERE symbol = %s AND timeframe = %s
                        ORDER BY time DESC LIMIT 1""",
                        (self.cfg["symbol"], self.cfg["timeframe"]),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    return {
                        "time": row[0], "symbol": row[1], "timeframe": row[2],
                        "open": float(row[3]), "high": float(row[4]),
                        "low": float(row[5]), "close": float(row[6]),
                        "volume": float(row[7]),
                    }
            finally:
                self._feature_pool.putconn(conn)

    def _load_features(self, ts: datetime) -> Optional[dict]:
        with self._feature_pool.getconn() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT ts, ema20, ema50, ema200, rsi14, atr14, adx14,
                           volume_ema20, volatility14, funding_rate, oi_delta_1_pct,
                           ls_ratio, liq_long_usd, liq_short_usd
                        FROM feature_values
                        WHERE symbol = %s AND timeframe = %s AND feature_set_id = %s
                          AND ts <= %s
                        ORDER BY ts DESC LIMIT 2""",
                        (self.cfg["symbol"], self.cfg["timeframe"],
                         self._feature_set_id, ts),
                    )
                    rows = cur.fetchall()
                    if not rows:
                        return None
                    row = rows[0]
                    return {
                        "ts": row[0], "ema20": float(row[1] or 0),
                        "ema50": float(row[2] or 0), "ema200": float(row[3] or 0),
                        "rsi14": float(row[4] or 0), "atr14": float(row[5] or 0),
                        "adx14": float(row[6] or 0),
                        "volume_ema20": float(row[7] or 0),
                        "volatility14": float(row[8] or 0),
                        "funding_rate": float(row[9] or 0),
                        "oi_delta_1_pct": float(row[10] or 0),
                        "ls_ratio": float(row[11] or 0),
                        "liq_long_usd": float(row[12] or 0),
                        "liq_short_usd": float(row[13] or 0),
                    }
            finally:
                self._feature_pool.putconn(conn)

    def tick(self) -> dict:
        from agents.orderflow_scorer import Calculate as calc_of, Input as OFInput  # noqa: E501
        from agents.regime_scorer import Calculate as calc_regime, Input as RegimeInput  # noqa: E501
        from agents.technical_scorer import Calculate as calc_tech, Input as TechInput  # noqa: E501
        from agents.trade_gate import GateInput  # noqa: E501

        candle = self._load_candle()
        if not candle:
            return {"action": "no_data"}

        ts = candle["time"]
        if self._last_bar_ts is not None and ts == self._last_bar_ts:
            return {"action": "same_bar"}

        is_new_bar = self._last_bar_ts is not None
        self._last_bar_ts = ts
        self._bar_count += 1

        if is_new_bar:
            self.gate.on_bar()
            if self.position:
                self.position["bars_held"] += 1
                self.store.update_bars_held(
                    self.position["id"], self.position["bars_held"],
                )

            day = ts.strftime("%Y-%m-%d")
            if day != self._current_day and not self.position:
                self._reset_day(day)

        features = self._load_features(ts)
        if not features:
            self._snapshot(ts)
            return {"action": "no_features", "ts": str(ts)}

        tech_score = calc_tech(TechInput(
            price=candle["close"], ema20=features["ema20"],
            ema50=features["ema50"], ema200=features["ema200"],
            rsi14=features["rsi14"], atr14=features["atr14"],
            volume=candle["volume"], vol_ema20=features["volume_ema20"],
            adx14=features["adx14"],
        ))

        of_score = calc_of(OFInput(
            funding_rate=features["funding_rate"],
            oi_delta_pct=features["oi_delta_1_pct"],
            ls_ratio=features["ls_ratio"],
            long_liq_usd=features["liq_long_usd"],
            short_liq_usd=features["liq_short_usd"],
        ))

        regime_score = calc_regime(RegimeInput(
            adx14=features["adx14"], atr14=features["atr14"],
            price=candle["close"], volatility=features["volatility14"],
        ))

        direction = decide_direction(
            tech_score.technical_score,
            self.cfg["long_threshold"], self.cfg["short_threshold"],
        )

        if self.position:
            closed = self._check_exit(candle, direction)
            self._snapshot(ts)
            return {
                "action": "exit" if closed else "holding",
                "ts": str(ts),
                "tech_score": tech_score.technical_score,
                "regime": regime_score.regime,
            }

        if not is_new_bar or self.state == "stopped" or direction == "no_trade":
            self._snapshot(ts)
            return {"action": "skip", "ts": str(ts)}

        ml_prob = self._fetch_ml_prob(ts)
        gate_input = GateInput(
            technical_score=tech_score.technical_score,
            orderflow_score=of_score.orderflow_score,
            regime_score=regime_score.regime_score,
            regime_label=regime_score.regime,
            meta_model_prob=ml_prob,
        )
        g_out = self.gate.evaluate(gate_input)
        if g_out.decision.value == "no_trade":
            self._snapshot(ts)
            return {
                "action": "gate_rejected",
                "ts": str(ts),
                "reason": g_out.reason,
            }

        atr = features["atr14"] if features["atr14"] > 0 else candle["close"] * 0.01
        size = calc_position_size(
            self._equity, candle["close"], atr,
            self.cfg["atr_multiplier"], self.cfg["risk_per_trade_pct"],
        )
        if size <= 0:
            self._snapshot(ts)
            return {"action": "no_size", "ts": str(ts)}

        size *= g_out.size_multiplier

        entry = simulate_entry(
            candle["close"], size, direction,
            self.cfg["slippage"], self.cfg["commission"], candle["volume"],
        )

        self._open_position(candle, entry, direction, g_out, tech_score,
                            of_score, regime_score, features, ts)

        self._snapshot(ts)
        return {
            "action": "entry",
            "ts": str(ts),
            "direction": direction,
            "size": size,
            "price": entry["fill_price"],
            "confidence": g_out.raw_confidence,
        }

    def _check_exit(self, candle: dict, direction: str) -> bool:
        if not self.position:
            return False

        pos = self.position
        closed = False
        exit_price = 0.0
        reason = ""

        if (pos["direction"] == "long" and candle["low"] <= pos["stop_price"]) or \
           (pos["direction"] == "short" and candle["high"] >= pos["stop_price"]):
            exit_price = pos["stop_price"]
            reason = "stop_loss"
            closed = True

        if not closed and pos["bars_held"] >= self.cfg["holding_bars"]:
            if pos["direction"] == "long":
                exit_price = candle["close"] * (1 - self.cfg["slippage"])
            else:
                exit_price = candle["close"] * (1 + self.cfg["slippage"])
            reason = "max_hold"
            closed = True

        if not closed and direction != "no_trade" and direction != pos["direction"]:
            if pos["direction"] == "long":
                exit_price = candle["close"] * (1 - self.cfg["slippage"])
            else:
                exit_price = candle["close"] * (1 + self.cfg["slippage"])
            reason = "opposite_signal"
            closed = True

        if not closed:
            if pos["direction"] == "long":
                new_stop = candle["close"] * (1 - self.cfg["atr_multiplier"] * 0.02)
                if new_stop > pos["stop_price"]:
                    self.position["stop_price"] = new_stop
            return False

        self._close_position(candle, exit_price, reason)
        return True

    def _open_position(self, candle: dict, entry: dict, direction: str,
                       g_out, tech_score, of_score, regime_score,
                       features: dict, ts: datetime) -> None:
        entry_reason = json.dumps({
            "technical_score": tech_score.technical_score,
            "orderflow_score": of_score.orderflow_score,
            "regime_score": regime_score.regime_score,
            "confidence": g_out.raw_confidence,
            "regime_label": regime_score.regime,
            "direction": direction,
        })

        snap = json.dumps({
            "technical_score": tech_score.technical_score,
            "orderflow_score": of_score.orderflow_score,
            "regime_score": regime_score.regime_score,
            "confidence": g_out.raw_confidence,
            "regime_label": regime_score.regime,
            "atr14": features["atr14"],
            "adx14": features["adx14"],
        })

        requested_size = entry["commission"] / self.cfg["commission"]
        order = {
            "symbol": self.cfg["symbol"],
            "timeframe": self.cfg["timeframe"],
            "direction": direction,
            "status": "filled",
            "requested_size": requested_size,
            "filled_size": requested_size,
            "fill_price": entry["fill_price"],
            "slippage_pct": entry["slippage_pct"],
            "commission": entry["commission"],
            "reason": entry_reason,
            "open_ts": ts,
        }
        order_id = self.store.insert_order(order)

        fill = {
            "order_id": order_id,
            "ts": ts,
            "side": "buy" if direction == "long" else "sell",
            "price": entry["fill_price"],
            "size": requested_size,
            "fee": entry["commission"],
        }
        self.store.insert_fill(fill)

        stop_distance = features["atr14"] * self.cfg["atr_multiplier"]
        if features["atr14"] <= 0:
            stop_distance = candle["close"] * 0.01 * self.cfg["atr_multiplier"]

        if direction == "long":
            stop_price = entry["fill_price"] - stop_distance
        else:
            stop_price = entry["fill_price"] + stop_distance

        pos = {
            "symbol": self.cfg["symbol"],
            "timeframe": self.cfg["timeframe"],
            "direction": direction,
            "entry_order_id": order_id,
            "quantity": requested_size,
            "entry_price": entry["fill_price"],
            "entry_fee": entry["commission"],
            "stop_price": stop_price,
            "open_ts": ts,
            "bars_held": 0,
            "status": "open",
        }
        pos_id = self.store.insert_position(pos)
        pos["id"] = pos_id

        self.position = pos
        self._balance -= entry["commission"]
        self.gate.on_trade_placed()

        logger.info(f"[PaperEngine] ENTRY {direction} price={entry['fill_price']:.4f} "
                    f"size={requested_size:.2f} stop={stop_price:.4f} equity={self._equity:.0f}")

    def _close_position(self, candle: dict, exit_price: float, reason: str) -> None:
        if not self.position:
            return

        pos = self.position
        exit_result = simulate_exit(
            exit_price, pos["quantity"], pos["direction"],
            self.cfg["slippage"], self.cfg["commission"],
        )

        if pos["direction"] == "long":
            gross_pnl = (exit_result["fill_price"] - pos["entry_price"]) / pos["entry_price"] * pos["quantity"]
        else:
            gross_pnl = (pos["entry_price"] - exit_result["fill_price"]) / pos["entry_price"] * pos["quantity"]

        total_commission = pos["entry_fee"] + exit_result["commission"]
        net_pnl = gross_pnl - total_commission
        return_pct = net_pnl / pos["quantity"] if pos["quantity"] > 0 else 0.0

        trade = {
            "position_id": pos["id"],
            "symbol": self.cfg["symbol"],
            "timeframe": self.cfg["timeframe"],
            "direction": pos["direction"],
            "entry_ts": pos["open_ts"],
            "exit_ts": candle["time"],
            "entry_price": pos["entry_price"],
            "exit_price": exit_result["fill_price"],
            "size": pos["quantity"],
            "gross_pnl": gross_pnl,
            "commission": total_commission,
            "net_pnl": net_pnl,
            "return_pct": return_pct,
            "holding_bars": pos["bars_held"],
            "exit_reason": reason,
        }
        self.store.insert_trade(trade)
        self.store.close_position(pos["id"])

        self._balance += net_pnl + pos["quantity"]
        self._total_pnl += net_pnl
        self._day_pnl += net_pnl
        self._day_trades += 1

        self.gate.update_pnl(net_pnl)
        self.gate.on_trade_closed()

        dd_pct = self._day_pnl / self.cfg["initial_capital"] * 100
        if dd_pct <= -self.cfg["max_daily_drawdown_pct"]:
            self.state = "stopped"
            logger.warning(f"[PaperEngine] DAILY DRAWDOWN: {dd_pct:.2f}%")

        total_dd = self._total_pnl / self.cfg["initial_capital"] * 100
        if total_dd <= -self.cfg["max_total_drawdown_pct"]:
            self.state = "stopped"
            logger.warning(f"[PaperEngine] TOTAL DRAWDOWN: {total_dd:.2f}%")

        self._equity = self._balance
        self.position = None

        logger.info(f"[PaperEngine] EXIT {pos['direction']} reason={reason} "
                    f"PnL={net_pnl:.2f} return={return_pct*100:.2f}% equity={self._equity:.0f}")

    def _snapshot(self, ts: datetime) -> None:
        self.store.insert_snapshot({
            "ts": ts,
            "balance": self._balance,
            "equity": self._equity,
            "unrealized_pnl": self._equity - self._balance if self.position else 0.0,
            "day_pnl": self._day_pnl,
            "day_trades": self._day_trades,
        })

    def _reset_day(self, day: str) -> None:
        day_pnl, day_trades = self.store.load_daily_stats(day)
        self._day_pnl = day_pnl
        self._day_trades = day_trades
        self._current_day = day
        self.gate.reset_day(day, self._day_pnl)
        if self.state == "stopped":
            self.state = "running"
            logger.info(f"[PaperEngine] Day reset {day} — resumed")

    def _fetch_ml_prob(self, ts: datetime) -> float:
        ml_url = self.cfg.get("ml_api_url", "")
        if not ml_url:
            return 1.0
        try:
            import urllib.request
            url = (f"{ml_url}/api/model/predict?ts={ts.isoformat()}"
                   f"&horizon=4&symbol={self.cfg['symbol']}&timeframe={self.cfg['timeframe']}")
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
                return float(data.get("prob", 1.0))
        except Exception:
            return 1.0
