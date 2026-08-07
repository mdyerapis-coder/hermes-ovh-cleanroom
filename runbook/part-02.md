Makefile
README.md
VERSION
```

---

# 13. PHASE 5 — GITHUB REPOSITORY GOVERNANCE

Configure:

- default branch: `main`;
- squash merge enabled;
- auto-merge enabled;
- head branches deleted after merge;
- Actions enabled;
- Actions token read-only by default;
- write permissions only at job level when needed.

## 13.1 Main protection / ruleset

Protect `main`.

Require:

- pull request before merge;
- zero required human approvals;
- status check `AUDIT-GATE`;
- up-to-date branch / strict validation where supported;
- no force push;
- no deletion;
- no routine bypass;
- no Grok administrator bypass;
- linear history if compatible.

Do not configure required human review.

## 13.2 Auditor isolation

Preferred:

- dedicated GitHub organisation ruleset / required reusable workflow;
- policy/auditor repository separate from application implementation;
- Grok does not have permission to modify that policy repository/ruleset during normal repair.

If unavailable on the account/plan:

```text
AUDITOR_ISOLATION_MODE=REPOSITORY_REQUIRED_CHECK
```

Record the reduced isolation explicitly.

## 13.3 Pin external actions

All third-party GitHub Actions used in audited workflows must be pinned to a verified full-length commit SHA.

Do not rely on mutable version tags for security-critical workflow steps.

---

# 14. PHASE 6 — PR AUDIT WORKFLOW

Create:

```text
.github/workflows/pr-audit.yml
```

Trigger on every PR targeting `main`.

Do not add a path filter that allows the required workflow to remain absent.

If merge queue is enabled, also support:

```yaml
merge_group:
```

## 14.1 Mandatory jobs

The minimum mandatory jobs are:

```text
repository-policy
format-lint
unit-tests
config-contract
secret-scan
dependency-audit
sast
iac-scan
container-build
container-vulnerability-scan
integration-tests
migration-dry-run
backup-restore-test
smoke-tests
docs-drift
fault-ledger-validation
audit-gate
```

Use project-native tooling where available.

Possible tools include:

- ShellCheck;
- Ruff;
- pytest;
- ESLint;
- repository-native test commands;
- Gitleaks;
- OSV-Scanner;
- Trivy;
- Semgrep;
- Checkov;
- Syft.

Do not add unreliable scanners just to inflate check count.

## 14.2 Repository policy failures

Fail CI when tracked content introduces, outside a documented allowlist:

- plaintext secrets;
- private keys;
- real `.env` values;
- unrestricted `chmod 777`;
- privileged containers;
- host PID namespace;
- host network without explicit justification;
- unrestricted Docker socket mount;
- `/` host mount;
- uncontrolled `/etc` mount;
- uncontrolled `/home` mount;
- curl-pipe-shell without version/integrity controls;
- workflow token write permissions that are not required;
- mutable production image `latest`;
- direct production mutation in PR CI;
- disabled security controls;
- production destructive commands;
- unaudited bypass flags.

## 14.3 Fault-ledger CI

`fault-ledger-validation` must verify:

- JSONL parses;
- unique `fault_id`;
- repair attempts reference valid faults;
- resolved faults contain verification;
- critical unresolved faults fail the PR;
- secret-like content is not present;
- timestamps are valid;
- no earlier fault records were deleted.

Where practical, compare the PR base ledger and ensure append-only semantics.

## 14.4 Final AUDIT-GATE

The final job runs even when dependencies fail.

Conceptual implementation:

```yaml
audit-gate:
  name: AUDIT-GATE
  if: always()
  needs:
    - repository-policy
    - format-lint
    - unit-tests
    - config-contract
    - secret-scan
    - dependency-audit
    - sast
    - iac-scan
    - container-build
    - container-vulnerability-scan
    - integration-tests
    - migration-dry-run
    - backup-restore-test
    - smoke-tests
    - docs-drift
    - fault-ledger-validation
  runs-on: ubuntu-latest
  steps:
    - name: Require exact success from every mandatory audit
      env:
        NEEDS_JSON: ${{ toJSON(needs) }}
      run: |
        python3 - <<'PY'
        import json, os, sys

        needs = json.loads(os.environ["NEEDS_JSON"])
        bad = {
            name: meta.get("result")
            for name, meta in needs.items()
            if meta.get("result") != "success"
        }

        if bad:
            print("AUDIT-GATE FAILED")
            for name, result in sorted(bad.items()):
                print(f"{name}: {result}")
            sys.exit(1)

        print("AUDIT-GATE PASSED")
        PY
```

`AUDIT-GATE` is the protected-branch required check.

---

# 15. PHASE 7 — AUTONOMOUS PR REPAIR LOOP

Create feature branch:

```bash
git switch -c "grok/ovh-cleanroom-${RUN_ID}"
```

Commit coherent changes.

Open PR.

Enable auto-merge immediately after the PR exists:

```bash
gh pr merge --auto --squash
```

Monitor:

```bash
gh pr checks --watch
```

For each failure:

1. log fault immediately;
2. download/capture relevant job evidence;
3. inspect logs;
4. determine root-cause hypothesis;
5. implement repair;
6. log repair attempt;
7. commit;
8. push;
9. rerun/reobserve CI;
10. update fault record;
11. repeat.

Never:

- rename a gate to evade a failure;
- use `continue-on-error` on mandatory validation;
- replace a test command with `true`;
- delete a failing test merely because it fails;
- lower a vulnerability threshold without documented risk justification;
- disable security scanning as a repair;
- merge an earlier green SHA after a later SHA failed.

---

# 16. PHASE 8 — OVH HOST PREFLIGHT

On the new OVH host:

```bash
hostnamectl
cat /etc/os-release
uname -r
nproc
free -h
df -hT
ip -brief address
ip route
lsblk
```

Record:

```text
evidence/host/preflight.txt
```

Check:

- CPU;
- RAM;
- disk;
- filesystem;
- time sync;
- DNS;
- outbound HTTPS;
- OVH console/recovery availability.

Any failed preflight is logged as a fault.

---

# 17. PHASE 9 — HOST ACCOUNTS AND SSH

Create dedicated runtime/deploy identities:

```text
hermes
deploy
```

Do not run Hermes application services as root.

## 17.1 Safe SSH hardening order

1. place authorised key;
2. prove new non-root key login;
3. keep current bootstrap connection open;
4. install/prove Tailscale;
5. prove Tailscale SSH or SSH over Tailscale;
6. configure firewall;
7. disable password auth;
8. disable keyboard-interactive auth if appropriate;
9. disable direct public root login;
10. close public SSH if deployment uses Tailscale.

Do not repeat a prior lockout pattern.

Never disable the last proven access path before a second proven path exists.

---

# 18. PHASE 10 — BASE HOST HARDENING

Install only required packages.

Typical baseline:

```text
ca-certificates
curl
git
jq
rsync
unzip
python3
python3-venv
build-essential (only if required)
Docker Engine + Compose plugin OR canonical container runtime
unattended-upgrades
fail2ban if public SSH remains
Tailscale
restic/rclone only if selected backup design requires them
```

Configure:

- automatic security updates;
- journald persistence/rotation;
- logrotate as needed;
- system time;
- minimum firewall;
- swap if required;
- predictable hostname.

---

# 19. PHASE 11 — TAILSCALE MANAGEMENT PLANE

Preferred clean-room hostname:

```text
hermes-ovh-cleanroom
```

Preferred CI deployment architecture:

```text
GitHub-hosted runner
   ↓ workload identity federation
ephemeral Tailscale node tagged tag:ci
   ↓ narrowly-scoped tailnet ACL
OVH clean-room node
```

Prefer workload identity federation over long-lived auth keys when available.

CI tag permissions must be limited to only the clean-room deployment endpoint(s).

Do not grant `tag:ci` broad access to the user's tailnet.

After Tailscale management is proven, close public SSH unless explicitly required.

---

# 20. PHASE 12 — FIREWALL AND PORT CONTRACT

Default inbound policy:

