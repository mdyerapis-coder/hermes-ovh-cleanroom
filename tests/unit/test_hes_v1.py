"""HES v1 operator surface tests."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HES = ROOT / "hes" / "bin" / "hes"


def run_hes(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = os.environ.copy()
    e["HPS_ALLOW_NON_CLEANROOM"] = "1"
    e["HPS_TEST_MODE"] = "1"
    e["HERMES_REPO"] = str(ROOT)
    e["HES_COLOR"] = "never"
    e["HPS_STATE_DIR"] = str(ROOT / "evidence" / "hps" / "test-state")
    if env:
        e.update(env)
    return subprocess.run(
        ["bash", str(HES), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=e,
    )


def test_status_banner_unambiguous_environment():
    r = run_hes(["status"])
    assert r.returncode == 0, r.stderr + r.stdout
    assert "HERMES OPERATOR SHELL" in r.stdout or "HERMES OVH" in r.stdout
    assert "environment:" in r.stdout
    assert "target_host:" in r.stdout
    assert "HADA_RUNTIME=NOT_DEPLOYED" in r.stdout
    assert "TELEGRAM_STATE=READY_FOR_EXCLUSIVE_CUTOVER" in r.stdout


def test_hada_truthful():
    r = run_hes(["hada"])
    assert r.returncode == 0
    assert "HADA_RUNTIME=NOT_DEPLOYED" in r.stdout


def test_help_lists_required_commands():
    r = run_hes(["help"])
    assert r.returncode == 0
    required = [
        "status",
        "health",
        "hosts",
        "services",
        "releases",
        "deploy",
        "rollback",
        "backup",
        "restore",
        "drift",
        "faults",
        "repairs",
        "audit",
        "github",
        "secrets",
        "cutover",
        "hada",
        "help",
    ]
    for cmd in required:
        assert cmd in r.stdout, f"missing {cmd} in help"


def test_hosts_delegates_to_hps():
    r = run_hes(["hosts"])
    assert r.returncode == 0, r.stderr + r.stdout
    assert "hermes-ovh-cleanroom" in r.stdout


def test_cutover_status():
    r = run_hes(["cutover", "status"])
    assert r.returncode == 0, r.stderr + r.stdout
    assert "cutover_state" in r.stdout or "PREPARING" in r.stdout or "READY" in r.stdout


def test_baseline_inventory_and_recovery_still_work():
    r = run_hes(["inventory"])
    assert r.returncode == 0
    assert "services.yaml" in r.stdout or "hermes-agent" in r.stdout
    r2 = run_hes(["recovery"])
    assert r2.returncode == 0


def test_audit_shows_markers():
    r = run_hes(["audit"])
    assert r.returncode == 0
    assert "AUTONOMY_DONE" in r.stdout
