#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="${HERMES_REPO:-/home/ubuntu/hermes-ovh-cleanroom}"
PROMPT_FILE="$REPO/ops/AUTONOMY_PROMPT.txt"
DONE_FILE="$REPO/evidence/control/AUTONOMY_DONE.json"

if [[ -d /var/lib/hermes-grok-controller && -w /var/lib/hermes-grok-controller ]]; then
  STATE_DIR=/var/lib/hermes-grok-controller
else
  STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/hermes-grok-controller"
fi

mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"

exec 9>"$STATE_DIR/controller.lock"
if ! flock -n 9; then
  echo "Another Hermes Grok controller instance is already running." >&2
  exit 75
fi

SESSION_FILE="$STATE_DIR/session-id"
STARTED_FILE="$STATE_DIR/started"
RUNLOG="$STATE_DIR/grok-output.log"
FAULTLOG="$STATE_DIR/controller-faults.jsonl"

log_controller_fault() {
  local rc="$1"
  local symptom="$2"
  python3 - "$FAULTLOG" "$rc" "$symptom" <<'PY'
import datetime
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

path, rc, symptom = sys.argv[1:4]
now = datetime.datetime.now(datetime.timezone.utc)
record = {
    "fault_id": "CTRL-" + now.strftime("%Y%m%dT%H%M%SZ"),
    "timestamp_utc": now.isoformat(),
    "timestamp_melbourne": now.astimezone(ZoneInfo("Australia/Melbourne")).isoformat(),
    "phase": "autonomous-controller",
    "host": "hermes-ovh-cleanroom",
    "exit_code": int(rc),
    "symptom": symptom,
    "classification": "controller",
    "severity": "warning" if int(rc) != 0 else "info",
    "repair_status": "retrying"
}
with pathlib.Path(path).open("a", encoding="utf-8") as f:
    f.write(json.dumps(record, separators=(",", ":")) + "\n")
PY
}

cd "$REPO"

test -s AGENTS.md
test -s runbook/RUNBOOK-MANIFEST.md
test -s policy/anti-hallucination-guardrails.md
test -s runbook/part-99-post-completion-evolution-policy.md
test -s "$PROMPT_FILE"
command -v grok >/dev/null
command -v gh >/dev/null
command -v git >/dev/null

if [[ ! -s "$SESSION_FILE" ]]; then
  python3 - <<'PY' > "$SESSION_FILE"
import uuid
print(uuid.uuid4())
PY
  chmod 600 "$SESSION_FILE"
fi

SESSION_ID="$(tr -d '[:space:]' < "$SESSION_FILE")"

if [[ -z "$SESSION_ID" ]]; then
  echo "Empty Grok session ID" >&2
  exit 70
fi

while true; do
  if [[ -s "$DONE_FILE" ]]; then
    if python3 - "$DONE_FILE" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
d = json.loads(p.read_text(encoding="utf-8"))
allowed = {
    "COMPLETE_CLEANROOM",
    "COMPLETE_READY_FOR_EXCLUSIVE_CUTOVER",
    "PARTIAL_WITH_EXTERNAL_BLOCKERS",
    "FAILED_SAFETY_GATE",
}
assert d.get("state") in allowed
assert d.get("evidence_verified") is True
assert d.get("verified_commit_sha")
assert d.get("final_report")
print("AUTONOMY_DONE=" + d["state"])
PY
    then
      echo "Verified autonomy completion marker present. Controller exiting cleanly."
      exit 0
    else
      log_controller_fault 65 "Invalid AUTONOMY_DONE.json; refusing to stop autonomous execution"
    fi
  fi

  if [[ ! -e "$STARTED_FILE" ]]; then
    PROMPT="$(cat "$PROMPT_FILE")"
    touch "$STARTED_FILE"
    chmod 600 "$STARTED_FILE"
  else
    PROMPT='Continue the existing Hermes OVH clean-room autonomous run. Re-read AGENTS.md and runbook/RUNBOOK-MANIFEST.md, inspect current Git/PR/CI/runtime/evidence state, ingest any controller faults from /var/lib/hermes-grok-controller/controller-faults.jsonl into the canonical fault ledger where applicable, and resume from the exact last verified point. Do not merely report progress. Keep executing and repairing until the manifest permits evidence/control/AUTONOMY_DONE.json to be created.'
  fi

  echo "[$(date --iso-8601=seconds)] Starting/resuming Grok session $SESSION_ID" | tee -a "$RUNLOG"

  set +e
  grok \
    --no-auto-update \
    --always-approve \
    --cwd "$REPO" \
    --session-id "$SESSION_ID" \
    --output-format plain \
    -p "$PROMPT" \
    2>&1 | tee -a "$RUNLOG"
  rc=${PIPESTATUS[0]}
  set -e

  if [[ "$rc" -ne 0 ]]; then
    log_controller_fault "$rc" "Grok headless run exited non-zero; controller will retry same named session"
    echo "Grok exited rc=$rc. Retrying same session after 300 seconds." | tee -a "$RUNLOG"
    sleep 300
  else
    if [[ -s "$DONE_FILE" ]]; then
      continue
    fi
    log_controller_fault 0 "Grok turn ended without a valid completion marker; continuing same named session"
    echo "Grok turn ended without AUTONOMY_DONE. Continuing after 30 seconds." | tee -a "$RUNLOG"
    sleep 30
  fi
done
