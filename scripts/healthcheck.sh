#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0
echo "=== hermes-ovh-cleanroom healthcheck ==="
echo "host=$(hostname)"
echo "time_utc=$(date -u --iso-8601=seconds)"

if [[ "$(hostname)" != "hermes-ovh-cleanroom" ]]; then
  echo "WARN: hostname is not hermes-ovh-cleanroom"
fi

for f in config/services.yaml config/ports.yaml config/secret-contract.yaml VERSION; do
  if [[ ! -f "$ROOT/$f" ]]; then
    echo "FAIL missing $f"
    FAIL=1
  else
    echo "OK $f"
  fi
done

if command -v tailscale >/dev/null; then
  if tailscale status >/dev/null 2>&1; then
    echo "OK tailscale"
  else
    echo "FAIL tailscale"
    FAIL=1
  fi
fi

echo "HADA_RUNTIME=NOT_DEPLOYED"
echo "TELEGRAM_STATE=READY_FOR_EXCLUSIVE_CUTOVER"

if python3 "$ROOT/scripts/ci/validate-config.py" >/dev/null; then
  echo "OK config-contract"
else
  echo "FAIL config-contract"
  FAIL=1
fi

if [[ -f /opt/hermes-cleanroom/shared/src/hermes-agent/.git/HEAD ]]; then
  echo "OK hermes-src-present"
else
  echo "PENDING hermes-src-not-installed"
fi

if [[ -x /opt/hermes-cleanroom/shared/venvs/hermes/bin/python ]]; then
  echo "OK hermes-venv"
else
  echo "PENDING hermes-venv"
fi

if bash "$ROOT/scripts/check-listeners.sh"; then
  echo "OK listeners"
else
  echo "FAIL listeners"
  FAIL=1
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "HEALTH=FAIL"
  exit 1
fi
echo "HEALTH=PASS"
