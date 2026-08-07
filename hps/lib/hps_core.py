#!/usr/bin/env python3
"""HPS v1 core — sole infrastructure/runtime mutation authority for Hermes clean-room."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

def find_root() -> Path:
    env = os.environ.get("HERMES_REPO")
    if env:
        return Path(env).resolve()
    # hps/lib/hps_core.py -> repo root
    return Path(__file__).resolve().parents[2]


ROOT = find_root()
INVENTORY_PATH = ROOT / "hps" / "inventory" / "hosts.yaml"
EVIDENCE_HPS = ROOT / "evidence" / "hps"
STATE_DIR = Path(os.environ.get("HPS_STATE_DIR", "/var/lib/hermes-hps"))
# Fall back to repo-local state when system state dir is unavailable (CI/dev)
if not STATE_DIR.exists():
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_DIR.chmod(0o700)
    except OSError:
        STATE_DIR = ROOT / "evidence" / "hps" / "runtime-state"
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_DIR.chmod(0o700)

PLANS_DIR = STATE_DIR / "plans"
PLANS_DIR.mkdir(parents=True, exist_ok=True)
CUTOVER_STATE_PATH = STATE_DIR / "cutover-state.json"
ARM_STATE_PATH = STATE_DIR / "arm.json"  # never committed to git
RELEASE_ROOT = Path(os.environ.get("HERMES_RELEASE_ROOT", "/opt/hermes-cleanroom"))

CUTOVER_STATES = {
    "PREPARING",
    "READY",
    "ARMED",
    "OLD_FENCED",
    "NEW_STARTING",
    "VERIFYING",
    "CUTOVER_COMPLETE",
    "ROLLBACK_STARTING",
    "ROLLED_BACK",
    "BLOCKED",
    "FAILED",
}

LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "PREPARING": {"READY", "BLOCKED", "FAILED"},
    "READY": {"ARMED", "BLOCKED", "FAILED", "PREPARING"},
    "ARMED": {"OLD_FENCED", "BLOCKED", "FAILED", "READY"},
    "OLD_FENCED": {"NEW_STARTING", "ROLLBACK_STARTING", "FAILED", "BLOCKED"},
    "NEW_STARTING": {"VERIFYING", "ROLLBACK_STARTING", "FAILED"},
    "VERIFYING": {"CUTOVER_COMPLETE", "ROLLBACK_STARTING", "FAILED"},
    "CUTOVER_COMPLETE": {"ROLLBACK_STARTING"},  # post-complete emergency only
    "ROLLBACK_STARTING": {"ROLLED_BACK", "FAILED"},
    "ROLLED_BACK": {"PREPARING", "READY"},
    "BLOCKED": {"PREPARING", "READY"},
    "FAILED": {"PREPARING", "ROLLBACK_STARTING"},
}

DEFAULT_CUTOVER = "PREPARING"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cmd(
    args: list[str],
    *,
    check: bool = False,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
        check=check,
        env=env,
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def append_fault(symptom: str, classification: str = "hps", severity: str = "error") -> str:
    """Append to canonical fault ledger.

    Expected fail-closed safety denials (tests / protect gates) use severity
    ``warning`` and are skipped when HPS_TEST_MODE=1 or state dir is test-state,
    so unit tests do not create unresolved critical ledger noise.
    """
    state_s = str(STATE_DIR)
    if os.environ.get("HPS_TEST_MODE") == "1" or "test-state" in state_s:
        return "FAULT_LOG_SKIPPED_TEST_MODE"
    # Fail-closed protection proofs are operationally important but not
    # unresolved outages — log as warning so AUDIT-GATE does not treat them
    # as open criticals.
    if classification == "safety" and severity == "critical":
        severity = "warning"
    script = ROOT / "scripts" / "fault-log.sh"
    if script.is_file():
        r = run_cmd(
            ["bash", str(script), "hps", symptom, classification, severity, "1", "hps", "ok", symptom]
        )
        return (r.stdout or "").strip() or "FAULT_LOG_UNKNOWN"
    return "FAULT_LOG_UNAVAILABLE"


def git_sha() -> str:
    r = run_cmd(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    if r.returncode == 0:
        return r.stdout.strip()
    return "unknown"


def load_inventory() -> dict[str, Any]:
    text = INVENTORY_PATH.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError("inventory root must be mapping")
        return data
    except ImportError:
        # Minimal YAML subset parser for our inventory shape
        return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Fallback parser for inventory without PyYAML (hosts map only)."""
    hosts: dict[str, Any] = {}
    environments: dict[str, Any] = {}
    section = None
    current_host = None
    current_env = None
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if re.match(r"^hosts:\s*$", raw):
            section = "hosts"
            current_host = None
            continue
        if re.match(r"^environments:\s*$", raw):
            section = "environments"
            current_env = None
            continue
        if section == "hosts":
            m = re.match(r"^  ([A-Za-z0-9._-]+):\s*$", raw)
            if m:
                current_host = m.group(1)
                hosts[current_host] = {}
                continue
            if current_host:
                km = re.match(r"^    ([a-z_]+):\s*(.+)\s*$", raw)
                if km:
                    key, val = km.group(1), km.group(2).strip()
                    if val.startswith("[") and val.endswith("]"):
                        items = [x.strip() for x in val[1:-1].split(",") if x.strip()]
                        hosts[current_host][key] = items
                    elif val in ("true", "false"):
                        hosts[current_host][key] = val == "true"
                    else:
                        hosts[current_host][key] = val
        elif section == "environments":
            m = re.match(r"^  ([A-Za-z0-9._-]+):\s*$", raw)
            if m:
                current_env = m.group(1)
                environments[current_env] = {}
                continue
            if current_env:
                km = re.match(r"^    ([a-z_]+):\s*(.+)\s*$", raw)
                if km:
                    environments[current_env][km.group(1)] = km.group(2).strip()
    return {"hosts": hosts, "environments": environments}


# ---------------------------------------------------------------------------
# Target resolution and identity
# ---------------------------------------------------------------------------

@dataclass
class Target:
    environment: str
    host_id: str
    host: dict[str, Any]
    mutation_policy: str


def resolve_target(environment: str | None = None, host_id: str | None = None) -> Target:
    inv = load_inventory()
    hosts = inv.get("hosts") or {}
    envs = inv.get("environments") or {}
    env = environment or os.environ.get("HPS_ENVIRONMENT") or "cleanroom"
    if env not in envs and env not in ("cleanroom", "production", "rollback", "test"):
        raise SystemExit(f"BLOCKED_UNKNOWN_ENVIRONMENT: {env}")
    env_meta = envs.get(env) or {}
    hid = host_id or os.environ.get("HPS_TARGET_HOST") or env_meta.get("default_host")
    if not hid or hid not in hosts:
        raise SystemExit(f"BLOCKED_UNKNOWN_HOST: {hid}")
    host = hosts[hid]
    policy = env_meta.get("mutation_policy") or (
        "blocked_until_armed" if env in ("production", "rollback") else "allowed_with_plan"
    )
    return Target(environment=env, host_id=hid, host=host, mutation_policy=policy)


def observe_local_identity() -> dict[str, Any]:
    identity: dict[str, Any] = {
        "hostname": platform.node(),
        "machine_id": None,
        "tailscale_ipv4": None,
        "tailscale_name": None,
        "git_sha": git_sha(),
        "release_current": None,
        "observed_at": utc_now(),
    }
    mid = Path("/etc/machine-id")
    if mid.is_file():
        identity["machine_id"] = mid.read_text(encoding="utf-8").strip()
    if shutil.which("tailscale"):
        r = run_cmd(["tailscale", "ip", "-4"])
        if r.returncode == 0 and r.stdout.strip():
            identity["tailscale_ipv4"] = r.stdout.strip().splitlines()[0]
        r2 = run_cmd(["tailscale", "status", "--json"])
        if r2.returncode == 0:
            try:
                ts = json.loads(r2.stdout)
                self_node = ts.get("Self") or {}
                dns = self_node.get("DNSName") or ""
                identity["tailscale_name"] = dns.rstrip(".") if dns else None
            except json.JSONDecodeError:
                pass
    cur = RELEASE_ROOT / "current"
    if cur.is_symlink() or cur.exists():
        try:
            identity["release_current"] = str(cur.resolve())
        except OSError:
            identity["release_current"] = str(cur)
    return identity


def verify_target_identity(target: Target) -> dict[str, Any]:
    observed = observe_local_identity()
    expected_host = target.host.get("expected_hostname") or target.host_id
    ok = True
    reasons: list[str] = []
    # For non-local production targets, mutation is blocked; identity on this host is N/A for remote
    if target.environment in ("production", "rollback") and observed["hostname"] != expected_host:
        # Remote production ops are not performed from wrong host without arm+ssh — fail closed for mutation
        ok = False
        reasons.append(
            f"local_hostname={observed['hostname']} != expected={expected_host} "
            f"(remote production mutation requires armed cutover path)"
        )
    elif target.environment in ("cleanroom", "test"):
        if observed["hostname"] != expected_host and os.environ.get("HPS_ALLOW_NON_CLEANROOM") != "1":
            ok = False
            reasons.append(f"hostname mismatch: {observed['hostname']} != {expected_host}")
    result = {
        "ok": ok,
        "target": {
            "environment": target.environment,
            "host_id": target.host_id,
            "expected_hostname": expected_host,
        },
        "observed": observed,
        "reasons": reasons,
    }
    if not ok and os.environ.get("HPS_ALLOW_NON_CLEANROOM") != "1":
        result["disposition"] = "BLOCKED_TARGET_IDENTITY_UNVERIFIED"
    return result


def production_mutation_allowed(target: Target) -> tuple[bool, str]:
    if target.mutation_policy != "blocked_until_armed":
        return True, "policy_allows"
    if not ARM_STATE_PATH.is_file():
        return False, "no_local_arm_state"
    try:
        arm = read_json(ARM_STATE_PATH)
    except (OSError, json.JSONDecodeError):
        return False, "arm_state_unreadable"
    exp = arm.get("expires_at_unix")
    if not isinstance(exp, (int, float)) or time.time() > float(exp):
        return False, "arm_expired_or_invalid"
    if arm.get("environment") not in (target.environment, "production"):
        return False, "arm_environment_mismatch"
    if arm.get("host_id") not in (None, target.host_id):
        return False, "arm_host_mismatch"
    # Also require cutover ARMED or later for production mutations
    st = load_cutover_state().get("state")
    if st not in ("ARMED", "OLD_FENCED", "NEW_STARTING", "VERIFYING", "ROLLBACK_STARTING"):
        return False, f"cutover_state_not_armed:{st}"
    return True, "armed_valid"


def assert_mutation_allowed(target: Target, operation: str) -> None:
    if target.mutation_policy == "blocked_until_armed":
        allowed, reason = production_mutation_allowed(target)
        if not allowed:
            append_fault(
                f"production mutation blocked op={operation} reason={reason}",
                "safety",
                "critical",
            )
            raise SystemExit(
                f"BLOCKED_PRODUCTION_MUTATION: op={operation} reason={reason} "
                f"target={target.environment}/{target.host_id}"
            )
    ident = verify_target_identity(target)
    if not ident.get("ok") and os.environ.get("HPS_ALLOW_NON_CLEANROOM") != "1":
        if operation in ("apply", "rollback", "restore", "cutover-mutate"):
            raise SystemExit("BLOCKED_TARGET_IDENTITY_UNVERIFIED: " + "; ".join(ident.get("reasons") or []))


# ---------------------------------------------------------------------------
# Inventory / status
# ---------------------------------------------------------------------------

def cmd_inventory(args: argparse.Namespace) -> int:
    inv = load_inventory()
    identity = observe_local_identity()
    out = {
        "command": "inventory",
        "timestamp_utc": utc_now(),
        "git_sha": git_sha(),
        "local_identity": identity,
        "inventory": inv,
    }
    EVIDENCE_HPS.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_HPS / f"inventory-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(path, out)
    print(json.dumps(out, indent=2, sort_keys=True))
    print(f"evidence={path}")
    return 0


def cmd_target(args: argparse.Namespace) -> int:
    target = resolve_target(args.environment, args.host)
    ident = verify_target_identity(target)
    allowed, reason = production_mutation_allowed(target) if target.mutation_policy == "blocked_until_armed" else (True, "n/a")
    out = {
        "environment": target.environment,
        "host_id": target.host_id,
        "host": target.host,
        "mutation_policy": target.mutation_policy,
        "identity_check": ident,
        "production_mutation_allowed": allowed,
        "production_mutation_reason": reason,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if ident.get("ok") or os.environ.get("HPS_ALLOW_NON_CLEANROOM") == "1" else 70


# ---------------------------------------------------------------------------
# Plan / apply / verify
# ---------------------------------------------------------------------------

def current_state_digest(target: Target) -> str:
    identity = observe_local_identity()
    payload = {
        "host_id": target.host_id,
        "environment": target.environment,
        "hostname": identity.get("hostname"),
        "release_current": identity.get("release_current"),
        "git_sha": identity.get("git_sha"),
        "services_contract": (ROOT / "config" / "services.yaml").read_text(encoding="utf-8")
        if (ROOT / "config" / "services.yaml").is_file()
        else "",
        "ports_contract": (ROOT / "config" / "ports.yaml").read_text(encoding="utf-8")
        if (ROOT / "config" / "ports.yaml").is_file()
        else "",
    }
    return sha256_text(canonical_json(payload))


def secret_references() -> list[dict[str, Any]]:
    """HSP secret references only — names and presence, never values."""
    refs: list[dict[str, Any]] = []
    contract = ROOT / "config" / "secret-contract.yaml"
    if not contract.is_file():
        return refs
    text = contract.read_text(encoding="utf-8")
    secrets_dir = Path(os.environ.get("HSP_SECRETS_DIR", "/opt/hermes-cleanroom/shared/secrets-runtime"))
    name = None
    required = False
    for line in text.splitlines():
        m = re.match(r"^  ([A-Z][A-Z0-9_]+):\s*$", line)
        if m:
            if name:
                present = name in os.environ or (secrets_dir / name).is_file()
                refs.append(
                    {
                        "name": name,
                        "required": required,
                        "present": present,
                        "source": "hsp_reference",
                    }
                )
            name = m.group(1)
            required = False
            continue
        if name and re.match(r"^    required:\s*(true|false)\s*$", line):
            required = line.strip().split(":", 1)[1].strip() == "true"
    if name:
        present = name in os.environ or (secrets_dir / name).is_file()
        refs.append(
            {"name": name, "required": required, "present": present, "source": "hsp_reference"}
        )
    return refs


def build_plan(target: Target) -> dict[str, Any]:
    sha = git_sha()
    identity = observe_local_identity()
    state_digest = current_state_digest(target)
    plan: dict[str, Any] = {
        "schema": "hps.plan.v1",
        "created_at": utc_now(),
        "git_sha": sha,
        "target": {
            "environment": target.environment,
            "host_id": target.host_id,
            "expected_hostname": target.host.get("expected_hostname"),
            "release_root": target.host.get("release_root"),
        },
        "current_state": {
            "identity": identity,
            "state_digest": state_digest,
            "release_current": identity.get("release_current"),
        },
        "desired_state": {
            "git_sha": sha,
            "release_path": f"{RELEASE_ROOT}/releases/{sha}",
            "services": ["hermes-agent", "hermes-gateway", "hsp", "hps", "hes"],
            "telegram_polling": "disabled_until_exclusive_cutover",
            "hada_runtime": "NOT_DEPLOYED",
        },
        "affected_resources": [
            str(RELEASE_ROOT / "releases" / sha),
            str(RELEASE_ROOT / "current"),
            str(RELEASE_ROOT / "previous"),
            "systemd:hermes-agent.service",
            "systemd:hermes-gateway.service",
        ],
        "secret_references": secret_references(),
        "backup_required": True,
        "rollback_target": identity.get("release_current"),
        "risk": "medium" if target.environment == "cleanroom" else "critical",
        "acceptance_tests": [
            "scripts/healthcheck.sh",
            "scripts/check-listeners.sh",
            "config-contract-validation",
        ],
        "phases": [
            "identity_verify",
            "backup",
            "accounts_dirs",
            "deploy_release",
            "verify",
        ],
        "production_protection": target.mutation_policy,
    }
    plan["plan_digest"] = sha256_text(canonical_json({k: v for k, v in plan.items() if k != "plan_digest"}))
    plan_id = f"plan-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{plan['plan_digest'][:12]}"
    plan["plan_id"] = plan_id
    return plan


def cmd_plan(args: argparse.Namespace) -> int:
    target = resolve_target(args.environment, args.host)
    # Plan is always allowed (read-only planning); production plans mark protection
    plan = build_plan(target)
    plan_path = PLANS_DIR / f"{plan['plan_id']}.json"
    write_json(plan_path, plan)
    # Also mirror under evidence for audit (no secrets)
    EVIDENCE_HPS.mkdir(parents=True, exist_ok=True)
    evidence_path = EVIDENCE_HPS / f"{plan['plan_id']}.json"
    write_json(evidence_path, plan)
    print(json.dumps({"plan_id": plan["plan_id"], "plan_digest": plan["plan_digest"], "path": str(plan_path)}, indent=2))
    print(f"plan_written={plan_path}")
    return 0


def load_plan(plan_id: str | None, plan_digest: str | None) -> dict[str, Any]:
    if not plan_id:
        # latest plan
        plans = sorted(PLANS_DIR.glob("plan-*.json"))
        if not plans:
            # try evidence
            plans = sorted(EVIDENCE_HPS.glob("plan-*.json"))
        if not plans:
            raise SystemExit("BLOCKED_NO_PLAN: run hps plan first")
        plan = read_json(plans[-1])
    else:
        path = PLANS_DIR / f"{plan_id}.json"
        if not path.is_file():
            path = EVIDENCE_HPS / f"{plan_id}.json"
        if not path.is_file():
            raise SystemExit(f"BLOCKED_PLAN_NOT_FOUND: {plan_id}")
        plan = read_json(path)
    stored_digest = plan.get("plan_digest")
    # plan_id is added after digest in builder — recompute without plan_id and plan_digest
    body = {k: v for k, v in plan.items() if k not in ("plan_digest", "plan_id")}
    recomputed = sha256_text(canonical_json(body))
    if stored_digest != recomputed:
        raise SystemExit(f"BLOCKED_PLAN_DIGEST_MISMATCH: stored={stored_digest} recomputed={recomputed}")
    if plan_digest and plan_digest != stored_digest:
        raise SystemExit(f"BLOCKED_PLAN_DIGEST_ARG_MISMATCH: arg={plan_digest} stored={stored_digest}")
    return plan


def cmd_apply(args: argparse.Namespace) -> int:
    target = resolve_target(args.environment, args.host)
    assert_mutation_allowed(target, "apply")
    plan = load_plan(args.plan_id, args.plan_digest)
    # Re-validate target matches plan
    if plan["target"]["environment"] != target.environment or plan["target"]["host_id"] != target.host_id:
        raise SystemExit("BLOCKED_PLAN_TARGET_MISMATCH")
    # State digest must be unchanged unless --force-state (never for production)
    now_digest = current_state_digest(target)
    if now_digest != plan["current_state"]["state_digest"]:
        if target.environment in ("production", "rollback"):
            raise SystemExit("BLOCKED_STATE_DIGEST_CHANGED: refuse production apply on drifted state")
        if os.environ.get("HPS_ALLOW_STATE_DRIFT") != "1" and not args.allow_state_drift:
            raise SystemExit(
                f"BLOCKED_STATE_DIGEST_CHANGED: plan={plan['current_state']['state_digest'][:12]} "
                f"now={now_digest[:12]} (re-plan or pass --allow-state-drift for cleanroom only)"
            )

    log_lines: list[str] = []
    def log(msg: str) -> None:
        line = f"{utc_now()} {msg}"
        log_lines.append(line)
        print(f"[hps apply] {msg}")

    log(f"apply start plan_id={plan['plan_id']} sha={plan['git_sha']}")

    # Backup first when required
    if plan.get("backup_required"):
        r = run_cmd(["bash", str(ROOT / "scripts" / "backup.sh")])
        log(f"backup exit={r.returncode}")
        if r.returncode != 0:
            append_fault("backup failed during apply", "backup", "error")
            raise SystemExit("APPLY_FAIL_BACKUP")

    # Deploy via existing deploy script (cleanroom only path)
    if target.environment in ("cleanroom", "test"):
        if (ROOT / "scripts" / "host-bootstrap.sh").is_file():
            run_cmd(["bash", str(ROOT / "scripts" / "host-bootstrap.sh")])
        r = run_cmd(["bash", str(ROOT / "scripts" / "deploy.sh"), plan["git_sha"]])
        log(f"deploy exit={r.returncode}")
        if r.returncode != 0:
            log("deploy failed; attempting rollback")
            run_cmd(["bash", str(ROOT / "scripts" / "rollback.sh")])
            append_fault("deploy failed; rollback attempted", "deploy", "error")
            raise SystemExit("APPLY_FAIL_DEPLOY")
    else:
        raise SystemExit("BLOCKED_PRODUCTION_APPLY_PATH: use cutover workflow for production")

    # Verify
    r = run_cmd(["bash", str(ROOT / "scripts" / "healthcheck.sh")])
    log(f"healthcheck exit={r.returncode}")
    if r.returncode != 0:
        log("acceptance failed; automatic rollback")
        run_cmd(["bash", str(ROOT / "scripts" / "rollback.sh")])
        append_fault("post-apply healthcheck failed; rolled back", "acceptance", "critical")
        raise SystemExit("APPLY_FAIL_VERIFY_ROLLED_BACK")

    result = {
        "status": "APPLY_OK",
        "plan_id": plan["plan_id"],
        "plan_digest": plan["plan_digest"],
        "git_sha": plan["git_sha"],
        "target": plan["target"],
        "timestamp_utc": utc_now(),
        "log": log_lines,
    }
    out = EVIDENCE_HPS / f"apply-{plan['plan_id']}.json"
    write_json(out, result)
    print(json.dumps({"status": "APPLY_OK", "evidence": str(out)}, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    target = resolve_target(args.environment, args.host)
    results: dict[str, Any] = {
        "command": "verify",
        "timestamp_utc": utc_now(),
        "target": {"environment": target.environment, "host_id": target.host_id},
        "checks": {},
    }
    r = run_cmd(["bash", str(ROOT / "scripts" / "healthcheck.sh")])
    results["checks"]["healthcheck"] = {
        "exit_code": r.returncode,
        "stdout_tail": (r.stdout or "")[-2000:],
    }
    r2 = run_cmd(["bash", str(ROOT / "scripts" / "check-listeners.sh")])
    results["checks"]["listeners"] = {"exit_code": r2.returncode}
    r3 = run_cmd(["python3", str(ROOT / "scripts" / "ci" / "validate-config.py")])
    results["checks"]["config_contract"] = {"exit_code": r3.returncode}
    ok = all(c.get("exit_code") == 0 for c in results["checks"].values())
    results["status"] = "VERIFY_OK" if ok else "VERIFY_FAIL"
    path = EVIDENCE_HPS / f"verify-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(path, results)
    print(json.dumps({"status": results["status"], "evidence": str(path)}, indent=2))
    return 0 if ok else 1


def cmd_preflight(args: argparse.Namespace) -> int:
    target = resolve_target(args.environment, args.host)
    out: dict[str, Any] = {"target": {"environment": target.environment, "host_id": target.host_id}}
    script = ROOT / "scripts" / "preflight.sh"
    if script.is_file():
        r = run_cmd(["bash", str(script)])
        out["preflight_exit"] = r.returncode
        out["stdout_tail"] = (r.stdout or "")[-2000:]
        print(json.dumps(out, indent=2))
        return r.returncode
    out["preflight_exit"] = 0
    out["note"] = "preflight script optional; identity only"
    out["identity"] = verify_target_identity(target)
    print(json.dumps(out, indent=2))
    return 0 if out["identity"].get("ok") or os.environ.get("HPS_ALLOW_NON_CLEANROOM") == "1" else 70


def cmd_resume(args: argparse.Namespace) -> int:
    print("resume: re-running verify then reporting; apply is idempotent via deploy.sh")
    return cmd_verify(args)


# ---------------------------------------------------------------------------
# Rollback / release / backup / restore / drift
# ---------------------------------------------------------------------------

def cmd_rollback(args: argparse.Namespace) -> int:
    target = resolve_target(args.environment, args.host)
    assert_mutation_allowed(target, "rollback")
    if target.environment not in ("cleanroom", "test"):
        raise SystemExit("BLOCKED_PRODUCTION_ROLLBACK_PATH: use cutover rollback workflow")
    r = run_cmd(["bash", str(ROOT / "scripts" / "rollback.sh")])
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        append_fault("rollback failed", "recovery", "error")
        return r.returncode
    result = {
        "status": "ROLLBACK_OK" if r.returncode == 0 else "ROLLBACK_FAIL",
        "timestamp_utc": utc_now(),
        "stdout": r.stdout,
        "target": {"environment": target.environment, "host_id": target.host_id},
    }
    path = EVIDENCE_HPS / f"rollback-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(path, result)
    print(f"evidence={path}")
    return r.returncode


def cmd_releases(args: argparse.Namespace) -> int:
    releases_dir = RELEASE_ROOT / "releases"
    items = []
    if releases_dir.is_dir():
        for p in sorted(releases_dir.iterdir()):
            if p.is_dir():
                items.append(p.name)
    current = None
    previous = None
    if (RELEASE_ROOT / "current").exists():
        try:
            current = str((RELEASE_ROOT / "current").resolve())
        except OSError:
            current = str(RELEASE_ROOT / "current")
    if (RELEASE_ROOT / "previous").exists():
        try:
            previous = str((RELEASE_ROOT / "previous").resolve())
        except OSError:
            previous = str(RELEASE_ROOT / "previous")
    out = {
        "release_root": str(RELEASE_ROOT),
        "releases": items,
        "current": current,
        "previous": previous,
        "git_sha": git_sha(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    r = run_cmd(["bash", str(ROOT / "scripts" / "backup.sh")])
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return r.returncode
    path = EVIDENCE_HPS / f"backup-cmd-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(
        path,
        {"status": "BACKUP_OK", "timestamp_utc": utc_now(), "stdout": r.stdout[-2000:]},
    )
    print(f"evidence={path}")
    return 0


def cmd_restore_test(args: argparse.Namespace) -> int:
    r = run_cmd(["bash", str(ROOT / "scripts" / "restore-test.sh")])
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
    path = EVIDENCE_HPS / f"restore-test-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(
        path,
        {
            "status": "RESTORE_TEST_OK" if r.returncode == 0 else "RESTORE_TEST_FAIL",
            "timestamp_utc": utc_now(),
            "exit_code": r.returncode,
            "stdout_tail": (r.stdout or "")[-2000:],
        },
    )
    print(f"evidence={path}")
    return r.returncode


def cmd_restore(args: argparse.Namespace) -> int:
    """Controlled restore into isolated workdir (non-destructive) unless --apply-live on cleanroom."""
    target = resolve_target(args.environment, args.host)
    if args.apply_live:
        assert_mutation_allowed(target, "restore")
        raise SystemExit(
            "BLOCKED_LIVE_RESTORE: live restore must use restore-test proven backup and explicit runbook; "
            "use restore-test for validation"
        )
    return cmd_restore_test(args)


def cmd_drift(args: argparse.Namespace) -> int:
    target = resolve_target(args.environment, args.host)
    identity = observe_local_identity()
    desired_sha = git_sha()
    current_path = identity.get("release_current") or ""
    current_sha = Path(current_path).name if current_path else None
    contract_ok = run_cmd(["python3", str(ROOT / "scripts" / "ci" / "validate-config.py")]).returncode == 0
    drifts: list[str] = []
    if current_sha and current_sha != desired_sha and current_sha != "unknown":
        # release path basename should be full sha
        if len(current_sha) >= 7 and not desired_sha.startswith(current_sha) and current_sha != desired_sha:
            drifts.append(f"release_sha_mismatch: deployed={current_sha} repo={desired_sha}")
    if not contract_ok:
        drifts.append("config_contract_invalid")
    # service file presence
    for unit in ("hermes-agent.service", "hermes-gateway.service"):
        unit_path = Path("/etc/systemd/system") / unit
        if not unit_path.is_file() and target.environment in ("cleanroom", "test"):
            # may still be ok if not installed yet
            if os.environ.get("HPS_STRICT_DRIFT") == "1":
                drifts.append(f"missing_unit:{unit}")
    out = {
        "status": "DRIFT_DETECTED" if drifts else "DRIFT_NONE",
        "timestamp_utc": utc_now(),
        "target": {"environment": target.environment, "host_id": target.host_id},
        "desired_git_sha": desired_sha,
        "deployed_release": current_path,
        "drifts": drifts,
        "state_digest": current_state_digest(target),
    }
    path = EVIDENCE_HPS / f"drift-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(path, out)
    print(json.dumps(out, indent=2, sort_keys=True))
    print(f"evidence={path}")
    return 0 if not drifts else 2


def cmd_secrets_refs(args: argparse.Namespace) -> int:
    refs = secret_references()
    out = {
        "command": "secrets-refs",
        "note": "names and presence only; values never disclosed",
        "references": refs,
        "timestamp_utc": utc_now(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    # Ensure no secret-like values leaked (heuristic)
    blob = json.dumps(out)
    if re.search(r"sk-[A-Za-z0-9]{10,}", blob):
        raise SystemExit("SAFETY: secret-like value detected in secrets-refs output")
    return 0


# ---------------------------------------------------------------------------
# Cutover state machine
# ---------------------------------------------------------------------------

def load_cutover_state() -> dict[str, Any]:
    if CUTOVER_STATE_PATH.is_file():
        try:
            return read_json(CUTOVER_STATE_PATH)
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "state": DEFAULT_CUTOVER,
        "updated_at": None,
        "history": [],
        "schema": "hps.cutover.v1",
    }


def save_cutover_state(state: dict[str, Any]) -> None:
    write_json(CUTOVER_STATE_PATH, state)
    # Mirror non-sensitive state to evidence
    EVIDENCE_HPS.mkdir(parents=True, exist_ok=True)
    mirror = {
        "state": state.get("state"),
        "updated_at": state.get("updated_at"),
        "history": state.get("history", [])[-20:],
        "schema": state.get("schema"),
        "note": "arm tokens never mirrored",
    }
    write_json(EVIDENCE_HPS / "cutover-state-mirror.json", mirror)


def cmd_cutover_status(args: argparse.Namespace) -> int:
    st = load_cutover_state()
    arm_present = ARM_STATE_PATH.is_file()
    arm_valid = False
    arm_reason = "absent"
    if arm_present:
        try:
            arm = read_json(ARM_STATE_PATH)
            exp = arm.get("expires_at_unix")
            if isinstance(exp, (int, float)) and time.time() <= float(exp):
                arm_valid = True
                arm_reason = "valid"
            else:
                arm_reason = "expired"
        except (OSError, json.JSONDecodeError):
            arm_reason = "unreadable"
    out = {
        "cutover_state": st.get("state"),
        "updated_at": st.get("updated_at"),
        "history_tail": (st.get("history") or [])[-5:],
        "arm_present": arm_present,
        "arm_valid": arm_valid,
        "arm_reason": arm_reason,
        "legal_next": sorted(LEGAL_TRANSITIONS.get(st.get("state") or DEFAULT_CUTOVER, set())),
        "telegram_exclusivity": "NOT_PROVEN",
        "production_discovery": "READ_ONLY_UNTIL_ARMED",
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def cmd_cutover_transition(args: argparse.Namespace) -> int:
    new_state = args.to_state
    if new_state not in CUTOVER_STATES:
        raise SystemExit(f"BLOCKED_UNKNOWN_CUTOVER_STATE: {new_state}")
    st = load_cutover_state()
    cur = st.get("state") or DEFAULT_CUTOVER
    legal = LEGAL_TRANSITIONS.get(cur, set())
    if new_state not in legal:
        append_fault(
            f"illegal cutover transition {cur} -> {new_state}",
            "safety",
            "critical",
        )
        raise SystemExit(f"BLOCKED_ILLEGAL_CUTOVER_TRANSITION: {cur} -> {new_state}")

    # Gate: cannot enter ARMED without valid local arm file when requiring arm
    if new_state == "ARMED":
        if not args.dry_run:
            # Creating ARMED requires an existing valid arm transaction written out-of-band
            if not ARM_STATE_PATH.is_file():
                raise SystemExit(
                    "BLOCKED_ARM_REQUIRED: write local arm state (hps cutover arm) before ARMED"
                )
            arm = read_json(ARM_STATE_PATH)
            exp = arm.get("expires_at_unix")
            if not isinstance(exp, (int, float)) or time.time() > float(exp):
                raise SystemExit("BLOCKED_ARM_EXPIRED")

    # Gate: OLD_FENCED and beyond require production mutation authority
    if new_state in ("OLD_FENCED", "NEW_STARTING", "VERIFYING", "CUTOVER_COMPLETE"):
        target = resolve_target("production", None)
        if not args.dry_run:
            allowed, reason = production_mutation_allowed(target)
            # When transitioning TO OLD_FENCED from ARMED, arm+ARMED is enough
            if new_state == "OLD_FENCED":
                if st.get("state") != "ARMED":
                    raise SystemExit("BLOCKED: must be ARMED before OLD_FENCED")
            else:
                if not allowed and st.get("state") not in (
                    "ARMED",
                    "OLD_FENCED",
                    "NEW_STARTING",
                    "VERIFYING",
                ):
                    raise SystemExit(f"BLOCKED_PRODUCTION_MUTATION: {reason}")

    if args.dry_run:
        print(json.dumps({"dry_run": True, "from": cur, "to": new_state, "allowed": True}, indent=2))
        return 0

    st.setdefault("history", []).append(
        {"from": cur, "to": new_state, "at": utc_now(), "reason": args.reason or ""}
    )
    st["state"] = new_state
    st["updated_at"] = utc_now()
    save_cutover_state(st)
    print(json.dumps({"status": "TRANSITION_OK", "from": cur, "to": new_state}, indent=2))
    return 0


def cmd_cutover_arm(args: argparse.Namespace) -> int:
    """Create expiring local arm transaction — operational state, never git."""
    if args.ttl_seconds < 60 or args.ttl_seconds > 86400:
        raise SystemExit("BLOCKED_ARM_TTL: must be 60..86400 seconds")
    nonce = hashlib.sha256(os.urandom(32)).hexdigest()
    arm = {
        "schema": "hps.arm.v1",
        "created_at": utc_now(),
        "expires_at_unix": int(time.time()) + int(args.ttl_seconds),
        "environment": args.environment or "production",
        "host_id": args.host or "hermes-station-1",
        "nonce_hash": sha256_text(nonce),
        "operator": os.environ.get("USER") or "unknown",
        "note": "nonce value not persisted; hash only",
    }
    # Ensure parent exists with tight perms
    ARM_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(ARM_STATE_PATH, arm)
    # Do not print nonce
    print(
        json.dumps(
            {
                "status": "ARMED_LOCAL",
                "expires_at_unix": arm["expires_at_unix"],
                "environment": arm["environment"],
                "host_id": arm["host_id"],
                "path": str(ARM_STATE_PATH),
                "note": "arm token is local operational state; not stored in git",
            },
            indent=2,
        )
    )
    return 0


def cmd_cutover_disarm(args: argparse.Namespace) -> int:
    if ARM_STATE_PATH.is_file():
        ARM_STATE_PATH.unlink()
    print(json.dumps({"status": "DISARMED", "arm_present": False}, indent=2))
    return 0


def cmd_protect(args: argparse.Namespace) -> int:
    """Report production protection status."""
    target = resolve_target(args.environment or "production", args.host)
    allowed, reason = production_mutation_allowed(target)
    out = {
        "environment": target.environment,
        "host_id": target.host_id,
        "mutation_policy": target.mutation_policy,
        "mutation_allowed": allowed,
        "reason": reason,
        "cutover": load_cutover_state().get("state"),
        "arm_path_exists": ARM_STATE_PATH.is_file(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not allowed or target.mutation_policy != "blocked_until_armed" else 0


# ---------------------------------------------------------------------------
# Reboot persistence check (report only)
# ---------------------------------------------------------------------------

def cmd_reboot_persistence(args: argparse.Namespace) -> int:
    """Observe reboot-persistence related paths; does not reboot."""
    checks = {
        "systemd_hermes_agent": Path("/etc/systemd/system/hermes-agent.service").is_file(),
        "systemd_hermes_gateway": Path("/etc/systemd/system/hermes-gateway.service").is_file(),
        "release_current": (RELEASE_ROOT / "current").exists(),
        "shared_data": (RELEASE_ROOT / "shared").exists(),
        "hps_state_dir": STATE_DIR.exists(),
    }
    # enabled units if systemctl available
    enabled = {}
    if shutil.which("systemctl"):
        for u in ("hermes-agent", "hermes-gateway"):
            r = run_cmd(["systemctl", "is-enabled", u])
            enabled[u] = (r.stdout or r.stderr or "").strip()
    out = {
        "command": "reboot-persistence",
        "timestamp_utc": utc_now(),
        "path_checks": checks,
        "unit_enabled": enabled,
        "status": "PERSISTENCE_OBSERVED" if all(checks.values()) else "PERSISTENCE_PARTIAL",
        "note": "Does not perform reboot; use scripts/reboot-test.sh for full test",
    }
    path = EVIDENCE_HPS / f"reboot-persistence-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(path, out)
    print(json.dumps(out, indent=2, sort_keys=True))
    print(f"evidence={path}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hps", description="Hermes Provisioning System v1")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_target_flags(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--environment", "-e", default=None)
        sp.add_argument("--host", default=None)

    sp = sub.add_parser("inventory", help="Authoritative host inventory")
    sp.set_defaults(func=cmd_inventory)

    sp = sub.add_parser("target", help="Resolve and verify target")
    add_target_flags(sp)
    sp.set_defaults(func=cmd_target)

    sp = sub.add_parser("preflight", help="Preflight checks")
    add_target_flags(sp)
    sp.set_defaults(func=cmd_preflight)

    sp = sub.add_parser("plan", help="Deterministic plan with digest")
    add_target_flags(sp)
    sp.set_defaults(func=cmd_plan)

    sp = sub.add_parser("apply", help="Apply validated plan")
    add_target_flags(sp)
    sp.add_argument("--plan-id", default=None)
    sp.add_argument("--plan-digest", default=None)
    sp.add_argument("--allow-state-drift", action="store_true")
    sp.set_defaults(func=cmd_apply)

    sp = sub.add_parser("verify", help="Post-apply / health verification")
    add_target_flags(sp)
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("resume", help="Idempotent resume")
    add_target_flags(sp)
    sp.set_defaults(func=cmd_resume)

    sp = sub.add_parser("rollback", help="Rollback to previous release")
    add_target_flags(sp)
    sp.set_defaults(func=cmd_rollback)

    sp = sub.add_parser("backup", help="Create backup via scripts/backup.sh")
    sp.set_defaults(func=cmd_backup)

    sp = sub.add_parser("restore-test", help="Isolated restore test")
    sp.set_defaults(func=cmd_restore_test)

    sp = sub.add_parser("restore", help="Restore (defaults to restore-test)")
    add_target_flags(sp)
    sp.add_argument("--apply-live", action="store_true")
    sp.set_defaults(func=cmd_restore)

    sp = sub.add_parser("releases", help="List releases / current / previous")
    sp.set_defaults(func=cmd_releases)

    sp = sub.add_parser("drift", help="Configuration/runtime drift detection")
    add_target_flags(sp)
    sp.set_defaults(func=cmd_drift)

    sp = sub.add_parser("secrets-refs", help="HSP secret references (names/presence only)")
    sp.set_defaults(func=cmd_secrets_refs)

    sp = sub.add_parser("protect", help="Production mutation protection status")
    add_target_flags(sp)
    sp.set_defaults(func=cmd_protect)

    sp = sub.add_parser("reboot-persistence", help="Observe reboot persistence markers")
    sp.set_defaults(func=cmd_reboot_persistence)

    # cutover group via nested-style: cutover <action>
    sp = sub.add_parser("cutover", help="Cutover state machine")
    csub = sp.add_subparsers(dest="cutover_cmd", required=True)

    c1 = csub.add_parser("status")
    c1.set_defaults(func=cmd_cutover_status)

    c2 = csub.add_parser("transition")
    c2.add_argument("to_state")
    c2.add_argument("--reason", default="")
    c2.add_argument("--dry-run", action="store_true")
    c2.set_defaults(func=cmd_cutover_transition)

    c3 = csub.add_parser("arm")
    c3.add_argument("--ttl-seconds", type=int, default=3600)
    c3.add_argument("--environment", default="production")
    c3.add_argument("--host", default="hermes-station-1")
    c3.set_defaults(func=cmd_cutover_arm)

    c4 = csub.add_parser("disarm")
    c4.set_defaults(func=cmd_cutover_disarm)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except SystemExit as e:
        if isinstance(e.code, int):
            return e.code
        if e.code is None:
            return 0
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
