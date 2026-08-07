#!/usr/bin/env bash
# Reboot clean-room host and verify recovery. Must only target hermes-ovh-cleanroom.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(hostname)" != "hermes-ovh-cleanroom" ]]; then
  echo "BLOCKED: reboot-test only on clean-room" >&2
  exit 70
fi
MARKER=/opt/hermes-cleanroom/shared/logs/reboot-test-marker
mkdir -p "$(dirname "$MARKER")"
echo "pre_reboot_utc=$(date -u --iso-8601=seconds)" | tee "$MARKER"
echo "pre_release=$(readlink -f /opt/hermes-cleanroom/current 2>/dev/null || true)" | tee -a "$MARKER"
bash "$ROOT/scripts/healthcheck.sh" | tee /opt/hermes-cleanroom/shared/logs/pre-reboot-health.txt
# Schedule reboot after 1 minute to allow marker flush
if [[ "${HERMES_REBOOT_EXECUTE:-}" == "1" ]]; then
  sudo shutdown -r +0 "hermes clean-room reboot test"
else
  echo "REBOOT_DRY_RUN=1 set HERMES_REBOOT_EXECUTE=1 to actually reboot"
fi
