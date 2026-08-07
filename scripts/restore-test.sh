#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK="$(mktemp -d /tmp/hermes-restore-test-XXXXXX)"
LATEST_FILE="${HERMES_BACKUP_DIR:-$ROOT/evidence/backups}/LATEST"
if [[ ! -f "$LATEST_FILE" ]]; then
  "$ROOT/scripts/backup.sh" >/dev/null
fi
SRC="$(cat "$LATEST_FILE")"
REPORT="$ROOT/evidence/backups/restore-test-$STAMP.md"
{
  echo "# Restore test $STAMP"
  echo
  echo "- source: $SRC"
  echo "- work: $WORK"
  if [[ -f "$SRC/config-and-state.tgz.enc" ]]; then
    if [[ -z "${BACKUP_ENCRYPTION_KEY_FILE:-}" ]]; then
      echo "- result: BLOCKED (encrypted backup, no key file)"
      exit 2
    fi
    openssl enc -d -aes-256-cbc -pbkdf2 \
      -in "$SRC/config-and-state.tgz.enc" \
      -out "$WORK/config-and-state.tgz" \
      -pass "file:${BACKUP_ENCRYPTION_KEY_FILE}"
  else
    cp "$SRC/config-and-state.tgz" "$WORK/"
  fi
  mkdir -p "$WORK/restore"
  tar -C "$WORK/restore" -xzf "$WORK/config-and-state.tgz"
  test -f "$WORK/restore/VERSION"
  test -d "$WORK/restore/config"
  echo "- result: PASS"
  echo "- restored VERSION: $(cat "$WORK/restore/VERSION")"
} | tee "$REPORT"
rm -rf "$WORK"
echo "restore_report=$REPORT"
