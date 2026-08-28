# hermes-ovh-cleanroom — context

**What this repo is:** an autonomous clean-room rebuild of the Hermes platform on a separate OVH host — three authority-separated planes (**HES** operator shell → **HPS** sole mutation authority → **HSP** secrets-presence plane), a Hermes agent+gateway runtime held read-only toward production, and Grok-driven autonomous execution governed by GitHub PR gates. Production Hermes is **read-only reference; never mutated; never double-poll Telegram**.

## Read this before editing

1. **Authority order**: `runbook/RUNBOOK-MANIFEST.md` → ordered runbook parts 00–05 + guardrails + evolution policies → `AGENTS.md`. Historical fragments (`part-01.md`, `part-02.md`) are preserved but NOT authoritative.
2. **Anti-hallucination mode**: fail closed on unsupported factual claims (`policy/anti-hallucination-guardrails.md`) — applies to agents, CI reports, HES/HPS/HSP output alike.
3. **Mutation funnel**: HES never mutates infrastructure itself; deploy/rollback/backup/cutover delegate to HPS, which applies only against an unchanged plan digest and auto-rollbacks on critical acceptance failure.
4. **Production protection**: cutover state machine is fail-closed on illegal transitions; production/rollback targets stay `blocked_until_armed` until local arm state exists (`hps_core.py:48-80,247`). Arm state is never committed.
5. **Secrets**: names+purposes only in Git (`config/secret-contract.yaml`); values resolve from env or 0600 local dir at runtime.

## Universes

| Universe | Members |
|---|---|
| live | hes/, hps/, hsp/, scripts/, systemd units, compose files, config contracts, runbook authoritative parts, governance workflows, ops controllers |
| leftover | historical bootstrap fragments (`runbook/part-01.md`, `part-02.md`) — preserve as evidence, not authority |
| ghost | supporting compose profiles not yet evidenced as needed (Postgres/Qdrant under profile `datastores`); `HADA_RUNTIME=NOT_DEPLOYED` unless evidenced |

## Conventions

- Evidence tree mirrors function: `evidence/{acceptance,baseline,claims,faults,deploy,...}` with timestamped artifacts; claim-evidence and fault-ledger validators run in `make validate`.
- Make targets are the operator surface: validate/test/lint/health/backup/restore-test/acceptance/hps-plan.
- Environment context always printed by HES; target environments explicit: cleanroom/production/rollback/test.
