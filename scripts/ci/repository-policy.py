#!/usr/bin/env python3
"""Repository policy scanner — fail closed on dangerous tracked content."""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Paths allowed to contain example secret-like patterns
ALLOW_PATH_FRAGMENTS = {
    "policy/anti-hallucination-guardrails.md",
    "runbook/",
    "docs/",
    "tests/",
    ".github/workflows/bootstrap-audit.yml",
}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

DANGEROUS_PATTERNS = [
    (re.compile(r"chmod" + r"\s+" + r"777"), "unrestricted chmod " + "777"),
    (re.compile(r"privileged:\s*true"), "privileged container"),
    (re.compile(r"network_mode:\s*host"), "host network"),
    (re.compile(r"/var/run/docker\.sock"), "docker socket mount"),
    (re.compile(r"gh\s+pr\s+merge\s+.*--admin"), "admin merge bypass"),
    (re.compile(r"image\s*:\s*\S+:latest\b"), "mutable image tag latest"),
]

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}

def allowed(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    for frag in ALLOW_PATH_FRAGMENTS:
        if frag in rel:
            return True
    return False

def main() -> int:
    errors = []
    # Bootstrap auditor must remain
    if not (ROOT / ".github/workflows/bootstrap-audit.yml").is_file():
        errors.append("trusted bootstrap-audit.yml missing")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".tgz", ".gz", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.name == ".env" or path.name.endswith(".env"):
            # Allow .env.example only
            if path.name != ".env.example":
                errors.append(f"tracked env file not allowed: {rel}")
        for pat in SECRET_PATTERNS:
            if pat.search(text) and not allowed(path):
                errors.append(f"secret-like content in {rel}")
                break
        if not allowed(path) and rel != "scripts/ci/repository-policy.py":
            for pat, label in DANGEROUS_PATTERNS:
                if pat.search(text):
                    # latest tag in lock comments / docs only warning except compose
                    if label.startswith("mutable latest") and path.suffix not in {".yml", ".yaml"}:
                        continue
                    if label.startswith("mutable latest") and "versions.lock" in rel:
                        continue
                    errors.append(f"{label} in {rel}")

    if errors:
        print("REPOSITORY POLICY FAIL")
        for e in sorted(set(errors)):
            print(f" - {e}")
        return 1
    print("REPOSITORY POLICY PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
