#!/usr/bin/env python3
"""Validate config contracts for hermes-ovh-cleanroom."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

try:
    import yaml  # type: ignore
except ImportError:
    # Minimal YAML subset via safe fallback for pure structure checks
    yaml = None

def load_yaml(path: Path):
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    # Fallback: require non-empty and key markers
    if not text.strip():
        raise ValueError(f"empty: {path}")
    return {"_raw": True, "text": text}

def main() -> int:
    errors = []
    for rel in [
        "config/services.yaml",
        "config/ports.yaml",
        "config/secret-contract.yaml",
        "config/versions.lock",
    ]:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing {rel}")
            continue
        if path.suffix in {".yaml", ".yml"}:
            try:
                data = load_yaml(path)
                if data is None:
                    errors.append(f"null yaml {rel}")
            except Exception as e:
                errors.append(f"parse {rel}: {e}")
        else:
            if path.stat().st_size == 0:
                errors.append(f"empty {rel}")

    # ports contract markers
    ports = (ROOT / "config/ports.yaml").read_text(encoding="utf-8")
    for token in ["component:", "port:", "exposure:"]:
        if token not in ports:
            errors.append(f"ports.yaml missing {token}")

    secrets = (ROOT / "config/secret-contract.yaml").read_text(encoding="utf-8")
    if "secrets:" not in secrets:
        errors.append("secret-contract missing secrets:")
    # Fail if something looks like a real secret assignment of long random material
    for line in secrets.splitlines():
        if ":" in line and any(x in line.lower() for x in ["sk-", "ghp_", "xoxb-", "-----begin"]):
            errors.append(f"possible secret material in secret-contract: {line[:40]}")

    services = (ROOT / "config/services.yaml").read_text(encoding="utf-8")
    if "NOT_DEPLOYED" not in services:
        errors.append("services.yaml must declare HADA_RUNTIME honesty (NOT_DEPLOYED)")
    if "READY_FOR_EXCLUSIVE_CUTOVER" not in services:
        errors.append("services.yaml must declare Telegram READY_FOR_EXCLUSIVE_CUTOVER")

    if errors:
        print("CONFIG CONTRACT FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("CONFIG CONTRACT PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
