# Hermes OVH Clean-room — Authoritative Execution Manifest

This manifest is the single entrypoint for autonomous Grok implementation and post-baseline evolution.

## Authority

Grok MUST read every authoritative file below in this exact order before making implementation changes:

1. `runbook/part-00.md` — original runbook lines 1-400
2. `runbook/full-part-01.md` — original runbook lines 401-800
3. `runbook/full-part-02.md` — original runbook lines 801-1200
4. `runbook/full-part-03.md` — original runbook lines 1201-1600
5. `runbook/full-part-04.md` — original runbook lines 1601-2000
6. `runbook/full-part-05.md` — original runbook lines 2001-2355
7. `policy/anti-hallucination-guardrails.md` — mandatory evidence/claim policy
8. `runbook/part-99-post-completion-evolution-policy.md` — mandatory additive-only post-completion evolution policy
9. `runbook/part-100-hps-hes-platform-completion.md` — authoritative HPS v1, HES v1, integration and production-cutover evolution phase

Together, items 1-6 are the complete original 2,355-line implementation runbook. Items 7-9 govern evidence and additive evolution beyond that baseline.

## Historical fragments

Earlier files `runbook/part-01.md`, `runbook/part-02.md`, and any other partial runbook fragments created during bootstrap are historical bootstrap artefacts only. They are NOT authoritative and MUST NOT override the ordered files above.

Do not delete those historical files. Preserve them as evidence of the bootstrap process.

## Conflict resolution

If any instruction conflicts:

1. Safety boundaries, Telegram exclusivity and explicit production cutover fencing win.
2. `policy/anti-hallucination-guardrails.md` wins for truth/evidence requirements.
3. `runbook/part-99-post-completion-evolution-policy.md` wins for preservation/non-removal.
4. `runbook/part-100-hps-hes-platform-completion.md` governs the post-baseline HPS/HES/cutover phase.
5. The numbered complete original runbook parts are then applied in order.
6. Unknown or unresolved facts MUST be `PENDING_VERIFICATION`; Grok must never guess.

## Mandatory operating mode

- Execute, do not merely plan or narrate.
- No routine human approvals.
- Every fault is logged when observed.
- Every repair attempt is logged, including failed attempts.
- Normal implementation changes go through branches and Pull Requests.
- GitHub CI is the independent merge auditor.
- Only exact-success required gates on the exact current head permit merge.
- Existing BOOTSTRAP-GATE and AUDIT-GATE remain mandatory.
- Host deployment/acceptance evidence is required in addition to CI for deployed/healthy claims.
- Failed releases roll back automatically where the authoritative workflow permits.
- Existing production systems are read-only references until the Part 100 cutover transaction is explicitly armed.
- Never run a duplicate production Telegram poller.
- Unsupported completion/health/deployment claims are prohibited.
- After the proven baseline is completed, Grok may expand indefinitely but must never remove or regress the preserved baseline.

## Clean-room completion marker

The original clean-room autonomous controller may stop only after Grok writes:

`evidence/control/AUTONOMY_DONE.json`

The file must contain at least:

```json
{
  "state": "COMPLETE_CLEANROOM | COMPLETE_READY_FOR_EXCLUSIVE_CUTOVER | PARTIAL_WITH_EXTERNAL_BLOCKERS | FAILED_SAFETY_GATE",
  "final_report": "evidence/final/final-report.md",
  "verified_commit_sha": "<sha>",
  "timestamp": "<ISO-8601>",
  "evidence_verified": true
}
```

A valid existing `AUTONOMY_DONE.json` is immutable baseline evidence for Part 100; it is not the stop marker for the platform-completion controller.

## Post-baseline platform completion marker

The Part 100 platform controller may stop only after a valid:

`evidence/control/PLATFORM_COMPLETION.json`

Allowed truthful dispositions are:

- `COMPLETE_PRODUCTION`
- `COMPLETE_HPS_HES_READY_FOR_CUTOVER`
- `PARTIAL_WITH_EXTERNAL_BLOCKERS`
- `FAILED_SAFETY_GATE`

The marker must contain `evidence_verified: true`, a `verified_commit_sha`, an existing `final_report` path and evidence appropriate to the disposition. `COMPLETE_PRODUCTION` additionally requires evidence-backed HPS v1, HES v1, HPS/HES integration, OVH production ownership, Telegram exclusivity, genuine Telegram live E2E, rollback availability and a production baseline.

Neither completion marker may be created merely because a Grok turn ended, a plan was produced, CI was started, code was written or a deployment was attempted. Completion is permitted only after final evidence reconciliation under the anti-hallucination policy.

## First action

Before changing code or host state, Grok must verify this manifest and all authoritative inputs are readable, record the current Git SHA, initialise/reconcile evidence and fault state, and create or refresh the relevant source-of-truth inventory. In Part 100 it must also validate the preserved clean-room completion/baseline before extending it.
