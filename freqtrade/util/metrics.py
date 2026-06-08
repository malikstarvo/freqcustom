# Python Prometheus metrics collector for Freqtrade
# Install: pip install prometheus_client
# Mount at: GET /metrics endpoint via FastAPI

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.registry import CollectorRegistry


registry = CollectorRegistry()

trades_total = Counter(
    "freqtrade_trades_total",
    "Total number of trades placed",
    ["pair", "side"],
    registry=registry,
)

trade_profit_pct = Histogram(
    "freqtrade_trade_profit_pct",
    "Trade profit percentage distribution",
    ["pair"],
    buckets=[-10, -5, -2, -1, 0, 1, 2, 5, 10, 20, 50],
    registry=registry,
)

ws_messages_total = Counter(
    "freqtrade_ws_messages_total",
    "WebSocket messages received",
    ["type"],
    registry=registry,
)

api_latency_seconds = Histogram(
    "freqtrade_api_latency_seconds",
    "API endpoint latency",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry,
)

model_prediction_prob = Histogram(
    "freqtrade_model_prediction_prob",
    "ML model prediction probability",
    ["model"],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=registry,
)

agent_scores = Histogram(
    "freqtrade_agent_score",
    "Multi-agent scoring system output",
    ["agent"],
    buckets=[0, 20, 40, 60, 80, 100],
    registry=registry,
)

open_positions = Gauge(
    "freqtrade_open_positions",
    "Number of currently open positions",
    registry=registry,
)

bot_state = Gauge(
    "freqtrade_bot_state",
    "Bot state (1=running, 0=stopped, 2=paused)",
    registry=registry,
)

daily_pnl = Gauge(
    "freqtrade_daily_pnl_pct",
    "Daily profit/loss percentage",
    registry=registry,
)


def get_metrics() -> bytes:
    return generate_latest(registry)
