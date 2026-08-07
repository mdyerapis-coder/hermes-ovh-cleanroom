#!/usr/bin/env bash
set -Eeuo pipefail
RELEASE_ROOT="${HERMES_RELEASE_ROOT:-/opt/hermes-cleanroom}"
if [[ ! -L "$RELEASE_ROOT/previous" ]]; then
  echo "No previous release to roll back to" >&2
  exit 1
fi
PREV="$(readlink -f "$RELEASE_ROOT/previous")"
CUR="$(readlink -f "$RELEASE_ROOT/current" || true)"
sudo ln -sfn "$PREV" "$RELEASE_ROOT/current"
if [[ -n "$CUR" ]]; then
  sudo ln -sfn "$CUR" "$RELEASE_ROOT/previous"
fi
echo "rolled_back_to=$PREV"
if [[ -x "$RELEASE_ROOT/current/scripts/healthcheck.sh" ]]; then
  "$RELEASE_ROOT/current/scripts/healthcheck.sh"
fi
