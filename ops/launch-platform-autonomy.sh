#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_REPO="/home/ubuntu/hermes-ovh-cleanroom"
REPO_SLUG="mdyerapis-coder/hermes-ovh-cleanroom"

if [[ "$REPO" != "$EXPECTED_REPO" ]]; then
  echo "Refusing launch from unexpected repository path: $REPO" >&2
  exit 64
fi

cd "$REPO"
sudo -n true
command -v gh >/dev/null
command -v grok >/dev/null
command -v git >/dev/null
command -v docker >/dev/null
command -v tailscale >/dev/null

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Repository working tree is not clean; refusing platform autonomy launch." >&2
  git status --short >&2
  exit 65
fi

git switch main
git pull --ff-only origin main

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Repository became dirty after main update; refusing launch." >&2
  exit 65
fi

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse origin/main)"
if [[ "$LOCAL_SHA" != "$REMOTE_SHA" ]]; then
  echo "Local main does not exactly match origin/main." >&2
  exit 66
fi

python3 - <<'PY'
import json
from pathlib import Path
p = Path("evidence/control/AUTONOMY_DONE.json")
d = json.loads(p.read_text(encoding="utf-8"))
assert d.get("evidence_verified") is True
assert d.get("state") in {"COMPLETE_CLEANROOM", "COMPLETE_READY_FOR_EXCLUSIVE_CUTOVER"}
assert d.get("verified_commit_sha")
print("CLEANROOM_BASELINE=PASS")
PY

PROTECTION="$(gh api "repos/$REPO_SLUG/branches/main/protection" --jq '{strict:.required_status_checks.strict,checks:[.required_status_checks.checks[].context],enforce_admins:.enforce_admins.enabled,force_pushes:.allow_force_pushes.enabled,deletions:.allow_deletions.enabled}')"
python3 - "$PROTECTION" <<'PY'
import json
import sys
p = json.loads(sys.argv[1])
checks = set(p.get("checks") or [])
assert p.get("strict") is True
assert p.get("enforce_admins") is True
assert p.get("force_pushes") is False
assert p.get("deletions") is False
assert {"BOOTSTRAP-GATE", "AUDIT-GATE"}.issubset(checks)
print("DUAL_GATE_PROTECTION=PASS")
PY

if [[ "$(systemctl is-active tailscaled.service)" != "active" ]]; then
  echo "tailscaled is not active" >&2
  exit 67
fi
if [[ "$(systemctl is-active docker.service)" != "active" ]]; then
  echo "docker is not active" >&2
  exit 67
fi

docker version --format 'Docker server={{.Server.Version}}'

# The completed clean-room controller has its own terminal marker. Stop it so
# there is never a competing repository automation process during this phase.
sudo systemctl stop hermes-grok-controller.service 2>/dev/null || true

if pgrep -af 'grok .*--no-auto-update' >/tmp/hermes-platform-prelaunch-grok.txt; then
  echo "An existing Grok headless process is present; refusing duplicate autonomous controller." >&2
  cat /tmp/hermes-platform-prelaunch-grok.txt >&2
  exit 68
fi

bash "$REPO/ops/install-platform-controller.sh"
sudo systemctl restart hermes-platform-controller.service
sleep 2

if [[ "$(systemctl is-active hermes-platform-controller.service)" != "active" ]]; then
  echo "Platform controller failed to become active." >&2
  sudo journalctl -u hermes-platform-controller.service -n 80 --no-pager >&2 || true
  exit 69
fi

SESSION_ID="$(sudo cat /var/lib/hermes-platform-controller/session-id 2>/dev/null || true)"

echo "========================================="
echo " HERMES PLATFORM AUTONOMY LAUNCHED"
echo "========================================="
echo "host=$(hostname)"
echo "tailscale=$(tailscale ip -4)"
echo "repo=$REPO_SLUG"
echo "main_sha=$LOCAL_SHA"
echo "controller=$(systemctl is-active hermes-platform-controller.service)"
echo "controller_enabled=$(systemctl is-enabled hermes-platform-controller.service)"
echo "session_id=$SESSION_ID"
echo "PLATFORM_AUTONOMY_LAUNCH=PASS"
