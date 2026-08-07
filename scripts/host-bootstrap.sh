#!/usr/bin/env bash
# Idempotent host bootstrap for hermes-ovh-cleanroom only
set -Eeuo pipefail
umask 077

if [[ "$(hostname)" != "hermes-ovh-cleanroom" ]]; then
  echo "BLOCKED: host-bootstrap only runs on hermes-ovh-cleanroom" >&2
  exit 70
fi

log() { echo "[host-bootstrap] $*"; }

# Swap 8G if missing
if ! swapon --show | grep -q .; then
  if [[ ! -f /swapfile ]]; then
    log "creating 8G swapfile"
    sudo fallocate -l 8G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=8192 status=progress
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
  fi
  sudo swapon /swapfile || true
  if ! grep -q '^/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
  fi
fi

# Packages
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  ca-certificates curl git jq rsync unzip python3 python3-venv python3-pip \
  unattended-upgrades fail2ban ufw openssl

# Unattended security updates
sudo dpkg-reconfigure -f noninteractive unattended-upgrades || true

# Accounts
id hermes >/dev/null 2>&1 || sudo useradd --system --create-home --home-dir /home/hermes --shell /usr/sbin/nologin hermes
id deploy >/dev/null 2>&1 || sudo useradd --system --create-home --home-dir /home/deploy --shell /bin/bash deploy

# Release layout
sudo mkdir -p /opt/hermes-cleanroom/{releases,shared/{data,models,backups,logs,secrets-runtime,hermes-home}}
sudo chown -R hermes:hermes /opt/hermes-cleanroom/shared/data /opt/hermes-cleanroom/shared/hermes-home || true
sudo chown root:ubuntu /opt/hermes-cleanroom/shared/backups || true
sudo chmod 775 /opt/hermes-cleanroom/shared/backups || true

# Backup encryption key
KEY=/opt/hermes-cleanroom/shared/secrets-runtime/BACKUP_ENCRYPTION_KEY
if [[ ! -f "$KEY" ]]; then
  openssl rand -base64 32 | sudo tee "$KEY" >/dev/null
fi
sudo chown root:ubuntu "$KEY"
sudo chmod 640 "$KEY"

# Firewall: allow SSH + Tailscale, default deny incoming (careful order)
if command -v ufw >/dev/null; then
  sudo ufw default deny incoming || true
  sudo ufw default allow outgoing || true
  sudo ufw allow OpenSSH || sudo ufw allow 22/tcp || true
  # Tailscale interface
  sudo ufw allow in on tailscale0 || true
  echo y | sudo ufw enable || true
  sudo ufw status verbose | tee /tmp/ufw-status.txt || true
fi

# Journald persistence
sudo mkdir -p /var/log/journal
sudo systemd-tmpfiles --create --prefix /var/log/journal || true

log "host-bootstrap complete"
