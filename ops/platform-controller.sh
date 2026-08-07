#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="${HERMES_REPO:-/home/ubuntu/hermes-ovh-cleanroom}"
PROMPT_FILE="$REPO/ops/PLATFORM_AUTONOMY_PROMPT.txt"
BASELINE_FILE="$REPO/evidence/control/AUTONOMY_DONE.json"
DONE_FILE="$REPO/evidence/control/PLATFORM_COMPLETION.json"

if [[ -d /var/lib/hermes-platform-controller && -w /var/lib/hermes-platform-controller ]]; then
  STATE_DIR=/var/lib/hermes-platform-controller
else
  STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/hermes-platform-controller"
fi

mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"

exec 9>"$STATE_DIR/controller.lock"
if ! flock -n 9; then
  echo "Another Hermes platform controller instance is already running." >&2
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
    "fault_id": "PLATCTRL-" + now.strftime("%Y%m%dT%H%M%SZ"),
    "timestamp_utc": now.isoformat(),
    "timestamp_melbourne": now.astimezone(ZoneInfo("Australia/Melbourne")).isoformat(),
    "phase": "platform-autonomous-controller",
    "host": "hermes-ovh-cleanroom",
    "exit_code": int(rc),
    "symptom": symptom,
    "classification": "controller",
    "severity": "warning" if int(rc) != 0 else "info",
    "repair_status": "retrying",
}
with pathlib.Path(path).open("a", encoding="utf-8") as f:
    f.write(json.dumps(record, separators=(",", ":")) + "\n")
PY
}

validate_baseline() {
  python3 - "$BASELINE_FILE" <<'PY'
import json
import pathlib
import sys

p = pathlib.Path(sys.argv[1])
if not p.is_file():
    raise SystemExit("missing clean-room baseline marker")
d = json.loads(p.read_text(encoding="utf-8"))
if not d.get("evidence_verified"):
    raise SystemExit("clean-room baseline is not evidence_verified")
if d.get("state") not in {
    "COMPLETE_CLEANROOM",
    "COMPLETE_READY_FOR_EXCLUSIVE_CUTOVER",
}:
    raise SystemExit("clean-room baseline is not a completed state")
if not d.get("verified_commit_sha"):
    raise SystemExit("clean-room baseline missing verified_commit_sha")
print("BASELINE=" + d["state"])
PY
}

validate_completion() {
  python3 - "$DONE_FILE" "$REPO" <<'PY'
import json
import pathlib
import sys

p = pathlib.Path(sys.argv[1])
repo = pathlib.Path(sys.argv[2])
d = json.loads(p.read_text(encoding="utf-8"))
allowed = {
    "COMPLETE_PRODUCTION",
    "COMPLETE_HPS_HES_READY_FOR_CUTOVER",
    "PARTIAL_WITH_EXTERNAL_BLOCKERS",
    "FAILED_SAFETY_GATE",
}
if d.get("state") not in allowed:
    raise SystemExit("invalid platform completion state")
if d.get("evidence_verified") is not True:
    raise SystemExit("platform completion is not evidence_verified")
if not d.get("verified_commit_sha"):
    raise SystemExit("platform completion missing verified_commit_sha")
report = d.get("final_report")
if not report or not (repo / report).is_file():
    raise SystemExit("platform completion final report missing")
if d.get("state") == "COMPLETE_PRODUCTION":
    required = {
        "HPS_V1": "PASS",
        "HES_V1": "PASS",
        "HPS_HES_INTEGRATION": "PASS",
        "Hermes_production_host": "hermes-ovh-cleanroom",
        "Telegram_exclusive": True,
        "Telegram_live_e2e": True,
        "rollback_available": True,
        "production_baseline_created": True,
    }
    for key, expected in required.items():
        if d.get(key) != expected:
            raise SystemExit(f"COMPLETE_PRODUCTION missing required proof field {key}")
print("PLATFORM_COMPLETION=" + d["state"])
PY
}

cd "$REPO"

test -s AGENTS.md
test -s runbook/RUNBOOK-MANIFEST.md
test -s runbook/part-100-hps-hes-platform-completion.md
test -s policy/anti-hallucination-guardrails.md
test -s runbook/part-99-post-completion-evolution-policy.md
test -s "$PROMPT_FILE"
command -v grok >/dev/null
command -v gh >/dev/null
command -v git >/dev/null

validate_baseline

if [[ ! -s "$SESSION_FILE" ]]; then
  python3 - <<'PY' >"$SESSION_FILE"
import uuid
print(uuid.uuid4())
PY
  chmod 600 "$SESSION_FILE"
fi

SESSION_ID="$(tr -d '[:space:]' <"$SESSION_FILE")"
if [[ -z "$SESSION_ID" ]]; then
  echo "Empty Grok platform session ID" >&2
  exit 70
fi

while true; do
  if [[ -s "$DONE_FILE" ]]; then
    if validate_completion; then
      echo "Verified platform completion marker present. Controller exiting cleanly."
      exit 0
    fi
    log_controller_fault 65 "Invalid PLATFORM_COMPLETION.json; refusing to stop autonomous execution"
  fi

  if [[ ! -e "$STARTED_FILE" ]]; then
    PROMPT="$(cat "$PROMPT_FILE")"
    MODE="new"
  else
    PROMPT='Continue the existing HPS/HES platform-completion mission. Re-read AGENTS.md, runbook/RUNBOOK-MANIFEST.md and runbook/part-100-hps-hes-platform-completion.md; inspect current Git/PR/CI/runtime/evidence/fault state; ingest platform controller faults from /var/lib/hermes-platform-controller/controller-faults.jsonl into the canonical fault ledger where applicable; resume from the exact last verified point. The old AUTONOMY_DONE.json is baseline only. Do not merely report progress. Keep implementing, testing, merging through exact gates, deploying and repairing until evidence/control/PLATFORM_COMPLETION.json is genuinely permitted.'
    MODE="resume"
  fi

  echo "[$(date --iso-8601=seconds)] Starting $MODE platform Grok session $SESSION_ID" | tee -a "$RUNLOG"

  set +e
  if [[ "$MODE" == "new" ]]; then
    grok \
      --no-auto-update \
      --always-approve \
      --cwd "$REPO" \
      --session-id "$SESSION_ID" \
      --output-format plain \
      -p "$PROMPT" \
      2>&1 | tee -a "$RUNLOG"
  else
    grok \
      --no-auto-update \
      --always-approve \
      --cwd "$REPO" \
      --resume "$SESSION_ID" \
      --output-format plain \
      -p "$PROMPT" \
      2>&1 | tee -a "$RUNLOG"
  fi
  rc=${PIPESTATUS[0]}
  set -e

  if [[ "$MODE" == "new" && ! -e "$STARTED_FILE" ]]; then
    touch "$STARTED_FILE"
    chmod 600 "$STARTED_FILE"
  fi

  if [[ "$rc" -ne 0 ]]; then
    log_controller_fault "$rc" "Platform Grok headless run exited non-zero; controller will retry the same session with --resume"
    echo "Grok exited rc=$rc. Retrying same platform session after 300 seconds." | tee -a "$RUNLOG"
    sleep 300
  else
    if [[ -s "$DONE_FILE" ]]; then
      continue
    fi
    log_controller_fault 0 "Platform Grok turn ended without a valid PLATFORM_COMPLETION marker; continuing same session"
    echo "Grok turn ended without PLATFORM_COMPLETION. Continuing after 30 seconds." | tee -a "$RUNLOG"
    sleep 30
  fi
done
