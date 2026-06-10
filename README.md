# Freqtrade AI V2

**AI-powered trading system** built on [Freqtrade](https://github.com/freqtrade/freqtrade) — forked and extended with multi-agent scoring, ML pipeline, edge study, paper trading engine, and a powerful CLI dashboard.

---

## Quick Start

```bash
# 1. Clone & configure
git clone https://github.com/malikstarvo/freqcustom.git && cd freqcustom

# 2. Launch the full stack (Docker)
docker compose --profile monitoring up -d

# 3. Use the CLI (inside container)
docker compose exec freqtrade freq --show
docker compose exec freqtrade freq dashboard
```

---

## CLI Usage (`freq`)

The `freq` CLI provides a full terminal dashboard — formatted tables, color-coded P&L, real-time market data, and bot control. All via the REST API.

```bash
freq --show                      # List all commands
freq dashboard                   # Full status overview
freq start                       # Start trading bot
freq stop                        # Stop trading bot

# Account & Performance
freq profit                      # Profit/loss summary
freq balance                     # Wallet balances
freq daily                       # Daily P&L breakdown
freq trades limit=10             # Recent trade history
freq performance                 # Per-pair performance

# Real-Time Market Data
freq markets limit=10            # Live prices from exchange

# Paper Trading
freq paper status                # Paper engine status
freq paper topup amount=5000     # Add simulated capital
freq paper trades limit=10       # Paper trade history

# Backtesting
freq backtest start              # Start backtest (uses config strategy)
freq backtest start strategy=MultiAgentStrategy timeframe=1h
freq backtest status             # Check progress
freq backtest history            # View results

# Config
freq config show                 # Show active configuration
freq config live pair=BTC/USDT:USDT  # Generate live trading config

# System
freq sysinfo                     # CPU/RAM usage
freq logs                        # Recent bot logs
freq health                      # Health check
freq whitelist                   # Show whitelisted pairs
freq strategies                  # List strategies

# Raw JSON
freq profit --json               # Machine-readable output
```

### Training Workflow

```bash
# 1. Download historical data
docker compose exec freqtrade freqtrade download-data --config /freqtrade/config.json

# 2. Run backtest
freq backtest start timeframe=15m timerange=20250101-20250601

# 3. Check results
freq backtest status
freq backtest history

# 4. Start paper trader
docker compose exec freqtrade freqtrade paper-trader --config /freqtrade/config.json

# 5. Monitor paper performance
freq paper status
freq paper account
```

### Deploy Dashboard to Vercel (Optional)

The frontend is a **Next.js** app in `web/`. Deploy it to Vercel for free:

1. Go to [vercel.com](https://vercel.com), import this repo
2. Set **Root Directory** to `web`
3. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL = http://YOUR_VPS_IP:8080/api/v1
   ```
4. Deploy — dashboard will be available at `https://your-project.vercel.app`

The VPS becomes a **pure backend** (API + TimescaleDB + Collector + Grafana). The web dashboard is optional — the CLI (`freq`) replaces it.

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

---

## Access via Cloudflare Tunnel

To expose the dashboard without opening firewall ports:

```bash
# 1. Install cloudflared
curl -fsSL https://pkg.cloudflare.com/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# 2. Login to Cloudflare (opens browser)
cloudflared tunnel login

# 3. Create tunnels (separate per service)
cloudflared tunnel create freqtrade-dashboard
cloudflared tunnel create freqtrade-api
cloudflared tunnel create freqtrade-grafana

# 4. Create config.yml — paste tunnel UUIDs from step 3
# ~/.cloudflared/config.yml — see docs/SETUP.md for full config
```

**Important:** Cloudflare Tunnel runs as a systemd service pointing at `localhost` ports. It is **fully independent** from the Freqtrade code:
- `git pull` / `git commit` / `git push` → **no effect on tunnel** — tunnel stays live
- `docker compose restart` → **no effect** — tunnel reconnects automatically
- Tunnel only needs restart if: you change `config.yml`, reboot VPS, or update the `cloudflared` binary

Full instructions: [`docs/SETUP.md` § Cloudflare Tunnel](docs/SETUP.md#cloudflare-tunnel)
