from pathlib import Path
import subprocess
import os

ROOT = Path(__file__).resolve().parents[2]

def test_hps_plan():
    env = os.environ.copy()
    env["HPS_ALLOW_NON_CLEANROOM"] = "1"
    r = subprocess.run(["bash", str(ROOT / "hps/bin/hps"), "plan"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
