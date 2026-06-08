# Freqtrade AI V2

**AI-powered trading system** built on [Freqtrade](https://github.com/freqtrade/freqtrade) — forked and extended with multi-agent scoring, ML pipeline, edge study, paper trading engine, and a comprehensive React dashboard.

---

## Quick Start

```bash
# 1. Clone & configure
git clone https://github.com/malikstarvo/freqcustom.git && cd freqcustom
cp docker/.env.example .env   # Edit passwords

# 2. Launch the full stack (Docker)
docker compose -f docker/docker-compose.monitoring.yml up -d

# 3. Open the dashboard
# → http://localhost:3000 (Dashboard)
# → http://localhost:3001 (Grafana: admin/admin)
# → http://localhost:8080/api/v1/ping (API)
```

For **detailed VPS setup**, see [`docs/SETUP.md`](docs/SETUP.md).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FREQTRADE AI V2                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────┐   ┌─────────────────────────┐ │
│  │ MULTI-AGENT SCORING SYSTEM          │   │ ML PIPELINE (FreqAI)    │ │
│  │  • Technical Agent   — 40% weight   │   │  • XGBoost GridSearchCV │ │
│  │  • OrderFlow Agent   — 40% weight   │   │  • 13 features (EMA,    │ │
│  │  • Regime Agent      — 20% weight   │   │    RSI, ATR, ADX, etc) │ │
│  │  • Trade Gate — confidence, cooldown, │   │  • Auto-optimization   │ │
│  │    drawdown stop, ML probability    │   │  • ROC-AUC metric      │ │
│  └─────────────────────────────────────┘   └─────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────┐   ┌─────────────────────────┐ │
│  │ EDGE STUDY (TimescaleDB)            │   │ PAPER TRADING ENGINE    │ │
│  │  • Pearson/Spearman correlation     │   │  • Realistic slippage   │ │
│  │  • Quantile profit factor & winrate   │   │  • Risk-based sizing    │ │
│  │  • Rolling stability & decay        │   │  • Dynamic top-up       │ │
│  │  • Regime-conditional breakdown     │   │  • Full audit trail     │ │
│  └─────────────────────────────────────┘   └─────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────┐   ┌─────────────────────────┐ │
│  │ REACT DASHBOARD (14 pages)          │   │ MONITORING              │ │
│  │  • Overview, Dashboard, Trading     │   │  • Prometheus metrics   │ │
│  │  • Market, Data Quality, Features  │   │  • Grafana dashboards   │ │
│  │  • Model, Backtest, Paper, Logs    │   │  • 9 custom panels      │ │
│  │  • Config, System, Balance, Trades  │   │  • WebSocket push       │ │
│  └─────────────────────────────────────┘   └─────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    TIMESCALEDB (PostgreSQL)                       │ │
│  │  • Hypertables: candles, features, labels, research_results      │ │
│  │  • Paper audit: orders, fills, positions, trades, snapshots      │ │
│  │  • Auto-compression after 7 days                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## What You Can Do

| Feature | Description | Command |
|---------|-------------|---------|
| **Live Trading** | Dry-run or live trading with multi-agent signals | `freqtrade trade --config config.json` |
| **Backtesting** | Run historical backtests with AI strategy | `freqtrade backtesting --strategy MultiAgentStrategy` |
| **Edge Study** | Analyze feature correlations & predictive power | `freqtrade edge-study --symbol BTCUSDT --timeframe 15m` |
| **Paper Trading** | Simulate realistic trading with slippage | `freqtrade paper-trader --config config.json` |
| **Training Report** | Generate HTML report combining edge + backtest | `freqtrade train-report --symbol BTCUSDT` |
| **ML Pipeline** | Auto-optimize XGBoost with GridSearchCV | Built into strategy |
| **Web Dashboard** | 14-page React UI with real-time charts | `http://localhost:3000` |
| **Monitoring** | Prometheus + Grafana with pre-built dashboards | `docker compose up -d` |
| **API Access** | 78 REST endpoints + WebSocket | `http://localhost:8080/api/v1` |

---

## Project Structure

```
freqtrade/
├── config/
│   ├── config_paper.json      # Full AI stack config (ready to use)
│   └── freqai_config.json     # ML pipeline config
├── docker/
│   ├── docker-compose.monitoring.yml  # Full stack (DB + bot + UI + metrics)
│   ├── .env.example           # Environment template
│   ├── timescale_setup.sql    # TimescaleDB schema (hypertables + paper tables)
│   ├── dashboards/freqtrade.json      # Grafana dashboard
│   └── grafana-*.yml, prometheus.yml  # Provisioning configs
├── docs/
│   ├── ai-trading.md          # Architecture & features doc
│   └── SETUP.md               # Detailed VPS setup guide
├── freqtrade/
│   ├── commands/
│   │   ├── edge_study_commands.py    # CLI: edge-study
│   │   ├── train_report_commands.py  # CLI: train-report
│   │   ├── paper_commands.py         # CLI: paper-trader
│   │   └── ... (34 standard Freqtrade commands)
│   ├── rpc/api_server/
│   │   ├── api_paper.py         # Paper trading REST API
│   │   └── api_*.py             # 78 total endpoints
│   ├── optimize/edge_study/     # 8 analysis modules
│   ├── papertrade/              # Paper engine + store
│   └── ...
├── user_data/
│   ├── strategies/
│   │   ├── multi_agent_strategy.py    # Main AI strategy
│   │   └── agents/                   # Technical, OrderFlow, Regime, TradeGate
│   └── freqaimodels/
│       └── XGBoostGridSearchModel.py  # ML model
├── web/
│   ├── src/                     # React 19 + Vite + Tailwind dashboard
│   ├── Dockerfile              # Multi-stage build (nginx)
│   └── nginx.conf              # Reverse proxy + WS support
└── README.md / docs/
```

---

## Key Technologies

| Layer | Tech |
|-------|------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, TimescaleDB |
| **Strategy** | Multi-agent scoring (3 agents + trade gate) |
| **ML** | XGBoost, scikit-learn, GridSearchCV, ROC-AUC |
| **Frontend** | React 19, Vite, Tailwind 4, Recharts, Lucide icons |
| **Data** | TimescaleDB hypertables, auto-compression |
| **Monitoring** | Prometheus + Grafana (auto-provisioned) |
| **Exchange** | Bybit (USDT perpetuals) |
| **Timeframe** | 15m (configurable) |

---

## License

- **Core Freqtrade**: [GPLv3](LICENSE) (forked from `freqtrade/freqtrade`)
- **AI Extensions**: Original work by this project

Upstream: `https://github.com/freqtrade/freqtrade.git`
Fork: `https://github.com/malikstarvo/freqcustom.git`

---

**For full VPS setup, all CLI commands, API reference, and troubleshooting — see [docs/SETUP.md](docs/SETUP.md).**
