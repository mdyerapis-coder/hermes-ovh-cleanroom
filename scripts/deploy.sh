#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHA="${1:-$(git -C "$ROOT" rev-parse HEAD)}"
TARGET_HOST="${HERMES_DEPLOY_HOST:-hermes-ovh-cleanroom}"
RELEASE_ROOT="${HERMES_RELEASE_ROOT:-/opt/hermes-cleanroom}"

echo "deploy: verifying target identity"
HOSTNAME_NOW="$(hostname)"
if [[ "$HOSTNAME_NOW" != "hermes-ovh-cleanroom" && "$HOSTNAME_NOW" != "$TARGET_HOST" ]]; then
  echo "BLOCKED_TARGET_IDENTITY_UNVERIFIED: hostname=$HOSTNAME_NOW expected=$TARGET_HOST" >&2
  exit 70
fi

# Additional identity signals
if command -v tailscale >/dev/null; then
  TS_IP="$(tailscale ip -4 2>/dev/null || true)"
  echo "tailscale_ipv4=${TS_IP:-unknown}"
fi

sudo mkdir -p "$RELEASE_ROOT/releases/$SHA" "$RELEASE_ROOT/shared"/{data,models,backups,logs,secrets-runtime}
# Stage release tree from repo (configs/scripts only; no secrets)
sudo rsync -a --delete \
  --exclude '.git' \
  --exclude 'evidence/backups' \
  --exclude 'evidence/control/AUTONOMY_DONE.json' \
  "$ROOT/" "$RELEASE_ROOT/releases/$SHA/"

# Atomic switch
if [[ -L "$RELEASE_ROOT/current" ]]; then
  PREV="$(readlink -f "$RELEASE_ROOT/current" || true)"
  if [[ -n "$PREV" ]]; then
    sudo ln -sfn "$PREV" "$RELEASE_ROOT/previous"
  fi
fi
sudo ln -sfn "$RELEASE_ROOT/releases/$SHA" "$RELEASE_ROOT/current"
echo "deployed_sha=$SHA"
echo "current=$(readlink -f "$RELEASE_ROOT/current")"

# Post-stage health of scripts
"$RELEASE_ROOT/current/scripts/healthcheck.sh" || {
  echo "healthcheck failed; attempting rollback" >&2
  "$ROOT/scripts/rollback.sh" || true
  exit 1
}

mkdir -p "$ROOT/evidence/deploy"
cat >"$ROOT/evidence/deploy/release-$SHA.json" <<JSON
{
  "sha": "$SHA",
  "host": "$HOSTNAME_NOW",
  "timestamp_utc": "$(date -u --iso-8601=seconds)",
  "path": "$RELEASE_ROOT/releases/$SHA",
  "status": "deployed_candidate"
}
JSON
echo "DEPLOY_OK=$SHA"
