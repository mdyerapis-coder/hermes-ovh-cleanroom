#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "evidence/baseline/baseline-manifest.json"
def main() -> int:
    if not MANIFEST.is_file():
        print("BASELINE-PRESERVATION SKIP: baseline not yet established (pre-completion)")
        return 0
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    protected_files = data.get("protected_files") or data.get("documentation_set") or []
    missing = []
    for rel in protected_files:
        if not (ROOT / rel).exists():
            missing.append(rel)
    required_jobs = data.get("required_ci_jobs") or []
    pr_audit = (ROOT / ".github/workflows/pr-audit.yml").read_text(encoding="utf-8")
    for job in required_jobs:
        if job not in pr_audit and job != "baseline-preservation":
            missing.append(f"ci-job:{job}")
    if "AUDIT-GATE" not in pr_audit:
        missing.append("AUDIT-GATE")
    if missing:
        print("BASELINE-PRESERVATION FAIL")
        for m in missing:
            print(f" - {m}")
        return 1
    print("BASELINE-PRESERVATION PASS")
    return 0
if __name__ == "__main__":
    sys.exit(main())
