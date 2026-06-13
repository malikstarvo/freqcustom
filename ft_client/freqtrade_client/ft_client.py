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

# ── Auto-load .env ────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


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
    all_methods.update({"config_live", "backtest_run", "entrylog",
                        "backtest_history", "backtest_history_result",
                        "backtest_history_delete", "doctor", "model_retrain"})

    _handler_docs = {
        "config_live": "Generate a live trading config file from user input",
        "doctor": "Run connection diagnostics: API, SSH, Docker",
        "model_retrain": "Retrain ML model: stop bot, delete model files, restart",
    }

    # ═══ Banner ══════════════════════════════════════
    console.print()
    art_lines = [
        "[bold cyan]███╗   ██╗  ██████╗  ███████╗  ██████╗  ███████╗  ████████╗[/]",
        "[bold cyan]████╗  ██║  ██╔════╝  ██╔════╝  ██╔══██╗  ██╔════╝  ╚══██╔══╝[/]",
        "[bold cyan]██╔██╗ ██║  ██║  ███╗  █████╗    ██████╔╝  █████╗     ██║   [/]",
        "[bold cyan]██║╚██╗██║  ██║   ██║  ██╔══╝    ██╔═══╝   ██╔══╝     ██║   [/]",
        "[bold cyan]██║ ╚████║  ╚██████╔╝  ███████╗  ██║       ███████╗   ██║   [/]",
        "[bold cyan]╚═╝  ╚═══╝   ╚═════╝   ╚══════╝  ╚═╝       ╚══════╝   ╚═╝   [/]",
    ]
    art_text = "\n".join(art_lines)
    sub = f"v{__version__}  ·  {len(all_methods)} commands  ·  REST + WebSocket"
    banner = Panel(
        Align.center(
            Text.assemble(
                Text.from_markup(art_text),
                "\n",
                (sub, "dim"),
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
        "System": ["ping", "sysinfo", "health", "version", "logs", "self_test", "doctor", "model_retrain"],
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
                method = getattr(client, name, None)
                if method is not None:
                    doc = method.__doc__ or ""
                else:
                    doc = _handler_docs.get(name, "")
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

    # SSH config hint
    ssh_host = os.environ.get("FT_SSH_HOST")
    if not ssh_host:
        try:
            cfg = load_config("config.json")
            ssh_host = cfg.get("ssh", {}).get("host", "")
        except Exception:
            ssh_host = ""
    if ssh_host:
        console.print(f"  [dim]SSH: [bold]{ssh_host}[/]  |  API: [bold]config.json[/]  |  "
                      f"Run [bold]freq doctor[/] to verify[/]")
    else:
        console.print(f"  [dim]SSH: not configured  |  "
                      f"Set [bold]FT_SSH_HOST[/] or [bold]ssh.host[/] in config.json  |  "
                      f"Run [bold]freq doctor[/] for diagnostics[/]")

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
            input=py_code.encode("utf-8"), capture_output=True, timeout=120,
        )
        stdout = result.stdout.decode("utf-8")
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            if stderr:
                _fail(f"SSH Python failed: {stderr}")
        return stdout
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
import json, glob, os, datetime
meta_dir = 'user_data/backtest_results'
results = []
pattern = os.path.join(meta_dir, '*.meta.json')
for fp in sorted(glob.glob(pattern)):
    try:
        meta = json.load(open(fp))
    except Exception:
        continue
    for strat_name, data in meta.items():
        ts = data.get('backtest_start_time', 0)
        st_ts = data.get('backtest_start_ts')
        et_ts = data.get('backtest_end_ts')
        timerange = ''
        if st_ts and et_ts:
            st_dt = datetime.datetime.fromtimestamp(st_ts)
            et_dt = datetime.datetime.fromtimestamp(et_ts)
            timerange = st_dt.strftime('%Y%m%d') + '-' + et_dt.strftime('%Y%m%d')
        results.append({
            'filename': os.path.basename(fp).replace('.meta.json', ''),
            'strategy': strat_name,
            'timeframe': data.get('timeframe', ''),
            'date': ts,
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
    # Sanitize: only allow safe characters to prevent code injection in f-string
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        _fail("Invalid filename. Use only letters, numbers, dots, hyphens, underscores.")

    py_code = f"""\
import json, zipfile, os
meta_dir = 'user_data/backtest_results'
zip_path = os.path.join(meta_dir, '{filename}.zip')
if not os.path.exists(zip_path):
    print(json.dumps({{"error": "File not found: {filename}"}}))
else:
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            main_name = '{filename}.json'
            namelist = z.namelist()
            if main_name not in namelist:
                alt = [n for n in namelist if n.endswith('.json') and '.meta.' not in n]
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
                p_total = s.get('profit_total', 0) or 0
                total_trades = s.get('total_trades', 0)
                wins = s.get('wins', 0)
                losses = s.get('losses', 0)
                draws = s.get('draws', 0)
                stats = {{
                    "strategy": strat_name or s.get('strategy_name', s.get('strategy', '')),
                    "total_trades": total_trades,
                    "winrate": (wins / max(total_trades, 1)) * 100,
                    "profit_total": p_total,
                    "profit_total_pct": s.get('profit_total_pct') or (p_total * 100),
                    "profit_total_abs": s.get('profit_total_abs', 0),
                    "profit_factor": s.get('profit_factor', 0),
                    "max_drawdown_account": -((s.get('max_drawdown_account') or s.get('max_drawdown') or 0) * 100),
                    "max_drawdown_abs": s.get('max_drawdown_abs', 0),
                    "sharpe": s.get('sharpe', 0),
                    "sortino": s.get('sortino', 0),
                    "timeframe": s.get('timeframe', ''),
                    "timerange": s.get('timerange', ''),
                    "backtest_start": s.get('backtest_start', ''),
                    "backtest_end": s.get('backtest_end', ''),
                    "avg_stake_amount": s.get('avg_stake_amount', 0),
                    "wins": wins,
                    "losses": losses,
                    "draws": draws,
                    "stake_currency": s.get('stake_currency', ''),
                    "stake_amount": s.get('stake_amount', 0),
                }}
                print(json.dumps(stats))
    except Exception as e:
        print(json.dumps({{"error": str(e)}}))
"""
    stdout = _ssh_python(py_code, ssh_host, ssh_user)

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        return {"error": str(e), "raw": stdout[:500]}


# ── Doctor (Diagnostic) ────────────────────────────────

def _handle_doctor(client, config: dict) -> dict:
    """Test all connection paths: API, SSH, Docker."""
    result = {}

    # Resolve config
    ssh_host = os.environ.get("FT_SSH_HOST") or config.get("ssh", {}).get("host") or _extract_host(client._serverurl)
    ssh_user = os.environ.get("FT_SSH_USER") or config.get("ssh", {}).get("user", "ubuntu")
    compose_dir = os.environ.get("FT_COMPOSE_DIR") or config.get("ssh", {}).get("compose_dir", "/home/ubuntu/freqtrade")
    server_url = client._serverurl

    result["config"] = {
        "server_url": server_url,
        "ssh_host": ssh_host,
        "ssh_user": ssh_user,
        "compose_dir": compose_dir,
    }

    # Test API connectivity
    api_ok = False
    api_detail = ""
    try:
        pong = client.ping()
        if pong and pong.get("status") == "pong":
            api_ok = True
            api_detail = "pong"
        else:
            api_detail = str(pong)
    except Exception as e:
        api_detail = str(e)
    result["api"] = {"ok": api_ok, "detail": api_detail}

    # Test SSH connectivity
    ssh_ok = False
    ssh_detail = ""
    if not ssh_host:
        ssh_detail = "SSH host not configured"
    elif ssh_host in ("127.0.0.1", "localhost"):
        ssh_detail = "SSH resolves to localhost; set FT_SSH_HOST"
    else:
        try:
            out = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
                 f"{ssh_user}@{ssh_host}", "echo ok"],
                capture_output=True, text=True, timeout=15,
            )
            if out.returncode == 0 and out.stdout.strip() == "ok":
                ssh_ok = True
                ssh_detail = "connected"
            else:
                ssh_detail = (out.stderr or out.stdout or "").strip()[:200]
        except FileNotFoundError:
            ssh_detail = "SSH client not found"
        except Exception as e:
            ssh_detail = str(e)[:200]
    result["ssh"] = {"ok": ssh_ok, "detail": ssh_detail}

    # Test Docker containers on server (if SSH works)
    docker_containers = {}
    docker_ok = False
    docker_detail = ""
    if ssh_ok:
        try:
            out = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new",
                 f"{ssh_user}@{ssh_host}",
                 "docker ps --format '{{.Names}}\t{{.Status}}' 2>/dev/null || echo 'docker_not_found'"],
                capture_output=True, text=True, timeout=15,
            )
            if out.returncode == 0:
                lines = out.stdout.strip().splitlines()
                if lines and lines[0] == "docker_not_found":
                    docker_detail = "Docker not found on server"
                else:
                    for line in lines:
                        parts = line.split("\t", 1)
                        if len(parts) == 2:
                            docker_containers[parts[0].strip()] = parts[1].strip()
                    docker_ok = True
                    docker_detail = f"{len(docker_containers)} containers running"
            else:
                docker_detail = (out.stderr or "").strip()[:200]
        except Exception as e:
            docker_detail = str(e)[:200]
    result["docker"] = {
        "ok": docker_ok,
        "detail": docker_detail,
        "containers": docker_containers,
    }

    # Docker exec python availability
    py_ok = False
    py_detail = ""
    if ssh_ok:
        try:
            out = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
                 f"{ssh_user}@{ssh_host}",
                 "docker exec freqtrade python3 --version 2>/dev/null || echo 'not_available'"],
                capture_output=True, text=True, timeout=10,
            )
            if out.returncode == 0:
                ver = out.stdout.strip()
                if ver and ver != "not_available":
                    py_ok = True
                    py_detail = ver
                else:
                    py_detail = "freqtrade container or python3 not available"
            else:
                py_detail = (out.stderr or "").strip()[:200]
        except Exception as e:
            py_detail = str(e)[:200]
    result["python"] = {"ok": py_ok, "detail": py_detail}

    return result


# ── Model Info (SSH-based with accuracy) ──────────────

def _handle_model_info(client, config: dict, kwargs: dict[str, str]) -> dict:
    """Read model metrics and compute accuracy via SSH."""
    ssh_host = os.environ.get("FT_SSH_HOST") or config.get("ssh", {}).get("host") or _extract_host(client._serverurl)
    ssh_user = os.environ.get("FT_SSH_USER") or config.get("ssh", {}).get("user", "ubuntu")

    result = {"_error": None}

    # 1. Get config info from REST API
    try:
        cfg = client.show_config()
        freqai = cfg.get("freqai") or {}
        fp = freqai.get("feature_parameters") or {}
        result["config"] = {
            "strategy": cfg.get("strategy", "\u2014"),
            "freqaimodel": cfg.get("freqaimodel", "\u2014"),
            "enabled": freqai.get("enabled", False),
            "identifier": freqai.get("identifier", "\u2014"),
            "train_period": freqai.get("train_period_days", 90),
            "backtest_period": freqai.get("backtest_period_days", 30),
            "timeframes": fp.get("include_timeframes", []),
            "label_period": fp.get("label_period_candles", 4),
            "pca": fp.get("principal_component_analysis", False),
            "weight_factor": fp.get("weight_factor", 0),
        }
        try:
            models_resp = client.freqaimodels()
            result["config"]["available_models"] = models_resp.get("freqaimodels", []) if models_resp else []
        except Exception:
            result["config"]["available_models"] = []
    except Exception as e:
        result["_error"] = str(e)
        result["config"] = {}

    # 2. Fallback: read local config.json
    try:
        with open("config.json", encoding="utf-8") as f:
            file_cfg = json.load(f)
        freqai_file = file_cfg.get("freqai") or {}
        fp_file = freqai_file.get("feature_parameters") or {}
        if not result["config"].get("identifier") or result["config"]["identifier"] in ("\u2014", ""):
            result["config"]["identifier"] = freqai_file.get("identifier", "\u2014")
        result["config"]["enabled"] = freqai_file.get("enabled", False) or result["config"].get("enabled", False)
        if result["config"].get("freqaimodel", "\u2014") in ("\u2014", ""):
            result["config"]["freqaimodel"] = file_cfg.get("freqaimodel", "\u2014")
        if not result["config"].get("timeframes"):
            result["config"]["timeframes"] = fp_file.get("include_timeframes", [])
        if not result["config"].get("available_models"):
            result["config"]["available_models"] = []
        if result["config"].get("label_period") == 4:
            result["config"]["label_period"] = fp_file.get("label_period_candles", 4)
        if freqai_file.get("train_period_days"):
            result["config"]["train_period"] = freqai_file["train_period_days"]
        if freqai_file.get("backtest_period_days"):
            result["config"]["backtest_period"] = freqai_file["backtest_period_days"]
    except Exception:
        pass

    # 3. Read model data from server via SSH
    if not ssh_host or ssh_host in ("127.0.0.1", "localhost"):
        result["ssh_status"] = "SSH not configured"
        return result
    result["ssh_status"] = "ok"

    identifier = result.get("config", {}).get("identifier", "multi_agent_v1")
    if identifier in ("\u2014", ""):
        identifier = "multi_agent_v1"

    py_code = f"""\
import json, os, sys, pickle, glob as _glob
try:
    import pandas as pd
    import numpy as np
except ImportError:
    print(json.dumps({{"error": "pandas/numpy not available"}}))
    sys.exit(0)

model_dir = 'user_data/models/{identifier}'
out = {{}}

# pair_dictionary.json
pd_path = os.path.join(model_dir, 'pair_dictionary.json')
if os.path.exists(pd_path):
    with open(pd_path) as f:
        out['pair_dict'] = json.load(f)

# metric_tracker.json
mt_path = os.path.join(model_dir, 'metric_tracker.json')
if os.path.exists(mt_path):
    with open(mt_path) as f:
        out['metrics'] = json.load(f)

# run_params.json
rp_path = os.path.join(model_dir, 'run_params.json')
if os.path.exists(rp_path):
    with open(rp_path) as f:
        rp = json.load(f)
        out['run_params'] = {{
            'train_period_days': rp.get('freqai', {{}}).get('train_period_days'),
            'backtest_period_days': rp.get('freqai', {{}}).get('backtest_period_days'),
            'live_retrain_hours': rp.get('freqai', {{}}).get('live_retrain_hours', 0),
        }}

# historic_predictions.pkl - compute accuracy
hp_path = os.path.join(model_dir, 'historic_predictions.pkl')
if os.path.exists(hp_path):
    try:
        with open(hp_path, 'rb') as f:
            hp_data = pickle.load(f)
        acc = {{'per_pair': {{}}, 'total_predictions': 0, 'total_correct': 0}}
        for pair, df in hp_data.items():
            if not isinstance(df, pd.DataFrame):
                continue
            label_col = '&s-up_or_down'
            if label_col not in df.columns:
                continue
            # Find prediction probability column (True = up probability)
            prob_col = 'True' if 'True' in df.columns else None
            pred_col = None
            if prob_col and prob_col in df.columns:
                pred_col = prob_col
            else:
                pred_cols = [c for c in df.columns if 'prediction' in c.lower()]
                pred_col = pred_cols[0] if pred_cols else None
            if not pred_col:
                continue
            valid = df[[pred_col, label_col]].dropna().copy()
            if len(valid) == 0:
                continue
            # Convert True prob column to numeric, label from string to 0/1
            prob_vals = pd.to_numeric(valid[pred_col], errors='coerce')
            preds = prob_vals.round().astype(int)
            if valid[label_col].dtype == 'object':
                actuals = valid[label_col].map({{'True': 1, 'False': 0}}).astype(int)
            else:
                actuals = valid[label_col].astype(int)
            correct = (preds == actuals).sum()
            total = len(valid)
            up_preds = int((preds == 1).sum())
            down_preds = int((preds == 0).sum())
            up_correct = int(((preds == 1) & (actuals == 1)).sum())
            down_correct = int(((preds == 0) & (actuals == 0)).sum())
            acc['per_pair'][pair] = {{
                'total': total,
                'correct': int(correct),
                'accuracy': round(float(correct / total), 4) if total > 0 else 0,
                'up_predicted': up_preds,
                'down_predicted': down_preds,
                'up_correct': up_correct,
                'down_correct': down_correct,
            }}
            acc['total_predictions'] += total
            acc['total_correct'] += int(correct)
        if acc['total_predictions'] > 0:
            acc['overall_accuracy'] = round(acc['total_correct'] / acc['total_predictions'], 4)
        else:
            acc['overall_accuracy'] = 0
        out['accuracy'] = acc
    except Exception as e:
        out['accuracy_error'] = str(e)

# sub-train directories for feature metadata
sub_dirs = sorted(_glob.glob(os.path.join(model_dir, 'sub-train-*')))
if sub_dirs:
    out['sub_train_count'] = len(sub_dirs)
    latest = sub_dirs[-1]
    meta_files = _glob.glob(os.path.join(latest, '*_metadata.json'))
    if meta_files:
        try:
            with open(meta_files[0]) as f:
                meta = json.load(f)
            out['features'] = {{
                'total': len(meta.get('training_features_list', [])),
                'list': meta.get('training_features_list', [])[:10],
            }}
            out['labels'] = {{
                'mean': meta.get('labels_mean', {{}}),
                'std': meta.get('labels_std', {{}}),
            }}
        except Exception:
            pass

print(json.dumps(out, default=str))
"""
    try:
        stdout = _ssh_python(py_code, ssh_host, ssh_user)
        ssh_data = json.loads(stdout)
        result.update(ssh_data)
    except Exception as e:
        result["ssh_error"] = str(e)

    return result


# ── Model Retrain ──────────────────────────────────────

def _handle_model_retrain(client, config: dict, kwargs: dict[str, str]) -> dict:
    """Retrain the ML model: stop bot, delete model files, restart bot."""
    ssh_host = os.environ.get("FT_SSH_HOST") or config.get("ssh", {}).get("host") or _extract_host(client._serverurl)
    ssh_user = os.environ.get("FT_SSH_USER") or config.get("ssh", {}).get("user", "ubuntu")
    compose_dir = os.environ.get("FT_COMPOSE_DIR") or config.get("ssh", {}).get("compose_dir", "/home/ubuntu/freqtrade")
    identifier = config.get("freqai", {}).get("identifier", "multi_agent_v1")

    if not ssh_host or ssh_host in ("127.0.0.1", "localhost"):
        _fail("Cannot determine SSH host. Set FT_SSH_HOST or ssh.host in config.json")

    steps = []

    # Step 1: Stop bot
    _ok("Stopping bot...")
    _ssh_exec(f"cd {compose_dir} && docker compose stop freqtrade 2>/dev/null; true", ssh_host, ssh_user)
    time.sleep(2)
    steps.append("stop")

    # Step 2: Delete model files
    _ok(f"Removing model files ({identifier})...")
    _ssh_exec(f"rm -rf /freqtrade/user_data/models/{identifier} 2>/dev/null; true", ssh_host, ssh_user)
    steps.append("delete_models")

    # Step 3: Restart bot
    _ok("Starting bot...")
    _ssh_exec(
        f"cd {compose_dir} && docker compose start freqtrade 2>/dev/null || docker compose up -d freqtrade",
        ssh_host, ssh_user,
    )
    steps.append("start")

    # Step 4: Wait for API
    _ok("Waiting for API...")
    for i in range(30):
        time.sleep(2)
        try:
            pong = client.ping()
            if pong and pong.get("status") == "pong":
                _ok("Bot is ready")
                steps.append("ready")
                break
        except Exception:
            pass
    else:
        steps.append("timeout")

    return {
        "status": "completed" if "ready" in steps else "partial",
        "steps": steps,
        "identifier": identifier,
    }


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
    valid.add("doctor")
    valid.add("model_retrain")
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

    # ── Special: doctor (diagnostic) ──
    if display_cmd == "doctor":
        res = _handle_doctor(client, config)
        format_output("doctor", res, force_json=parsed.get("json", False))
        sys.exit(0)

    # ── Special: model_info (SSH-based with accuracy) ──
    if display_cmd == "model_info":
        res = _handle_model_info(client, config, kwargs)
        format_output("model_info", res, force_json=parsed.get("json", False))
        sys.exit(0)

    # ── Special: model_retrain (SSH-based) ──
    if display_cmd == "model_retrain":
        if parsed.get("json", False):
            _fail("model retrain does not support --json (interactive workflow)")
        res = _handle_model_retrain(client, config, kwargs)
        format_output("model_retrain", res, force_json=False)
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
