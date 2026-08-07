from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_required_scripts():
    for rel in [
        "scripts/fault-log.sh",
        "scripts/preflight.sh",
        "scripts/validate-config.sh",
        "scripts/backup.sh",
        "scripts/restore-test.sh",
        "scripts/deploy.sh",
        "scripts/healthcheck.sh",
        "scripts/acceptance.sh",
        "scripts/rollback.sh",
    ]:
        p = ROOT / rel
        assert p.is_file(), rel
        assert p.stat().st_mode & 0o111, f"{rel} not executable"
