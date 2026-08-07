from pathlib import Path
import subprocess
import sys
import json

ROOT = Path(__file__).resolve().parents[2]

def test_fault_ledger_validates():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/ci/fault-ledger-validate.py")], cwd=ROOT)
    assert r.returncode == 0

def test_fault_ids_unique():
    lines = [ln for ln in (ROOT / "evidence/faults/fault-ledger.jsonl").read_text().splitlines() if ln.strip()]
    ids = [json.loads(ln)["fault_id"] for ln in lines]
    assert len(ids) == len(set(ids))
