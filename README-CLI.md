# Freqtrade CLI — Dokumentasi Lengkap

CLI client untuk mengontrol Freqtrade bot via REST API.
Installasi: `pipx install git+https://github.com/malikstarvo/freqcustom.git#subdirectory=ft_client`

---

## Daftar Isi

- [Quick Start](#quick-start)
- [Semua Command](#semua-command)
- [Namespace Aliases](#namespace-aliases)
- [Backtest Workflow](#backtest-workflow)
- [Live Trading Setup](#live-trading-setup)
- [Raw JSON Output](#raw-json-output)

---

## Quick Start

```bash
# Set server URL (default: http://127.0.0.1:8080)
export FT_SERVER_URL=http://43.159.56.168:8080
export FT_SERVER_USERNAME=admin
export FT_SERVER_PASSWORD=admin

# Cek koneksi
freq ping

# Dashboard lengkap
freq dashboard

# Lihat profit
freq profit

# Lihat balance
freq balance

# Lihat market real-time
freq markets limit=10

# Start/stop bot
freq start
freq stop

# Self-test semua endpoint
freq self test
```

Atau gunakan flag `--server`:

```bash
freq --server http://43.159.56.168:8080 ping
```

---

## Semua Command

### Bot Control

| Command | Deskripsi | Contoh |
|---|---|---|
| `start` | Start bot (running → stopped) | `freq start` |
| `stop` | Stop bot | `freq stop` |
| `stopbuy` | Stop buy aja, sell tetap jalan | `freq stopbuy` |
| `reload_config` | Reload config dari disk | `freq reload_config` |

### Dashboard

| Command | Deskripsi | Contoh |
|---|---|---|
| `dashboard` | Overview lengkap: state, P&L, balance, open trades, paper equity, health | `freq dashboard` |

### Account

| Command | Deskripsi | Contoh |
|---|---|---|
| `balance` | Wallet balances (free, used, est_stake) | `freq balance` |
| `profit` | Profit/loss summary dengan risk metrics (Sharpe, Sortino, Calmar, dll) | `freq profit` |
| `daily [days]` | Profit per hari | `freq daily 7` |
| `weekly [weeks]` | Profit per minggu | `freq weekly 4` |
| `monthly [months]` | Profit per bulan | `freq monthly 6` |
| `count` | Jumlah open trades vs max | `freq count` |
| `stats` | Report durasi & sell-reasons | `freq stats` |

### Trades

| Command | Deskripsi | Contoh |
|---|---|---|
| `status` | Open trades saat ini | `freq status` |
| `trades [limit=N] [offset=N]` | Riwayat trades (max 500) | `freq trades limit=10` |
| `trade ID` | Detail satu trade spesifik | `freq trade 123` |
| `performance` | Performa per pair | `freq performance` |
| `entries [pair]` | Performa berdasarkan entry tag | `freq entries BTC/USDT` |
| `exits [pair]` | Performa berdasarkan exit reason | `freq exits` |
| `mix_tags [pair]` | Performa entry tag + exit reason | `freq mix_tags` |

### Trading (Manual)

| Command | Deskripsi | Contoh |
|---|---|---|
| `forceenter pair=X side=long\|short [price=N] [leverage=N] [stake_amount=N]` | Force entry trade | `freq forceenter pair=BTC/USDT:USDT side=long leverage=2` |
| `forceexit tradeid=N [ordertype=market\|limit] [amount=N]` | Force exit trade | `freq forceexit tradeid=123` |
| `forcebuy pair=X [price=N]` | Force buy (legacy) | `freq forcebuy pair=BTC/USDT` |
| `delete_trade ID` | Hapus trade dari database | `freq delete_trade 123` |
| `cancel_open_order ID` | Cancel open order untuk trade | `freq cancel_open_order 123` |

### Locks

| Command | Deskripsi | Contoh |
|---|---|---|
| `locks` | Lihat semua lock aktif | `freq locks` |
| `lock_add pair=X until="YYYY-MM-DD HH:MM:SSZ" [side=*\|long\|short] [reason=...]` | Lock pair | `freq lock_add pair=BTC/USDT until="2026-07-01 00:00:00Z" side=long` |
| `delete_lock ID` | Hapus/unlock | `freq delete_lock 42` |

### Paper Trading

| Command | Deskripsi | Contoh |
|---|---|---|
| `paper status` | Status paper engine: equity, balance, P&L, posisi | `freq paper status` |
| `paper topup amount=N` | Tambah modal paper trading | `freq paper topup amount=5000` |
| `paper trades limit=N` | Riwayat trade paper | `freq paper trades limit=20` |
| `paper account limit=N` | Snapshot equity paper (time-series) | `freq paper account limit=30` |

### Backtest

| Command | Deskripsi | Contoh |
|---|---|---|
| `backtest run [strategy=X] timeframe=X timerange=X [max_open_trades=N] [stake_amount=N]` | **AUTO** — stop trade → webserver → run → hasil → restart trade | `freq backtest run timeframe=15m timerange=20250601-20250610` |
| `backtest start [strategy=X] [timeframe=X] [timerange=X] [max_open_trades=N] [stake_amount=N] [enable_protections=true]` | Mulai backtest (butuh webserver mode manual) | `freq backtest start timeframe=15m timerange=20250601-20250610` |
| `backtest status` | Cek progress backtest | `freq backtest status` |
| `backtest history` | Lihat riwayat hasil backtest | `freq backtest history` |
| `backtest history result file=X strategy=X` | Load detail hasil backtest | `freq backtest history result file=backtest-result-2025.json strategy=MultiAgentStrategy` |
| `backtest history delete file=X` | Hapus file hasil backtest | `freq backtest history delete file=backtest-result-old.json` |
| `backtest abort` | Batalkan backtest yang sedang jalan | `freq backtest abort` |
| `backtest delete` | Reset/hapus backtest yang sedang jalan | `freq backtest delete` |

### Strategy

| Command | Deskripsi | Contoh |
|---|---|---|
| `strategies` | List semua strategy yang tersedia | `freq strategies` |
| `strategy [name]` | Detail strategy (timeframe, stoploss, trailing, dll) | `freq strategy MultiAgentStrategy` |
| `plot_config` | Konfigurasi plot dari strategy | `freq plot_config` |

### Model (FreqAI / ML)

| Command | Deskripsi | Contoh |
|---|---|---|
| `model info` | Info model ML: status FreqAI, identifier, train period, PCA, available models | `freq model info` |

### Pairs

| Command | Deskripsi | Contoh |
|---|---|---|
| `whitelist` | Lihat whitelist aktif | `freq whitelist` |
| `blacklist [add=PAIR1 PAIR2]` | Lihat / tambah blacklist | `freq blacklist add=BNB/USDT BTC/USDT` |
| `pair candles pair=X timeframe=1h [limit=N]` | Candlestick real-time dari exchange | `freq pair candles pair=BTC/USDT:USDT timeframe=15m limit=100` |
| `pair history pair=X timeframe=1h strategy=X [timerange=X]` | Dataframe historis ter-analisa | `freq pair history pair=BTC/USDT timeframe=1h strategy=MultiAgentStrategy timerange=20250601-` |
| `available_pairs [timeframe=1h] [stake_currency=USDT]` | Pair yang tersedia untuk backtest | `freq available_pairs timeframe=1h` |
| `pairlists_available` | List semua pairlist provider | `freq pairlists_available` |
| `markets limit=N` | Data market real-time (price, 24h change, high/low, volume) dari exchange | `freq markets limit=10` |
| `data list` | Ringkasan semua data yang sudah di-download | `freq data list` |

### Config

| Command | Deskripsi | Contoh |
|---|---|---|
| `show_config` | Lihat konfigurasi aktif bot | `freq show_config` |
| `config live pair=X [timeframe=15m] [stake=100] [leverage=1] [exchange=bybit]` | Generate file config live trading | `freq config live pair=BTC/USDT:USDT stake=50 timeframe=1h` |

### System

| Command | Deskripsi | Contoh |
|---|---|---|
| `ping` | Cek koneksi ke bot | `freq ping` |
| `version` | Versi bot | `freq version` |
| `sysinfo` | Info sistem: CPU, RAM, load average | `freq sysinfo` |
| `health` | Bot heartbeat: startup time, last process | `freq health` |
| `logs [limit=N]` | Log bot terbaru | `freq logs limit=100` |
| `self test` | Test suite komprehensif semua endpoint | `freq self test` |

### Custom Data

| Command | Deskripsi | Contoh |
|---|---|---|
| `list_open_trades_custom_data [key=X]` | Custom data dari open trades | `freq list_open_trades_custom_data` |
| `list_custom_data trade_id=N [key=X]` | Custom data untuk trade spesifik | `freq list_custom_data trade_id=123` |

---

## Namespace Aliases

Command bisa dipanggil dengan 2 cara:

| Namespace | Langsung | Contoh |
|---|---|---|
| `paper status` | `paper_status` | `freq paper status` |
| `paper topup amount=N` | `paper_topup amount=N` | `freq paper topup amount=5000` |
| `paper trades limit=N` | `paper_trades limit=N` | `freq paper trades limit=10` |
| `paper account limit=N` | `paper_account limit=N` | `freq paper account limit=20` |
| `backtest run` | `backtest_run` **AUTO** (SSH mode switch) | `freq backtest run timeframe=15m timerange=20250601-20250610` |
| `backtest start [key=val]` | `backtest_start [key=val]` | `freq backtest start timeframe=15m` |
| `backtest status` | `backtest_status` | `freq backtest status` |
| `backtest history` | `backtest_history` | `freq backtest history` |
| `backtest abort` | `backtest_abort` | `freq backtest abort` |
| `backtest delete` | `backtest_delete` | `freq backtest delete` |
| `backtest history result file=X strategy=Y` | `backtest_history_result` | `freq backtest history result file=backtest.json strategy=Multi` |
| `backtest history delete file=X` | `backtest_history_delete` | `freq backtest history delete file=backtest.json` |
| `pair candles` | `pair_candles` | `freq pair candles pair=BTC/USDT timeframe=15m` |
| `pair history` | `pair_history` | `freq pair history pair=BTC/USDT timeframe=1h strategy=MultiAgentStrategy` |
| `data list` | `data_list` | `freq data list` |
| `model info` | `model_info` | `freq model info` |
| `self test` | `self_test` | `freq self test` |
| `config live` | `config_live` | `freq config live pair=BTC/USDT:USDT stake=100` |
| `config show` | `show_config` | `freq config show` |

### Reverse alias khusus

Beberapa command mendukung **reverse alias** — subcommand ditulis sebelum command:

| Yang kamu ketik | Sama dengan | Contoh |
|---|---|---|
| `freq config show` | `freq show_config` | `freq config show` |
| `freq self test` | `freq self_test` | `freq self test` |

Juga support hyphens: `freq self-test` → otomatis jadi `self_test`.

---

## Backtest Workflow

### Cara Cepat (Otomatis)

```bash
freq backtest run timeframe=15m timerange=20250601-20250610
```

Ini akan:
1. Stop trade bot via API
2. SSH ke server → restart container di webserver mode
3. Start backtest via API
4. Poll progress sampai selesai
5. SSH ke server → restart container di trade mode
6. Start trade bot via API
7. Tampilkan hasil

### Manual

Backtest cuma bisa jalan di **webserver mode**, bukan trade mode.

```bash
# 1. Stop trade bot dulu
freq stop

# 2. Restart di webserver mode (via SSH ke server)
ssh ubuntu@43.159.56.168
cd /home/ubuntu/freqtrade
docker compose down freqtrade
docker compose run --rm -p 8080:8080 freqtrade webserver -c /freqtrade/config.json

# 3. Jalankan backtest (di terminal lokal)
freq backtest start strategy=MultiAgentStrategy timeframe=15m timerange=20250601-20250610

# 4. Cek progress
freq backtest status

# 5. Lihat history hasil
freq backtest history

# 6. Load detail hasil spesifik
freq backtest history result file=backtest-result-20250601_20250610.json strategy=MultiAgentStrategy

# 7. Kembali ke trade mode
docker compose up -d freqtrade
freq start
```

---

## Live Trading Setup

Generate file config untuk live trading:

```bash
freq config live pair=BTC/USDT:USDT timeframe=15m stake=100 leverage=1
```

Output:
```
╔══════════════════════════════════╗
║    Live Trading Config Setup      ║
║  ⚠ REAL MONEY WILL BE TRADED ⚠   ║
╚══════════════════════════════════╝
  Pair        BTC/USDT:USDT
  Timeframe   15m
  Stake       100
  Leverage    1x
  Exchange    bybit

  ══ Next Steps ════════════
  1. Edit config.live.json — tambah API keys exchange
  2. cp config.live.json config.json
  3. docker compose restart freqtrade
  4. freq start
```

---

## Raw JSON Output

Semua command bisa output JSON mentah untuk scripting/CI:

```bash
freq profit --json
freq balance --json
freq self test --json
freq trades limit=50 --json
```

---

## Exit Codes

| Code | Arti |
|---|---|
| `0` | Sukses |
| `1` | Error (unknown command, API error, config not found) |

---

## Config SSH untuk `backtest run`

`freq backtest run` butuh SSH akses ke server untuk switch mode trade↔webserver.

Konfigurasi (prioritas: env var > config.json > default):

| Setting | Env Var | config.json | Default |
|---|---|---|---|
| SSH Host | `FT_SSH_HOST` | `ssh.host` | (dari server URL) |
| SSH User | `FT_SSH_USER` | `ssh.user` | `ubuntu` |
| Compose Dir | `FT_COMPOSE_DIR` | `ssh.compose_dir` | `/home/ubuntu/freqtrade` |

Contoh di `config.json`:
```json
{
  "ssh": {
    "host": "43.159.56.168",
    "user": "ubuntu",
    "compose_dir": "/home/ubuntu/freqtrade"
  }
}
```

## Catatan Penting

1. **Bot harus running** — semua command (kecuali `config live`) butuh API server aktif
2. **Backtest perlu webserver mode** — trade mode gak support backtest API
3. **Config show** — pake `freq show_config` atau `freq config show` (keduanya bisa)
4. **Self-test** — bisa pake `freq self test`, `freq self-test`, atau `freq self_test`
5. **Paper trading** — terpisah dari mode dry-run; perlu `freqai` atau paper engine terpisah
