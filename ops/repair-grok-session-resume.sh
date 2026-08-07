#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="/home/ubuntu/hermes-ovh-cleanroom"
BOOT_ROOT="/home/ubuntu/hermes-bootstrap/evidence"
FAULT_LEDGER="$BOOT_ROOT/faults/fault-ledger.jsonl"
REPAIR_DIR="$BOOT_ROOT/repairs"
SERVICE="hermes-grok-controller.service"
SESSION_FILE="/var/lib/hermes-grok-controller/session-id"

mkdir -p "$REPAIR_DIR" "$(dirname "$FAULT_LEDGER")"
NOW_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
NOTE="$REPAIR_DIR/${NOW_UTC}-grok-session-resume-repair.md"
ATTEMPT="$REPAIR_DIR/${NOW_UTC}-grok-session-resume-repair.json"
SESSION_ID="$(sudo cat "$SESSION_FILE" 2>/dev/null | tr -d '[:space:]' || true)"

write_note_header() {
  cat >"$NOTE" <<EOF
# Grok session-resume repair note

- UTC: $(date -u --iso-8601=seconds)
- Melbourne: $(TZ=Australia/Melbourne date --iso-8601=seconds)
- Host: $(hostname)
- Service: $SERVICE
- Session ID: ${SESSION_ID:-PENDING_VERIFICATION}
- Purpose: repair repeated 'Session ID ... is already in use' controller loop without deleting session history.

## Pre-repair evidence

### Service state

\`\`\`
$(systemctl status "$SERVICE" --no-pager -l 2>&1 || true)
\`\`\`

### Recent controller journal

\`\`\`
$(sudo journalctl -u "$SERVICE" -n 80 --no-pager 2>&1 || true)
\`\`\`

### Grok processes before stop

\`\`\`
$(pgrep -af '(^|/)(grok)( |$)' || true)
\`\`\`
EOF
}

append_fault_record() {
  python3 - "$FAULT_LEDGER" "$NOTE" "$SESSION_ID" <<'PY'
import datetime, json, pathlib, sys, uuid
from zoneinfo import ZoneInfo
ledger, note, session = sys.argv[1:4]
now = datetime.datetime.now(datetime.timezone.utc)
rec = {
    "fault_id": "FLT-" + now.strftime("%Y%m%d-") + uuid.uuid4().hex[:8].upper(),
    "timestamp_utc": now.isoformat(),
    "timestamp_melbourne": now.astimezone(ZoneInfo("Australia/Melbourne")).isoformat(),
    "phase": "autonomous-controller-repair",
    "host": "hermes-ovh-cleanroom",
    "repository": "mdyerapis-coder/hermes-ovh-cleanroom",
    "branch": "main",
    "symptom": "Grok controller repeatedly received Session ID already in use after first headless turn",
    "expected": "Existing named Grok session resumes after controller turn/restart",
    "observed": "Controller retried --session-id against an already-created session and exited rc=1",
    "classification": "configuration",
    "severity": "error",
    "root_cause": "Controller used --session-id for retries instead of --resume after initial session creation",
    "repair_status": "repairing",
    "repair_attempts": 1,
    "evidence_paths": [note],
    "session_id": session or None,
    "final_disposition": None,
}
pathlib.Path(ledger).parent.mkdir(parents=True, exist_ok=True)
with pathlib.Path(ledger).open("a", encoding="utf-8") as f:
    f.write(json.dumps(rec, separators=(",", ":")) + "\n")
print(rec["fault_id"])
PY
}

write_attempt() {
  local result="$1"
  local details="$2"
  python3 - "$ATTEMPT" "$NOTE" "$SESSION_ID" "$result" "$details" <<'PY'
import datetime, json, pathlib, sys
from zoneinfo import ZoneInfo
out, note, session, result, details = sys.argv[1:6]
now = datetime.datetime.now(datetime.timezone.utc)
rec = {
    "timestamp_utc": now.isoformat(),
    "timestamp_melbourne": now.astimezone(ZoneInfo("Australia/Melbourne")).isoformat(),
    "repair": "grok-session-resume",
    "session_id": session or None,
    "change": "Use --session-id only for first launch and --resume for subsequent turns/restarts",
    "verification": details,
    "result": result,
    "note": note,
}
pathlib.Path(out).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
PY
}

fail_repair() {
  local rc="$1"
  local msg="$2"
  {
    echo
    echo "## Repair result"
    echo
    echo "FAILED: $msg"
  } >>"$NOTE"
  write_attempt fail "$msg"
  echo "$msg" >&2
  exit "$rc"
}

write_note_header
FAULT_ID="$(append_fault_record)"
echo "Logged repair fault record: $FAULT_ID"
echo "Repair note: $NOTE"

cd "$REPO"

sudo systemctl stop "$SERVICE"
sleep 2

REMAINING="$(pgrep -af '(^|/)(grok)( |$)' || true)"
if [[ -n "$REMAINING" ]]; then
  {
    echo
    echo "## Unexpected Grok processes after service stop"
    echo
    echo '```'
    echo "$REMAINING"
    echo '```'
  } >>"$NOTE"
  fail_repair 75 "Unexpected Grok process remains after stopping the controller; refusing to kill or delete session state automatically."
fi

if [[ -n "$(git status --porcelain)" ]]; then
  git status --short >>"$NOTE"
  fail_repair 76 "Repository working tree is dirty after controller stop; refusing destructive reset."
fi

git switch main
git pull --ff-only origin main

grep -q -- '--resume "$SESSION_ID"' ops/grok-controller.sh || fail_repair 77 "Audited source does not contain expected --resume session repair."

bash ops/install-grok-controller.sh >>"$NOTE" 2>&1

START_MARK="$(date --iso-8601=seconds)"
sudo systemctl start "$SERVICE"
sleep 8

systemctl is-active --quiet "$SERVICE" || fail_repair 78 "Controller did not remain active after audited reinstall."

POST_JOURNAL="$(sudo journalctl -u "$SERVICE" --since "$START_MARK" --no-pager 2>&1 || true)"
{
  echo
  echo "## Post-repair journal"
  echo
  echo '```'
  echo "$POST_JOURNAL"
  echo '```'
} >>"$NOTE"

if grep -Fq 'is already in use' <<<"$POST_JOURNAL"; then
  fail_repair 79 "Session collision still appears after audited --resume repair."
fi

write_attempt pass "Controller active after audited reinstall; no 'Session ID ... is already in use' message observed in post-restart journal window."
{
  echo
  echo "## Repair result"
  echo
  echo "PASS: audited controller reinstalled and restarted; existing session UUID preserved."
} >>"$NOTE"

echo
echo "=== GROK SESSION REPAIR ==="
echo "fault_id=$FAULT_ID"
echo "session_id=${SESSION_ID:-PENDING_VERIFICATION}"
echo "controller=$(systemctl is-active "$SERVICE")"
echo "controller_enabled=$(systemctl is-enabled "$SERVICE")"
echo "note=$NOTE"
echo "attempt=$ATTEMPT"
echo "GROK_SESSION_REPAIR=PASS"
