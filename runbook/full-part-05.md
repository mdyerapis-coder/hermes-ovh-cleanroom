- containers;
- language dependencies.

Updates must use normal PR CI and `AUDIT-GATE`.

Do not auto-update directly on `main`.

Security updates may be prioritised, but still pass the same audit.

---

# 41. PHASE 33 — DOCUMENTATION

Generate/update:

```text
docs/architecture.md
docs/service-inventory.md
docs/operations.md
docs/recovery.md
docs/secrets-contract.md
docs/network-contract.md
docs/backup-restore.md
docs/autonomous-governance.md
```

Documentation must reflect deployed reality.

`docs-drift` CI should compare key generated inventories/contracts with runtime manifests.

---

# 42. REQUIRED FINAL EVIDENCE BUNDLE

Produce:

```text
evidence/final/
  final-report.md
  service-inventory.tsv
  versions.tsv
  repository-inventory.tsv
  ports.tsv
  systemd-units.txt
  container-inventory.json
  health-results.json
  acceptance-results.json
  backup-results.md
  restore-results.md
  fault-ledger.jsonl
  fault-summary.md
  unresolved-blockers.md
  release-manifest.json
  checksums.sha256
```

The final report must distinguish:

```text
PASS
READY_FOR_EXCLUSIVE_CUTOVER
BLOCKED_EXTERNAL_SECRET
BLOCKED_EXTERNAL_ENTITLEMENT
BLOCKED_RESOURCE_FLOOR
BLOCKED_AUTONOMOUS_REPAIR_LIMIT
BLOCKED_UNSAFE_IRREVERSIBLE_MIGRATION
NOT_DEPLOYED
NOT_APPLICABLE
```

Do not label blocked functions as PASS.

---

# 43. COMPLETION CRITERIA

The clean-room build is `COMPLETE` only when all applicable conditions below pass.

## GitHub / governance

- repository exists;
- main protected;
- human approvals not required;
- `AUDIT-GATE` required;
- auto-merge enabled;
- actions pinned appropriately;
- direct/bypass merge path unavailable to normal Grok workflow;
- audited PR successfully auto-merged.

## Host

- OVH host provisioned;
- hardened;
- Tailscale connected;
- intended firewall active;
- persistent access path proven;
- reboot test passed.

## Core runtime

- Hermes installed;
- Hermes healthy;
- profiles/skills/memory verified;
- providers validated;
- local fallback verified if applicable.

## Telegram

Either:

- separate test bot E2E passed; or
- production gateway fully tested synthetically and marked:
  `READY_FOR_EXCLUSIVE_CUTOVER`.

## HSP

- secret contract complete;
- no plaintext secrets in Git;
- mandatory secret checks pass;
- fail-closed behaviour verified.

## HPS

- full apply;
- verify;
- second-run idempotency;
- evidence;
- recovery/resume.

## HES

- CLI/TUI operational;
- real status;
- audit/recovery views;
- truthful HADA state.

## Supporting services

All current applicable services healthy and persistence-tested.

## Backup/recovery

- backup completes;
- isolated restore succeeds;
- deployment rollback test succeeds.

## Faults

- every detected fault logged;
- every repair attempt logged;
- no unresolved critical fault;
- unresolved external blockers explicitly classified;
- fault ledger included in final evidence.

## Deployment

- audited merge automatically deployed;
- post-deploy acceptance passed;
- known-good SHA recorded.

---

# 44. AUTONOMOUS STOP CONDITIONS

Routine errors are not stop conditions.

Repair them.

Stop mutating only the affected area when one of these applies:

1. 12 repair attempts exhausted for the same root fault;
2. required external credential does not exist;
3. required paid entitlement/account permission is absent;
4. hardware cannot satisfy minimum safe resource requirement;
5. source-of-truth conflict cannot be resolved without guessing;
6. migration is destructive/irreversible and has no proven recovery path;
7. operation would mutate the existing production host;
8. operation would start a duplicate Telegram poller;
9. operation would weaken the auditor to make a failed PR pass.

Continue all independent work.

---

# 45. WHAT GROK MUST NEVER DO

Never:

- claim work was done if only planned;
- claim CI passed without checking the run;
- claim deployment passed without acceptance evidence;
- claim HADA is running without runtime evidence;
- silently skip failed checks;
- erase failed repair history;
- expose tokens;
- copy secrets into Git;
- use `--admin` merge;
- disable branch protection to merge;
- change production to make the clean-room test easier;
- run duplicate production Telegram polling;
- use mutable production image tags;
- deploy code that did not pass the required audit;
- leave a failed candidate running after rollback is possible;
- declare completion with unresolved critical faults.

---

# 46. FIRST IMPLEMENTATION PR

The first implementation PR should establish, at minimum:

1. repository structure;
2. fault logging framework;
3. CI auditor;
4. `AUDIT-GATE`;
5. GitHub governance automation/documentation;
6. host preflight;
7. provisioning framework;
8. network/secret contracts;
9. deployment/rollback skeleton;
10. test harness.

Once that PR passes and auto-merges, use subsequent audited PRs for larger runtime components if this materially improves fault isolation.

It is acceptable to use multiple PRs.

It is not acceptable to bypass CI because the user requested "complete implementation".

---

# 47. SUGGESTED PR SEQUENCE

A practical autonomous sequence is:

```text
PR-01 governance + auditor + fault ledger
PR-02 OVH bootstrap + Tailscale + firewall + system accounts
PR-03 HSP
PR-04 HPS
PR-05 Hermes core runtime
PR-06 profiles + skills + memory + providers + local fallback
PR-07 Telegram gateway isolated acceptance
PR-08 supporting services
PR-09 HES
PR-10 backups + recovery + rollback
PR-11 end-to-end acceptance + reboot/chaos validation
PR-12 documentation/evidence hardening
```

Each PR:

```text
open → CI → fault log → repair loop → AUDIT-GATE → auto-merge → deploy → acceptance
```

A failed deployment becomes the input to the next repair PR.

---

# 48. FINAL REPORT FORMAT

At completion, return a concise operator report containing:

## Identity

- OVH hostname;
- Tailscale hostname/IP;
- OS;
- deployed Git SHA;
- deployment timestamp Melbourne time.

## GitHub governance

- repository;
- protected branch;
- required gate;
- auto-merge state;
- last audited PR;
- last audit workflow run.

## Runtime

Table:

```text
Component | Version | State | Bind/Exposure | Evidence
```

## Fault/repair summary

Table:

```text
Fault ID | Phase | Severity | Root Cause | Attempts | Final State | Repair Commit
```

## Backups

- latest successful backup;
- restore test;
- recovery point.

## Remaining blockers

Only real blockers.

## Overall disposition

One of:

```text
COMPLETE_CLEANROOM
COMPLETE_READY_FOR_EXCLUSIVE_CUTOVER
PARTIAL_WITH_EXTERNAL_BLOCKERS
FAILED_SAFETY_GATE
```

---

# 49. INITIAL COMMAND TO GROK

After receiving this runbook, begin with:

```text
Execute the attached runbook autonomously from Phase 0 through final acceptance.
Do not merely restate it.
Do not ask for routine approvals.
Log every fault and every repair attempt as it occurs.
Use GitHub PR + CI as the independent auditor.
Auto-merge only when AUDIT-GATE is exact-success green.
Automatically deploy green merges to the separate OVH clean-room server.
Automatically roll back failed releases.
Never mutate the existing Hermes production environment.
Continue independent work when an external credential or entitlement is unavailable.
At the end, provide the final evidence-backed completion report and the complete fault/repair ledger.
```

---

# 50. DESIGN NOTES VALIDATED AGAINST CURRENT PLATFORM BEHAVIOUR

The implementation should account for these current platform facts:

- GitHub auto-merge can merge a PR automatically after configured repository requirements are satisfied.
- Required status checks apply to the current/latest valid commit state.
- A skipped GitHub Actions job can be interpreted as successful for merge gating; therefore this runbook requires an explicit aggregate gate that checks every mandatory job result for exact `success`.
- GitHub supports protecting a branch with required status checks and preventing bypass.
- GitHub recommends pinning Actions to full-length commit SHAs for immutable action references.
- Tailscale's GitHub Action supports ephemeral CI nodes and workload identity federation, allowing GitHub Actions to reach private infrastructure without leaving the OVH host publicly exposed.

These behaviours are implementation inputs, not substitutes for the stronger controls defined in this runbook.

---

# END OF RUNBOOK
