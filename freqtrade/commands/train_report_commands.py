import json
import logging
import os
import time as time_mod
from datetime import datetime

import psycopg2
import psycopg2.pool

from freqtrade.optimize.edge_study.types import StudyConfig, FeatureInfo, LabelHorizon
from freqtrade.optimize.edge_study.correlation import EdgeStore
from freqtrade.optimize.edge_study.study import Study

logger = logging.getLogger(__name__)

HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Training Report — {symbol} {timeframe}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a1a;color:#e0e0e0;font-family:system-ui,sans-serif;padding:2rem}}
h1{{color:#00d4ff;margin-bottom:.25rem}}h2{{color:#7b68ee;margin:2rem 0 .5rem}}
.meta{{color:#666;margin-bottom:1.5rem}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1rem 0}}
.card{{background:#1a1a2e;border:1px solid #2a2d3e;border-radius:8px;padding:1rem}}
.card .label{{font-size:.7rem;text-transform:uppercase;color:#888}}
.card .value{{font-size:1.8rem;font-weight:bold;margin:.25rem 0}}
.good{{color:#00ff88}}.bad{{color:#ff4466}}.warn{{color:#ffaa00}}
table{{width:100%;border-collapse:collapse;margin:1rem 0}}
th{{background:#16213e;color:#00d4ff;padding:.5rem;text-align:left;border-bottom:2px solid #7b68ee}}
td{{padding:.4rem .5rem;border-bottom:1px solid #222;font-size:.85rem}}
tr:hover{{background:#16213e}}
.bar{{height:6px;background:#2a2d3e;border-radius:3px;overflow:hidden;margin-top:2px}}
.bar-fill{{height:100%;border-radius:3px}}
pre{{background:#111;padding:1rem;border-radius:4px;font-size:.75rem;overflow:auto}}
</style>
</head>
<body>
<h1>Training Report</h1>
<p class="meta">{meta_line}</p>

<h2>Strategy Performance</h2>
<div class="grid">
{perf_cards}
</div>

<h2>Feature Importance (Top 10)</h2>
<table>
<tr><th>Rank</th><th>Feature</th><th>Composite Score</th><th>Profit Factor</th><th>Stability</th></tr>
{feature_rows}
</table>

<h2>Edge Study Metrics</h2>
<table>
<tr><th>Feature</th><th>Pearson</th><th>Spearman</th><th>Q Top PF</th><th>Q Top WR</th><th>Decay Rate</th><th>Regime Consistency</th></tr>
{edge_rows}
</table>

<h2>Training Details</h2>
<pre>{training_json}</pre>

<p style="margin-top:2rem;color:#666;font-size:.7rem">Generated {gen_time}</p>
</body>
</html>
"""


def _load_edge_study_results(store: EdgeStore, symbol: str, timeframe: str,
                             feature_set_id: int) -> list[dict]:
    cfg = StudyConfig(
        symbols=[symbol],
        timeframes=[timeframe],
        feature_set_id=feature_set_id,
        label_horizons=[
            LabelHorizon(name="future_return_4", col="future_return_4"),
            LabelHorizon(name="future_return_12", col="future_return_12"),
            LabelHorizon(name="future_return_24", col="future_return_24"),
        ],
        features=[
            FeatureInfo(name="ema20", col="ema20"),
            FeatureInfo(name="ema50", col="ema50"),
            FeatureInfo(name="ema200", col="ema200"),
            FeatureInfo(name="rsi14", col="rsi14"),
            FeatureInfo(name="atr14", col="atr14"),
            FeatureInfo(name="adx14", col="adx14"),
            FeatureInfo(name="volume_ema20", col="volume_ema20"),
            FeatureInfo(name="volatility14", col="volatility14"),
            FeatureInfo(name="funding_rate", col="funding_rate"),
            FeatureInfo(name="oi_delta_1_pct", col="oi_delta_1_pct"),
            FeatureInfo(name="ls_ratio", col="ls_ratio"),
            FeatureInfo(name="liq_long_usd", col="liq_long_usd"),
            FeatureInfo(name="liq_short_usd", col="liq_short_usd"),
        ],
    )
    study = Study(store, cfg)
    study.run_all()
    return [{
        "feature_name": r.feature_name,
        "label_horizon": r.label_horizon,
        "metric_name": r.metric_name,
        "metric_value": r.metric_value,
        "samples": r.samples,
    } for r in study.all_results]


def _extract_edge_metrics(results: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    by_feature: dict[str, dict] = {}
    for r in results:
        fn = r["feature_name"]
        if fn not in by_feature:
            by_feature[fn] = {}
        key = r["metric_name"]
        if r["label_horizon"]:
            key = f"{r['metric_name']}_{r['label_horizon']}"
        by_feature[fn][key] = r["metric_value"]

    composite_scores = []
    for fn, metrics in by_feature.items():
        score = metrics.get("composite_score", 0)
        pf = 0.0
        stability = 0.0
        for mkey, val in metrics.items():
            if mkey.startswith("q_top_pf"):
                pf = max(pf, val)
            if mkey.startswith("rolling_stability"):
                stability = max(stability, val)
        composite_scores.append({
            "feature": fn,
            "composite": score,
            "profit_factor": pf,
            "stability": stability,
        })

    composite_scores.sort(key=lambda x: x["composite"], reverse=True)
    return composite_scores, by_feature


def _generate_html(symbol: str, timeframe: str, edge_results: list[dict],
                   backtest_perf: dict, training_info: dict) -> str:
    meta_line = f"{symbol} · {timeframe} · Edge Study + ML Training + Backtest"
    gen_time = datetime.now().isoformat()

    composite_scores, by_feature = _extract_edge_metrics(edge_results)

    perf_cards = f"""
    <div class="card"><div class="label">Win Rate</div>
    <div class="value {"good" if backtest_perf.get("winrate", 0) >= 0.55 else "bad"}">{backtest_perf.get("winrate", 0)*100:.1f}%</div></div>
    <div class="card"><div class="label">Profit Factor</div>
    <div class="value {"good" if backtest_perf.get("profit_factor", 0) >= 1.5 else "warn"}">{backtest_perf.get("profit_factor", 0):.2f}x</div></div>
    <div class="card"><div class="label">Sharpe Ratio</div>
    <div class="value {"good" if backtest_perf.get("sharpe", 0) >= 1.0 else "warn"}">{backtest_perf.get("sharpe", 0):.2f}</div></div>
    <div class="card"><div class="label">Max Drawdown</div>
    <div class="value {"good" if backtest_perf.get("max_drawdown", 0) <= 0.15 else "bad"}">{backtest_perf.get("max_drawdown", 0)*100:.1f}%</div></div>
    <div class="card"><div class="label">Trade Count</div>
    <div class="value">{backtest_perf.get("trade_count", 0)}</div></div>
    <div class="card"><div class="label">Avg Return</div>
    <div class="value {"good" if backtest_perf.get("profit_all_percent", 0) >= 0 else "bad"}">{backtest_perf.get("profit_all_percent", 0):.2f}%</div></div>
    """

    feature_rows = ""
    for i, f in enumerate(composite_scores[:10]):
        feature_rows += f"""<tr>
        <td>{i+1}</td><td>{f["feature"]}</td>
        <td>{f["composite"]:.3f}</td><td>{f["profit_factor"]:.2f}x</td>
        <td>{f["stability"]:.3f}</td></tr>"""

    edge_rows = ""
    for fn in sorted(by_feature.keys()):
        m = by_feature[fn]
        pearson = m.get("pearson", 0)
        spearman = m.get("spearman", 0)
        pf = max([v for k, v in m.items() if k.startswith("q_top_pf")], default=0)
        wr = max([v for k, v in m.items() if k.startswith("q_top_wr")], default=0)
        decay = m.get("decay_rate", 0)
        regime = 0.0
        regime_keys = [k for k in m if k.startswith("regime_")]
        regime_vals = [v for k, v in m.items() if k.startswith("regime_")]
        if len(regime_vals) >= 2:
            regime = 1.0 - (max(regime_vals) - min(regime_vals))

        edge_rows += f"""<tr>
        <td>{fn}</td><td>{pearson:.4f}</td><td>{spearman:.4f}</td>
        <td>{pf:.2f}x</td><td>{wr*100:.1f}%</td>
        <td>{decay:.4f}</td><td>{regime:.3f}</td></tr>"""

    training_json_str = json.dumps(training_info, indent=2, default=str)

    return HTML_REPORT_TEMPLATE.format(
        symbol=symbol, timeframe=timeframe,
        meta_line=meta_line, gen_time=gen_time,
        perf_cards=perf_cards,
        feature_rows=feature_rows,
        edge_rows=edge_rows,
        training_json=training_json_str,
    )


def start_train_report(args: dict) -> None:
    config = args.get("config", {})
    symbol = args.get("symbol", "BTCUSDT")
    timeframe = args.get("timeframe", "15m")
    output = args.get("output", "training_report.html")
    edge_config = config.get("edge_study", {})
    ts_config = config.get("timescaledb", {})
    dsn = ts_config.get("database_url", edge_config.get("database_url", ""))

    if not dsn:
        logger.error("timescaledb.database_url required for edge study")
        return

    feature_set_id = ts_config.get("feature_set_id", 1)

    logger.info(f"Running training report: {symbol} {timeframe}")
    start_time = time_mod.time()

    edge_results: list[dict] = []
    try:
        store = EdgeStore(dsn)
        edge_results = _load_edge_study_results(store, symbol, timeframe, feature_set_id)
        logger.info(f"Edge study: {len(edge_results)} metrics")
    except Exception as e:
        logger.warning(f"Edge study skipped: {e}")

    backtest_perf = {
        "winrate": 0.0,
        "profit_factor": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "trade_count": 0,
        "profit_all_percent": 0.0,
    }

    training_info = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "timeframe": timeframe,
        "feature_set_id": feature_set_id,
        "edge_study_metrics": len(edge_results),
        "backtest": backtest_perf,
    }

    html = _generate_html(symbol, timeframe, edge_results, backtest_perf, training_info)

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    elapsed = time_mod.time() - start_time
    logger.info(f"Training report generated: {output} ({elapsed:.1f}s)")
    logger.info(f"  Edge study metrics: {len(edge_results)}")
    logger.info(f"  Open in browser: file:///{os.path.abspath(output)}")
