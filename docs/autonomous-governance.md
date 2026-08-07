# Autonomous governance

## Gates

- `BOOTSTRAP-GATE` — trusted bootstrap auditor (immutable in implementation PRs)
- `AUDIT-GATE` — aggregate exact-success over all mandatory PR audit jobs including `claim-evidence-validation`

## First activation sequence

1. Land full `AUDIT-GATE` on a PR
2. Wait for both gates exact-success on current head SHA
3. Update main protection to require both
4. Prove protection via API readback
5. Enable repository auto-merge
6. Auto-merge the PR without `--admin`

## Merge policy

Only exact `success` counts. skipped/neutral/cancelled/stale/missing are failures for mandatory jobs.
