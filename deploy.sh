#!/bin/bash
set -euo pipefail

# =========================================================
# deploy.sh — Deploy Freqtrade Web Dashboard ke VPS
# =========================================================
# Cara pakai:
#   1. Copy .env.deploy.example → .env.deploy, isi VPS_HOST
#   2. Jalankan: bash deploy.sh
#
# Atau langsung: VPS_HOST=user@1.2.3.4 bash deploy.sh
# =========================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Config ──────────────────────────────────────────────
# Bisa di-override lewat .env.deploy atau environment variable
VPS_HOST="${VPS_HOST:-}"
VPS_PATH="${VPS_PATH:-/home/freqtrade/freqtrade}"
VPS_WEB_DIR="${VPS_WEB_DIR:-$VPS_PATH/web/out}"

# ── Source .env.deploy kalau ada ────────────────────────
if [ -f "$SCRIPT_DIR/.env.deploy" ]; then
  echo "Loading .env.deploy..."
  set -a
  source "$SCRIPT_DIR/.env.deploy"
  set +a
fi

# ── Validasi ────────────────────────────────────────────
if [ -z "$VPS_HOST" ]; then
  echo "ERROR: VPS_HOST belum di-set."
  echo ""
  echo "Caranya:"
  echo "  1. cp .env.deploy.example .env.deploy"
  echo "  2. Edit .env.deploy, isi VPS_HOST=user@ip-vps-anda"
  echo "  3. Jalankan ulang: bash deploy.sh"
  echo ""
  echo "Atau langsung: VPS_HOST=user@1.2.3.4 bash deploy.sh"
  exit 1
fi

WEB_DIR="$SCRIPT_DIR/web"

# ── Build ───────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building web frontend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$WEB_DIR"

if ! npm run build; then
  echo ""
  echo "ERROR: Build gagal. Cek error di atas."
  exit 1
fi

cd "$SCRIPT_DIR"

# ── Deploy ──────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Deploying ke $VPS_HOST:$VPS_WEB_DIR ..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Hapus file lama dulu biar ga numpuk cache
ssh "$VPS_HOST" "rm -rf $VPS_WEB_DIR/*"

# Upload hasil build
scp -r "$WEB_DIR/out/"* "$VPS_HOST:$VPS_WEB_DIR/"

echo ""
echo "  File terkirim. Restarting container..."

# Restart container web
ssh "$VPS_HOST" "cd $VPS_PATH && docker compose restart web"

# ── Verifikasi ──────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Memeriksa status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh "$VPS_HOST" "cd $VPS_PATH && docker compose ps web"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Deploy selesai."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
