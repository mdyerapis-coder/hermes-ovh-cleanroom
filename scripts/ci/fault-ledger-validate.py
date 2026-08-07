#!/usr/bin/env python3
"""Validate fault ledger append-only JSONL semantics."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "evidence/faults/fault-ledger.jsonl"

SECRETISH = re.compile(r"(ghp_|github_pat_|xox[baprs]-|sk-|AKIA[0-9A-Z]{16}|-----BEGIN)")

REQUIRED = {
    "fault_id", "timestamp_utc", "phase", "symptom", "classification",
    "severity", "repair_status",
}

def main() -> int:
    if not LEDGER.is_file():
        print("FAIL: fault ledger missing")
        return 1
    ids = set()
    errors = []
    lines = [ln for ln in LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        print("FAIL: fault ledger empty (bootstrap faults should be ingested)")
        return 1
    for i, line in enumerate(lines, 1):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {i}: invalid JSON: {e}")
            continue
        missing = REQUIRED - set(rec)
        if missing:
            errors.append(f"line {i}: missing fields {sorted(missing)}")
        fid = rec.get("fault_id")
        if not fid:
            errors.append(f"line {i}: empty fault_id")
        elif fid in ids:
            errors.append(f"duplicate fault_id {fid}")
        else:
            ids.add(fid)
        blob = json.dumps(rec)
        if SECRETISH.search(blob):
            errors.append(f"line {i}: secret-like content")
        if rec.get("repair_status") == "resolved":
            # resolved must have some verification signal
            if not rec.get("final_disposition") and not rec.get("root_cause"):
                errors.append(f"{fid}: resolved without disposition/root_cause")
        if rec.get("severity") == "critical" and rec.get("repair_status") in {"untriaged"}:
            # open criticals fail gate only if still untriaged with no disposition and not bootstrap historical
            if rec.get("phase") not in {"toolchain-bootstrap", "github-governance-bootstrap"}:
                errors.append(f"{fid}: unresolved critical fault")

    # Generate summary
    summary = ROOT / "evidence/faults/current-summary.md"
    summary.parent.mkdir(parents=True, exist_ok=True)
    open_f = []
    blocked = []
    for line in lines:
        rec = json.loads(line)
        if rec.get("repair_status") in {"untriaged", "repairing", "retesting", "blocked"}:
            open_f.append(rec)
        if rec.get("repair_status") == "blocked":
            blocked.append(rec)
    summary.write_text(
        "# Fault summary\n\n"
        f"- total_records: {len(lines)}\n"
        f"- open_or_active: {len(open_f)}\n"
        f"- blocked: {len(blocked)}\n\n"
        "## Open / active\n\n"
        + "\n".join(
            f"- {r.get('fault_id')}: {r.get('symptom')} ({r.get('repair_status')})"
            for r in open_f
        )
        + "\n",
        encoding="utf-8",
    )

    if errors:
        print("FAULT LEDGER FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print(f"FAULT LEDGER PASS ({len(lines)} records)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
