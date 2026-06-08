# FreqTrade AI — AI-Powered Trading System

## Overview

FreqTrade AI extends the open-source [Freqtrade](https://github.com/freqtrade/freqtrade) trading framework with a suite of AI-powered components for enhanced signal accuracy, risk management, and monitoring.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     FREQTRADE AI EXTENDED                        │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Multi-Agent      │  │ Edge Study       │  │ Paper Engine │  │
│  │ Scoring System   │  │ Feature Valid.   │  │ (Slippage,   │  │
│  │ Technical  40%   │  │ Pearson/Spearman │  │ Risk sizing, │  │
│  │ OrderFlow  40%   │  │ Quantile PF      │  │ Dynamic top- │  │
│  │ Regime     20%   │  │ Rolling Stability│  │ up balance)  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ TimescaleDB      │  │ XGBoost          │  │ React Dash-  │  │
│  │ Hypertables      │  │ GridSearchCV     │  │ board         │  │
│  │ (10-100x query)  │  │ (Auto-opt)       │  │ (10 pages)    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │            Prometheus + Grafana Monitoring                 │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Features

### Multi-Agent Scoring System
Three specialized agents score each trade independently:
- **Technical Agent (40%)** — EMA alignment, RSI zones, volume ratio, ATR volatility, ADX bonus
- **OrderFlow Agent (40%)** — Funding rate, OI delta, LS ratio, liquidation imbalance
- **Regime Agent (20%)** — 4-state market classification (trending/ranging × high/low vol)
- **Trade Gate** — Confidence threshold, cooldown, max trades/day, drawdown stop, ML probability gate

### Edge Study — Feature Validation
Statistical framework answering "which features are truly predictive?":
- Pearson + Spearman correlation vs future return
- Quantile profit factor & win rate (top 10% vs bottom 10%)
- Rolling stability across 50/100/200 bar windows
- Regime-conditional correlation breakdown
- Decay analysis across 4/12/24 bar horizons
- Composite ranking: PF×0.40 + WR×0.25 + Stability×0.15 + Regime×0.10 + Corr×0.10

### XGBoost Grid Search Pipeline
- Auto-optimization: max_depth, learning_rate, n_estimators, subsample, colsample_bytree
- 3-fold cross-validated ROC-AUC scoring
- Only top-ranked features from Edge Study used for training
- ML probability gate (≥0.45) required for trade execution

### Paper Trading Engine
- Realistic fill simulation with slippage + volume premium
- Fixed-fraction risk sizing: `equity × risk% / (ATR × multiplier)`
- 5 exit conditions: stop loss, max hold, opposite signal, daily drawdown, total drawdown
- Dynamic balance top-up (add capital mid-run)
- Full audit trail: orders → fills → positions → trades → account snapshots

### TimescaleDB Integration
- Hypertable storage for candles, features, labels
- 10-100x faster time-series queries vs standard PostgreSQL
- Auto-compression after 7 days
- Read-only adapter for Freqtrade's DataProvider

### React Dashboard (10 Pages)
- Dashboard, Trading, Trades, Balance, Paper, Model, Backtest, Logs, Config, System
- WebSocket push every 10s
- Feature importance bar chart, AUC donut gauge
- Paper trading: live position tracking, top-up form, trade history

### Prometheus + Grafana Monitoring
- Custom metrics: trades, profit, API latency, WebSocket messages, agent scores, ML predictions
- Pre-built Grafana dashboard with 8 panels
- Auto-provisioned datasource and dashboard

## Quick Start

```bash
# 1. Copy environment template
cp docker/.env.example .env
# Edit .env — set TIMESCALE_PASSWORD to a secure value

# 2. Start infrastructure
docker compose -f docker/docker-compose.monitoring.yml up -d
# Starts: TimescaleDB, Freqtrade, React Dashboard, Prometheus, Grafana

# 3. Run edge study (feature validation)
freqtrade edge-study --symbol BTCUSDT --timeframe 15m \
  --config config/config_paper.json

# 4. Train ML model
freqtrade trade --config config/config_paper.json \
  --freqaimodel XGBoostGridSearchModel

# 5. Run backtest
freqtrade backtesting --strategy MultiAgentStrategy \
  --config config/config_paper.json

# 6. Generate training report
freqtrade train-report --symbol BTCUSDT --timeframe 15m \
  --config config/config_paper.json

# 7. Start paper trader
freqtrade paper-trader --config config/config_paper.json
```

## Access URLs

| Service | URL | Default Login |
|---------|-----|---------------|
| React Dashboard | http://localhost:3000 | API auth (admin/admin) |
| Freqtrade API | http://localhost:8080/api/v1/ping | admin / admin |
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | — |

## CLI Commands

| Command | Description |
|---------|-------------|
| `freqtrade edge-study` | Run feature importance analysis with TimescaleDB |
| `freqtrade train-report` | Generate comprehensive HTML training report |
| `freqtrade paper-trader` | Start paper trading engine (background) |
| `freqtrade trade` | Run live/dry-run trading with strategy |
| `freqtrade backtesting` | Backtest strategy on historical data |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ping` | GET | Health check |
| `/api/v1/profit` | GET | Profit statistics |
| `/api/v1/trades` | GET | Trade history |
| `/api/v1/balance` | GET | Account balance |
| `/api/v1/paper/status` | GET | Paper trader state, equity, P&L |
| `/api/v1/paper/topup` | POST | Add simulated capital |
| `/api/v1/paper/trades` | GET | Paper trade history |
| `/api/v1/message/ws` | WS | Real-time trade/status WebSocket |

## Configuration

Config presets available in `config/`:

| File | Purpose |
|------|---------|
| `config/config_paper.json` | Full config: paper trader, FreqAI, TimescaleDB, edge study |
| `config/freqai_config.json` | FreqAI-only config for training/backtesting |

## Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Basic Freqtrade (pre-built image) |
| `docker/docker-compose-freqai.yml` | Freqtrade + FreqAI |
| `docker/docker-compose-jupyter.yml` | Freqtrade + JupyterLab |
| `docker/docker-compose.monitoring.yml` | Full AI stack: TimescaleDB, Freqtrade, React, Prometheus, Grafana |

## Requirements

- Docker 24+ with Docker Compose v2
- Python 3.11+ (for CLI commands)
- PostgreSQL/TimescaleDB (included in Docker stack)
- 4GB RAM, 10GB disk (recommended)

## Docs

- [AI Trading Deep Dive](docs/ai-trading.md) — Multi-agent scoring, edge study, paper engine, training pipeline

## License

MIT — same as upstream Freqtrade.
