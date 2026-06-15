"""Convert downloaded funding_rate to freqtrade-compatible OHLCV format.

Freqtrade auto-downloaded funding_rate files have OHLCV schema with the
funding rate written to the 'open' column (other columns 0). Reformat
our downloaded file to match.
"""
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SRC = Path("user_data/data/bybit/futures/SOL_USDT_USDT-1h-funding_rate.feather")

if SRC.exists():
    df = pd.read_feather(SRC)
    if list(df.columns) == ["date", "funding_rate"]:
        print("Converting to OHLCV format...", flush=True)
        out = pd.DataFrame({
            "date": df["date"],
            "open": df["funding_rate"],
            "high": df["funding_rate"],
            "low": df["funding_rate"],
            "close": df["funding_rate"],
            "volume": 0.0,
        })
        out.to_feather(SRC)
        print(f"Converted: {len(out)} rows", flush=True)
    else:
        print(f"Already OHLCV: {df.columns.tolist()}", flush=True)
else:
    print(f"missing: {SRC}", flush=True)
