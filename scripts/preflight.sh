#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/evidence/host/preflight.txt}"
mkdir -p "$(dirname "$OUT")"
{
  echo "=== preflight $(date -u --iso-8601=seconds) ==="
  hostnamectl || true
  cat /etc/os-release
  uname -a
  nproc
  free -h
  df -hT
  ip -brief address || true
  timedatectl || true
  docker --version || true
  docker compose version || true
  tailscale status || true
  ss -lntup || true
} >"$OUT" 2>&1
echo "preflight written: $OUT"
