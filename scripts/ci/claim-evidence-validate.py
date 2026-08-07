#!/usr/bin/env python3
"""Anti-hallucination claim-evidence validation (mandatory AUDIT-GATE dependency)."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "evidence/claims/claim-evidence-map.jsonl"

ALLOWED_STATUS = {
    "VERIFIED", "PENDING_VERIFICATION", "BLOCKED", "NOT_APPLICABLE",
    "SUPERSEDED", "REPLACED", "TRIALLED",
}

COMPLETION_WORDS = re.compile(
    r"\b(complete|completed|deployed|operational|healthy|fixed|resolved|restored|migrated|verified|production-ready)\b",
    re.I,
)

def main() -> int:
    errors = []
    if not MAP.is_file():
        print("FAIL: claim-evidence-map.jsonl missing")
        return 1

    lines = [ln for ln in MAP.read_text(encoding="utf-8").splitlines() if ln.strip()]
    claims = []
    for i, line in enumerate(lines, 1):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {i}: invalid JSON: {e}")
            continue
        for field in ("claim_id", "claim", "status", "component", "evidence"):
            if field not in rec:
                errors.append(f"line {i}: missing {field}")
        status = rec.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"line {i}: invalid status {status}")
        if status == "VERIFIED":
            evidence = rec.get("evidence") or []
            if not evidence:
                errors.append(f"{rec.get('claim_id')}: VERIFIED without evidence")
            for ev in evidence:
                # local paths must exist if relative
                if isinstance(ev, str) and not ev.startswith("http") and not ev.startswith("run:"):
                    p = ROOT / ev
                    if not p.exists():
                        errors.append(f"{rec.get('claim_id')}: missing evidence artifact {ev}")
        # HADA rule
        claim = (rec.get("claim") or "") + " " + (rec.get("component") or "")
        if re.search(r"\bHADA\b", claim, re.I) and status == "VERIFIED":
            if "NOT_DEPLOYED" not in json.dumps(rec) and "runtime" in claim.lower():
                # verified HADA runtime requires runtime evidence
                blob = json.dumps(rec).lower()
                if "runtime" in blob and "not_deployed" not in blob:
                    errors.append(f"{rec.get('claim_id')}: HADA deployed claim requires runtime evidence")
        # Telegram live rule
        if re.search(r"telegram.*(live|e2e)", claim, re.I) and status == "VERIFIED":
            errors.append(f"{rec.get('claim_id')}: Telegram LIVE/E2E must not be VERIFIED without permitted E2E evidence")
        claims.append(rec)

    # Check final status files if present for unsupported VERIFIED completion language
    final_dir = ROOT / "evidence/final"
    if final_dir.is_dir():
        for path in final_dir.rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            # If document asserts VERIFIED completion, require map entries
            if "VERIFIED" in text and COMPLETION_WORDS.search(text):
                if not any(c.get("status") == "VERIFIED" for c in claims):
                    errors.append(f"{path}: completion language without verified claims")

    if errors:
        print("CLAIM-EVIDENCE VALIDATION FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print(f"CLAIM-EVIDENCE VALIDATION PASS ({len(claims)} claims)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
