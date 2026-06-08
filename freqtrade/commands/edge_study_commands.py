import logging

from freqtrade.optimize.edge_study.correlation import EdgeStore
from freqtrade.optimize.edge_study.report import export_csv, export_html, export_json
from freqtrade.optimize.edge_study.study import Study
from freqtrade.optimize.edge_study.types import FeatureInfo, LabelHorizon, StudyConfig


logger = logging.getLogger(__name__)


DEFAULT_FEATURES = [
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
    FeatureInfo(name="liq_imbalance", col="liq_imbalance"),
]


def setup_edge_study_config(args: dict) -> StudyConfig:
    symbols = args.get("symbols", args.get("symbol", ""))
    if isinstance(symbols, str):
        symbols = [s.strip() for s in symbols.split(",") if s.strip()]

    timeframes = args.get("timeframes", args.get("timeframe", "15m"))
    if isinstance(timeframes, str):
        timeframes = [t.strip() for t in timeframes.split(",") if t.strip()]

    horizons = args.get("horizons", "4,12,24")
    if isinstance(horizons, str):
        horizons = [int(h.strip()) for h in horizons.split(",") if h.strip().isdigit()]

    feature_set_id = int(args.get("feature_set_id", 1))

    label_horizons = []
    for h in horizons:
        name = f"future_return_{h}"
        col = f"future_return_{h}"
        label_horizons.append(LabelHorizon(name=name, col=col))

    features = DEFAULT_FEATURES

    return StudyConfig(
        symbols=symbols,
        timeframes=timeframes,
        feature_set_id=feature_set_id,
        label_horizons=label_horizons,
        rolling_windows=[50, 100, 200],
        quantile_n_buckets=10,
        regime_pct=0.5,
        features=features,
    )


def start_edge_study(args: dict) -> None:
    config = args.get("config", {})
    edge_config = config.get("edge_study", {})
    dsn = edge_config.get("database_url", "")

    if not dsn:
        logger.error("Edge study requires database_url in config['edge_study']")
        return

    study_cfg = setup_edge_study_config(args)

    store = EdgeStore(dsn)
    study = Study(store, study_cfg)

    logger.info("Starting edge study...")
    study.run_all()

    output_dir = args.get("output", "edge_study_results")
    html_path = f"{output_dir}/edge_report.html"
    csv_path = f"{output_dir}/feature_ranking.csv"
    json_path = f"{output_dir}/metrics.json"

    export_html(study, html_path)
    export_csv(study, csv_path)
    export_json(study, json_path)

    logger.info(f"Edge study complete. Results saved to {output_dir}/")
    logger.info(f"  HTML: {html_path}")
    logger.info(f"  CSV:  {csv_path}")
    logger.info(f"  JSON: {json_path}")

    top = study.top_features(5)
    logger.info("Top 5 features by composite score:")
    for i, f in enumerate(top):
        logger.info(f"  {i+1}. {f}")
