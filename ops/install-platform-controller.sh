#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_REPO="/home/ubuntu/hermes-ovh-cleanroom"
SERVICE_PATH="/home/ubuntu/.grok/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

if [[ "$REPO" != "$EXPECTED_REPO" ]]; then
  echo "Refusing install from unexpected repository path: $REPO" >&2
  echo "Expected: $EXPECTED_REPO" >&2
  exit 64
fi

cd "$REPO"

for path in \
  AGENTS.md \
  runbook/RUNBOOK-MANIFEST.md \
  runbook/part-100-hps-hes-platform-completion.md \
  policy/anti-hallucination-guardrails.md \
  runbook/part-99-post-completion-evolution-policy.md \
  evidence/control/AUTONOMY_DONE.json \
  ops/PLATFORM_AUTONOMY_PROMPT.txt \
  ops/platform-controller.sh \
  systemd/hermes-platform-controller.service; do
  test -s "$path" || {
    echo "Required platform controller input missing: $path" >&2
    exit 65
  }
done

command -v grok >/dev/null
command -v gh >/dev/null
command -v docker >/dev/null
command -v tailscale >/dev/null
sudo -n true

sudo -u ubuntu env \
  HOME=/home/ubuntu \
  GROK_HOME=/home/ubuntu/.grok \
  PATH="$SERVICE_PATH" \
  bash -c 'command -v grok >/dev/null'

grep -Fq 'Environment=PATH=/home/ubuntu/.grok/bin:' systemd/hermes-platform-controller.service

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

sudo install -d -m 0755 /usr/local/libexec
sudo install -m 0755 "$REPO/ops/platform-controller.sh" /usr/local/libexec/hermes-platform-controller
sudo install -m 0644 "$REPO/systemd/hermes-platform-controller.service" /etc/systemd/system/hermes-platform-controller.service

sudo systemctl daemon-reload
sudo systemctl enable hermes-platform-controller.service
sudo systemd-analyze verify /etc/systemd/system/hermes-platform-controller.service
systemctl show hermes-platform-controller.service -p Environment --value | grep -Fq '/home/ubuntu/.grok/bin:'

echo "=== PLATFORM CONTROLLER INSTALL VERIFIED ==="
echo "repo=$REPO"
echo "grok=$(grok version 2>/dev/null || grok --version 2>/dev/null || true)"
echo "service_grok=$(sudo -u ubuntu env HOME=/home/ubuntu GROK_HOME=/home/ubuntu/.grok PATH="$SERVICE_PATH" command -v grok)"
echo "github=$(gh api user --jq .login)"
echo "tailscale=$(tailscale ip -4)"
echo "docker=$(docker version --format '{{.Server.Version}}')"
echo "unit_enabled=$(systemctl is-enabled hermes-platform-controller.service)"
echo "PLATFORM_CONTROLLER_INSTALL=PASS"
echo
echo "Controller installed and enabled but not started by this installer."
