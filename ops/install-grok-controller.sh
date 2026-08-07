#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_REPO="/home/ubuntu/hermes-ovh-cleanroom"

if [[ "$REPO" != "$EXPECTED_REPO" ]]; then
  echo "Refusing install from unexpected repository path: $REPO" >&2
  echo "Expected: $EXPECTED_REPO" >&2
  exit 64
fi

cd "$REPO"

for path in \
  AGENTS.md \
  runbook/RUNBOOK-MANIFEST.md \
  policy/anti-hallucination-guardrails.md \
  runbook/part-99-post-completion-evolution-policy.md \
  ops/AUTONOMY_PROMPT.txt \
  ops/grok-controller.sh \
  systemd/hermes-grok-controller.service; do
  test -s "$path" || {
    echo "Required controller input missing: $path" >&2
    exit 65
  }
done

command -v grok >/dev/null
command -v gh >/dev/null
command -v docker >/dev/null
command -v tailscale >/dev/null

sudo -n true

sudo install -d -m 0755 /usr/local/libexec
sudo install -m 0755 "$REPO/ops/grok-controller.sh" /usr/local/libexec/hermes-grok-controller
sudo install -m 0644 "$REPO/systemd/hermes-grok-controller.service" /etc/systemd/system/hermes-grok-controller.service

sudo systemctl daemon-reload
sudo systemctl enable hermes-grok-controller.service

sudo systemd-analyze verify /etc/systemd/system/hermes-grok-controller.service

echo "=== CONTROLLER INSTALL VERIFIED ==="
echo "repo=$REPO"
echo "grok=$(grok version 2>/dev/null || grok --version 2>/dev/null || true)"
echo "github=$(gh api user --jq .login)"
echo "tailscale=$(tailscale ip -4)"
echo "docker=$(docker version --format '{{.Server.Version}}')"
echo "unit_enabled=$(systemctl is-enabled hermes-grok-controller.service)"
echo

echo "Controller is installed but NOT started by this installer."
echo "Start only after GitHub bootstrap governance has been enabled and verified."
