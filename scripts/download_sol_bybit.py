"""
Download SOL/USDT:USDT 1m historical data from Bybit via CCXT.
Outputs freqtrade-compatible feather file.

Usage: python download_sol_bybit.py
"""
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import ccxt
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ── Config ───────────────────────────────────────────────────────
SYMBOL = "SOL/USDT:USDT"
TIMEFRAME = "1m"
EXCHANGE_NAME = "bybit"
START = datetime(2021, 3, 1, tzinfo=timezone.utc)
END = datetime.now(timezone.utc)
BATCH_SIZE = 1000
RATE_SLEEP = 0.12
MAX_RETRIES = 5
OUT_DIR = Path("user_data/data/bybit/futures")
OUT_FILE = OUT_DIR / f"SOL_USDT_USDT-1m.feather"


def fetch_all_ohlcv(exchange, symbol, timeframe, start_ms, end_ms):
    """Walk forward through history, 1000 candles per request."""
    all_candles = []
    cursor = start_ms
    batch_num = 0
    last_ts = None

    while cursor < end_ms:
        for attempt in range(MAX_RETRIES):
            try:
                candles = exchange.fetch_ohlcv(
                    symbol, timeframe, since=cursor, limit=BATCH_SIZE
                )
                break
            except ccxt.RateLimitExceeded as e:
                wait = 5 * (attempt + 1)
                print(f"  rate-limited, sleep {wait}s ...", flush=True)
                time.sleep(wait)
            except ccxt.NetworkError as e:
                wait = 2 * (attempt + 1)
                print(f"  network error: {e}, sleep {wait}s ...", flush=True)
                time.sleep(wait)
            except ccxt.ExchangeError as e:
                wait = 3 * (attempt + 1)
                print(f"  exchange error: {e}, sleep {wait}s ...", flush=True)
                time.sleep(wait)
        else:
            print(f"  failed after {MAX_RETRIES} retries, aborting", flush=True)
            sys.exit(1)

        if not candles:
            break

        all_candles.extend(candles)
        last_ts = candles[-1][0]
        batch_num += 1

        if batch_num % 20 == 0:
            n = len(all_candles)
            head = datetime.fromtimestamp(candles[0][0] / 1000, tz=timezone.utc)
            tail = datetime.fromtimestamp(candles[-1][0] / 1000, tz=timezone.utc)
            print(f"  batch {batch_num:4d}: {n:>8} candles | {head} → {tail}", flush=True)

        if last_ts == cursor:
            print("  cursor stalled, advancing 1ms", flush=True)
            cursor += 60_000
        else:
            cursor = last_ts + 60_000

        time.sleep(RATE_SLEEP)

    return all_candles


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUT_FILE.exists():
        print(f"already exists: {OUT_FILE}", flush=True)
        return 0

    print(f"Exchange: {EXCHANGE_NAME}", flush=True)
    print(f"Symbol:   {SYMBOL}", flush=True)
    print(f"Range:    {START.date()} → {END.date()}", flush=True)
    print(f"Output:   {OUT_FILE}", flush=True)
    print("=" * 60, flush=True)

    exchange = getattr(ccxt, EXCHANGE_NAME)({
        "options": {"defaultType": "linear"},
        "enableRateLimit": False,
        "hostname": "bytick.com",
    })
    exchange.load_markets()

    if SYMBOL not in exchange.markets:
        print(f"ERROR: {SYMBOL} not found on {EXCHANGE_NAME}", flush=True)
        return 1

    start_ms = int(START.timestamp() * 1000)
    end_ms = int(END.timestamp() * 1000)
    t0 = time.time()
    raw = fetch_all_ohlcv(exchange, SYMBOL, TIMEFRAME, start_ms, end_ms)
    elapsed = time.time() - t0

    if not raw:
        print("no data received", flush=True)
        return 1

    df = pd.DataFrame(raw, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

    head = datetime.fromtimestamp(df["date"].iloc[0] / 1000, tz=timezone.utc)
    tail = datetime.fromtimestamp(df["date"].iloc[-1] / 1000, tz=timezone.utc)
    expected_days = (END - head).days
    print("=" * 60, flush=True)
    print(f"Fetched:  {len(df):>8} candles", flush=True)
    print(f"Range:    {head} → {tail}", flush=True)
    print(f"Elapsed:  {elapsed:.1f}s ({elapsed/60:.1f} min)", flush=True)
    print(f"File:     {OUT_FILE}", flush=True)

    df.to_feather(OUT_FILE)
    print("OK", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
