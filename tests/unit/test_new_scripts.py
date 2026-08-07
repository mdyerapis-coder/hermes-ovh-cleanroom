from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parents[2]

def test_host_and_runtime_scripts_exist():
    for rel in [
        "scripts/host-bootstrap.sh",
        "scripts/install-hermes-runtime.sh",
        "scripts/check-listeners.sh",
        "scripts/reboot-test.sh",
        "scripts/post-reboot-verify.sh",
        "scripts/chaos-recovery-test.sh",
        "scripts/ci/baseline-preservation.py",
    ]:
        assert (ROOT / rel).is_file()

def test_baseline_preservation_pre_baseline():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/ci/baseline-preservation.py")], cwd=ROOT)
    assert r.returncode == 0
