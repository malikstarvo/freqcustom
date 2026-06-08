import logging
import threading
import time

import psycopg2
import psycopg2.pool

from freqtrade.papertrade.engine import PaperEngine
from freqtrade.papertrade.store import PaperStore

logger = logging.getLogger(__name__)


def _build_pool(database_url: str) -> psycopg2.pool.ThreadedConnectionPool:
    return psycopg2.pool.ThreadedConnectionPool(1, 5, database_url)


def start_paper_trader(args: dict) -> None:
    config = args.get("config", {})
    paper_cfg = config.get("paper_trader", {})
    ts_cfg = config.get("timescaledb", {})

    database_url = ts_cfg.get("database_url", "")
    if not database_url:
        logger.error("timescaledb.database_url is required in config")
        return

    engine_config = {
        "symbol": paper_cfg.get("symbol", "BTCUSDT"),
        "timeframe": paper_cfg.get("timeframe", "15m"),
        "initial_capital": paper_cfg.get("initial_capital", 10_000.0),
        "commission": paper_cfg.get("commission", 0.00055),
        "slippage": paper_cfg.get("slippage", 0.0005),
        "atr_multiplier": paper_cfg.get("atr_multiplier", 2.0),
        "holding_bars": paper_cfg.get("holding_bars", 24),
        "poll_interval_sec": paper_cfg.get("poll_interval_sec", 60),
        "risk_per_trade_pct": paper_cfg.get("risk_per_trade_pct", 1.0),
        "max_daily_drawdown_pct": paper_cfg.get("max_daily_drawdown_pct", 5.0),
        "max_total_drawdown_pct": paper_cfg.get("max_total_drawdown_pct", 15.0),
        "long_threshold": paper_cfg.get("long_threshold", 60.0),
        "short_threshold": paper_cfg.get("short_threshold", 40.0),
        "ml_api_url": paper_cfg.get("ml_api_url", ""),
        "feature_set_id": ts_cfg.get("feature_set_id", 1),
    }

    store = PaperStore(database_url)
    feature_pool = _build_pool(database_url)
    engine = PaperEngine(engine_config, store, feature_pool)

    engine.recover()

    stop_event = threading.Event()

    def _run_loop() -> None:
        logger.info(f"[PaperTrader] Started: {engine_config['symbol']} "
                    f"{engine_config['timeframe']} capital={engine_config['initial_capital']}")
        while not stop_event.is_set():
            try:
                result = engine.tick()
                if result.get("action") in ("entry", "exit"):
                    logger.info(f"[PaperTrader] {result}")
            except Exception as e:
                logger.error(f"[PaperTrader] tick error: {e}")

            stop_event.wait(timeout=engine_config["poll_interval_sec"])

    thread = threading.Thread(target=_run_loop, daemon=True)
    thread.start()

    logger.info("[PaperTrader] Running in background. Use API to check status.")

    try:
        while thread.is_alive():
            thread.join(1)
    except KeyboardInterrupt:
        stop_event.set()
        logger.info("[PaperTrader] Shutting down...")
