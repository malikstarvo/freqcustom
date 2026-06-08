from dataclasses import dataclass, field


@dataclass
class FeatureInfo:
    name: str = ""
    col: str = ""


@dataclass
class EdgeFilter:
    symbol: str = ""
    timeframe: str = ""
    feature_set_id: int = 0


@dataclass
class LabelHorizon:
    name: str = ""
    col: str = ""


@dataclass
class StudyConfig:
    symbols: list[str] = field(default_factory=list)
    timeframes: list[str] = field(default_factory=list)
    feature_set_id: int = 0
    label_horizons: list[LabelHorizon] = field(default_factory=list)
    rolling_windows: list[int] = field(default_factory=lambda: [50, 100, 200])
    quantile_n_buckets: int = 10
    regime_pct: float = 0.5
    features: list[FeatureInfo] = field(default_factory=list)


@dataclass
class MetricResult:
    feature_name: str = ""
    label_horizon: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    samples: int = 0
    metadata: dict = field(default_factory=dict)
