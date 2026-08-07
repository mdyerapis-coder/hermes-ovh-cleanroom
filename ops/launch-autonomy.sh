#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="/home/ubuntu/hermes-ovh-cleanroom"
cd "$REPO"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Refusing launch with a dirty bootstrap checkout:" >&2
  git status --short >&2
  exit 64
fi

git switch main
git pull --ff-only origin main

bash ./ops/bootstrap-github-governance.sh
bash ./ops/install-grok-controller.sh

sudo systemctl start hermes-grok-controller.service
sleep 3

if ! sudo systemctl is-active --quiet hermes-grok-controller.service; then
  echo "Autonomous controller failed to remain active." >&2
  sudo systemctl status hermes-grok-controller.service --no-pager -l >&2 || true
  sudo journalctl -u hermes-grok-controller.service -n 100 --no-pager >&2 || true
  exit 70
fi

echo
echo "========================================="
echo " HERMES AUTONOMY LAUNCHED"
echo "========================================="
echo "host=$(hostname)"
echo "tailscale=$(tailscale ip -4)"
echo "repo=mdyerapis-coder/hermes-ovh-cleanroom"
echo "controller=$(systemctl is-active hermes-grok-controller.service)"
echo "controller_enabled=$(systemctl is-enabled hermes-grok-controller.service)"
echo "session_id=$(sudo cat /var/lib/hermes-grok-controller/session-id 2>/dev/null || echo pending)"
echo
echo "You may disconnect SSH after this PASS block."
echo "Monitor later with:"
echo "  sudo systemctl status hermes-grok-controller --no-pager"
echo "  sudo journalctl -u hermes-grok-controller -f"
echo "  gh pr list --repo mdyerapis-coder/hermes-ovh-cleanroom"
echo
echo "AUTONOMY_LAUNCH=PASS"
