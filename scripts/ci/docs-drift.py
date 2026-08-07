#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
required = [
    "docs/architecture.md",
    "docs/service-inventory.md",
    "docs/operations.md",
    "docs/recovery.md",
    "docs/secrets-contract.md",
    "docs/network-contract.md",
    "docs/backup-restore.md",
    "docs/autonomous-governance.md",
    "README.md",
    "config/services.yaml",
    "config/ports.yaml",
    "config/secret-contract.yaml",
]
missing = [r for r in required if not (ROOT / r).is_file() or (ROOT / r).stat().st_size == 0]
if missing:
    print("DOCS-DRIFT FAIL")
    for m in missing:
        print(f" - missing/empty {m}")
    sys.exit(1)
# services doc should mention clean-room identity
arch = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
if "clean-room" not in arch.lower() and "cleanroom" not in arch.lower():
    print("DOCS-DRIFT FAIL: architecture.md must describe clean-room")
    sys.exit(1)
print("DOCS-DRIFT PASS")
