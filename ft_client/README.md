# Freqtrade Client

CLI for remote management of a [Freqtrade](https://github.com/freqtrade/freqtrade) AI trading bot via REST API + SSH.

## Installation

```bash
# From local build
pip install -e /path/to/ft_client

# Or via pipx (isolated, recommended)
pipx install /path/to/ft_client
```

After installation, the `freq` command is available globally.

```
freq --show
```

## Prerequisites

- **Python 3.11+**
- **OpenSSH client** — required for SSH-based commands (`ssh` must be in PATH)
- **SSH key access** to the server (passwordless login via key pair)
- **Server URL** — your freqtrade API endpoint (e.g. `http://43.159.56.168:8080`)

### SSH Key Setup (one time)

```bash
# Generate a key pair (if you don't have one)
ssh-keygen -t ed25519 -C "freqtrade-client"

# Copy public key to the server
ssh-copy-id ubuntu@43.159.56.168

# Verify passwordless login works
ssh ubuntu@43.159.56.168 echo ok
```

## Configuration

The CLI resolves configuration in this order (env vars take highest priority):

### 1. Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `FT_SERVER_URL` | — | API endpoint (e.g. `http://43.159.56.168:8080`) |
| `FT_SERVER_USERNAME` | `api_server.username` | API auth username |
| `FT_SERVER_PASSWORD` | `api_server.password` | API auth password |
| `FT_SSH_HOST` | `ssh.host` then extract from Server URL | SSH server address |
| `FT_SSH_USER` | `ubuntu` | SSH user |
| `FT_COMPOSE_DIR` | `/home/ubuntu/freqtrade` | Docker compose directory on server |

```bash
# Example: set everything via env vars
export FT_SERVER_URL=http://43.159.56.168:8080
export FT_SERVER_USERNAME=admin
export FT_SERVER_PASSWORD=admin
export FT_SSH_HOST=43.159.56.168
export FT_SSH_USER=ubuntu
```

### 2. Config File (`config.json`)

```json
{
  "api_server": {
    "username": "admin",
    "password": "admin",
    "listen_ip_address": "0.0.0.0",
    "listen_port": 8080
  },
  "ssh": {
    "host": "43.159.56.168",
    "user": "ubuntu",
    "compose_dir": "/home/ubuntu/freqtrade"
  }
}
```

Use `-c /path/to/config.json` to specify a custom config file.

### 3. Command-Line Flag

```bash
freq -s http://43.159.56.168:8080 dashboard
```

### Auto-Detection

If you don't set any SSH config, the CLI will try to extract the hostname from your API server URL. This works if your API is accessible on the same host you SSH into.

## Commands

### REST API (no SSH needed)

These commands only need the API server URL:

- `freq dashboard` — full status overview
- `freq balance` — wallet balances
- `freq profit` — profit/loss summary
- `freq trades` — trade history
- `freq start / stop` — start/stop the bot
- `freq status` — open trades
- `freq daily` — daily P&L breakdown
- `freq markets limit=10` — real-time market data
- `freq logs` — latest bot logs
- `freq self-test` — run API test suite
- ...and 40+ more

### SSH-Based Commands

These need both API access AND SSH access to the server:

- `freq backtest history` — list backtest results on the server
- `freq backtest history result filename=X` — load a specific backtest result
- `freq entrylog` — view real-time entry logs with gate scores
- `freq backtest run` — automated backtest with mode switching

### Model

- `freq model info` — model config, training status, prediction accuracy, metrics (SSH)
- `freq model retrain` — retrain ML model: stop bot, delete model files, restart (SSH)

### Diagnostic

- `freq doctor` — test all connection paths (API, SSH, Docker)

## Usage Examples

```bash
# Basic dashboard
freq dashboard

# Profit report
freq profit

# Backtest history (needs SSH)
freq backtest history

# Load specific backtest result (needs SSH)
freq backtest history result filename=backtest-result-2025-06-12_06-39-54

# Entry logs with gate scores (needs SSH)
freq entrylog
freq entrylog latest=10                # last 10 entries
freq entrylog pair=BTC/USDT:USDT       # filter by pair

# Paper trading
freq paper status
freq paper topup amount=1000

# All commands with descriptions
freq --show

# Raw JSON output
freq dashboard --json
```

## Quick Start from Another Device

```bash
# 1. Install
pipx install /path/to/ft_client

# 2. Set env vars (or create config.json)
export FT_SERVER_URL=http://43.159.56.168:8080
export FT_SERVER_USERNAME=admin
export FT_SERVER_PASSWORD=admin
export FT_SSH_HOST=43.159.56.168

# 3. Copy SSH key
ssh-copy-id ubuntu@43.159.56.168

# 4. Test connectivity
freq doctor

# 5. Use it
freq dashboard
freq backtest history
```

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Cannot determine SSH host` | No SSH config found | Set `FT_SSH_HOST` env var or `ssh.host` in config |
| `SSH client not found` | OpenSSH not installed | Install OpenSSH client |
| `SSH failed: ...` | Authentication error | Run `ssh-copy-id ubuntu@HOST` |
| `Connection refused` on API | Bot not running / wrong port | Check `docker ps` on server |
| `401 Unauthorized` | Wrong API credentials | Check `FT_SERVER_USERNAME`/`PASSWORD` |

## Building / Development

```bash
cd ft_client
pip install -e .
```
