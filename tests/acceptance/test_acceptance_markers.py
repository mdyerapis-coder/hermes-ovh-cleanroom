from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_bootstrap_auditor_preserved():
    text = (ROOT / ".github/workflows/bootstrap-audit.yml").read_text()
    assert "BOOTSTRAP-GATE" in text

def test_audit_gate_workflow_present():
    text = (ROOT / ".github/workflows/pr-audit.yml").read_text()
    assert "AUDIT-GATE" in text
    assert "claim-evidence-validation" in text

def test_no_admin_merge_in_ops():
    # ops scripts must not teach admin bypass for implementation merges
    for path in (ROOT / "ops").glob("*.sh"):
        text = path.read_text()
        assert "--admin" not in text or "never" in text.lower()
