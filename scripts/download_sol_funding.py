"""Download SOL/USDT:USDT historical funding rate from Bybit via CCXT.

Bybit linear perpetual funding happens every 8h.
Max 200 records per request. ~6,000 events from 2021-03 to 2026-06 = ~30 requests.
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

SYMBOL = "SOL/USDT:USDT"
EXCHANGE_NAME = "bybit"
START = datetime(2021, 3, 1, tzinfo=timezone.utc)
END = datetime.now(timezone.utc)
BATCH_SIZE = 200
RATE_SLEEP = 0.25
MAX_RETRIES = 5
OUT_DIR = Path("user_data/data/bybit/futures")
OUT_FILE = OUT_DIR / "SOL_USDT_USDT-1h-funding_rate.feather"


def fetch_all_funding(exchange, symbol, start_ms, end_ms):
    """Walk backward through funding rate history using direct v5 API.

    Bybit v5 funding history endpoint accepts startTime + endTime, returns
    newest-first. CCXT's high-level wrapper does not honor endTime.
    """
    all_records = []
    cursor_end = end_ms
    batch_num = 0

    while cursor_end > start_ms:
        for attempt in range(MAX_RETRIES):
            try:
                r = exchange.publicGetV5MarketFundingHistory(
                    exchange.extend({
                        "category": "linear",
                        "symbol": "SOLUSDT",
                        "limit": BATCH_SIZE,
                        "startTime": start_ms,
                        "endTime": cursor_end,
                    })
                )
                break
            except ccxt.RateLimitExceeded:
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

        data = r.get("result", {}).get("list", [])
        if not data:
            break

        # v5 returns newest first; convert to ccxt-like record
        for item in data:
            ts = int(item["fundingRateTimestamp"])
            all_records.append({
                "timestamp": ts,
                "datetime": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat(),
                "symbol": symbol,
                "fundingRate": float(item["fundingRate"]),
            })

        batch_num += 1
        if batch_num % 5 == 0:
            n = len(all_records)
            head_ts = int(data[0]["fundingRateTimestamp"])
            tail_ts = int(data[-1]["fundingRateTimestamp"])
            head = datetime.fromtimestamp(head_ts / 1000, tz=timezone.utc)
            tail = datetime.fromtimestamp(tail_ts / 1000, tz=timezone.utc)
            print(f"  batch {batch_num:3d}: {n:>6} records | {head} → {tail}", flush=True)

        oldest_ts = int(data[-1]["fundingRateTimestamp"])
        if oldest_ts >= cursor_end - 1000:
            break
        cursor_end = oldest_ts
        time.sleep(RATE_SLEEP)

    return all_records


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
        "options": {"defaultType": "swap", "defaultSubType": "linear"},
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
    raw = fetch_all_funding(exchange, SYMBOL, start_ms, end_ms)
    elapsed = time.time() - t0

    if not raw:
        print("no data received", flush=True)
        return 1

    df = pd.DataFrame(raw)
    if "timestamp" in df.columns:
        df = df[["timestamp", "fundingRate"]].copy()
        df = df.rename(columns={"timestamp": "date", "fundingRate": "funding_rate"})
    else:
        print(f"unexpected columns: {df.columns.tolist()}", flush=True)
        return 1

    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

    head = df["date"].iloc[0]
    tail = df["date"].iloc[-1]
    print("=" * 60, flush=True)
    print(f"Fetched:  {len(df):>6} records", flush=True)
    print(f"Range:    {head} → {tail}", flush=True)
    print(f"Elapsed:  {elapsed:.1f}s", flush=True)
    print(f"File:     {OUT_FILE}", flush=True)

    df.to_feather(OUT_FILE)
    print("OK", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
