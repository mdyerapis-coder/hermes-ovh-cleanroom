"""HPS v1 unit tests — plan digest, target protection, cutover transitions."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HPS = ROOT / "hps" / "bin" / "hps"
CORE = ROOT / "hps" / "lib" / "hps_core.py"


def run_hps(args: list[str], env: dict | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    e = os.environ.copy()
    e["HPS_ALLOW_NON_CLEANROOM"] = "1"
    e["HPS_TEST_MODE"] = "1"
    e["HERMES_REPO"] = str(ROOT)
    # Isolate state in tmp under repo evidence for tests
    state = ROOT / "evidence" / "hps" / "test-state"
    state.mkdir(parents=True, exist_ok=True)
    e["HPS_STATE_DIR"] = str(state)
    if env:
        e.update(env)
    return subprocess.run(
        ["python3", str(CORE), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=e,
        check=check,
    )


def test_hps_help_via_bash():
    r = subprocess.run(["bash", str(HPS), "help"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0
    assert "plan" in r.stdout
    assert "cutover" in r.stdout


def test_inventory_lists_cleanroom_and_production():
    r = run_hps(["inventory"])
    assert r.returncode == 0, r.stderr + r.stdout
    assert "hermes-ovh-cleanroom" in r.stdout
    assert "hermes-station-1" in r.stdout


def test_plan_has_digest_and_required_fields():
    r = run_hps(["plan", "-e", "cleanroom"])
    assert r.returncode == 0, r.stderr + r.stdout
    assert "plan_id" in r.stdout
    assert "plan_digest" in r.stdout
    # load latest plan from state
    state = ROOT / "evidence" / "hps" / "test-state" / "plans"
    plans = sorted(state.glob("plan-*.json"))
    assert plans, "expected plan file"
    plan = json.loads(plans[-1].read_text(encoding="utf-8"))
    for key in (
        "target",
        "current_state",
        "desired_state",
        "affected_resources",
        "secret_references",
        "backup_required",
        "rollback_target",
        "risk",
        "acceptance_tests",
        "plan_digest",
        "plan_id",
    ):
        assert key in plan


def test_plan_digest_mismatch_blocks_apply(tmp_path, monkeypatch):
    r = run_hps(["plan", "-e", "cleanroom"])
    assert r.returncode == 0, r.stderr
    state = ROOT / "evidence" / "hps" / "test-state" / "plans"
    plans = sorted(state.glob("plan-*.json"))
    plan_path = plans[-1]
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["desired_state"]["git_sha"] = "deadbeef" * 5
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    r2 = run_hps(["apply", "-e", "cleanroom", "--plan-id", plan["plan_id"], "--allow-state-drift"])
    assert r2.returncode != 0
    assert "DIGEST_MISMATCH" in (r2.stderr + r2.stdout)


def test_production_apply_blocked_without_arm():
    # Ensure disarmed
    run_hps(["cutover", "disarm"])
    r = run_hps(["apply", "-e", "production", "--host", "hermes-station-1"])
    assert r.returncode != 0
    blob = r.stderr + r.stdout
    assert "BLOCKED_PRODUCTION_MUTATION" in blob or "BLOCKED" in blob


def test_cutover_illegal_transition_fails():
    run_hps(["cutover", "disarm"])
    # reset state by writing PREPARING
    state_path = ROOT / "evidence" / "hps" / "test-state" / "cutover-state.json"
    state_path.write_text(
        json.dumps({"state": "PREPARING", "history": [], "schema": "hps.cutover.v1"}),
        encoding="utf-8",
    )
    r = run_hps(["cutover", "transition", "OLD_FENCED"])
    assert r.returncode != 0
    assert "ILLEGAL_CUTOVER_TRANSITION" in (r.stderr + r.stdout)


def test_cutover_legal_path_preparing_to_ready():
    state_path = ROOT / "evidence" / "hps" / "test-state" / "cutover-state.json"
    state_path.write_text(
        json.dumps({"state": "PREPARING", "history": [], "schema": "hps.cutover.v1"}),
        encoding="utf-8",
    )
    r = run_hps(["cutover", "transition", "READY", "--reason", "unit-test"])
    assert r.returncode == 0, r.stderr + r.stdout
    st = json.loads(state_path.read_text(encoding="utf-8"))
    assert st["state"] == "READY"


def test_armed_requires_arm_file():
    state_path = ROOT / "evidence" / "hps" / "test-state" / "cutover-state.json"
    state_path.write_text(
        json.dumps({"state": "READY", "history": [], "schema": "hps.cutover.v1"}),
        encoding="utf-8",
    )
    run_hps(["cutover", "disarm"])
    r = run_hps(["cutover", "transition", "ARMED"])
    assert r.returncode != 0
    assert "ARM_REQUIRED" in (r.stderr + r.stdout)


def test_arm_then_armed_transition():
    state_path = ROOT / "evidence" / "hps" / "test-state" / "cutover-state.json"
    state_path.write_text(
        json.dumps({"state": "READY", "history": [], "schema": "hps.cutover.v1"}),
        encoding="utf-8",
    )
    r = run_hps(["cutover", "arm", "--ttl-seconds", "600"])
    assert r.returncode == 0, r.stderr + r.stdout
    r2 = run_hps(["cutover", "transition", "ARMED", "--reason", "test"])
    assert r2.returncode == 0, r2.stderr + r2.stdout
    st = json.loads(state_path.read_text(encoding="utf-8"))
    assert st["state"] == "ARMED"


def test_secrets_refs_no_values():
    r = run_hps(["secrets-refs"])
    assert r.returncode == 0, r.stderr
    assert "TELEGRAM_BOT_TOKEN" in r.stdout or "references" in r.stdout
    assert "sk-" not in r.stdout


def test_protect_production_reports_blocked():
    run_hps(["cutover", "disarm"])
    state_path = ROOT / "evidence" / "hps" / "test-state" / "cutover-state.json"
    state_path.write_text(
        json.dumps({"state": "PREPARING", "history": [], "schema": "hps.cutover.v1"}),
        encoding="utf-8",
    )
    r = run_hps(["protect", "-e", "production"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["mutation_allowed"] is False


def test_legal_transitions_table_complete():
    sys.path.insert(0, str(ROOT / "hps" / "lib"))
    import hps_core  # type: ignore

    for st in hps_core.CUTOVER_STATES:
        assert st in hps_core.LEGAL_TRANSITIONS
    # known illegal
    assert "CUTOVER_COMPLETE" not in hps_core.LEGAL_TRANSITIONS["PREPARING"]
    assert "ARMED" in hps_core.LEGAL_TRANSITIONS["READY"]
