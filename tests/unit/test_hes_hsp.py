from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def test_hes_status_banner():
    r = subprocess.run(["bash", str(ROOT / "hes/bin/hes"), "status"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0
    assert "HERMES OVH CLEANROOM" in r.stdout
    assert "HADA_RUNTIME=NOT_DEPLOYED" in r.stdout

def test_hes_hada_truthful():
    r = subprocess.run(["bash", str(ROOT / "hes/bin/hes"), "hada"], cwd=ROOT, capture_output=True, text=True)
    assert "NOT_DEPLOYED" in r.stdout

def test_hsp_status():
    r = subprocess.run(["bash", str(ROOT / "hsp/bin/hsp"), "status"], cwd=ROOT, capture_output=True, text=True)
    # may exit 2 if required secrets missing in CI — still should not print secret values
    assert "HSP_STATUS" in r.stdout or "HSP_" in r.stdout
    assert "sk-" not in r.stdout
