"""Run freqtrade backtest with bytick.com hostname override (workaround for
local network blocking api.bybit.com SSL).
"""
import json
import os
import sys
import time
import shutil
import subprocess
import zipfile
from pathlib import Path

PROJECT = Path(r"C:\Users\avav\Documents\freqtrade")
SRC_CONFIG = PROJECT / "config.json"
LOG_DIR = Path(r"C:\Users\avav\AppData\Local\Temp\opencode")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def make_patched_config(src: Path, dst: Path) -> Path:
    """Patch ccxt_config to add bytick.com hostname override (top-level)."""
    cfg = json.loads(src.read_text())
    exch = cfg.setdefault("exchange", {})
    # Top-level hostname (not nested in options) - ccxt reads it correctly
    ccxt_cfg = exch.setdefault("ccxt_config", {})
    ccxt_cfg["hostname"] = "bytick.com"
    ccxt_async = exch.setdefault("ccxt_async_config", {})
    ccxt_async["hostname"] = "bytick.com"
    dst.write_text(json.dumps(cfg, indent=2))
    return dst


def run_backtest(timerange, timeframe, pairs, tag, timeout_sec=1800):
    cfg_local = LOG_DIR / f"config_{tag}.json"
    patched = make_patched_config(SRC_CONFIG, cfg_local)
    log = LOG_DIR / f"bt_{tag}.log"
    err = LOG_DIR / f"bt_{tag}.log.err"
    cmd = [
        "freqtrade", "backtesting",
        "--config", str(patched),
        "--timerange", timerange,
        "--timeframe", timeframe,
        "--pairs", pairs,
        "--userdir", "user_data",
    ]
    print(f"$ {' '.join(cmd)}", flush=True)
    print(f"  log: {log}", flush=True)
    t0 = time.time()
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "2"
    env["OPENBLAS_NUM_THREADS"] = "2"
    env["MKL_NUM_THREADS"] = "2"
    with open(log, "w") as outf, open(err, "w") as errf:
        r = subprocess.run(cmd, stdout=outf, stderr=errf, cwd=str(PROJECT), env=env, timeout=timeout_sec)
    elapsed = time.time() - t0
    print(f"  exit: {r.returncode}, elapsed: {elapsed:.1f}s", flush=True)
    if r.returncode != 0:
        print(f"  STDERR (last 1500 chars):", flush=True)
        print(err.read_text()[-1500:], flush=True)
        return None
    return elapsed


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        tag = sys.argv[1]
    else:
        tag = "iter1_baseline"
    timerange = sys.argv[2] if len(sys.argv) >= 3 else "20240101-20251231"
    elapsed = run_backtest(timerange, "15m", "SOL/USDT:USDT", tag)
    if elapsed is None:
        sys.exit(1)
    print(f"DONE in {elapsed:.1f}s")
