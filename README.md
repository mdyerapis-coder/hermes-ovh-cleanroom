# hermes-ovh-cleanroom

Autonomous clean-room Hermes / HPS / HES deployment for a separate OVH host.

**Existing production Hermes is read-only. Never mutate it. Never double-poll Telegram.**

## Authority

1. `runbook/RUNBOOK-MANIFEST.md`
2. Complete runbook parts + anti-hallucination policy + post-completion evolution policy
3. `AGENTS.md`

## Governance

- Required checks (after first governance PR activation): `BOOTSTRAP-GATE` + `AUDIT-GATE`
- Auto-merge only after dual exact-success green
- Deploy only to `hermes-ovh-cleanroom`

## Quick start (operator)

```bash
make validate
make test
./hes/bin/hes status
```
