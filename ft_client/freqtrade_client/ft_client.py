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
    "Bot Control":   "\u25b6",   # ▶
    "Dashboard":     "\u25c9",   # ◉
    "Account":       "\u25cb",   # ○
    "Trades":        "\u21c4",   # ⇄
    "Trading":       "\u26a1",   # ⚡
    "Locks":         "\u26d4",   # ⛔
    "Paper Trading": "\u25a1",   # □
    "Backtest":      "\u21bb",   # ↻
    "Strategy": "\u2666",   # ♦
    "Model": "\u25c6",      # ◆
    "Pairs": "\u21c6",   # ⇆
    "Config":        "\u2699",   # ⚙
    "System":        "\u2302",   # ⌂
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
        "Model": ["model_info", "model"],
        "Pairs": ["whitelist", "blacklist", "pair_candles", "pair_history", "available_pairs",
                   "pairlists_available", "markets"],
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
        f"  [dim]\u25b8 {len(all_methods)} commands in "
        f"{len(commands_by_category)} categories  |  "
        f"Use [bold]--json[/] for raw output  |  "
        f"v{__version__}[/]"
    )
    console.print(
        "  [dim]Namespace: [bold]paper status[/], "
        "[bold]backtest start[/], [bold]paper topup amount=1000[/][/]"
    )
    console.print()
    console.print("  [bold cyan]\u2500\u2500 Quick Start \u2500\u2500[/]")
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


# ── Main ────────────────────────────────────────────

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

    valid = {x for x, _ in inspect.getmembers(client) if not x.startswith("_")}
    command = parsed["command"]
    cmd_args = parsed["command_arguments"]

    # ── Namespace support: "paper status" → paper_status() ──
    if command not in valid:
        pos_args = [x for x in cmd_args if "=" not in x]
        if pos_args:
            subcmd = pos_args[0]
            compound = f"{command}_{subcmd}"
            if compound in valid:
                display_cmd = compound  # for formatting
                command = compound
                cmd_args = [x for x in cmd_args if x != subcmd]  # remove subcommand from args
            else:
                _fail(f"Unknown command: {command}\nRun [bold]freq --show[/] to see all commands.")
        else:
            _fail(f"Unknown command: {command}\nRun [bold]freq --show[/] to see all commands.")
    else:
        display_cmd = command

    # ── Special: config live (client-side, no API call) ──
    if display_cmd == "config_live":
        res = _handle_config_live(kwargs)
        format_output("config_live", res, force_json=parsed.get("json", False))
        sys.exit(0)

    kwargs = {x.split("=", 1)[0]: x.split("=", 1)[1] for x in cmd_args if "=" in x}
    args_list = [x for x in cmd_args if "=" not in x]

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
