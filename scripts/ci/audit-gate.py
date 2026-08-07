#!/usr/bin/env python3
"""Require exact success from every mandatory job in needs JSON."""
from __future__ import annotations
import json
import os
import sys

def main() -> int:
    raw = os.environ.get("NEEDS_JSON", "{}")
    needs = json.loads(raw)
    bad = {
        name: meta.get("result")
        for name, meta in needs.items()
        if meta.get("result") != "success"
    }
    if bad:
        print("AUDIT-GATE FAILED")
        for name, result in sorted(bad.items()):
            print(f"{name}: {result}")
        return 1
    print("AUDIT-GATE PASSED")
    for name in sorted(needs):
        print(f"{name}: {needs[name].get('result')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
