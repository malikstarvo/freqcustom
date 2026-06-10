"""
TimescaleDB persistence for paper trading engine.

Ported from internal/papertrade/store.go
"""

from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

import psycopg2
import psycopg2.pool


PAPER_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS paper_orders (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    requested_size DECIMAL,
    filled_size DECIMAL,
    fill_price DECIMAL,
    slippage_pct DECIMAL,
    commission DECIMAL,
    reason TEXT,
    open_ts TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS paper_fills (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES paper_orders(id),
    ts TIMESTAMPTZ NOT NULL,
    side TEXT NOT NULL,
    price DECIMAL NOT NULL,
    size DECIMAL NOT NULL,
    fee DECIMAL NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_positions (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_order_id BIGINT NOT NULL REFERENCES paper_orders(id),
    quantity DECIMAL NOT NULL,
    entry_price DECIMAL NOT NULL,
    entry_fee DECIMAL NOT NULL,
    stop_price DECIMAL NOT NULL,
    open_ts TIMESTAMPTZ NOT NULL,
    bars_held INTEGER DEFAULT 0,
    status TEXT DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS paper_trades (
    id BIGSERIAL PRIMARY KEY,
    position_id BIGINT NOT NULL REFERENCES paper_positions(id),
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_ts TIMESTAMPTZ NOT NULL,
    exit_ts TIMESTAMPTZ NOT NULL,
    entry_price DECIMAL NOT NULL,
    exit_price DECIMAL NOT NULL,
    size DECIMAL NOT NULL,
    gross_pnl DECIMAL NOT NULL DEFAULT 0,
    commission DECIMAL NOT NULL DEFAULT 0,
    net_pnl DECIMAL NOT NULL DEFAULT 0,
    return_pct DECIMAL NOT NULL DEFAULT 0,
    holding_bars INTEGER DEFAULT 0,
    exit_reason TEXT,
    entry_reason TEXT,
    feature_snapshot TEXT
);

CREATE TABLE IF NOT EXISTS paper_account_snapshots (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    balance DECIMAL NOT NULL,
    equity DECIMAL NOT NULL,
    unrealized_pnl DECIMAL DEFAULT 0,
    day_pnl DECIMAL DEFAULT 0,
    day_trades INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS paper_topups (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    amount DECIMAL NOT NULL,
    balance_before DECIMAL NOT NULL,
    balance_after DECIMAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paper_orders_symbol ON paper_orders(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_paper_positions_open ON paper_positions(symbol, timeframe) WHERE status = 'open';
CREATE INDEX IF NOT EXISTS idx_paper_trades_symbol ON paper_trades(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_paper_snapshots_ts ON paper_account_snapshots(ts DESC);
CREATE INDEX IF NOT EXISTS idx_paper_topups_ts ON paper_topups(ts DESC);
"""


class PaperStore:
    def __init__(self, dsn: str) -> None:
        self._pool = psycopg2.pool.ThreadedConnectionPool(1, 5, dsn)
        self._init_tables()

    @contextmanager
    def _conn(self) -> Iterator:
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    def _init_tables(self) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(PAPER_TABLES_SQL)
            conn.commit()

    def insert_order(self, order: dict) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO paper_orders
                    (symbol, timeframe, direction, status, requested_size,
                     filled_size, fill_price, slippage_pct, commission, reason, open_ts)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id""",
                    (order["symbol"], order["timeframe"], order["direction"],
                     order["status"], order["requested_size"], order["filled_size"],
                     order["fill_price"], order["slippage_pct"], order["commission"],
                     order["reason"], order["open_ts"]),
                )
                row = cur.fetchone()
                order_id = row[0] if row else 0
            conn.commit()
        return order_id

    def insert_fill(self, fill: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO paper_fills (order_id, ts, side, price, size, fee)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    (fill["order_id"], fill["ts"], fill["side"],
                     fill["price"], fill["size"], fill["fee"]),
                )
            conn.commit()

    def insert_position(self, pos: dict) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO paper_positions
                    (symbol, timeframe, direction, entry_order_id, quantity,
                     entry_price, entry_fee, stop_price, open_ts)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id""",
                    (pos["symbol"], pos["timeframe"], pos["direction"],
                     pos["entry_order_id"], pos["quantity"], pos["entry_price"],
                     pos["entry_fee"], pos["stop_price"], pos["open_ts"]),
                )
                row = cur.fetchone()
                pos_id = row[0] if row else 0
            conn.commit()
        return pos_id

    def close_position(self, position_id: int) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE paper_positions SET status = 'closed' WHERE id = %s",
                    (position_id,),
                )
            conn.commit()

    def update_bars_held(self, position_id: int, bars: int) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE paper_positions SET bars_held = %s WHERE id = %s",
                    (bars, position_id),
                )
            conn.commit()

    def insert_trade(self, trade: dict) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO paper_trades
                    (position_id, symbol, timeframe, direction, entry_ts, exit_ts,
                     entry_price, exit_price, size, gross_pnl, commission,
                     net_pnl, return_pct, holding_bars, exit_reason,
                     entry_reason, feature_snapshot)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id""",
                    (trade["position_id"], trade["symbol"], trade["timeframe"],
                     trade["direction"], trade["entry_ts"], trade["exit_ts"],
                     trade["entry_price"], trade["exit_price"], trade["size"],
                     trade["gross_pnl"], trade["commission"], trade["net_pnl"],
                     trade["return_pct"], trade["holding_bars"],
                     trade["exit_reason"], trade.get("entry_reason", ""),
                     trade.get("feature_snapshot", "")),
                )
                row = cur.fetchone()
                trade_id = row[0] if row else 0
            conn.commit()
        return trade_id

    def insert_snapshot(self, snap: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO paper_account_snapshots
                    (ts, balance, equity, unrealized_pnl, day_pnl, day_trades)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    (snap["ts"], snap["balance"], snap["equity"],
                     snap["unrealized_pnl"], snap["day_pnl"], snap["day_trades"]),
                )
            conn.commit()

    def insert_top_up(self, amount: float, balance_before: float,
                      balance_after: float, ts: datetime) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO paper_topups (ts, amount, balance_before, balance_after)
                    VALUES (%s,%s,%s,%s)""",
                    (ts, amount, balance_before, balance_after),
                )
            conn.commit()

    def load_open_position(self, symbol: str, timeframe: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, symbol, timeframe, direction, entry_order_id,
                       quantity, entry_price, entry_fee, stop_price, open_ts,
                       bars_held, status
                    FROM paper_positions
                    WHERE symbol = %s AND timeframe = %s AND status = 'open'
                    ORDER BY id DESC LIMIT 1""",
                    (symbol, timeframe),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "id": row[0], "symbol": row[1], "timeframe": row[2],
                    "direction": row[3], "entry_order_id": row[4],
                    "quantity": float(row[5]), "entry_price": float(row[6]),
                    "entry_fee": float(row[7]), "stop_price": float(row[8]),
                    "open_ts": row[9], "bars_held": row[10], "status": row[11],
                }

    def load_daily_stats(self, day: str) -> tuple[float, int]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT COALESCE(SUM(net_pnl), 0), COUNT(*)
                    FROM paper_trades
                    WHERE entry_ts::date = %s::date""",
                    (day,),
                )
                row = cur.fetchone()
                if row:
                    return float(row[0]), int(row[1])
                return 0.0, 0

    def load_total_pnl(self) -> float:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(SUM(net_pnl), 0) FROM paper_trades")
                row = cur.fetchone()
                return float(row[0]) if row else 0.0

    def get_trades(self, limit: int = 50) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, symbol, direction, entry_price, exit_price,
                              size, net_pnl, return_pct, holding_bars, exit_reason,
                              entry_ts, exit_ts
                       FROM paper_trades
                       ORDER BY id DESC LIMIT %s""",
                    (limit,),
                )
                rows = cur.fetchall()
                return [
                    {
                        "id": r[0],
                        "symbol": r[1],
                        "direction": r[2],
                        "entry_price": float(r[3]),
                        "exit_price": float(r[4]),
                        "size": float(r[5]),
                        "net_pnl": float(r[6]),
                        "return_pct": float(r[7]) if r[7] else 0.0,
                        "holding_bars": int(r[8]) if r[8] else 0,
                        "exit_reason": r[9] or "",
                        "entry_ts": str(r[10]) if r[10] else "",
                        "exit_ts": str(r[11]) if r[11] else "",
                    }
                    for r in rows
                ]

    def get_account_snapshots(self, limit: int = 100) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT ts, balance, equity, unrealized_pnl, day_pnl, day_trades
                       FROM paper_account_snapshots
                       ORDER BY ts DESC LIMIT %s""",
                    (limit,),
                )
                rows = cur.fetchall()
                return [
                    {
                        "ts": str(r[0]) if r[0] else "",
                        "balance": float(r[1]),
                        "equity": float(r[2]),
                        "unrealized_pnl": float(r[3]) if r[3] else 0.0,
                        "day_pnl": float(r[4]) if r[4] else 0.0,
                        "day_trades": int(r[5]) if r[5] else 0,
                    }
                    for r in rows
                ]
