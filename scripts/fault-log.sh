#!/usr/bin/env bash
# Append a fault record to the canonical ledger (values must be pre-redacted).
set -Eeuo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LEDGER="${ROOT}/evidence/faults/fault-ledger.jsonl"
mkdir -p "$(dirname "$LEDGER")"

PHASE="${1:-other}"
SYMPTOM="${2:-unspecified fault}"
CLASSIFICATION="${3:-unknown}"
SEVERITY="${4:-error}"
EXIT_CODE="${5:-1}"
COMMAND="${6:-}"
EXPECTED="${7:-success}"
OBSERVED="${8:-failure}"

python3 - "$LEDGER" "$PHASE" "$SYMPTOM" "$CLASSIFICATION" "$SEVERITY" "$EXIT_CODE" "$COMMAND" "$EXPECTED" "$OBSERVED" <<'PY'
import datetime, json, pathlib, sys, uuid, subprocess, os
from zoneinfo import ZoneInfo
path, phase, symptom, classification, severity, exit_code, command, expected, observed = sys.argv[1:10]
now = datetime.datetime.now(datetime.timezone.utc)
try:
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
except Exception:
    sha = None
try:
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL).strip() or None
except Exception:
    branch = None
rec = {
    "fault_id": "FLT-" + now.strftime("%Y%m%d-") + uuid.uuid4().hex[:8].upper(),
    "timestamp_utc": now.isoformat(),
    "timestamp_melbourne": now.astimezone(ZoneInfo("Australia/Melbourne")).isoformat(),
    "phase": phase,
    "host": os.uname().nodename,
    "repository": "mdyerapis-coder/hermes-ovh-cleanroom",
    "branch": branch,
    "commit_sha": sha,
    "pull_request": os.environ.get("GITHUB_REF"),
    "workflow_run": os.environ.get("GITHUB_RUN_ID"),
    "job": os.environ.get("GITHUB_JOB"),
    "command": command or None,
    "exit_code": int(exit_code),
    "symptom": symptom,
    "expected": expected,
    "observed": observed,
    "evidence_paths": [],
    "classification": classification,
    "severity": severity,
    "root_cause": None,
    "repair_status": "untriaged",
    "repair_attempts": 0,
    "final_disposition": None,
}
with pathlib.Path(path).open("a", encoding="utf-8") as f:
    f.write(json.dumps(rec, separators=(",", ":")) + "\n")
print(rec["fault_id"])
PY
