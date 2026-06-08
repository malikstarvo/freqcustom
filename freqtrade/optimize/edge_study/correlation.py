import math
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg2
import psycopg2.pool


def _correlation_sql() -> str:
    return """
        SELECT
            CORR(fv.{feature_col}::numeric, l.{label_col}::numeric) AS pearson,
            CORR(
                RANK() OVER (ORDER BY fv.{feature_col}),
                RANK() OVER (ORDER BY l.{label_col})
            ) AS spearman,
            COUNT(*) AS samples
        FROM feature_values fv
        JOIN labels l ON fv.symbol = l.symbol
            AND fv.timeframe = l.timeframe
            AND fv.ts = l.ts
        WHERE fv.symbol = %s
            AND fv.timeframe = %s
            AND fv.feature_set_id = %s
            AND fv.{feature_col} IS NOT NULL
            AND l.{label_col} IS NOT NULL
    """


def _quantile_sql() -> str:
    return """
        WITH ranked AS (
            SELECT
                fv.{feature_col},
                l.{label_col},
                NTILE(%s) OVER (ORDER BY fv.{feature_col}) AS bucket
            FROM feature_values fv
            JOIN labels l ON fv.symbol = l.symbol
                AND fv.timeframe = l.timeframe
                AND fv.ts = l.ts
            WHERE fv.symbol = %s
                AND fv.timeframe = %s
                AND fv.feature_set_id = %s
                AND fv.{feature_col} IS NOT NULL
                AND l.{label_col} IS NOT NULL
        )
        SELECT
            bucket,
            MIN({feature_col}) AS feature_min,
            MAX({feature_col}) AS feature_max,
            AVG({label_col}) AS avg_return,
            SUM(CASE WHEN {label_col} > 0 THEN {label_col} ELSE 0 END) /
                NULLIF(SUM(CASE WHEN {label_col} < 0 THEN ABS({label_col}) ELSE 0 END), 0) AS profit_factor,
            SUM(CASE WHEN {label_col} > 0 THEN 1 ELSE 0 END)::float /
                NULLIF(COUNT(*), 0) AS win_rate,
            COUNT(*) AS trades,
            SUM({label_col}) AS total_return
        FROM ranked
        GROUP BY bucket
        ORDER BY bucket
    """


def _rolling_correlation_sql() -> str:
    return """
        WITH ordered AS (
            SELECT
                fv.ts,
                fv.{feature_col},
                l.{label_col}
            FROM feature_values fv
            JOIN labels l ON fv.symbol = l.symbol
                AND fv.timeframe = l.timeframe
                AND fv.ts = l.ts
            WHERE fv.symbol = %s
                AND fv.timeframe = %s
                AND fv.feature_set_id = %s
                AND fv.{feature_col} IS NOT NULL
                AND l.{label_col} IS NOT NULL
            ORDER BY fv.ts
        ),
        indexed AS (
            SELECT
                ts,
                {feature_col},
                {label_col},
                ROW_NUMBER() OVER (ORDER BY ts) AS rn
            FROM ordered
        )
        SELECT
            CORR(f.{feature_col}, f.{label_col}) AS corr,
            (SELECT ts FROM indexed WHERE rn = f.end_rn) AS ts
        FROM (
            SELECT
                end_rn,
                UNNEST(
                    ARRAY_AGG({feature_col}) OVER (ORDER BY rn ROWS BETWEEN %s - 1 PRECEDING AND CURRENT ROW)
                ) AS {feature_col},
                UNNEST(
                    ARRAY_AGG({label_col}) OVER (ORDER BY rn ROWS BETWEEN %s - 1 PRECEDING AND CURRENT ROW)
                ) AS {label_col}
            FROM indexed
        ) f
        WHERE f.end_rn >= %s
        GROUP BY f.end_rn
        ORDER BY f.end_rn
    """


def _regime_correlation_sql() -> str:
    return """
        SELECT
            CASE
                WHEN fv.adx14 >= 25 AND fv.volatility14 >= 1.5
                    THEN 'trending_high_vol'
                WHEN fv.adx14 >= 25 AND fv.volatility14 < 1.5
                    THEN 'trending_low_vol'
                WHEN fv.adx14 < 25 AND fv.volatility14 >= 1.5
                    THEN 'ranging_high_vol'
                ELSE 'ranging_low_vol'
            END AS regime,
            CORR(fv.{feature_col}::numeric, l.{label_col}::numeric) AS corr,
            COUNT(*) AS samples
        FROM feature_values fv
        JOIN labels l ON fv.symbol = l.symbol
            AND fv.timeframe = l.timeframe
            AND fv.ts = l.ts
        WHERE fv.symbol = %s
            AND fv.timeframe = %s
            AND fv.feature_set_id = %s
            AND fv.{feature_col} IS NOT NULL
            AND l.{label_col} IS NOT NULL
        GROUP BY regime
        ORDER BY regime
    """


class EdgeStore:
    def __init__(self, dsn: str) -> None:
        self._pool = psycopg2.pool.ThreadedConnectionPool(1, 5, dsn)

    @contextmanager
    def _conn(self) -> Iterator:
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    def correlation(
        self, feature_col: str, label_col: str,
        symbol: str, timeframe: str, feature_set_id: int,
    ) -> tuple[float, float, int]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                sql = _correlation_sql().format(
                    feature_col=feature_col, label_col=label_col,
                )
                cur.execute(sql, (symbol, timeframe, feature_set_id))
                row = cur.fetchone()
                if row and row[0] is not None:
                    pearson = float(row[0]) if not (row[0] is None or math.isnan(row[0])) else 0.0
                    spearman = float(row[1]) if not (row[1] is None or math.isnan(row[1])) else 0.0
                    samples = int(row[2]) if row[2] else 0
                    return pearson, spearman, samples
                return 0.0, 0.0, 0

    def quantiles(
        self, feature_col: str, label_col: str,
        symbol: str, timeframe: str, feature_set_id: int, n_buckets: int,
    ) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                sql = _quantile_sql().format(
                    feature_col=feature_col, label_col=label_col,
                )
                cur.execute(sql, (n_buckets, symbol, timeframe, feature_set_id))
                rows = cur.fetchall()
                result = []
                for row in rows:
                    result.append({
                        "bucket": int(row[0]),
                        "feature_min": float(row[1]) if row[1] else 0,
                        "feature_max": float(row[2]) if row[2] else 0,
                        "avg_return": float(row[3]) if row[3] else 0,
                        "profit_factor": float(row[4]) if row[4] else 0,
                        "win_rate": float(row[5]) if row[5] else 0,
                        "trades": int(row[6]) if row[6] else 0,
                        "total_return": float(row[7]) if row[7] else 0,
                    })
                return result

    def rolling_correlation(
        self, feature_col: str, label_col: str,
        symbol: str, timeframe: str, feature_set_id: int, window: int,
    ) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                sql = _rolling_correlation_sql().format(
                    feature_col=feature_col, label_col=label_col,
                )
                cur.execute(sql, (symbol, timeframe, feature_set_id,
                                window, window, window))
                rows = cur.fetchall()
                result = []
                for row in rows:
                    corr = float(row[0]) if row[0] is not None and not math.isnan(row[0]) else 0.0
                    ts = row[1]
                    result.append({"corr": corr, "ts": ts})
                return result

    def regime_correlations(
        self, feature_col: str, label_col: str,
        symbol: str, timeframe: str, feature_set_id: int,
    ) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                sql = _regime_correlation_sql().format(
                    feature_col=feature_col, label_col=label_col,
                )
                cur.execute(sql, (symbol, timeframe, feature_set_id))
                rows = cur.fetchall()
                result = []
                for row in rows:
                    result.append({
                        "regime": row[0],
                        "corr": float(row[1]) if row[1] is not None and not math.isnan(row[1]) else 0.0,
                        "samples": int(row[2]) if row[2] else 0,
                    })
                return result

    def count_features(self, feature_set_id: int) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM feature_values WHERE feature_set_id = %s",
                    (feature_set_id,),
                )
                row = cur.fetchone()
                return int(row[0]) if row else 0
