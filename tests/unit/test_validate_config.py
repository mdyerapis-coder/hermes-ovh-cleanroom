from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

def test_validate_config_passes():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/ci/validate-config.py")], cwd=ROOT)
    assert r.returncode == 0

def test_repository_policy_passes():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/ci/repository-policy.py")], cwd=ROOT)
    assert r.returncode == 0

def test_version_file_exists():
    assert (ROOT / "VERSION").read_text().strip()

def test_services_honesty():
    text = (ROOT / "config/services.yaml").read_text()
    assert "NOT_DEPLOYED" in text
    assert "READY_FOR_EXCLUSIVE_CUTOVER" in text
