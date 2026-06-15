"""Resample 1m feather to 5m/15m/1h/4h feather files (freqtrade-compatible).

Freqtrade expects feather files to have a 'date' column as datetime64 dtype
(not int64). The handler calls `.dt.as_unit("ms")` on the date column.
"""
import sys
from pathlib import Path

import pandas as pd

SRC = Path("/freqtrade/user_data/data/bybit/futures/SOL_USDT_USDT-1m.feather")
DST_DIR = SRC.parent
TIMEFRAMES = {
    "5m": "5min",
    "15m": "15min",
    "1h": "1h",
    "4h": "4h",
}


def main():
    if not SRC.exists():
        print(f"missing: {SRC}", flush=True)
        return 1

    print(f"reading: {SRC}", flush=True)
    df = pd.read_feather(SRC)
    print(f"  rows:   {len(df):>10}", flush=True)
    print(f"  date head: {df['date'].iloc[0]} | tail: {df['date'].iloc[-1]}", flush=True)

    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
    df = df.set_index("date").sort_index()
    print(f"  range:  {df.index.min()} → {df.index.max()}", flush=True)

    for tf, rule in TIMEFRAMES.items():
        out = DST_DIR / f"SOL_USDT_USDT-{tf}.feather"
        if out.exists():
            print(f"  exists: {out.name}", flush=True)
            continue
        agg = df.resample(rule).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna(subset=["open"])
        agg = agg.reset_index()
        agg = agg[["date", "open", "high", "low", "close", "volume"]]
        agg.to_feather(out)
        print(f"  wrote:  {out.name:30s} {len(agg):>9} rows | {agg['date'].iloc[0]} → {agg['date'].iloc[-1]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
