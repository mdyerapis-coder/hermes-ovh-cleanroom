from pathlib import Path
import subprocess
import os
import json

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "hps" / "lib" / "hps_core.py"


def test_hps_plan():
    env = os.environ.copy()
    env["HPS_ALLOW_NON_CLEANROOM"] = "1"
    env["HPS_TEST_MODE"] = "1"
    env["HERMES_REPO"] = str(ROOT)
    env["HPS_STATE_DIR"] = str(ROOT / "evidence" / "hps" / "test-state")
    r = subprocess.run(
        ["python3", str(CORE), "plan", "-e", "cleanroom"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "plan_digest" in r.stdout


def test_hps_bash_plan_wrapper():
    env = os.environ.copy()
    env["HPS_ALLOW_NON_CLEANROOM"] = "1"
    env["HPS_TEST_MODE"] = "1"
    env["HERMES_REPO"] = str(ROOT)
    env["HPS_STATE_DIR"] = str(ROOT / "evidence" / "hps" / "test-state")
    r = subprocess.run(
        ["bash", str(ROOT / "hps/bin/hps"), "plan", "-e", "cleanroom"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout


def test_wrong_host_production_protect():
    env = os.environ.copy()
    env["HPS_ALLOW_NON_CLEANROOM"] = "1"
    env["HPS_TEST_MODE"] = "1"
    env["HERMES_REPO"] = str(ROOT)
    env["HPS_STATE_DIR"] = str(ROOT / "evidence" / "hps" / "test-state")
    # disarm
    subprocess.run(
        ["python3", str(CORE), "cutover", "disarm"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    r = subprocess.run(
        ["python3", str(CORE), "apply", "-e", "production", "--host", "hermes-station-1"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert "BLOCKED" in (r.stderr + r.stdout)
