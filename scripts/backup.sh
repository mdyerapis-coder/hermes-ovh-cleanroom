#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${HERMES_BACKUP_DIR:-$ROOT/evidence/backups}/backup-$STAMP"
mkdir -p "$DEST"
# Backup configs, evidence (non-secret), release markers — never secret values
tar -C "$ROOT" -czf "$DEST/config-and-state.tgz" \
  config \
  VERSION \
  evidence/discovery \
  evidence/claims \
  evidence/faults/fault-ledger.jsonl \
  2>/dev/null || tar -C "$ROOT" -czf "$DEST/config-and-state.tgz" config VERSION
# Optional encryption if key material path set (file content never logged)
if [[ -n "${BACKUP_ENCRYPTION_KEY_FILE:-}" && -f "${BACKUP_ENCRYPTION_KEY_FILE}" ]]; then
  openssl enc -aes-256-cbc -pbkdf2 -salt \
    -in "$DEST/config-and-state.tgz" \
    -out "$DEST/config-and-state.tgz.enc" \
    -pass "file:${BACKUP_ENCRYPTION_KEY_FILE}"
  rm -f "$DEST/config-and-state.tgz"
  echo "encrypted_backup=$DEST/config-and-state.tgz.enc"
else
  echo "plaintext_local_backup=$DEST/config-and-state.tgz"
  echo "note=BACKUP_ENCRYPTION_KEY_FILE not set; local unencrypted backup used for CI/self-test only"
fi
sha256sum "$DEST"/* >"$DEST/checksums.sha256"
echo "backup_dir=$DEST"
echo "$DEST" >"${HERMES_BACKUP_DIR:-$ROOT/evidence/backups}/LATEST"
