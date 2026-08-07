#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Fail if unexpected public listeners beyond allowed contract
# Allowed public: ssh 22. Databases must not be public.
python3 - "$ROOT" <<'PY'
import subprocess, re, sys
from pathlib import Path
root = Path(sys.argv[1])
ss = subprocess.check_output(["ss", "-lntu"], text=True, stderr=subprocess.DEVNULL)
public_bad = []
for line in ss.splitlines()[1:]:
    parts = line.split()
    if len(parts) < 5:
        continue
    local = parts[4]
    # formats 0.0.0.0:5432 or *:5432 or [::]:5432
    m = re.search(r'([*0-9\.:\[\]]+):(\d+)$', local)
    if not m:
        continue
    addr, port = m.group(1), m.group(2)
    is_public = addr in {"0.0.0.0", "*", "[::]", "::"} or (addr.startswith(":::") )
    if not is_public:
        continue
    if port in {"22"}:  # ssh allowed during bootstrap
        continue
    # tailscale etc may show differently; flag common internal ports if public
    if port in {"5432", "6333", "5678", "8642", "8643", "5432"}:
        public_bad.append(f"{addr}:{port}")
if public_bad:
    print("LISTENER CONTRACT FAIL: unexpected public binds:", public_bad)
    sys.exit(1)
print("LISTENER CONTRACT PASS")
print(ss)
PY
