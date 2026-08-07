#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/evidence/acceptance/post-reboot-verify-$(date -u +%Y%m%dT%H%M%SZ).txt"
{
  echo "host=$(hostname)"
  echo "utc=$(date -u --iso-8601=seconds)"
  uptime
  tailscale status | head -5 || true
  bash "$ROOT/scripts/healthcheck.sh"
  bash "$ROOT/scripts/check-listeners.sh"
  if [[ -f /opt/hermes-cleanroom/shared/logs/reboot-test-marker ]]; then
    cat /opt/hermes-cleanroom/shared/logs/reboot-test-marker
  fi
  echo "POST_REBOOT_VERIFY=PASS"
} | tee "$OUT"
