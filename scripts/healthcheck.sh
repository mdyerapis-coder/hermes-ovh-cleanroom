#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0
echo "=== hermes-ovh-cleanroom healthcheck ==="
echo "host=$(hostname)"
echo "time_utc=$(date -u --iso-8601=seconds)"

# Identity
if [[ "$(hostname)" != "hermes-ovh-cleanroom" ]]; then
  echo "WARN: hostname is not hermes-ovh-cleanroom"
fi

# Required files
for f in config/services.yaml config/ports.yaml config/secret-contract.yaml VERSION; do
  if [[ ! -f "$ROOT/$f" ]]; then
    echo "FAIL missing $f"
    FAIL=1
  else
    echo "OK $f"
  fi
done

# Tailscale if present
if command -v tailscale >/dev/null; then
  if tailscale status >/dev/null 2>&1; then
    echo "OK tailscale"
  else
    echo "FAIL tailscale"
    FAIL=1
  fi
fi

# HADA honesty
echo "HADA_RUNTIME=NOT_DEPLOYED"

# Telegram honesty
echo "TELEGRAM_STATE=READY_FOR_EXCLUSIVE_CUTOVER"

# Config validate
if python3 "$ROOT/scripts/ci/validate-config.py" >/dev/null; then
  echo "OK config-contract"
else
  echo "FAIL config-contract"
  FAIL=1
fi

if [[ "$FAIL" -ne 0 ]]; then
  exit 1
fi
echo "HEALTH=PASS"
