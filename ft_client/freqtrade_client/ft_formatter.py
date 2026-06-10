"""Rich formatting for freqtrade-client CLI commands."""

import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Any

# ── Timezone: Jakarta WIB (UTC+7) ────────────────────
WIB = timezone(timedelta(hours=7))

def _to_wib(ts) -> str:
    """Convert timestamp (seconds or ISO string) to WIB string."""
    if not ts:
        return "\u2014"
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(WIB)
        elif isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(WIB)
        else:
            return str(ts)
        return dt.strftime("%Y-%m-%d %H:%M WIB")
    except Exception:
        return str(ts)[:19]

def _safe_val(val, default=0):
    """Get value with proper None/null handling."""
    if val is None:
        return default
    return val

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

    # ── Dry-run Warning ────────────────────────────────
    if data.get("dry_run"):
        console.print(
            Panel(
                Text("  \u26a0  DRY RUN MODE \u2014 No real money is being traded. Simulation only.  ", style="bold yellow"),
                box=box.SIMPLE, border_style="yellow",
            )
        )

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


def _bar(percent: float, width: int = 12) -> str:
    """Render a visual bar: '████████░░░░'"""
    pct = max(0, min(abs(percent) / 100, 1)) if percent else 0
    filled = int(pct * width)
    empty = width - filled
    c = _profit_color(percent)
    FILLED = "\u2588"
    EMPTY = "\u2591"
    return f"[{c}]{FILLED * filled}[/][dim]{EMPTY * empty}[/]"


def fmt_profit(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data)
        return

    total_pnl_pct = _safe_val(data.get("profit_all_percent"))
    total_pnl_coin = _safe_val(data.get("profit_all_coin"))
    winrate = _safe_val(data.get("winrate")) * 100
    pf = _safe_val(data.get("profit_factor"))
    max_dd = _safe_val(data.get("max_drawdown")) * 100
    current_dd = _safe_val(data.get("current_drawdown")) * 100
    sharpe = _safe_val(data.get("sharpe"))
    sortino = _safe_val(data.get("sortino"))
    calmar = _safe_val(data.get("calmar"))
    cagr = _safe_val(data.get("cagr")) * 100
    sqn = _safe_val(data.get("sqn"))
    avg_dur = data.get("avg_duration") or "\u2014"
    trade_count = _safe_val(data.get("trade_count"))
    closed_count = _safe_val(data.get("closed_trade_count"))
    best_pair = data.get("best_pair") or "\u2014"
    best_rate = _safe_val(data.get("best_rate")) * 100
    winning = _safe_val(data.get("winning_trades"))
    losing = _safe_val(data.get("losing_trades"))
    pf_val = _safe_val(data.get("profit_factor"))
    expectancy = _safe_val(data.get("expectancy"))

    console.print()

    # ═══ Header: Big P&L ═══════════════════════════════
    pnl_color = "green" if total_pnl_pct >= 0 else "red"
    pnl_sign = "+" if total_pnl_pct >= 0 else ""
    pnl_arrow = "\u25b2" if total_pnl_pct >= 0 else "\u25bc"

    header = Table.grid(padding=(0, 2))
    header.add_column(justify="center")
    header.add_row(
        Text("Profit Summary", style="bold cyan")
    )
    header.add_row(
        Text.assemble(
            (f"  {pnl_arrow} ", f"bold {pnl_color}"),
            (f"{pnl_sign}{total_pnl_pct:.2f}%", f"bold {pnl_color}"),
            ("  Total P&L", "dim"),
        )
    )
    if total_pnl_coin:
        header.add_row(Text(f"{total_pnl_coin:.4f} BTC", style="dim"))
    if closed_count:
        header.add_row(Text(
            f"{closed_count} closed / {trade_count} total trades  \u00b7  "
            f"Best: {best_pair} {_pct(best_rate)}", style="dim"
        ))

    console.print(Panel(header, box=box.DOUBLE, border_style=pnl_color, padding=(1, 3)))

    # ═══ Performance Bars ══════════════════════════════
    console.print(_section("Performance"))
    perf = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    perf.add_column(style="bold cyan", width=16)
    perf.add_column(style="white", width=14)
    perf.add_column(width=14)
    perf.add_column(style="dim")

    wr_bar = _bar(winrate)
    pf_bar = _bar(min(pf * 20, 100))  # scale PF to 0-100 for visual

    perf.add_row("Win Rate", f"{winrate:.1f}%", wr_bar,
                 f"{winning}W / {losing}L")
    perf.add_row("Profit Factor", f"{pf_val:.2f}", pf_bar,
                 f"Expectancy: {expectancy:.2f}")

    console.print(Panel(perf, border_style="dim blue", padding=(1, 2)))

    # ═══ Risk Metrics ══════════════════════════════════
    console.print(_section("Risk Metrics"))
    risk = Table.grid(padding=(0, 4))
    risk.add_column(justify="left")
    risk.add_column(justify="left")
    risk.add_column(justify="left")
    risk.add_column(justify="left")

    risk.add_row(
        Text.assemble(("  Sharpe  ", "bold cyan"), (f"{sharpe:.2f}", "white")),
        Text.assemble(("Sortino  ", "bold cyan"), (f"{sortino:.2f}", "white")),
        Text.assemble(("SQN  ", "bold cyan"), (f"{sqn:.2f}", "white")),
        Text.assemble(("Calmar  ", "bold cyan"), (f"{calmar:.2f}", "white")),
    )
    risk.add_row(
        Text.assemble(("  CAGR  ", "bold cyan"), (_pct(cagr), "white")),
        Text.assemble(("Max DD  ", "bold cyan"), (f"[red]{-abs(max_dd):.2f}%[/]", "white")),
        Text.assemble(("Current DD  ", "bold cyan"), (f"[red]{-abs(current_dd):.2f}%[/]", "white")),
        Text.assemble(("Duration  ", "bold cyan"), (f"{avg_dur}", "white")),
    )

    console.print(Panel(risk, border_style="dim blue", padding=(1, 2)))

    # ═══ P&L Breakdown ═════════════════════════════════
    console.print(_section("P&L Breakdown"))
    bd = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    bd.add_column(style="bold cyan", width=18)
    bd.add_column(style="white", width=14)
    bd.add_column(style="bold cyan", width=18)
    bd.add_column(style="white", width=14)

    bd.add_row(
        "Total P&L %", _pct(total_pnl_pct),
        "Total Coin", f"{total_pnl_coin:.4f}",
    )
    bd.add_row(
        "Closed P&L %", _pct(data.get("profit_closed_percent", 0)),
        "Closed Coin", f"{data.get('profit_closed_coin', 0):.4f}",
    )
    fiat = data.get("profit_all_fiat", 0) or data.get("profit_closed_fiat", 0)
    if fiat:
        bd.add_row("Fiat Value", f"${fiat:,.2f}", "", "")

    console.print(Panel(bd, border_style="dim blue", padding=(1, 2)))
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
        _json_output(data); return

    state = data.get("_state", data.get("status", "ok"))
    is_running = state == "running"
    state_color = "green" if is_running else "yellow"
    state_icon = "\u25cf" if is_running else "\u25b6"
    dry_run = data.get("_dry_run", data.get("dry_run", False))
    strategy = data.get("_strategy") or data.get("strategy") or "\u2014"
    exchange = data.get("_exchange") or data.get("exchange") or "\u2014"
    mode = data.get("_trading_mode") or data.get("trading_mode") or "\u2014"

    console.print()
    header = Table.grid(padding=(0, 2))
    header.add_column(justify="center")
    header.add_row(Text("Bot Started", style="bold cyan"))

    info = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    info.add_column(style="bold cyan", width=16)
    info.add_column(style="white")

    info.add_row("State", f"[{state_color}]{state_icon} {state.upper()}[/]")
    if strategy: info.add_row("Strategy", strategy)
    if exchange: info.add_row("Exchange", exchange)
    DRY_BADGE = "[yellow](DRY RUN \u2014 simulation)[/]"
    LIVE_BADGE = "[red](LIVE)[/]"
    if mode: info.add_row("Mode", f"{mode} {DRY_BADGE if dry_run else LIVE_BADGE}")

    console.print(Panel(info, box=box.DOUBLE, border_style=state_color, padding=(1, 2)))
    console.print(f"  [dim]Run [bold]freqtrade-client dashboard[/] for full status.[/]\n")


def fmt_stop(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data); return

    state = data.get("_state", data.get("status", "stopped"))

    console.print()
    info = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    info.add_column(style="bold cyan", width=16)
    info.add_column(style="white")
    info.add_row("Status", f"[red]\u25a0[/] {state.upper()}")
    console.print(Panel(info, box=box.DOUBLE, border_style="red", padding=(1, 2)))
    console.print(f"  [dim]Run [bold]freqtrade-client start[/] to restart the bot.[/]\n")


def fmt_config(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data); return
    console.print(); console.print(_header("  Active Configuration  "))
    dry = data.get("dry_run", True)
    if dry:
        console.print(Panel(Text("  \u26a0  DRY RUN MODE \u2014 Simulation only. No real money.", style="bold yellow"), box=box.SIMPLE, border_style="yellow"))
    else:
        console.print(Panel(Text("  \u26a0  LIVE MODE \u2014 Real money will be traded!", style="bold red"), box=box.SIMPLE, border_style="red"))

    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=16)
    tbl.add_column(style="white")
    skip = ("internals", "api_server", "entry_pricing", "exit_pricing", "unfilledtimeout", "order_types",
            "freqai", "freqaimodel", "freqaimodel_path", "dry_run", "dry_run_wallet", "minimal_roi")
    keys = ["strategy", "strategy_path", "exchange", "trading_mode", "margin_mode",
            "stake_currency", "stake_amount", "max_open_trades", "timeframe",
            "stoploss", "trailing_stop", "position_adjustment_enable", "short_allowed",
            "cancel_open_orders_on_exit"]
    for k in keys:
        v = data.get(k)
        if v is not None:
            tbl.add_row(str(k).replace("_", " ").title(), str(v))
    # append remaining keys not in skip or keys
    for k, v in data.items():
        if k not in skip and k not in keys and not k.startswith("_"):
            tbl.add_row(str(k).replace("_", " ").title(), str(v))
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))
    console.print()

def fmt_config_live(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data); return

    console.print()
    banner = Panel(
        Align.center(Text.assemble(
            ("\n  Live Trading Config Setup\n\n", "bold white"),
            ("  \u26a0  REAL MONEY WILL BE TRADED  \u26a0\n", "bold red"),
        )),
        box=box.DOUBLE, border_style="red", padding=(0, 2),
    )
    console.print(banner)

    pair = data.get("pair", "\u2014")
    tf = data.get("timeframe", "15m")
    stake = data.get("stake_amount", "unlimited")
    lev = data.get("leverage", "1")
    exc = data.get("exchange", "bybit")

    tbl = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    tbl.add_column(style="bold cyan", width=16)
    tbl.add_column(style="white")
    tbl.add_row("Pair", pair)
    tbl.add_row("Timeframe", tf)
    tbl.add_row("Stake Amount", str(stake))
    tbl.add_row("Leverage", f"{lev}x")
    tbl.add_row("Exchange", exc)
    tbl.add_row("Max Trades", str(data.get("max_open_trades", "3")))
    tbl.add_row("Config File", data.get("_config_file", "config.live.json"))
    console.print(Panel(tbl, border_style="dim blue", padding=(1, 2)))

    console.print()
    console.print(_section("Next Steps"))
    steps = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    steps.add_column(width=3, style="bold cyan")
    steps.add_column(style="white")
    steps.add_row("1.", f"Edit {data.get('_config_file', 'config.live.json')} \u2014 add exchange API keys")
    steps.add_row("2.", f"cp config.live.json config.json")
    steps.add_row("3.", f"docker compose restart freqtrade")
    steps.add_row("4.", f"freqtrade-client start")
    console.print(Panel(steps, border_style="dim green", padding=(1, 2)))
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


def fmt_markets(data: dict) -> None:
    if not HAS_RICH:
        _json_output(data); return

    exchange_name = data.get("exchange", "unknown").upper()
    pairs = data.get("pairs", [])
    error = data.get("_error")
    dry = data.get("dry_run", True)

    console.print()

    # Header
    hdr = Table.grid(padding=(0, 2))
    hdr.add_column(justify="center")
    hdr.add_row(Text(f"Market Data", style="bold cyan"))
    hdr.add_row(Text(f"{exchange_name}  \u00b7  {'DRY RUN' if dry else 'LIVE'}",
                      style="dim"))
    console.print(Panel(hdr, box=box.DOUBLE, border_style="cyan", padding=(1, 2)))

    if error:
        console.print(Panel(
            Text(f"  {error}", style="red"),
            box=box.SIMPLE, border_style="red"
        ))
        console.print()
        return

    if not pairs:
        console.print("  [dim]No market data available[/]\n")
        return

    # Ticker Table
    tbl = Table(
        box=box.SIMPLE, padding=(0, 1),
        show_header=True, header_style="bold cyan",
    )
    tbl.add_column("Symbol", style="bold white", width=14)
    tbl.add_column("Price", justify="right", width=12)
    tbl.add_column("24h Chg", justify="right", width=10)
    tbl.add_column("High", justify="right", width=12)
    tbl.add_column("Low", justify="right", width=12)
    tbl.add_column("Volume", justify="right", width=12)
    tbl.add_column("Bid/Ask", justify="right", width=16)

    for p in pairs:
        symbol = p.get("symbol", "")
        last = p.get("last", 0)
        chg = p.get("change_pct", 0)
        high = p.get("high", 0)
        low = p.get("low", 0)
        vol = p.get("volume", 0)
        bid = p.get("bid", 0)
        ask = p.get("ask", 0)

        # Color coding
        chg_color = "green" if chg >= 0 else "red"
        chg_arrow = "\u25b2" if chg >= 0 else "\u25bc"
        price_color = "green" if chg >= 0 else "red"

        # Format volume
        if vol >= 1e9:
            vol_str = f"${vol/1e9:.1f}B"
        elif vol >= 1e6:
            vol_str = f"${vol/1e6:.1f}M"
        elif vol >= 1e3:
            vol_str = f"${vol/1e3:.1f}K"
        else:
            vol_str = f"${vol:.0f}"

        # Price precision
        if last >= 1000:
            price_fmt = f"{last:,.0f}"
        elif last >= 1:
            price_fmt = f"{last:,.2f}"
        else:
            price_fmt = f"{last:.6f}"

        # High/Low same precision
        if high >= 1000:
            hl_fmt = "{:,.0f}"
        elif high >= 1:
            hl_fmt = "{:,.2f}"
        else:
            hl_fmt = "{:.6f}"

        tbl.add_row(
            symbol,
            f"[{price_color}]${price_fmt}[/]",
            f"[{chg_color}]{chg_arrow} {abs(chg):.2f}%[/]",
            hl_fmt.format(high),
            hl_fmt.format(low),
            vol_str,
            f"{bid:.4f}/{ask:.4f}" if bid and ask else "\u2014",
        )

    console.print(Panel(tbl, border_style="dim blue", padding=(1, 1)))

    # Footer
    console.print(f"  [dim]{len(pairs)} pairs  \u00b7  {exchange_name}  \u00b7  Real-time data[/]\n")


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
    "config_live":  fmt_config_live,
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
    "markets":            fmt_markets,
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
