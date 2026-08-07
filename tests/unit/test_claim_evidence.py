from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

def test_claim_evidence_validates():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/ci/claim-evidence-validate.py")], cwd=ROOT)
    assert r.returncode == 0
