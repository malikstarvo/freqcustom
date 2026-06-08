# VPS Setup Guide — Freqtrade AI V2

Complete step-by-step guide to deploy Freqtrade AI on a fresh VPS.

**Tested on:** Ubuntu 22.04/24.04 LTS, 4GB RAM, 20GB disk, 2 vCPU.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Setup](#system-setup)
3. [Clone & Configure](#clone--configure)
4. [Install Python Dependencies](#install-python-dependencies)
5. [Build React Dashboard](#build-react-dashboard)
6. [Docker Stack Setup](#docker-stack-setup)
7. [First Run](#first-run)
8. [What You Can Do](#what-you-can-do)
9. [CLI Commands Reference](#cli-commands-reference)
10. [API Reference](#api-reference)
11. [Dashboard Pages](#dashboard-pages)
12. [Configuration Files](#configuration-files)
13. [Troubleshooting](#troubleshooting)
14. [Advanced Topics](#advanced-topics)

---

## Prerequisites

### Minimum VPS Specs

| Resource | Minimum | Recommended |
|----------|---------|-----------|
| RAM | 2 GB | 4 GB |
| Disk | 10 GB | 20 GB |
| vCPU | 1 | 2 |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

### Required Ports

| Port | Service | Purpose |
|------|---------|---------|
| 22 | SSH | Remote access |
| 3000 | React Dashboard | Web UI |
| 8080 | Freqtrade API | REST API + WebSocket |
| 3001 | Grafana | Monitoring dashboards |
| 9090 | Prometheus | Metrics collection |
| 5432 | TimescaleDB | PostgreSQL (optional external) |

### Required Software

- Python 3.11+ (3.11, 3.12, 3.13, or 3.14)
- Docker 24+ & Docker Compose v2
- Node.js 22+ (for building dashboard)
- TA-Lib C library
- Git

---

## System Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Base Dependencies

```bash
sudo apt install -y \
  python3.11 python3.11-venv python3.11-dev python3-pip \
  build-essential git curl wget \
  libssl-dev libffi-dev libxml2-dev libxslt1-dev \
  libjpeg-dev zlib1g-dev libopenblas-dev \
  pkg-config
```

### 3. Install TA-Lib (C Library)

TA-Lib is required for technical indicators. Must be installed **before** Python dependencies.

```bash
# Download and compile TA-Lib
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib

# Configure, build, and install
./configure --prefix=/usr
make
sudo make install

# Verify
ls /usr/lib/libta_lib.*
# Should show: libta_lib.so, libta_lib.a, etc.
```

### 4. Install Docker

```bash
# Remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc

# Install Docker
sudo apt install -y ca-certificates gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group (logout & login required)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### 5. Install Node.js 22

```bash
# Using NodeSource
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version   # v22.x.x
npm --version    # 10.x.x
```

---

## Clone & Configure

### 6. Clone the Repository

```bash
cd ~
git clone https://github.com/malikstarvo/freqcustom.git
mv freqcustom freqtrade
```

### 7. Setup Environment Variables

```bash
cd ~/freqtrade
cp docker/.env.example .env
nano .env
```

Edit the following in `.env`:

```env
# --- REQUIRED ---
TIMESCALE_PASSWORD=change_this_to_strong_password
GRAFANA_PASSWORD=change_this_to_strong_password

# --- API CREDENTIALS ---
API_USERNAME=admin
API_PASSWORD=change_this_to_strong_password

# --- OPTIONAL: Go Collector (if running separately) ---
TIMESCALE_DSN=postgresql://freqtrade:${TIMESCALE_PASSWORD}@timescaledb:5432/freqtrade?sslmode=disable
BYBIT_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT
BYBIT_TIMEFRAMES=15m,1h,4h
```

> **Security:** Never commit `.env` to git. It's already in `.gitignore`.

---

## Install Python Dependencies

### 8. Create Virtual Environment

```bash
cd ~/freqtrade
python3.11 -m venv .venv
source .venv/bin/activate
```

> Note: Always activate the venv before running any `freqtrade` command.

### 9. Install Core + AI Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install Freqtrade itself (editable mode)
pip install -e .

# Install core requirements
pip install -r requirements.txt

# Install FreqAI (ML pipeline)
pip install -r requirements-freqai.txt

# Install TimescaleDB adapter
pip install psycopg2-binary

# Optional: Install all extras (dev, plotting, etc.)
# pip install -r requirements-dev.txt
```

### 10. Verify Installation

```bash
freqtrade --version
# Should show: freqtrade x.x.x

freqtrade --help
# Should show all 37 commands
```

---

## Build React Dashboard

### 11. Install Node Dependencies

```bash
cd ~/freqtrade/web
npm install
```

### 12. Build the Dashboard

```bash
npm run build
# Creates: web/dist/ folder
```

> The dashboard is built into static files and served by Nginx in Docker.

---

## Docker Stack Setup

### 13. Start the Full Stack

```bash
cd ~/freqtrade/docker
docker compose -f docker-compose.monitoring.yml up -d
```

This starts 5 services:

| Service | Port | Description |
|---------|------|-------------|
| `timescaledb` | 5432 | TimescaleDB for OHLCV, features, labels, paper audit |
| `freqtrade` | 8080 | Trading bot + REST API |
| `react-dashboard` | 3000 | React web UI (Nginx) |
| `prometheus` | 9090 | Metrics collection |
| `grafana` | 3001 | Dashboard visualization |

### 14. Verify Docker Services

```bash
docker compose -f docker-compose.monitoring.yml ps
```

All 5 containers should show `running`.

### 15. Initialize Database

The TimescaleDB schema is auto-loaded from `timescale_setup.sql` via Docker volume mount. To verify:

```bash
# Check if tables exist
docker exec -it freqtrade-timescaledb-1 psql -U freqtrade -d freqtrade -c "\dt"
```

You should see:
- `candles`, `feature_values`, `labels`
- `research_results`
- `paper_orders`, `paper_fills`, `paper_positions`, `paper_trades`, `paper_account_snapshots`, `paper_topups`

---

## First Run

### 16. Download Market Data

Before running backtests or live trading, download historical data:

```bash
cd ~/freqtrade
source .venv/bin/activate

freqtrade download-data \
  --config config/config_paper.json \
  --timeframe 15m \
  --timerange 20250101- \
  --pairs BTC/USDT:USDT
```

### 17. Run Your First Backtest

```bash
freqtrade backtesting \
  --config config/config_paper.json \
  --strategy MultiAgentStrategy
```

### 18. Start Dry-Run Trading

```bash
freqtrade trade \
  --config config/config_paper.json \
  --freqaimodel XGBoostGridSearchModel
```

> **Important:** Start with `--dry-run` (enabled in `config_paper.json`). Only switch to live trading after extensive testing.

### 19. Verify Web Access

| Service | URL | Default Login |
|---------|-----|---------------|
| React Dashboard | http://YOUR_VPS_IP:3000 | API user/pass |
| Freqtrade API | http://YOUR_VPS_IP:8080/api/v1/ping | admin/admin |
| Grafana | http://YOUR_VPS_IP:3001 | admin/admin |
| Prometheus | http://YOUR_VPS_IP:9090 | — |

> Replace `YOUR_VPS_IP` with your actual server IP. Use `ufw` or `iptables` to restrict access if needed.

---

## What You Can Do

### Live / Dry-Run Trading

Start the bot with AI signal generation and ML predictions:

```bash
freqtrade trade --config config/config_paper.json
```

Features active:
- Multi-agent scoring (Technical 40% + OrderFlow 40% + Regime 20%)
- Trade gate with confidence threshold, cooldown, drawdown stop
- XGBoost ML probability gate (GridSearchCV auto-tuned)
- ATR-based trailing stop
- Max hold bars exit

### Backtesting

Test strategies on historical data:

```bash
# Basic backtest
freqtrade backtesting \
  --config config/config_paper.json \
  --strategy MultiAgentStrategy \
  --timerange 20250101-20250301

# With FreqAI
freqtrade backtesting \
  --config config/config_paper.json \
  --strategy MultiAgentStrategy \
  --freqaimodel XGBoostGridSearchModel

# Show results
freqtrade backtesting-show \
  --config config/config_paper.json
```

### Edge Study

Analyze which features have predictive power:

```bash
# Run edge study for a single pair
freqtrade edge-study \
  --symbol BTCUSDT \
  --timeframe 15m \
  --config config/config_paper.json

# Multiple pairs
freqtrade edge-study \
  --symbols BTCUSDT,ETHUSDT \
  --timeframes 15m,1h \
  --config config/config_paper.json

# Custom output
freqtrade edge-study \
  --symbol BTCUSDT \
  --timeframe 15m \
  --horizons 4,12,24 \
  --output edge_study_results \
  --config config/config_paper.json
```

Edge study performs:
- Pearson & Spearman correlation per feature
- Quantile profit factor & winrate
- Rolling stability analysis
- Regime-conditional breakdown
- Feature decay analysis
- Composite ranking

Outputs: HTML report, CSV, JSON.

### Paper Trading

Run realistic simulation without real money:

```bash
freqtrade paper-trader \
  --config config/config_paper.json
```

Paper trading features:
- Slippage simulation (0.05%)
- Commission (0.055%)
- Fixed-fraction risk sizing (1% per trade)
- 5 exit conditions: stop loss, target profit, max hold, trailing stop, ML gate
- Dynamic balance top-up via API
- Full audit trail stored in TimescaleDB

Top-up via API:
```bash
curl -X POST http://localhost:8080/api/v1/paper/topup \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000}'
```

Or via Dashboard → Paper Trading page.

### Training Report

Generate comprehensive HTML report combining edge study and backtest:

```bash
freqtrade train-report \
  --symbol BTCUSDT \
  --timeframe 15m \
  --config config/config_paper.json
```

### Web Dashboard

14-page React dashboard accessible at `http://YOUR_VPS_IP:3000`:

| Page | Purpose |
|------|---------|
| **Overview** | Command center — all KPIs at a glance |
| **Dashboard** | Equity curve, daily P&L charts, 6 KPI cards |
| **Trading** | Open positions, closed trade history |
| **Trades** | Full trade table with CSV export |
| **Balance** | Portfolio value + currency breakdown |
| **Paper** | Paper equity, top-up form, trade history |
| **Market** | Market list, search, candle preview |
| **Data Quality** | Coverage monitoring, data freshness |
| **Features** | Strategy registry, FreqAI models, edge study docs |
| **Model** | Feature importance, AUC gauge, grid search params |
| **Backtest** | Runner form, live progress, results, history |
| **Logs** | Searchable, color-coded, auto-scroll |
| **Config** | Sectioned config viewer with reload |
| **System** | CPU/RAM gauges, state control, Prometheus links |

Features:
- Light/dark theme toggle
- WebSocket real-time updates (entry/exit signals)
- Toast notifications
- CSV export (Trades, Paper, Dashboard)
- Responsive layout (mobile sidebar)

### Monitoring

Pre-built Grafana dashboard at `http://YOUR_VPS_IP:3001`:

| Panel | Metric |
|-------|--------|
| Equity Curve | Total equity over time |
| Open Positions | Count of active positions |
| Bot State | Running/stopped/paused |
| Trades by Pair | Trade volume per pair |
| Profit Distribution | Histogram of trade P&L |
| API Latency | P95 response time |
| WebSocket Messages/sec | Real-time throughput |
| Agent Scores | Average confidence per agent |
| ML Predictions | Prediction probability distribution |

### API Access

78 REST endpoints + 1 WebSocket endpoint:

```bash
# Health check
curl http://localhost:8080/api/v1/ping

# Get profit summary
curl http://localhost:8080/api/v1/profit

# Get trade list
curl "http://localhost:8080/api/v1/trades?limit=50"

# Get balance
curl http://localhost:8080/api/v1/balance

# Get paper status
curl http://localhost:8080/api/v1/paper/status

# WebSocket
wscat -c ws://localhost:8080/api/v1/message/ws
```

See [API Reference](#api-reference) below for full endpoint list.

---

## CLI Commands Reference

### Standard Freqtrade Commands (34)

| Command | Description |
|---------|-------------|
| `freqtrade trade` | Start live/dry-run trading |
| `freqtrade create-userdir` | Create user data directory |
| `freqtrade new-config` | Create new configuration file |
| `freqtrade show-config` | Show resolved configuration |
| `freqtrade new-strategy` | Create new strategy template |
| `freqtrade download-data` | Download backtesting data |
| `freqtrade convert-data` | Convert OHLCV data formats |
| `freqtrade convert-trade-data` | Convert trade data formats |
| `freqtrade trades-to-ohlcv` | Convert trades to candles |
| `freqtrade list-data` | List downloaded data |
| `freqtrade backtesting` | Run backtesting |
| `freqtrade backtesting-show` | Show past backtest results |
| `freqtrade backtesting-analysis` | Analyze entry/exit signals |
| `freqtrade edge` | Edge module (deprecated) |
| `freqtrade hyperopt` | Run hyperopt optimization |
| `freqtrade hyperopt-list` | List hyperopt results |
| `freqtrade hyperopt-show` | Show hyperopt result details |
| `freqtrade list-exchanges` | List available exchanges |
| `freqtrade list-markets` | List exchange markets |
| `freqtrade list-pairs` | List trading pairs |
| `freqtrade list-strategies` | List available strategies |
| `freqtrade list-hyperoptloss` | List loss functions |
| `freqtrade list-freqaimodels` | List FreqAI models |
| `freqtrade list-timeframes` | List available timeframes |
| `freqtrade show-trades` | Show trade history |
| `freqtrade test-pairlist` | Test pairlist configuration |
| `freqtrade convert-db` | Migrate database |
| `freqtrade install-ui` | Install FreqUI frontend |
| `freqtrade plot-dataframe` | Plot candles + indicators |
| `freqtrade plot-profit` | Plot profit chart |
| `freqtrade webserver` | Start API webserver |
| `freqtrade strategy-updater` | Update strategy syntax |
| `freqtrade lookahead-analysis` | Detect look-ahead bias |
| `freqtrade recursive-analysis` | Detect recursive formula issues |

### AI-Only Commands (3)

| Command | Description | Output |
|---------|-------------|--------|
| `freqtrade edge-study` | Feature correlation & predictive power analysis | HTML, CSV, JSON |
| `freqtrade train-report` | Combined edge study + backtest HTML report | HTML report |
| `freqtrade paper-trader` | Realistic paper trading simulation | TimescaleDB audit |

---

## API Reference

### Authentication

- **JWT Login:** `POST /api/v1/token/login` (returns access + refresh tokens)
- **JWT Refresh:** `POST /api/v1/token/refresh`

All private endpoints require `Authorization: Bearer <token>` header.

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ping` | Health check (public) |
| GET | `/api/v1/version` | API version |
| GET | `/api/v1/show_config` | Bot configuration |
| GET | `/api/v1/logs` | Bot logs |
| GET | `/api/v1/sysinfo` | System info (CPU, RAM) |
| GET | `/api/v1/health` | Bot health |

### Trading Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/balance` | Account balance |
| GET | `/api/v1/count` | Open trade count |
| GET | `/api/v1/performance` | Performance per pair |
| GET | `/api/v1/profit` | Profit summary |
| GET | `/api/v1/profit_all` | Profit (all/long/short) |
| GET | `/api/v1/stats` | Trade statistics |
| GET | `/api/v1/daily` | Daily P&L |
| GET | `/api/v1/weekly` | Weekly P&L |
| GET | `/api/v1/monthly` | Monthly P&L |
| GET | `/api/v1/status` | Open positions |
| GET | `/api/v1/trades` | All trades |
| GET | `/api/v1/trade/{tradeid}` | Single trade |
| DELETE | `/api/v1/trades/{tradeid}` | Delete trade |
| POST | `/api/v1/forceenter` | Force entry |
| POST | `/api/v1/forceexit` | Force exit |
| GET | `/api/v1/blacklist` | Blacklisted pairs |
| POST | `/api/v1/blacklist` | Add to blacklist |
| DELETE | `/api/v1/blacklist` | Remove from blacklist |
| GET | `/api/v1/whitelist` | Whitelisted pairs |
| GET | `/api/v1/locks` | Trade locks |
| POST | `/api/v1/locks` | Create lock |
| POST | `/api/v1/start` | Start bot |
| POST | `/api/v1/stop` | Stop bot |
| POST | `/api/v1/pause` | Pause bot |
| POST | `/api/v1/reload_config` | Reload config |
| GET | `/api/v1/pair_candles` | Candle data |
| GET | `/api/v1/pair_history` | Pair history with signals |

### Backtest Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/backtest` | Start backtest |
| GET | `/api/v1/backtest` | Get status |
| DELETE | `/api/v1/backtest` | Reset backtest |
| GET | `/api/v1/backtest/abort` | Abort backtest |
| GET | `/api/v1/backtest/history` | List backtest history |
| GET | `/api/v1/backtest/history/result` | View result |
| DELETE | `/api/v1/backtest/history/{file}` | Delete result |
| PATCH | `/api/v1/backtest/history/{file}` | Update notes |

### Paper Trading Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/paper/status` | Paper trader status |
| POST | `/api/v1/paper/topup` | Add balance |
| GET | `/api/v1/paper/trades` | Paper trades |
| GET | `/api/v1/paper/account` | Account history |

### WebSocket

| Type | Endpoint | Description |
|------|----------|-------------|
| WebSocket | `/api/v1/message/ws` | Real-time messages (entry, exit, status) |

Subscribe via JSON:
```json
{"type": "subscribe", "data": ["ENTRY", "EXIT", "STATUS"]}
```

---

## Dashboard Pages

### 1. Overview (`/overview`)
Command center — 4 hero KPI cards (P&L, Winrate, Drawdown, Sharpe), open positions, recent exits, system status, 8 secondary metrics.

### 2. Dashboard (`/dashboard`)
Equity curve (Recharts AreaChart), daily P&L bars (green/red), 6 KPI cards, top pairs, key metrics panel.

### 3. Trading (`/trading`)
Trading terminal — open positions list, closed trade history table.

### 4. Trades (`/trades`)
Full trade history (200 rows), CSV export, sortable columns.

### 5. Balance (`/balance`)
Portfolio total value, currency breakdown table.

### 6. Paper (`/paper`)
Paper equity, balance, day P&L, open position detail (bars-held gauge), top-up form, trade history.

### 7. Market (`/market`)
Exchange market list, search/filter, whitelist status, candle preview with timeframe selector.

### 8. Data Quality (`/data-quality`)
Coverage monitoring per pair, data freshness (fresh/stale/missing), age indicator, color-coded table.

### 9. Features (`/features`)
Strategy registry, FreqAI model list, strategy parameter table, edge study documentation.

### 10. Model (`/model`)
Feature importance bar chart, AUC radial gauge, grid search best params, training pipeline diagram.

### 11. Backtest (`/backtest`)
Backtest runner form (strategy, timeframe, timerange), live progress bar, results KPIs, trade log, history list.

### 12. Logs (`/logs`)
Log level filter (ALL/INFO/WARNING/ERROR), debounced search, auto-scroll toggle, color-coded rows.

### 13. Config (`/config`)
6 section cards (Bot Info, Exchange, Strategy, Risk, ROI, FreqAI), reload button, raw JSON.

### 14. System (`/system`)
CPU/RAM progress bars, load averages, state control (start/stop/refresh), Prometheus/Grafana links.

---

## Configuration Files

### `config/config_paper.json`

Full AI stack configuration:
- **Exchange:** Bybit (USDT perpetuals)
- **Stake:** Unlimited, 3 max open trades
- **Dry run:** Enabled
- **Strategy:** MultiAgentStrategy
- **FreqAI:** XGBoostGridSearchModel, 90-day train, 30-day backtest
- **Features:** 13 columns (EMA, RSI, ATR, ADX, volume, funding, OI, LS ratio, liquidations)
- **API:** Enabled on 0.0.0.0:8080
- **Paper Trader:** BTCUSDT, 15m, $10k capital, 0.055% commission, 0.05% slippage

### `config/freqai_config.json`

ML pipeline configuration:
- **Features:** Same 13 columns as above
- **Label:** 4-bar forward return
- **Model:** XGBoost binary:logistic
- **Grid Search:** max_depth [3,5], learning_rate [0.03,0.05,0.1], n_estimators [200,500], subsample [0.8,1.0], colsample_bytree [0.8,1.0]
- **Validation:** 3-fold CV, ROC-AUC metric

### `docker/.env`

Environment variables:
- `TIMESCALE_PASSWORD` — TimescaleDB password
- `GRAFANA_PASSWORD` — Grafana admin password
- `API_USERNAME` / `API_PASSWORD` — API credentials
- `TIMESCALE_DSN` — Database connection string
- `BYBIT_SYMBOLS` / `BYBIT_TIMEFRAMES` — Collector config

---

## Troubleshooting

### TA-Lib Not Found

```bash
# Error: "TA-Lib wrapper not found"
# Fix: Reinstall after system TA-Lib is installed
pip uninstall ta-lib
pip install ta-lib
```

### Port Already in Use

```bash
# Check what uses the port
sudo lsof -i :8080
# Or
sudo netstat -tlnp | grep 8080

# Kill the process
sudo kill -9 <PID>

# Or change the port in docker/.env
```

### Database Connection Error

```bash
# Check if TimescaleDB is running
docker compose -f docker/docker-compose.monitoring.yml ps

# Check logs
docker compose -f docker-compose.monitoring.yml logs timescaledb

# Verify connection from inside container
docker exec -it freqtrade-timescaledb-1 psql -U freqtrade -d freqtrade -c "SELECT 1;"
```

### Dashboard Not Loading

```bash
# Check if dashboard container is running
docker ps | grep react-dashboard

# Check logs
docker logs freqtrade-react-dashboard-1

# Verify Nginx config
docker exec -it freqtrade-react-dashboard-1 cat /etc/nginx/conf.d/default.conf
```

### Permission Denied (Docker)

```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
# Or:
newgrp docker
```

### Python Module Not Found

```bash
# Make sure venv is activated
source ~/freqtrade/.venv/bin/activate

# Reinstall
pip install -e .
pip install -r requirements-freqai.txt
```

### Out of Memory

```bash
# Check memory usage
free -h

# Reduce Docker memory limits
docker update --memory=1g freqtrade-timescaledb-1

# Or add swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### WebSocket Not Connecting

```bash
# Check if Nginx is proxying WS correctly
docker exec freqtrade-react-dashboard-1 nginx -t

# Verify API is reachable
curl http://localhost:8080/api/v1/ping
```

---

## Advanced Topics

### Running Without Docker

If you prefer running natively on the VPS:

```bash
# 1. Install TimescaleDB natively
# Follow: https://docs.timescale.com/latest/getting-started/installation

# 2. Initialize database
psql -U freqtrade -d freqtrade -f docker/timescale_setup.sql

# 3. Start Freqtrade
freqtrade trade --config config/config_paper.json

# 4. Start dashboard (in another terminal)
cd web && npm run dev
```

### Using a Different Exchange

Edit `config/config_paper.json`:

```json
"exchange": {
  "name": "binance",
  "key": "your_key",
  "secret": "your_secret"
}
```

Then download data for the new exchange:

```bash
freqtrade download-data --config config/config_paper.json --timeframe 15m
```

### Adding New Strategy

```bash
# Create from template
freqtrade new-strategy --strategy MyStrategy

# Edit: user_data/strategies/MyStrategy.py
# Add your indicators and logic

# Test with backtest
freqtrade backtesting --config config/config_paper.json --strategy MyStrategy
```

### Custom FreqAI Model

```bash
# Copy template
cp user_data/freqaimodels/XGBoostGridSearchModel.py user_data/freqaimodels/MyModel.py

# Edit the class, change hyperparameters
# Update config.json: "freqai.model_path": "user_data/freqaimodels"
```

### Backup & Restore

```bash
# Backup database
docker exec freqtrade-timescaledb-1 pg_dump -U freqtrade freqtrade > backup.sql

# Restore database
cat backup.sql | docker exec -i freqtrade-timescaledb-1 psql -U freqtrade -d freqtrade

# Backup config
cp config/config_paper.json config/config_paper.json.backup
```

### Updating the Code

```bash
cd ~/freqtrade
git fetch origin
git pull origin main

# Rebuild dashboard
cd web && npm run build && cd ..

# Restart Docker
docker compose -f docker/docker-compose.monitoring.yml down
docker compose -f docker/docker-compose.monitoring.yml up -d
```

---

## Security Checklist

- [ ] Change all default passwords in `docker/.env`
- [ ] Use `ufw` to restrict ports:
  ```bash
  sudo ufw default deny incoming
  sudo ufw allow 22/tcp
  sudo ufw allow 3000/tcp
  sudo ufw enable
  ```
- [ ] Enable HTTPS with Nginx + Let's Encrypt
- [ ] Use strong API credentials
- [ ] Never commit `.env` or API keys
- [ ] Keep Docker images updated: `docker compose pull`

---

**For more details, see the main documentation: `docs/ai-trading.md` (architecture) and `docs/SETUP.md` (this file).**
