# Hermes OVH Clean-room — Authoritative Execution Manifest

This manifest is the single entrypoint for the autonomous Grok implementation.

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

Together, items 1-6 are the complete 2,355-line implementation runbook.

## Historical fragments

Earlier files `runbook/part-01.md`, `runbook/part-02.md`, and any other partial runbook fragments created during bootstrap are historical bootstrap artefacts only. They are NOT authoritative and MUST NOT override the ordered files above.

Do not delete those historical files. Preserve them as evidence of the bootstrap process.

## Conflict resolution

If any instruction conflicts:

1. Safety boundaries and non-mutation of the existing production Hermes environment win.
2. `policy/anti-hallucination-guardrails.md` wins for truth/evidence requirements.
3. `runbook/part-99-post-completion-evolution-policy.md` wins for post-completion preservation/non-removal.
4. The numbered complete runbook parts are then applied in order.
5. Unknown or unresolved facts MUST be `PENDING_VERIFICATION`; Grok must never guess.

## Mandatory operating mode

- Execute, do not merely plan or narrate.
- No routine human approvals.
- Every fault is logged when observed.
- Every repair attempt is logged, including failed attempts.
- Normal implementation changes go through branches and Pull Requests.
- GitHub CI is the independent merge auditor.
- Only exact-success `AUDIT-GATE` permits auto-merge.
- Green merges deploy automatically to `hermes-ovh-cleanroom` only.
- Failed releases roll back automatically.
- Existing Hermes production systems are read-only references and never mutation targets.
- Never run a duplicate production Telegram poller.
- Unsupported completion/health/deployment claims are prohibited.
- After the proven baseline is completed, Grok may expand indefinitely but must never remove or regress the preserved baseline.

## Completion marker

The autonomous controller may stop only after Grok writes:

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

`AUTONOMY_DONE.json` MUST NOT be created merely because a Grok turn ended, a plan was produced, CI was started, or a deployment was attempted. It is permitted only after final evidence reconciliation under the anti-hallucination policy.

## First action

Before changing code or host state, Grok must verify this manifest and all eight authoritative inputs are readable, record their Git SHA, initialise the evidence/fault ledger, and create a source-of-truth inventory.
