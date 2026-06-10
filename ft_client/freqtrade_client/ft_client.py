import argparse
import inspect
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

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
    console = Console()
    _err_console = Console(stderr=True)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("ft_rest_client")


# ── Args ────────────────────────────────────────────

def add_arguments(args: Any = None):
    parser = argparse.ArgumentParser(
        prog="freqtrade-client",
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
        _err_console.print(f"\n  [red]\u2717[/] {msg}")
    else:
        print(f"ERROR: {msg}")
    sys.exit(1)


def _ok(msg: str) -> None:
    if HAS_RICH:
        console.print(f"  [green]\u2713[/] {msg}")
    else:
        print(f"OK: {msg}")


# ── Show Commands ───────────────────────────────────

def print_commands():
    client = FtRestClient(None)

    if not HAS_RICH:
        print("Possible commands:\n")
        for name, _ in inspect.getmembers(client):
            if not name.startswith("_"):
                doc = re.sub(r":return:.*", "", getattr(client, name).__doc__ or "", flags=re.MULTILINE).strip()
                print(f"  {name}\n\t{doc}\n")
        return

    console.print()
    console.print(Panel(
        Align.center(Text("Freqtrade REST Client", style="bold cyan")),
        box=box.HEAVY, border_style="cyan", padding=(1, 4),
    ))

    commands_by_category: dict[str, list[tuple[str, str]]] = {
        "Bot Control": ["start", "stop", "stopbuy", "reload_config"],
        "Dashboard": ["dashboard"],
        "Account": ["balance", "count", "profit", "daily", "weekly", "monthly", "stats"],
        "Trades": ["trades", "trade", "status", "performance", "entries", "exits", "mix_tags"],
        "Trading": ["forceenter", "forceexit", "forcebuy", "delete_trade", "cancel_open_order"],
        "Locks": ["locks", "lock_add", "delete_lock"],
        "Paper Trading": ["paper_status", "paper_topup", "paper_trades", "paper_account"],
        "Backtest": ["backtest_start", "backtest_status", "backtest_delete", "backtest_abort",
                      "backtest_history", "backtest_history_result", "backtest_history_delete"],
        "Strategy": ["strategies", "strategy", "plot_config"],
        "Pairs": ["whitelist", "blacklist", "pair_candles", "pair_history", "available_pairs",
                   "pairlists_available"],
        "System": ["ping", "show_config", "sysinfo", "health", "version", "logs"],
    }

    all_methods = {n for n, _ in inspect.getmembers(client) if not n.startswith("_")}

    for category, cmds in commands_by_category.items():
        console.print(f"\n  [bold yellow]{category}[/]")
        for name in cmds:
            if name in all_methods:
                doc = getattr(client, name).__doc__ or ""
                doc = doc.strip().split("\n")[0].rstrip(".")
                console.print(f"    [bold cyan]{name:<28}[/] [dim]{doc}[/]")

    console.print(f"\n  [dim]Add [bold]--json[/] for raw output.  |  {len(all_methods)} commands total.[/]\n")


# ── Main ────────────────────────────────────────────

def main_exec(parsed: dict[str, Any]):
    if parsed.get("show") or parsed.get("command") in ("show", "help"):
        print_commands()
        sys.exit()

    if not parsed.get("command"):
        print_commands()
        sys.exit()

    config = load_config(parsed["config"])
    url = config.get("api_server", {}).get("listen_ip_address", "127.0.0.1")
    port = config.get("api_server", {}).get("listen_port", "8080")
    username = config.get("api_server", {}).get("username")
    password = config.get("api_server", {}).get("password")

    server_url = f"http://{url}:{port}"
    client = FtRestClient(server_url, username, password)

    valid = [x for x, _ in inspect.getmembers(client) if not x.startswith("_")]
    command = parsed["command"]

    if command not in valid:
        _fail(f"Unknown command: {command}\nRun [bold]freqtrade-client --show[/] to see all commands.")

    kwargs = {x.split("=", 1)[0]: x.split("=", 1)[1] for x in parsed["command_arguments"] if "=" in x}
    args_list = [x for x in parsed["command_arguments"] if "=" not in x]

    try:
        res = getattr(client, command)(*args_list, **kwargs)
    except TypeError as e:
        _fail(f"Invalid arguments for '{command}': {e}")
    except Exception as e:
        _fail(f"API error: {e}")

    format_output(command, res, force_json=parsed.get("json", False))


def main():
    args = add_arguments()
    main_exec(args)
