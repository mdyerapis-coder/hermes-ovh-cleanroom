# Part 100 — HPS/HES Platform Completion and Hermes Production Cutover

Date established: 2026-08-07
Baseline host: `hermes-ovh-cleanroom`

## Purpose

This is the authoritative post-clean-room execution phase. The previous clean-room completion remains preserved as a verified baseline. This phase expands the platform in this mandatory order:

1. HPS v1 production-grade provisioning/control plane.
2. HES v1 production-grade operator CLI/TUI.
3. HPS/HES/HSP/GitHub integration.
4. Hermes migration implemented as an HPS cutover transaction exposed through HES.
5. Exclusive production cutover only after all safety gates and external prerequisites are genuinely satisfied.
6. Production validation, rollback retention, soak, and final production baseline.
7. HADA may follow only after the platform is stable; until then `HADA_RUNTIME=NOT_DEPLOYED`.

The existing `evidence/control/AUTONOMY_DONE.json` is a preserved clean-room baseline marker. It is not the stop marker for this phase.

The stop marker for this phase is:

`evidence/control/PLATFORM_COMPLETION.json`

## Non-negotiable architecture

- HPS is the sole infrastructure/runtime mutation authority.
- HES is the operator interface and must delegate mutations to HPS.
- HSP is the secrets plane; HPS/HES never become alternate secret stores.
- GitHub branch/PR/CI is the independent change gate.
- Existing `BOOTSTRAP-GATE` and `AUDIT-GATE` remain mandatory.
- Proven baseline capability is additive-first and may not be silently removed or weakened.
- Production Hermes remains read-only until a genuine HPS cutover transaction reaches its armed phase.
- There must never be two production Telegram pollers.
- Unknowns are `PENDING_VERIFICATION`.
- All completion, health, deployment, repair, cutover, and rollback claims require evidence.

## HPS v1

HPS must evolve from the current baseline into the production control plane.

Required capabilities:

- authoritative host inventory and identity;
- explicit target environments: cleanroom, production, rollback, test;
- deterministic `plan` with target, current state, desired state, affected resources, secret references, backup requirement, rollback target, risk and acceptance tests;
- `apply` only against an unchanged valid plan/digest;
- post-apply verification;
- automatic rollback for critical acceptance failures;
- backup, list, verify, restore-test, restore, retention and known-good markers;
- release/current/previous management;
- configuration/runtime drift detection;
- HSP secret-reference consumption without secret disclosure;
- canonical append-only fault and repair evidence;
- production mutation protection;
- reboot persistence;
- HPS cutover state-machine support.

HPS completion evidence:

- `evidence/hps/HPS_V1.json`
- `evidence/hps/HPS_V1.md`

`HPS_V1=PASS` requires evidence-backed PASS for inventory, target resolution, plan, apply, verify, rollback, backup, restore-test, restore, drift, release management, secret references, production protection, fault ledger, evidence output, GitHub governance and reboot persistence.

## HES v1

HES must remain terminal-emulator agnostic and use a dark/black, blue-primary, high-contrast operator design where terminal capabilities permit it. Plain text fallback must remain fully usable.

Required command surface includes at minimum:

- `/status` and `hes status`
- `/health`
- `/hosts`
- `/host`
- `/services`
- `/service`
- `/releases`
- `/deploy`
- `/rollback`
- `/backup`
- `/restore`
- `/drift`
- `/faults`
- `/repairs`
- `/audit`
- `/github`
- `/secrets`
- `/cutover`
- `/hada`
- `/help`

Every operational view must make environment and target host unambiguous. Production context must never be hidden or inferred only from hostname.

`/hada` must show `HADA_RUNTIME=NOT_DEPLOYED` unless genuine runtime evidence exists.

HES must expose HPS operation state, GitHub gates, deployed/current SHA, faults/repairs, backup/restore state and cutover state. Telegram-friendly concise output must be available.

HES completion evidence:

- `evidence/hes/HES_V1.json`
- `evidence/hes/HES_V1.md`

## Integration

Required authority flow:

`User / Telegram / HES -> HPS -> HSP / managed host / runtime -> evidence -> HES status`

HES must never independently mutate managed infrastructure and must not claim an HPS operation successful until HPS verification is complete.

Create evidence for `HPS_HES_INTEGRATION=PASS`.

## Hermes cutover as HPS workflow

Do not create a parallel temporary deployment authority. Implement Hermes production migration as a native HPS cutover workflow and expose it through HES.

Allowed cutover states:

- `PREPARING`
- `READY`
- `ARMED`
- `OLD_FENCED`
- `NEW_STARTING`
- `VERIFYING`
- `CUTOVER_COMPLETE`
- `ROLLBACK_STARTING`
- `ROLLED_BACK`
- `BLOCKED`
- `FAILED`

Illegal state transitions must fail closed and be tested.

## Production discovery

Known production host reference: `hermes-station-1`.

Production inventory remains read-only until the cutover reaches `ARMED`. Previously observed Telegram gateway identity is `hermes-gateway-rebuild.service`, but this must be re-verified live before any mutation.

Read-only inventory should capture service names, process identities, users/groups, config/state paths, memory/profile/skill state, scheduled jobs, runtime version, provider credential presence, Telegram credential presence, health and backup state. Secret values must never be recorded.

If access remains blocked by external ACL/permission, record the blocker and continue independent HPS/HES work.

## State migration

Migrate only authoritative state. Do not blindly copy caches, stale sessions, obsolete services, superseded configuration or fabricated HADA state.

Use initial sync plus checksum/inventory and a final delta sync immediately before fencing when the cutover is armed.

## Cutover readiness

Before any production mutation, require evidence-backed PASS for:

- HPS v1;
- HES v1;
- HPS/HES integration;
- new-host health;
- backup and restore test;
- rollback readiness;
- required provider authentication;
- state sync;
- required secret presence;
- new Telegram poller disabled;
- production inventory.

Then and only then may `CUTOVER_READY=PASS` be asserted.

## Arm gate

Production mutation requires an explicit, expiring, local arm transaction. The arm token/nonce is operational state and must not be stored in Git.

Without a valid arm state, HPS must refuse production mutation.

## Telegram exclusivity gate

Mandatory order:

1. Verify the old production gateway identity.
2. Stop the old production poller.
3. Disable/fence automatic restart.
4. Prove the old unit is inactive.
5. Prove no production poller process remains.
6. Record fence evidence.
7. Only then permit the OVH production poller to start.

Required exact condition before starting the new poller:

- `OLD_GATEWAY_ACTIVE=false`
- `OLD_GATEWAY_PROCESS_COUNT=0`
- `OLD_GATEWAY_RESTART_ALLOWED=false`
- `TELEGRAM_EXCLUSIVITY_GATE=PASS`

If exclusivity cannot be proven, abort and do not start the new poller.

## Live production verification

After exclusivity passes, start the OVH production gateway and verify service/process/provider/bot identity. A genuine Telegram inbound -> Hermes -> model -> outbound E2E using a one-time nonce is mandatory before `TELEGRAM_LIVE_E2E=PASS`.

Do not record unnecessary conversation content in evidence.

## Automatic rollback

Critical failures before finalization must trigger reverse exclusivity:

1. stop the new poller;
2. prove it is dead;
3. restore new-host known-good state if required;
4. re-enable old production gateway;
5. start old production gateway;
6. verify old Telegram operation;
7. record `ROLLED_BACK` only after verification.

Never permit overlap during rollback.

## Soak and permanent fence

After successful cutover, keep the old host as fenced rollback standby for at least 24 hours unless a stronger evidence-backed retention policy is adopted. Monitor gateway stability, Telegram/provider failures, state errors, scheduled jobs, disk, RAM, backups, HSP and service restarts.

After successful soak, prefer Telegram token rotation so only OVH HSP contains the active credential and accidental old-host restart cannot regain polling ownership.

## Fault policy

For each distinct fault: detect, classify, capture evidence, attempt repair, and retest the original failure. Preserve failed attempts. Maximum autonomous attempts per distinct fault is 12, after which record `BLOCKED_AUTONOMOUS_REPAIR_LIMIT` and continue independent work.

## CI and tests

Preserve the entire existing CI floor and add HPS/HES/cutover-specific tests/jobs without weakening any existing gate.

At minimum test:

- HPS state transitions;
- wrong-host/target prevention;
- plan/apply digest mismatch;
- backup/restore and rollback;
- drift detection;
- HSP reference handling;
- HES command parsing and target banner;
- `/hada` truthfulness;
- cutover legal/illegal transitions;
- Telegram exclusivity and rollback exclusivity;
- evidence validation;
- baseline preservation.

## Completion disposition

The strongest preferred final marker is:

`evidence/control/PLATFORM_COMPLETION.json`

For a genuine completed production state it must contain at least:

```json
{
  "state": "COMPLETE_PRODUCTION",
  "evidence_verified": true,
  "HPS_V1": "PASS",
  "HES_V1": "PASS",
  "HPS_HES_INTEGRATION": "PASS",
  "Hermes_production_host": "hermes-ovh-cleanroom",
  "Telegram_exclusive": true,
  "Telegram_live_e2e": true,
  "rollback_available": true,
  "production_baseline_created": true,
  "verified_commit_sha": "<protected-main-sha>",
  "final_report": "evidence/final/platform-completion-report.md"
}
```

If the software platform is complete but genuine external permission/secrets/arm state prevent the exclusive cutover, the controller may stop truthfully with `COMPLETE_HPS_HES_READY_FOR_CUTOVER` or `PARTIAL_WITH_EXTERNAL_BLOCKERS`, accompanied by exact blocker evidence. It must never fabricate production completion.

## Execution priority

Proceed autonomously:

`HPS v1 -> HES v1 -> integration -> cutover workflow -> resolve available blockers -> exclusive cutover if safely armed -> E2E -> soak -> production baseline -> final evidence -> HADA phase`

Do not stop at plans, TODOs, skeletons, proposed commands, attempted deployments, or partially passing tests. Continue until the strongest truthful completion state permitted by actual evidence is reached.
