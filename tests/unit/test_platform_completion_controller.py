from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_platform_controller_has_separate_completion_marker():
    text = read("ops/platform-controller.sh")
    assert 'DONE_FILE="$REPO/evidence/control/PLATFORM_COMPLETION.json"' in text
    assert 'BASELINE_FILE="$REPO/evidence/control/AUTONOMY_DONE.json"' in text
    assert "COMPLETE_PRODUCTION" in text
    assert "COMPLETE_HPS_HES_READY_FOR_CUTOVER" in text


def test_platform_controller_uses_new_then_resume_session_semantics():
    text = read("ops/platform-controller.sh")
    assert '--session-id "$SESSION_ID"' in text
    assert '--resume "$SESSION_ID"' in text
    assert 'MODE="new"' in text
    assert 'MODE="resume"' in text
    assert "already running" in text


def test_platform_controller_requires_verified_cleanroom_baseline():
    text = read("ops/platform-controller.sh")
    assert "validate_baseline" in text
    assert 'd.get("evidence_verified")' in text
    assert "COMPLETE_READY_FOR_EXCLUSIVE_CUTOVER" in text


def test_complete_production_requires_core_proof_fields():
    text = read("ops/platform-controller.sh")
    for field in (
        "HPS_V1",
        "HES_V1",
        "HPS_HES_INTEGRATION",
        "Hermes_production_host",
        "Telegram_exclusive",
        "Telegram_live_e2e",
        "rollback_available",
        "production_baseline_created",
    ):
        assert field in text


def test_part_100_is_authoritative_and_registered():
    manifest = read("runbook/RUNBOOK-MANIFEST.md")
    agents = read("AGENTS.md")
    assert "runbook/part-100-hps-hes-platform-completion.md" in manifest
    assert "runbook/part-100-hps-hes-platform-completion.md" in agents
    assert "PLATFORM_COMPLETION.json" in manifest
    assert "PLATFORM_COMPLETION.json" in agents


def test_launch_requires_dual_gate_protection_and_clean_main():
    text = read("ops/launch-platform-autonomy.sh")
    assert '"BOOTSTRAP-GATE", "AUDIT-GATE"' in text
    assert 'git pull --ff-only origin main' in text
    assert 'git status --porcelain' in text
    assert "DUAL_GATE_PROTECTION=PASS" in text


def test_platform_prompt_preserves_telegram_exclusivity_and_hps_authority():
    text = read("ops/PLATFORM_AUTONOMY_PROMPT.txt")
    assert "HPS is the only infrastructure/runtime mutation authority" in text
    assert "Never run two production Telegram pollers" in text
    assert "The old AUTONOMY_DONE.json is baseline only" in text
