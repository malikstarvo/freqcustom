import argparse
import inspect
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import rapidjson
except ImportError:
    rapidjson = json

from freqtrade_client import __version__
from freqtrade_client.ft_rest_client import FtRestClient
from freqtrade_client.ft_formatter import format_output

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

if HAS_RICH:
    # Force UTF-8 on Windows to avoid cp1252 Unicode errors with Rich
    if sys.platform == "win32":
        import io
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    console = Console()
    _err_console = Console(stderr=True)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("ft_rest_client")


# ── Args ────────────────────────────────────────────

def add_arguments(args: Any = None):
    parser = argparse.ArgumentParser(
        prog="freq",
        description="\U0001f4c8 Freqtrade REST API Client",
    )
    parser.add_argument(
        "command", help="Command to execute (use --show to list).", nargs="?"
    )
    parser.add_argument(
        "-V", "--version", action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--show", action="store_true", default=False,
        help="List all available commands."
    )
    parser.add_argument(
        "--json", action="store_true", default=False,
        help="Output raw JSON instead of formatted tables."
    )
    parser.add_argument(
        "-c", "--config", type=str, metavar="PATH", default="config.json",
        help="Configuration file (default: config.json)."
    )
    parser.add_argument(
        "-s", "--server", type=str, metavar="URL", default=None,
        help="API server URL (e.g. http://43.159.56.168:8080)."
    )
    parser.add_argument(
        "command_arguments", nargs="*", default=[],
        help="Arguments for [command] as key=value pairs."
    )
    pargs = parser.parse_args(args)
    return vars(pargs)


# ── Config ──────────────────────────────────────────

def load_config(configfile: str) -> dict:
    file = Path(configfile)
    if file.is_file():
        with file.open("r") as f:
            if rapidjson is json:
                return rapidjson.load(f)
            return rapidjson.load(
                f, parse_mode=rapidjson.PM_COMMENTS | rapidjson.PM_TRAILING_COMMAS
            )
    _fail(f"Config file not found: {configfile}")


# ── Helpers ─────────────────────────────────────────

def _fail(msg: str) -> None:
    if HAS_RICH:
        _err_console.print(f"  [red]!![/] {msg}")
    else:
        print(f"ERROR: {msg}")
    sys.exit(1)


def _ok(msg: str) -> None:
    if HAS_RICH:
        console.print(f"  [green]>>[/] {msg}")
    else:
        print(f"OK: {msg}")


# ── Show Commands ───────────────────────────────────

CATEGORY_ICONS = {
    "Bot Control":   ">>",
    "Dashboard":     "()",
    "Account":       "$$",
    "Trades":        "<>",
    "Trading":       "!!",
    "Locks":         "##",
    "Paper Trading": "[]",
    "Backtest":      "~~",
    "Strategy":      "**",
    "Model":         "**",
    "Pairs":         "<>",
    "Config":        "{}",
    "System":        "ii",
}

def print_commands():
    client = FtRestClient(None)

    if not HAS_RICH:
        print("Possible commands:\n")
        for name, _ in inspect.getmembers(client):
            if not name.startswith("_"):
                doc = re.sub(r":return:.*", "", getattr(client, name).__doc__ or "", flags=re.MULTILINE).strip()
                print(f"  {name}\n\t{doc}\n")
        return

    all_methods = {n for n, _ in inspect.getmembers(client) if not n.startswith("_")}

    # ═══ Banner ══════════════════════════════════════
    console.print()
    banner = Panel(
        Align.center(
            Text.assemble(
                ("\n     ", "bold cyan"),
                (" Freqtrade AI Dashboard CLI ", "bold white"),
                ("\n", "bold cyan"),
                ("     ", "bold cyan"),
                (f" v{__version__}  .  ", "dim"),
                (f"{len(all_methods)} commands ", "white"),
                (f" .  ", "dim"),
                ("REST + WebSocket", "dim"),
                ("\n", "bold cyan"),
                ("     ", "bold cyan"),
                ("-" * 34, "bold cyan"),
                ("", "bold cyan"),
            )
        ),
        box=box.DOUBLE, border_style="cyan",
        padding=(0, 4),
    )
    console.print(banner)

    # ═══ Category Tables ══════════════════════════════
    commands_by_category: dict[str, list[str]] = {
        "Bot Control": ["start", "stop", "stopbuy", "reload_config"],
        "Dashboard": ["dashboard"],
        "Account": ["balance", "count", "profit", "daily", "weekly", "monthly", "stats"],
        "Trades": ["trades", "trade", "status", "performance", "entries", "exits", "mix_tags"],
        "Trading": ["forceenter", "forceexit", "forcebuy", "delete_trade", "cancel_open_order"],
        "Locks": ["locks", "lock_add", "delete_lock"],
        "Paper Trading": ["paper_status", "paper_topup", "paper_trades", "paper_account"],
        "Backtest": ["backtest_start", "backtest_status", "backtest_delete", "backtest_abort",
                      "backtest_history", "backtest_history_result", "backtest_history_delete",
                      "backtest_run"],
        "Strategy": ["strategies", "strategy", "plot_config"],
        "Model": ["model_info", "model"],
        "Pairs": ["whitelist", "blacklist", "pair_candles", "pair_history", "available_pairs",
                   "pairlists_available", "markets", "data_list"],
        "Data": ["entrylog"],
        "Config": ["show_config", "config_live"],
        "System": ["ping", "sysinfo", "health", "version", "logs", "self_test"],
    }

    for category, cmds in commands_by_category.items():
        icon = CATEGORY_ICONS.get(category, "\u2022")
        tbl = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style=f"bold {_cat_color(category)}",
            padding=(0, 1),
            title=f" {icon}  {category} ",
            title_style=f"bold {_cat_color(category)}",
            title_justify="left",
            border_style="dim",
        )
        tbl.add_column("Command", width=26, style="bold cyan", no_wrap=True)
        tbl.add_column("Description", style="dim")

        count = 0
        for name in cmds:
            if name in all_methods:
                doc = getattr(client, name).__doc__ or ""
                doc = doc.strip().split("\n")[0].rstrip(".")
                tbl.add_row(f"  {name}", doc)
                count += 1
        if count > 0:
            console.print(tbl)

    # ═══ Footer ═══════════════════════════════════════
    console.print()
    console.print(
        f"  [dim]> {len(all_methods)} commands in "
        f"{len(commands_by_category)} categories  |  "
        f"Use [bold]--json[/] for raw output  |  "
        f"v{__version__}[/]"
    )
    console.print(
        "  [dim]Namespace: [bold]paper status[/], "
        "[bold]backtest start[/], [bold]paper topup amount=1000[/][/]"
    )
    console.print()
    console.print("  [bold cyan]-- Quick Start --[/]")
    qs = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    qs.add_column(width=32, style="bold white")
    qs.add_column(style="dim")
    qs.add_row("  freq dashboard", "Full status overview")
    qs.add_row("  freq start / stop", "Start or stop the bot")
    qs.add_row("  freq profit", "Profit/loss summary")
    qs.add_row("  freq balance", "Wallet balances")
    qs.add_row("  freq markets limit=10", "Real-time market data")
    qs.add_row("  freq backtest start", "Run a backtest")
    qs.add_row("  freq paper status", "Paper trading status")
    qs.add_row("  freq config live pair=BTC/USDT:USDT", "Setup live trading config")
    console.print(qs)
    console.print()


def _cat_color(category: str) -> str:
    colors = {
        "Bot Control": "green",
        "Dashboard": "cyan",
        "Account": "yellow",
        "Trades": "magenta",
        "Trading": "red",
        "Locks": "yellow",
        "Paper Trading": "blue",
        "Backtest": "green",
        "Strategy": "cyan",
        "Model": "magenta",
        "Pairs": "magenta",
        "Config": "cyan",
        "System": "white",
    }
    return colors.get(category, "dim")


# ── SSH Helpers ───────────────────────────────────────

def _extract_host(server_url: str) -> str:
    """Extract hostname from a server URL."""
    try:
        parsed = urlparse(server_url)
        return parsed.hostname or "127.0.0.1"
    except Exception:
        return "127.0.0.1"


def _ssh_exec(cmd: str, host: str, user: str = "ubuntu") -> str:
    """Run a command on a remote host via SSH. Returns stdout."""
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new",
             f"{user}@{host}", cmd],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if stderr:
                _fail(f"SSH failed: {stderr}")
        return result.stdout
    except subprocess.TimeoutExpired:
        _fail(f"SSH command timed out after 120s")
    except FileNotFoundError:
        _fail("SSH client not found. Install OpenSSH or use manual mode.")
    except Exception as e:
        _fail(f"SSH error: {e}")


# ── Backtest Run (automated mode switching) ───────────

def _handle_backtest_run(client, kwargs: dict[str, str], config: dict) -> dict:
    """Run a complete backtest with automatic trade→webserver→trade switching."""
    ssh_host = os.environ.get("FT_SSH_HOST") or config.get("ssh", {}).get("host") or _extract_host(client._serverurl)
    ssh_user = os.environ.get("FT_SSH_USER") or config.get("ssh", {}).get("user", "ubuntu")
    compose_dir = os.environ.get("FT_COMPOSE_DIR") or config.get("ssh", {}).get("compose_dir", "/home/ubuntu/freqtrade")

    if ssh_host in ("127.0.0.1", "localhost"):
        _fail("Cannot determine SSH host. Set FT_SSH_HOST or ssh.host in config.json")

    _ok(f"SSH target: {ssh_user}@{ssh_host}")

    # Step 1: Ensure bot is running, check current state
    was_running = False
    try:
        client.start()  # ensure running — no-op if already running
        time.sleep(1)
        cfg = client.show_config()
        was_running = (cfg or {}).get("state") == "running"
    except Exception as e:
        _ok(f"Bot API not reachable (will restart after backtest): {e}")

    def _wait_for_webserver(timeout=60):
        for i in range(timeout):
            try:
                r = client.ping()
                if r and r.get("status") == "pong":
                    return True
            except Exception:
                pass
            time.sleep(1)
        _fail("Webserver did not become ready within 60s")

    # Step 2: Free port 8080 — stop trade container gracefully
    if was_running:
        _ok("Stopping trade bot...")
        try:
            client.stop()
        except Exception:
            pass
        time.sleep(1)

    _ok("Freeing port 8080 on server...")
    _ssh_exec(f"cd {compose_dir} && docker compose stop freqtrade 2>/dev/null; true", ssh_host, ssh_user)
    _ssh_exec("docker kill ft-webserver 2>/dev/null; true", ssh_host, ssh_user)
    time.sleep(2)

    # Step 3: Start webserver
    _ok("Starting webserver mode...")
    _ssh_exec(
        f"cd {compose_dir} && docker compose run -d --rm -p 8080:8080 --name ft-webserver "
        f"freqtrade webserver -c /freqtrade/config.json",
        ssh_host, ssh_user,
    )
    _wait_for_webserver()
    _ok("Webserver ready")

    # Step 4: Start backtest via API
    strategy = kwargs.get("strategy")
    timeframe = kwargs.get("timeframe")
    timerange = kwargs.get("timerange")

    if not timeframe:
        _fail("timeframe= is required. Example: timeframe=15m")
    if not timerange:
        _fail("timerange= is required. Example: timerange=20250601-20250610")

    _ok(f"Starting backtest: {timeframe}  {timerange}")
    if strategy:
        _ok(f"Strategy: {strategy}")

    result = client.backtest_start(
        strategy=strategy,
        timeframe=timeframe,
        timerange=timerange,
        max_open_trades=kwargs.get("max_open_trades"),
        stake_amount=kwargs.get("stake_amount"),
        enable_protections=kwargs.get("enable_protections", False),
        freqaimodel=kwargs.get("freqaimodel"),
    )

    # Step 5: Poll for completion
    _ok("Backtest started — monitoring...")
    max_poll = int(kwargs.get("max_poll_seconds", 3600))
    polled = 0
    bt_result = None
    bt_history = None
    consecutive_errors = 0

    while polled < max_poll:
        try:
            status = client.backtest_status()
            consecutive_errors = 0
            if isinstance(status, dict):
                running = status.get("running", True)
                if not running:
                    bt_result = status
                    print()
                    break
                progress = status.get("progress", 0)
                step = status.get("step", "")
                trade_count = status.get("trade_count", "")
                if HAS_RICH:
                    console.print(
                        f"  [cyan]>>[/] Progress: {float(progress)*100:.0f}%  "
                        f"Step: [bold]{step}[/]  "
                        f"Trades: {trade_count}",
                        end="\r",
                    )
                else:
                    print(f"  Progress: {float(progress)*100:.0f}%  Step: {step}  Trades: {trade_count}")
        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors >= 5:
                if HAS_RICH:
                    _err_console.print(f"  [red]!![/] Backend unreachable ({consecutive_errors} errors) — assuming done")
                else:
                    print(f"  Backend unreachable ({consecutive_errors} errors) — assuming done")
                break
            time.sleep(5)
        time.sleep(5)
        polled += 5
    else:
        _fail("Backtest did not finish within the time limit. Use backtest status to check.")

    # Step 6: Get history
    try:
        bt_history = client.backtest_history()
    except Exception as e:
        bt_history = {"_error": str(e)}

    # Step 7: Capture detailed result from poll
    detail = None
    if bt_result and bt_result.get("backtest_result"):
        detail = bt_result["backtest_result"]

    # Step 8: Switch back to trade mode
    _ok("Cleaning up webserver...")
    _ssh_exec("docker kill ft-webserver 2>/dev/null; true", ssh_host, ssh_user)
    time.sleep(1)

    # Always restart the trade bot after backtest
    _ok("Restarting trade bot...")
    _ssh_exec(
        f"cd {compose_dir} && docker compose start freqtrade 2>/dev/null || docker compose up -d freqtrade",
        ssh_host, ssh_user,
    )
    time.sleep(3)
    try:
        client.start()
        _ok("Trade bot restarted")
    except Exception as e:
        _fail(f"Failed to restart trade bot: {e}")

    return {
        "status": "completed",
        "result": result,
        "bt_result": bt_result,
        "history": bt_history,
        "detail": detail,
        "was_running": was_running,
        "strategy": strategy or "default",
        "timeframe": timeframe,
        "timerange": timerange,
    }

def _handle_config_live(kwargs: dict[str, str]) -> dict[str, Any]:
    """Generate a live trading config file from user input."""
    pair = kwargs.get("pair", "")
    timeframe = kwargs.get("timeframe", "15m")
    stake = kwargs.get("stake", kwargs.get("stake_amount", "unlimited"))
    leverage = kwargs.get("leverage", "1")
    max_trades = kwargs.get("max", kwargs.get("max_trades", "3"))
    exchange = kwargs.get("exchange", "bybit")

    if not pair:
        _fail("pair= is required. Example: pair=BTC/USDT:USDT")

    config_data = {
        "max_open_trades": int(max_trades),
        "stake_currency": "USDT",
        "stake_amount": stake,
        "tradable_balance_ratio": 0.99,
        "dry_run": False,
        "timeframe": timeframe,
        "trading_mode": "futures",
        "margin_mode": "isolated",
        "exchange": {
            "name": exchange,
            "key": "YOUR_API_KEY",
            "secret": "YOUR_API_SECRET",
            "ccxt_config": {},
            "ccxt_async_config": {},
            "pair_whitelist": [pair],
        },
        "pairlists": [{"method": "StaticPairList"}],
        "entry_pricing": {
            "price_side": "same",
            "use_order_book": True,
            "order_book_top": 1,
            "price_last_balance": 0.0,
            "check_depth_of_market": {"enabled": False, "bids_to_ask_delta": 1},
        },
        "exit_pricing": {
            "price_side": "same",
            "use_order_book": True,
            "order_book_top": 1,
        },
        "strategy": "MultiAgentStrategy",
        "strategy_path": "user_data/strategies",
        "api_server": {
            "enabled": True,
            "listen_ip_address": "0.0.0.0",
            "listen_port": 8080,
            "verbosity": "error",
            "enable_openapi": False,
            "jwt_secret_key": "ChangeMeToARandomLongStringAtLeast32Chars!",
            "CORS_origins": ["*"],
            "username": "admin",
            "password": "admin",
        },
        "internals": {"process_throttle_secs": 5},
    }

    out_path = Path("config.live.json")
    with out_path.open("w") as f:
        json.dump(config_data, f, indent=4)

    return {
        "pair": pair,
        "timeframe": timeframe,
        "stake_amount": stake,
        "leverage": leverage,
        "max_open_trades": int(max_trades),
        "exchange": exchange,
        "_config_file": str(out_path.resolve()),
    }


# ── Entry Log Reader ────────────────────────────────

def _handle_entrylog(client, config: dict, kwargs: dict[str, str]) -> dict:
    """Read entry log from the server via SSH."""
    ssh_host = os.environ.get("FT_SSH_HOST") or config.get("ssh", {}).get("host") or _extract_host(client._serverurl)
    ssh_user = os.environ.get("FT_SSH_USER") or config.get("ssh", {}).get("user", "ubuntu")

    if not ssh_host or ssh_host in ("127.0.0.1", "localhost"):
        _fail("Cannot determine SSH host. Set FT_SSH_HOST or ssh.host in config.json")

    pair = kwargs.get("pair", "")
    latest = kwargs.get("latest", "")

    logfile = "user_data/trade_logs/entry_logs.jsonl"

    # Build shell pipeline: cat + optional tail
    cmd = f"cat /freqtrade/{logfile}"
    if latest:
        try:
            cmd = f"tail -n {int(latest)} /freqtrade/{logfile}"
        except ValueError:
            pass

    stdout = _ssh_exec(f"docker exec freqtrade sh -c '{cmd}'", ssh_host, ssh_user)

    entries = []
    pair_lower = pair.lower() if pair else ""
    for line in stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            if pair_lower and pair_lower not in entry.get("pair", "").lower():
                continue
            entries.append(entry)
        except json.JSONDecodeError:
            pass

    return {"entries": entries, "count": len(entries)}


# ── SSH Python Helper ──────────────────────────────────

def _ssh_python(py_code: str, ssh_host: str, ssh_user: str = "ubuntu") -> str:
    """Run Python code on remote via SSH stdin pipe to docker exec."""
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new",
             f"{ssh_user}@{ssh_host}", "docker exec -i freqtrade python3"],
            input=py_code, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if stderr:
                _fail(f"SSH Python failed: {stderr}")
        return result.stdout
    except subprocess.TimeoutExpired:
        _fail("SSH Python timed out after 120s")
    except FileNotFoundError:
        _fail("SSH client not found. Install OpenSSH or use manual mode.")
    except Exception as e:
        _fail(f"SSH Python error: {e}")


# ── Backtest History Reader ─────────────────────────────

def _handle_backtest_history(client, config: dict, kwargs: dict[str, str]) -> dict:
    """List backtest results from the server via SSH (reads .meta.json files)."""
    ssh_host = os.environ.get("FT_SSH_HOST") or config.get("ssh", {}).get("host") or _extract_host(client._serverurl)
    ssh_user = os.environ.get("FT_SSH_USER") or config.get("ssh", {}).get("user", "ubuntu")

    if not ssh_host or ssh_host in ("127.0.0.1", "localhost"):
        _fail("Cannot determine SSH host. Set FT_SSH_HOST or ssh.host in config.json")

    py_code = """\
import json, glob, os
meta_dir = 'user_data/backtest_results'
results = []
pattern = os.path.join(meta_dir, '*.meta.json')
for fp in sorted(glob.glob(pattern)):
    try:
        meta = json.load(open(fp))
    except Exception:
        continue
    for strat_name, data in meta.items():
        ts = data.get('backtest_start_time', '')
        date_str = str(ts)[:10] if ts else ''
        timerange = data.get('timerange', '')
        results.append({
            'filename': os.path.basename(fp).replace('.meta.json', ''),
            'strategy': strat_name,
            'timeframe': data.get('timeframe', ''),
            'date': date_str,
            'timerange': timerange,
            'run_id': (data.get('run_id', '') or '')[:8],
        })
print(json.dumps(results))
"""
    stdout = _ssh_python(py_code, ssh_host, ssh_user)

    try:
        data = json.loads(stdout)
        return {"results": data, "count": len(data)}
    except json.JSONDecodeError as e:
        return {"results": [], "error": str(e), "raw": stdout[:500]}


def _handle_backtest_history_result(client, config: dict, kwargs: dict[str, str]) -> dict:
    """Read a specific backtest result zip from the server via SSH."""
    ssh_host = os.environ.get("FT_SSH_HOST") or config.get("ssh", {}).get("host") or _extract_host(client._serverurl)
    ssh_user = os.environ.get("FT_SSH_USER") or config.get("ssh", {}).get("user", "ubuntu")

    if not ssh_host or ssh_host in ("127.0.0.1", "localhost"):
        _fail("Cannot determine SSH host. Set FT_SSH_HOST or ssh.host in config.json")

    filename = kwargs.get("filename", "")
    if not filename:
        _fail("filename= is required. Example: filename=backtest-result-2025-06-12_06-39-54")

    py_code = f"""\
import json, zipfile, os
meta_dir = 'user_data/backtest_results'
zip_path = os.path.join(meta_dir, '{filename}.zip')
if not os.path.exists(zip_path):
    print(json.dumps({{"error": "File not found: {filename}"}}))
else:
    try:
        z = zipfile.ZipFile(zip_path, 'r')
        main_name = '{filename}.json'
        if main_name not in z.namelist():
            alt = [n for n in z.namelist() if n.endswith('.json') and '.meta.' not in n]
            main_name = alt[0] if alt else None
        if not main_name:
            print(json.dumps({{"error": "No result json found in zip"}}))
        else:
            raw = json.load(z.open(main_name))
            strat_raw = raw.get('strategy', {{}})
            if isinstance(strat_raw, dict) and strat_raw:
                s = list(strat_raw.values())[0]
                strat_name = list(strat_raw.keys())[0]
            else:
                s = strat_raw or {{}}
                strat_name = ''
            stats = {{
                "strategy": strat_name or s.get('strategy_name', s.get('strategy', '')),
                "total_trades": s.get('total_trades', 0),
                "winrate": s.get('winrate', s.get('wins', 0) / max(s.get('total_trades', 1), 1)),
                "profit_total_pct": s.get('profit_total_pct', 0),
                "profit_total_abs": s.get('profit_total_abs', 0),
                "profit_factor": s.get('profit_factor', 0),
                "max_drawdown_account": s.get('max_drawdown_account', s.get('max_drawdown', 0)),
                "max_drawdown_abs": s.get('max_drawdown_abs', 0),
                "sharpe": s.get('sharpe', 0),
                "sortino": s.get('sortino', 0),
                "timeframe": s.get('timeframe', ''),
                "timerange": s.get('timerange', ''),
                "backtest_start": s.get('backtest_start', ''),
                "backtest_end": s.get('backtest_end', ''),
                "avg_stake_amount": s.get('avg_stake_amount', 0),
                "wins": s.get('wins', 0),
                "losses": s.get('losses', 0),
                "draws": s.get('draws', 0),
                "stake_currency": s.get('stake_currency', ''),
                "stake_amount": s.get('stake_amount', 0),
            }}
            print(json.dumps(stats))
        z.close()
    except Exception as e:
        print(json.dumps({{"error": str(e)}}))
"""
    stdout = _ssh_python(py_code, ssh_host, ssh_user)

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        return {"error": str(e), "raw": stdout[:500]}


def main_exec(parsed: dict[str, Any]):
    if parsed.get("show") or parsed.get("command") in ("show", "help"):
        print_commands()
        sys.exit()

    if not parsed.get("command"):
        print_commands()
        sys.exit()

    config = load_config(parsed["config"])

    # Resolution chain: --server flag > FT_SERVER_URL env > client_server_url config > api_server config > 127.0.0.1
    server_url = parsed.get("server") or os.environ.get("FT_SERVER_URL")
    if server_url:
        if "://" not in server_url:
            server_url = f"http://{server_url}"
        username = os.environ.get("FT_SERVER_USERNAME") or config.get("api_server", {}).get("username")
        password = os.environ.get("FT_SERVER_PASSWORD") or config.get("api_server", {}).get("password")
    elif client_url := config.get("client_server_url"):
        server_url = client_url
        if "://" not in server_url:
            server_url = f"http://{server_url}"
        username = config.get("api_server", {}).get("username")
        password = config.get("api_server", {}).get("password")
    else:
        url = config.get("api_server", {}).get("listen_ip_address", "127.0.0.1")
        port = config.get("api_server", {}).get("listen_port", "8080")
        server_url = f"http://{url}:{port}"
        username = config.get("api_server", {}).get("username")
        password = config.get("api_server", {}).get("password")

    client = FtRestClient(server_url, username, password)

    valid = {x for x, _ in inspect.getmembers(client) if not x.startswith("_")}
    valid.add("config_live")
    valid.add("backtest_run")
    valid.add("entrylog")
    valid.add("backtest_history")
    valid.add("backtest_history_result")
    command = parsed["command"]
    cmd_args = parsed["command_arguments"]

    # ── Hyphen → underscore (e.g. "self-test" → "self_test") ──
    command = command.replace("-", "_")

    # ── Multi-pass namespace: "backtest history" → backtest_history, "backtest history result" → backtest_history_result ──
    display_cmd = command
    while True:
        pos_args = [x for x in cmd_args if "=" not in x]
        if not pos_args:
            break
        subcmd = pos_args[0]
        compound = f"{command}_{subcmd}"
        if compound in valid:
            display_cmd = compound
            command = compound
            cmd_args = [x for x in cmd_args if x != subcmd]
        elif f"{subcmd}_{command}" in valid:
            display_cmd = f"{subcmd}_{command}"
            command = f"{subcmd}_{command}"
            cmd_args = [x for x in cmd_args if x != subcmd]
        else:
            break

    if command not in valid:
        _fail(f"Unknown command: {command}\nRun [bold]freq --show[/] to see all commands.")

    # Extract key=value args and positional args
    kwargs = {x.split("=", 1)[0]: x.split("=", 1)[1] for x in cmd_args if "=" in x}
    args_list = [x for x in cmd_args if "=" not in x]

    # ── Special: config_live (client-side, no API call) ──
    if display_cmd == "config_live":
        res = _handle_config_live(kwargs)
        format_output("config_live", res, force_json=parsed.get("json", False))
        sys.exit(0)

    # ── Special: backtest_run (automated SSH + mode switching) ──
    if display_cmd == "backtest_run":
        if parsed.get("json", False):
            _fail("backtest run does not support --json (interactive workflow)")
        res = _handle_backtest_run(client, kwargs, config)
        format_output("backtest_run", res, force_json=False)
        sys.exit(0)

    # ── Special: entrylog (SSH-based file read) ──
    if display_cmd == "entrylog":
        res = _handle_entrylog(client, config, kwargs)
        format_output("entrylog", res, force_json=parsed.get("json", False))
        sys.exit(0)

    # ── Special: backtest_history (SSH-based reader) ──
    if display_cmd == "backtest_history":
        res = _handle_backtest_history(client, config, kwargs)
        format_output("backtest_history", res, force_json=parsed.get("json", False))
        sys.exit(0)

    # ── Special: backtest_history_result (SSH-based reader) ──
    if display_cmd == "backtest_history_result":
        res = _handle_backtest_history_result(client, config, kwargs)
        format_output("backtest_history_result", res, force_json=parsed.get("json", False))
        sys.exit(0)

    try:
        res = getattr(client, command)(*args_list, **kwargs)
    except TypeError as e:
        _fail(f"Invalid arguments for '{display_cmd}': {e}")
    except Exception as e:
        _fail(f"API error: {e}")

    format_output(display_cmd, res, force_json=parsed.get("json", False))


def main():
    args = add_arguments()
    main_exec(args)
