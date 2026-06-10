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

CATEGORY_ICONS = {
    "Bot Control": "\u25b6",
    "Dashboard": "\ud83d\udcca",
    "Account": "\ud83d\udcb0",
    "Trades": "\ud83d\udcc8",
    "Trading": "\u26a1",
    "Locks": "\ud83d\udd12",
    "Paper Trading": "\ud83d\udcdd",
    "Backtest": "\ud83d\udd2c",
    "Strategy": "\ud83e\udde0",
    "Pairs": "\ud83d\udcb1",
    "System": "\ud83d\udd27",
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
                ("\n    \u2554", "bold cyan"),
                (" Freqtrade AI Dashboard CLI ", "bold white"),
                ("\u2557\n", "bold cyan"),
                ("    \u2551", "bold cyan"),
                (f" v{__version__}  \u00b7  ", "dim"),
                (f"{len(all_methods)} commands ", "white"),
                (f" \u00b7  ", "dim"),
                ("REST + WebSocket", "dim"),
                ("\u2551\n", "bold cyan"),
                ("    \u255a", "bold cyan"),
                ("\u2550" * 34, "bold cyan"),
                ("\u255d", "bold cyan"),
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
                      "backtest_history", "backtest_history_result", "backtest_history_delete"],
        "Strategy": ["strategies", "strategy", "plot_config"],
        "Pairs": ["whitelist", "blacklist", "pair_candles", "pair_history", "available_pairs",
                   "pairlists_available"],
        "System": ["ping", "show_config", "sysinfo", "health", "version", "logs"],
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
        f"  [dim]\U0001f4a1 {len(all_methods)} commands in "
        f"{len(commands_by_category)} categories  |  "
        f"Use [bold]--json[/] for raw output  |  "
        f"v{__version__}[/]"
    )
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
        "Pairs": "magenta",
        "System": "white",
    }
    return colors.get(category, "dim")


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
