#!/usr/bin/env bash
# Install Hermes Agent runtime into clean-room shared path from pinned tag.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${HERMES_AGENT_TAG:-v2026.8.3}"
SRC_DIR="/opt/hermes-cleanroom/shared/src/hermes-agent"
VENV_DIR="/opt/hermes-cleanroom/shared/venvs/hermes"
HOME_DIR="/opt/hermes-cleanroom/shared/hermes-home"
REPO_URL="${HERMES_AGENT_REPO:-https://github.com/mdyerapis-coder/hermes-agent.git}"

if [[ "$(hostname)" != "hermes-ovh-cleanroom" && "${HERMES_ALLOW_NON_CLEANROOM:-}" != "1" ]]; then
  echo "install-hermes-runtime restricted to clean-room host" >&2
  exit 70
fi

sudo mkdir -p "$(dirname "$SRC_DIR")" "$(dirname "$VENV_DIR")" "$HOME_DIR"
sudo chown -R ubuntu:ubuntu /opt/hermes-cleanroom/shared/src /opt/hermes-cleanroom/shared/venvs 2>/dev/null || true
sudo chown -R hermes:hermes "$HOME_DIR" 2>/dev/null || sudo chown -R ubuntu:ubuntu "$HOME_DIR"

if [[ ! -d "$SRC_DIR/.git" ]]; then
  git clone --depth 1 --branch "$TAG" "$REPO_URL" "$SRC_DIR" || \
    git clone --depth 1 "$REPO_URL" "$SRC_DIR"
  # if tag clone failed due to branch name, fetch tags
  if ! git -C "$SRC_DIR" describe --tags --exact-match 2>/dev/null; then
    git -C "$SRC_DIR" fetch --tags --depth 1 origin "$TAG" 2>/dev/null || true
    git -C "$SRC_DIR" checkout "$TAG" 2>/dev/null || true
  fi
else
  git -C "$SRC_DIR" fetch --tags --depth 1 origin "$TAG" 2>/dev/null || git -C "$SRC_DIR" fetch --tags
  git -C "$SRC_DIR" checkout "$TAG" 2>/dev/null || true
fi

# Install uv if needed
if ! command -v uv >/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh
  # basic integrity: non-empty script with expected strings
  grep -q 'uv' /tmp/uv-install.sh
  sh /tmp/uv-install.sh
  export PATH="$HOME/.local/bin:$PATH"
fi
export PATH="$HOME/.local/bin:$PATH"

uv venv "$VENV_DIR" --python 3.12 || uv venv "$VENV_DIR" --python 3.11
# Install package (prefer editable all extras when possible)
set +e
uv pip install --python "$VENV_DIR/bin/python" -e "$SRC_DIR"
RC=$?
set -e
if [[ $RC -ne 0 ]]; then
  uv pip install --python "$VENV_DIR/bin/python" "$SRC_DIR"
fi

# Minimal hermes home config — no production tokens
sudo mkdir -p "$HOME_DIR"
sudo tee "$HOME_DIR/cleanroom.env" >/dev/null <<ENV
HERMES_ENV=cleanroom
HERMES_HOME=$HOME_DIR
# Telegram polling intentionally disabled on clean-room until exclusive cutover
HERMES_TELEGRAM_POLLING=0
HERMES_GATEWAY_POLLING=0
ENV
sudo chown -R hermes:hermes "$HOME_DIR" || true

# Record install evidence
mkdir -p "$ROOT/evidence/deploy"
{
  echo "tag=$TAG"
  echo "src=$SRC_DIR"
  echo "venv=$VENV_DIR"
  echo "sha=$(git -C "$SRC_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "installed_utc=$(date -u --iso-8601=seconds)"
  "$VENV_DIR/bin/python" -c 'import sys; print(sys.version)' || true
} | tee "$ROOT/evidence/deploy/hermes-runtime-install.txt"

echo "HERMES_RUNTIME_INSTALL=OK"
