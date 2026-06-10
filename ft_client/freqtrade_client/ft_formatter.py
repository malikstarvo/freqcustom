"""Rich formatting for freqtrade-client CLI commands."""

import json
import sys
from typing import Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
    from rich.progress import Progress
    from rich.spinner import Spinner
    from rich.live import Live
    from rich.style import Style
    from rich.align import Align
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

if HAS_RICH:
    console = Console()


# ── Helpers ─────────────────────────────────────────

def _profit_color(value: float) -> str:
    if value > 0:
        return "green"
    elif value < 0:
        return "red"
    return "dim"

def _profit_icon(value: float) -> str:
    if value > 0:
        return "[green]\u2191[/]"
    elif value < 0:
        return "[red]\u2193[/]"
    return "[dim]\u2014[/]"

def _pct(value: float) -> str:
    c = _profit_color(value)
    sign = "+" if value > 0 else ""
    return f"[{c}]{sign}{value:.2f}%[/]"

def _pnl(value: float) -> str:
    c = _profit_color(value)
    sign = "+" if value > 0 else ""
    return f"[{c}]{sign}{value:.2f}[/]"

def _header(title: str) -> Panel:
    return Panel(
        Align.center(Text(title, style="bold cyan")),
        box=box.HEAVY,
        border_style="cyan",
        padding=(0, 4),
    )

def _section(title: str) -> Text:
    return Text(f"\n  {title}", style="bold yellow")

def _json_output(data: Any) -> None:
    """Fallback: print raw JSON."""
    print(json.dumps(data, indent=2, default=str))


# ── Format Functions ────────────────────────────────

def fmt_ping(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return
    status = data.get("status", "unknown")
    color = "green" if status == "pong" else "red"
    icon = "\u25cf" if status == "pong" else "\u25cb"
    console.print(f"\n  [{color}]{icon}[/]  Bot Status: [{color} bold]{status.upper()}[/]")


def fmt_dashboard(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    state_color = "green" if data.get("state") == "running" else "yellow"
    state_icon = "\u25cf" if data.get("state") == "running" else "\u25cb"

    console.print()
    console.print(_header("  Freqtrade AI Dashboard  "))

    # Top row: State + Config
    grid = Table.grid(padding=(0, 4))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)

    left = Table.grid(padding=(0, 2))
    left.add_column(style="bold cyan", width=16)
    left.add_column(style="white")
    left.add_row("State", f"[{state_color}]{state_icon} {data.get('state', 'offline').upper()}[/]")
    left.add_row("Strategy", str(data.get("strategy", "\u2014")))
    left.add_row("Exchange", str(data.get("exchange", "\u2014")))
    mode = data.get("trading_mode", "\u2014") or "\u2014"
    left.add_row("Mode", f"{mode} {'(dry)' if data.get('dry_run') else '(live)'}")

    right = Table.grid(padding=(0, 2))
    right.add_column(style="bold cyan", width=16)
    right.add_column(style="white")
    right.add_row("Max Trades", str(data.get("max_open_trades", "\u2014")))
    right.add_row("Currency", str(data.get("stake_currency", "\u2014")))
    right.add_row("Total Balance", f"${data.get('total_balance', 0):,.2f}" if data.get("total_balance") else "\u2014")
    right.add_row("Last Process", str(data.get("last_process", "\u2014")))

    grid.add_row(left, right)
    console.print(Panel(grid, border_style="dim blue", padding=(1, 2)))

    # Performance
    if data.get("profit_all_pct") is not None:
        console.print(_section("Performance"))
        perf = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        perf.add_column(style="bold cyan", width=16)
        perf.add_column(style="white")
        perf.add_column(style="dim", width=24)

        pnl = data.get("profit_all_pct", 0)
        wr = data.get("winrate", 0)
        dd = data.get("max_drawdown", 0)
        pf = data.get("profit_factor", 0)

        perf.add_row("Total P&L", _pct(pnl),
                     f"{data.get('profit_closed_coin', 0):.4f} {data.get('balance_symbol', '')}")
        perf.add_row("Win Rate", f"{wr:.1f}%",
                     f"{data.get('trade_count', 0)} trades ({data.get('closed_trade_count', 0)} closed)")
        perf.add_row("Max Drawdown", _pct(-abs(dd)),
                     f"PF: {pf:.2f}" if pf else "")
        best_pair = data.get("best_pair") or "\u2014"
        perf.add_row("Sharpe", f"{data.get('sharpe', 0):.2f}",
                     f"Best: {best_pair}")
        perf.add_row("Avg Duration", str(data.get("avg_duration", "\u2014")),
                     f"Open: {data.get('open_trades', 0)}")

        console.print(Panel(perf, border_style="dim blue", padding=(1, 2)))

    # Paper Trading
    if data.get("paper_equity") is not None:
        console.print(_section("Paper Trading"))
        paper = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        paper.add_column(style="bold cyan", width=16)
        paper.add_column(style="white")
        paper.add_column(style="dim", width=24)

        paper.add_row("Equity", f"${data.get('paper_equity', 0):,.2f}",
                      f"Balance: ${data.get('paper_balance', 0):,.2f}")
        paper.add_row("Day P&L", _pnl(data.get("paper_day_pnl", 0)),
                      f"Trades: {data.get('paper_day_trades', 0)}")
        paper.add_row("Total P&L", _pnl(data.get("paper_total_pnl", 0)),
                      f"Balance: ${data.get('paper_balance', 0):,.2f}")

        pos = data.get("paper_position")
        if pos:
            paper.add_row("Position",
                          f"[bold]{pos.get('direction', '').upper()}[/] {pos.get('symbol', '')}",
                          f"Entry: ${pos.get('entry_price', 0):,.2f}")

        console.print(Panel(paper, border_style="dim blue", padding=(1, 2)))

    console.print()


def fmt_paper_status(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    console.print()
    console.print(_header("  Paper Trading Status  "))

    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=16)
    tbl.add_column(style="white")
    tbl.add_column(style="dim")

    tbl.add_row("State", str(data.get("state", "\u2014")),
                f"Uptime: {int(data.get('uptime_sec', 0)) // 60}m")
    tbl.add_row("Equity", f"[bold]${data.get('equity', 0):,.2f}[/]",
                f"Balance: ${data.get('balance', 0):,.2f}")
    tbl.add_row("Total P&L", _pnl(data.get("total_pnl", 0)),
                f"Day P&L: {_pnl(data.get('day_pnl', 0))}")
    tbl.add_row("Day Trades", str(data.get("day_trades", 0)),
                f"Bars: {data.get('bar_count', 0)}")

    pos = data.get("position")
    if pos:
        tbl.add_row("Position",
                    f"[bold]{pos.get('direction', '').upper()}[/] {pos.get('symbol', '')}",
                    f"Entry: ${pos.get('entry_price', 0):,.2f}  Qty: {pos.get('quantity', 0)}")

    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_profit(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    console.print()
    console.print(_header("  Profit Summary  "))

    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=18)
    tbl.add_column(style="white")
    tbl.add_column(style="dim")

    tbl.add_row("Total P&L", _pct(data.get("profit_all_percent", 0)),
                f"{data.get('profit_all_coin', 0):.4f}")
    tbl.add_row("Closed P&L", _pct(data.get("profit_closed_percent", 0)),
                f"{data.get('profit_closed_coin', 0):.4f}")
    tbl.add_row("Win Rate", f"{data.get('winrate', 0) * 100:.1f}%",
                f"{data.get('winning_trades', 0)}W / {data.get('losing_trades', 0)}L")
    tbl.add_row("Profit Factor", f"{data.get('profit_factor', 0):.2f}",
                f"Trades: {data.get('trade_count', 0)}")
    tbl.add_row("Max Drawdown", _pct(-abs(data.get("max_drawdown", 0) * 100)),
                f"Current: {_pct(-abs(data.get('current_drawdown', 0) * 100))}")
    tbl.add_row("Sharpe", f"{data.get('sharpe', 0):.2f}",
                f"Sortino: {data.get('sortino', 0):.2f}")
    avg_dur = data.get("avg_duration") or "\u2014"
    tbl.add_row("CAGR", _pct(data.get("cagr", 0) * 100),
                f"Avg Duration: {avg_dur}")

    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_balance(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    currencies = data.get("currencies", [])
    console.print()
    console.print(_header(f"  Balance  ({data.get('symbol', '')})  "))
    console.print(f"  [bold]Total: ${data.get('total', 0):,.2f}[/]\n")

    tbl = Table(box=box.SIMPLE, padding=(0, 2), show_header=True, header_style="bold cyan")
    tbl.add_column("Currency", style="bold white")
    tbl.add_column("Free", justify="right", style="green")
    tbl.add_column("Used", justify="right", style="yellow")
    tbl.add_column("Balance", justify="right", style="bold white")
    tbl.add_column("Est. Stake", justify="right", style="dim")

    for c in currencies[:20]:
        tbl.add_row(
            c.get("currency", ""),
            f"{c.get('free', 0):.4f}",
            f"{c.get('used', 0):.4f}",
            f"{c.get('balance', 0):.4f}",
            f"{c.get('est_stake', 0):.2f}",
        )

    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_trades(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    trades_list = data.get("trades", data) if isinstance(data, dict) else data
    if isinstance(trades_list, dict):
        trades_list = trades_list.get("trades", [])

    console.print()
    console.print(_header(f"  Trade History ({len(trades_list)})  "))

    if not trades_list:
        console.print("  [dim]No trades found[/]")
        return

    tbl = Table(box=box.SIMPLE, padding=(0, 1), show_header=True, header_style="bold cyan")
    tbl.add_column("ID", justify="right", width=6)
    tbl.add_column("Pair", style="bold white")
    tbl.add_column("Side", width=6)
    tbl.add_column("Entry", justify="right")
    tbl.add_column("Exit", justify="right")
    tbl.add_column("P&L %", justify="right")
    tbl.add_column("Reason", style="dim", width=14)
    tbl.add_column("Closed", style="dim", width=10)

    for t in trades_list[:50]:
        is_open = t.get("is_open", False)
        pnl = (t.get("profit_pct") or 0)
        side = "SHORT" if t.get("is_short") else "LONG"
        side_color = "red" if t.get("is_short") else "green"

        tbl.add_row(
            str(t.get("trade_id", "")),
            t.get("pair", ""),
            f"[{side_color}]{side}[/]" if not is_open else "[dim]OPEN[/]",
            f"{t.get('open_rate', 0):.2f}",
            f"{t.get('close_rate', 0):.2f}" if not is_open else "\u2014",
            _pct(pnl),
            t.get("exit_reason", "\u2014") or "\u2014",
            t.get("close_date", "")[:10] if not is_open else "\u2014",
        )

    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_sysinfo(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    console.print()
    console.print(_header("  System Info  "))

    cpu_pct = sum(data.get("cpu_load", [])) / max(len(data.get("cpu_load", [])), 1) if data.get("cpu_load") else 0

    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=16)
    tbl.add_column(style="white")

    tbl.add_row("CPU Usage", f"{cpu_pct:.1f}%")
    tbl.add_row("CPU Cores", str(data.get("cpu_count", "\u2014")))
    tbl.add_row("RAM Usage", f"{data.get('ram_pct', 0):.1f}%")

    load = data.get("cpu_load_avg", {})
    if load:
        tbl.add_row("Load Avg",
                    f"1m: {load.get('1m', 0):.2f}  "
                    f"5m: {load.get('5m', 0):.2f}  "
                    f"15m: {load.get('15m', 0):.2f}")

    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_health(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    console.print()
    console.print(_header("  Health  "))

    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=20)
    tbl.add_column(style="white")

    tbl.add_row("Last Process", str(data.get("last_process", "\u2014")))
    tbl.add_row("Bot Startup", str(data.get("bot_startup", "\u2014")))
    tbl.add_row("Bot Started", str(data.get("bot_start", "\u2014")))

    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_performance(data: list) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    console.print()
    console.print(_header(f"  Pair Performance ({len(data) if isinstance(data, list) else 0})  "))

    tbl = Table(box=box.SIMPLE, padding=(0, 2), show_header=True, header_style="bold cyan")
    tbl.add_column("Pair", style="bold white")
    tbl.add_column("Trades", justify="right", style="dim")
    tbl.add_column("P&L %", justify="right")
    tbl.add_column("Profit", justify="right", style="green")

    for p in (data if isinstance(data, list) else [])[:30]:
        pnl = p.get("profit_pct", 0)
        tbl.add_row(
            p.get("pair", ""),
            str(p.get("count", 0)),
            _pct(pnl),
            f"{p.get('profit_abs', 0):.4f}",
        )

    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_start(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return
    console.print(f"\n  [green]\u25b6[/] Bot started: [green]{data.get('status', 'ok')}[/]")


def fmt_stop(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return
    console.print(f"\n  [red]\u25a0[/] Bot stopped: [yellow]{data.get('status', 'ok')}[/]")


def fmt_config(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data); return
    console.print(); console.print(_header("  Configuration  "))
    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=16)
    tbl.add_column(style="white")
    for k, v in data.items():
        if k not in ("internals", "api_server", "entry_pricing", "exit_pricing", "unfilledtimeout", "order_types"):
            tbl.add_row(str(k).replace("_", " ").title(), str(v))
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_strategies(data):
    if not HAS_RICH:
        _json_output(data); return
    strategies = data.get("strategies") if isinstance(data, dict) else data if isinstance(data, list) else []
    console.print(); console.print(_header(f"  Strategies ({len(strategies) if isinstance(strategies, list) else 0})  "))
    if not strategies:
        console.print("  [dim]No strategies found[/]")
    else:
        for s in (strategies if isinstance(strategies, list) else []):
            console.print(f"  [cyan]\u25b8[/] [bold white]{s}[/]")
    console.print()


def fmt_daily(data):
    if not HAS_RICH:
        _json_output(data); return
    records = data.get("data") if isinstance(data, dict) else data if isinstance(data, list) else []
    currency = str(data.get("stake_currency", "")) if isinstance(data, dict) else ""
    console.print(); console.print(_header(f"  P&L ({len(records) if isinstance(records, list) else 0} days, {currency})  "))
    if not records:
        console.print("  [dim]No data[/]"); console.print(); return
    tbl = Table(box=box.SIMPLE, padding=(0, 1), show_header=True, header_style="bold cyan")
    tbl.add_column("Date", style="white", width=12)
    tbl.add_column("P&L", justify="right"); tbl.add_column("Balance", justify="right"); tbl.add_column("Trades", justify="right", style="dim", width=8)
    for r in reversed(records if isinstance(records, list) else []):
        tbl.add_row(str(r.get("date", ""))[:10], _pnl(r.get("abs_profit", 0)), f"{r.get('starting_balance', 0):,.2f}", str(r.get("trade_count", 0)))
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_logs(data):
    if not HAS_RICH:
        _json_output(data); return
    logs = data.get("logs") if isinstance(data, dict) else data
    console.print(); console.print(_header(f"  Bot Logs ({data.get('log_count', 0) if isinstance(data, dict) else 0} lines)  "))
    if not logs:
        console.print("  [dim]No logs[/]"); console.print(); return
    for e in (logs if isinstance(logs, list) else [])[-100:]:
        if isinstance(e, str):
            console.print(f"  [dim]{e}[/]")
        elif isinstance(e, (list, tuple)):
            ts = str(e[0]) if len(e) > 0 else ""
            lvl = str(e[1]) if len(e) > 1 else ""
            msg = " ".join(str(x) for x in e[2:]) if len(e) > 2 else ""
            c = "red" if "ERROR" in lvl.upper() else "yellow" if "WARN" in lvl.upper() else ""
            console.print(f"  [dim]{ts[:19]}[/] [{c or 'dim'}]{lvl:8}[/] {msg}")
    console.print()


def fmt_trade_status(data):
    if not HAS_RICH:
        _json_output(data); return
    trades = data if isinstance(data, list) else data.get("trades", [])
    console.print(); console.print(_header(f"  Open Trades ({len(trades) if isinstance(trades, list) else 0})  "))
    if not trades:
        console.print("  [dim]No open trades[/]"); console.print(); return
    tbl = Table(box=box.SIMPLE, padding=(0, 1), show_header=True, header_style="bold cyan")
    tbl.add_column("ID", justify="right", width=6); tbl.add_column("Pair", style="bold white")
    tbl.add_column("Side", width=6); tbl.add_column("Amount", justify="right")
    tbl.add_column("Entry", justify="right")
    for t in (trades if isinstance(trades, list) else [])[:30]:
        side = "SHORT" if t.get("is_short") else "LONG"
        sc = "red" if t.get("is_short") else "green"
        tbl.add_row(str(t.get("trade_id", "")), t.get("pair", ""),
                    f"[{sc}]{side}[/]", f"{t.get('amount', 0):.4f}",
                    f"{t.get('open_rate', 0):.2f}")
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_backtest_status(data):
    if not HAS_RICH:
        _json_output(data); return
    console.print(); console.print(_header("  Backtest Status  "))
    running = data.get("running", False)
    status = "[green]\u25b6 RUNNING[/]" if running else "[dim]\u25a0 IDLE[/]"
    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=16); tbl.add_column(style="white")
    tbl.add_row("Status", status)
    tbl.add_row("Progress", f"{data.get('progress', 0) * 100:.1f}%")
    tbl.add_row("Step", str(data.get("step", "\u2014")))
    tbl.add_row("Trades", str(data.get("trade_count", "\u2014")))
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_backtest_history(data):
    if not HAS_RICH:
        _json_output(data); return
    entries = data if isinstance(data, list) else []
    console.print(); console.print(_header(f"  Backtest History ({len(entries) if isinstance(entries, list) else 0})  "))
    if not entries:
        console.print("  [dim]No history[/]"); console.print(); return
    tbl = Table(box=box.SIMPLE, padding=(0, 1), show_header=True, header_style="bold cyan")
    tbl.add_column("File", style="white", width=30); tbl.add_column("Strategy"); tbl.add_column("TF", width=6); tbl.add_column("Date", style="dim", width=12)
    for e in (entries if isinstance(entries, list) else [])[:20]:
        tbl.add_row(str(e.get("filename", ""))[:30], str(e.get("strategy", "\u2014")),
                    str(e.get("timeframe", "\u2014")), str(e.get("backtest_start_time", ""))[:10] if e.get("backtest_start_time") else "\u2014")
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_backtest_start(data):
    if not HAS_RICH:
        _json_output(data); return
    console.print(f"\n  [green]\u25b6[/] Backtest started. [dim]Check: freqtrade-client backtest status[/]")


def fmt_topup(data):
    if not HAS_RICH:
        _json_output(data); return
    console.print(); console.print(_header("  Paper Top-Up  "))
    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=16); tbl.add_column(style="white")
    tbl.add_row("Amount", f"[green]+${data.get('amount', 0):,.2f}[/]")
    tbl.add_row("Before", f"${data.get('old_balance', 0):,.2f}")
    tbl.add_row("After", f"[bold]${data.get('new_balance', 0):,.2f}[/]")
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_paper_trades(data):
    if not HAS_RICH:
        _json_output(data); return
    trades = data if isinstance(data, list) else data.get("trades", [])
    console.print(); console.print(_header(f"  Paper Trades ({len(trades) if isinstance(trades, list) else 0})  "))
    if not trades:
        console.print("  [dim]No paper trades[/]"); console.print(); return
    tbl = Table(box=box.SIMPLE, padding=(0, 1), show_header=True, header_style="bold cyan")
    tbl.add_column("ID", justify="right", width=5); tbl.add_column("Symbol", style="bold white")
    tbl.add_column("Dir", width=5); tbl.add_column("Entry", justify="right")
    tbl.add_column("Exit", justify="right"); tbl.add_column("P&L $", justify="right"); tbl.add_column("Return", justify="right")
    for t in (trades if isinstance(trades, list) else [])[:30]:
        d = t.get("direction", ""); dc = "red" if d == "short" else "green"
        tbl.add_row(str(t.get("id", "")), t.get("symbol", ""), f"[{dc}]{d[:4].upper()}[/]",
                    f"{t.get('entry_price', 0):,.2f}", f"{t.get('exit_price', 0):,.2f}",
                    _pnl(t.get("net_pnl", 0)), _pct(t.get("return_pct", 0) * 100))
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_paper_account(data):
    if not HAS_RICH:
        _json_output(data); return
    snaps = data if isinstance(data, list) else data.get("snapshots", [])
    console.print(); console.print(_header(f"  Paper Account ({len(snaps) if isinstance(snaps, list) else 0})  "))
    if not snaps:
        console.print("  [dim]No snapshots[/]"); console.print(); return
    tbl = Table(box=box.SIMPLE, padding=(0, 1), show_header=True, header_style="bold cyan")
    tbl.add_column("Time", style="dim", width=20); tbl.add_column("Equity", justify="right"); tbl.add_column("Day P&L", justify="right")
    for s in (snaps if isinstance(snaps, list) else [])[:30]:
        tbl.add_row(str(s.get("ts", "")), f"{s.get('equity', 0):,.2f}", _pnl(s.get("day_pnl", 0)))
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_count(data):
    if not HAS_RICH:
        _json_output(data); return
    console.print(f"\n  [bold cyan]Open Trades:[/] [white]{data.get('current', 0)}[/] / {data.get('max', 0)} max")

def fmt_pair_candles(data):
    if not HAS_RICH:
        _json_output(data); return
    console.print(); console.print(_header("  Candle Data  "))
    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=16); tbl.add_column(style="white")
    tbl.add_row("Pair", str(data.get("pair", "\u2014")))
    tbl.add_row("Timeframe", str(data.get("timeframe", "\u2014")))
    tbl.add_row("Candles", str(data.get("length", 0)))
    signals_l = data.get("enter_long_signals", 0) or data.get("buy_signals", 0)
    signals_s = data.get("enter_short_signals", 0) or data.get("sell_signals", 0)
    tbl.add_row("Signals", f"[green]{signals_l}[/] long  [red]{signals_s}[/] short")
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


def fmt_whitelist(data):
    if not HAS_RICH:
        _json_output(data); return
    pairs = data if isinstance(data, list) else data.get("whitelist") or data.get("blacklist") or data.get("pairs")
    if pairs is None:
        pairs = [] if isinstance(data, dict) else [str(data)]
    if not isinstance(pairs, list):
        pairs = [str(pairs)]
    label = "Pairs"
    if isinstance(data, dict):
        if "whitelist" in data:
            label = f"Whitelist ({data.get('length', len(pairs))})"
        elif "blacklist" in data:
            label = f"Blacklist ({data.get('length', len(pairs))})"
        elif "pairs" in data:
            label = f"Available Pairs ({data.get('length', len(pairs))})"
    console.print(); console.print(_header(f"  {label}  "))
    if not pairs:
        console.print("  [dim]No pairs[/]"); console.print(); return
    tbl = Table(box=box.SIMPLE, padding=(0, 1), show_header=True, header_style="bold cyan")
    tbl.add_column("#", justify="right", style="dim", width=4)
    tbl.add_column("Pair", style="bold white")
    for i, p in enumerate(pairs, 1):
        tbl.add_row(str(i), str(p))
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()


# ── Command → Formatter Mapping ──────────────────────

FORMATTERS = {
    # Core
    "dashboard":    fmt_dashboard,
    "ping":         fmt_ping,
    # Bot Control
    "start":        fmt_start,
    "stop":         fmt_stop,
    "stopbuy":      fmt_stop,
    "reload_config": fmt_start,
    # Account
    "profit":       fmt_profit,
    "balance":      fmt_balance,
    "daily":        fmt_daily,
    "weekly":       fmt_daily,
    "monthly":      fmt_daily,
    "count":        fmt_count,
    # Trades
    "trades":       fmt_trades,
    "status":       fmt_trade_status,
    "performance":  fmt_performance,
    "entries":      fmt_performance,
    "exits":        fmt_performance,
    "mix_tags":     fmt_performance,
    # Config & Info
    "show_config":  fmt_config,
    "version":      fmt_start,
    "sysinfo":      fmt_sysinfo,
    "health":       fmt_health,
    "strategies":   fmt_strategies,
    "strategy":     fmt_strategies,
    "whitelist":    fmt_whitelist,
    "blacklist":    fmt_whitelist,
    "logs":         fmt_logs,
    # Paper Trading
    "paper_status":  fmt_paper_status,
    "paper_topup":   fmt_topup,
    "paper_trades":  fmt_paper_trades,
    "paper_account": fmt_paper_account,
    # Backtest
    "backtest_start":  fmt_backtest_start,
    "backtest_status": fmt_backtest_status,
    "backtest_history": fmt_backtest_history,
    "backtest_history_result": fmt_dashboard,
    # Pairs & Data
    "pair_candles":       fmt_pair_candles,
    "pair_history":       fmt_pair_candles,
    "available_pairs":    fmt_whitelist,
    "pairlists_available": fmt_strategies,
}


def format_output(command: str, data: Any, force_json: bool = False) -> None:
    """Route command output to the appropriate formatter, or print JSON."""
    if force_json or not HAS_RICH:
        _json_output(data)
        return

    formatter = FORMATTERS.get(command)
    if formatter:
        try:
            formatter(data)
        except Exception:
            _json_output(data)  # fallback on formatting error
    else:
        _json_output(data)
