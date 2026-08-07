#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/evidence/acceptance"
mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="$OUT_DIR/acceptance-$STAMP.json"
python3 - "$ROOT" "$REPORT" <<'PY'
import json, os, subprocess, sys, datetime
from pathlib import Path
root = Path(sys.argv[1])
report_path = Path(sys.argv[2])
checks = []

def run(name, cmd, cwd=None):
    try:
        p = subprocess.run(cmd, cwd=cwd or root, capture_output=True, text=True, timeout=120)
        ok = p.returncode == 0
        checks.append({
            "name": name,
            "status": "PASS" if ok else "FAIL",
            "exit_code": p.returncode,
            "stdout_tail": (p.stdout or "")[-500:],
            "stderr_tail": (p.stderr or "")[-500:],
        })
    except Exception as e:
        checks.append({"name": name, "status": "FAIL", "error": str(e)})

run("healthcheck", ["bash", "scripts/healthcheck.sh"])
run("validate-config", ["python3", "scripts/ci/validate-config.py"])
# Prefer project venv for pytest when present
venv_py = root / ".venv/bin/python"
py = str(venv_py) if venv_py.exists() else "python3"
run("unit-tests", [py, "-m", "pytest", "-q", "tests/unit"])
run("backup", ["bash", "scripts/backup.sh"])
run("restore-test", ["bash", "scripts/restore-test.sh"])

# Truthfulness checks
text = (root / "config" / "services.yaml").read_text()
checks.append({
    "name": "hada-not-fabricated",
    "status": "PASS" if "NOT_DEPLOYED" in text else "FAIL",
})
checks.append({
    "name": "telegram-not-live-without-e2e",
    "status": "PASS" if "READY_FOR_EXCLUSIVE_CUTOVER" in text else "FAIL",
})

failed = [c for c in checks if c["status"] != "PASS"]
result = {
    "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "host": os.uname().nodename,
    "checks": checks,
    "overall": "PASS" if not failed else "FAIL",
}
report_path.write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
sys.exit(0 if not failed else 1)
PY
