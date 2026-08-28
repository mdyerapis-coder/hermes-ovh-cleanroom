# hermes-ovh-cleanroom — system map

**What this repo is:** an autonomous clean-room rebuild of the Hermes platform on a separate OVH host — three authority-separated planes (**HES** operator shell → **HPS** sole mutation authority → **HSP** secrets-presence plane), a Hermes agent+gateway runtime held read-only toward production, and Grok-driven autonomous execution governed by GitHub PR gates.

This `map/` folder is single-contract style: `map/CONTEXT.md` is both catalog and walk guide (the repo's own `AGENTS.md` at root carries contributor rules). Start there.

## Universes

| Universe | Members |
|---|---|
| live | hes/, hps/, hsp/, scripts/, systemd units, compose files, config contracts, runbook authoritative parts, governance workflows, ops controllers |
| leftover | historical bootstrap fragments (`runbook/part-01.md`, `part-02.md`) — evidence, not authority |
| ghost | compose profiles not yet evidenced (Postgres/Qdrant under profile `datastores`); `HADA_RUNTIME=NOT_DEPLOYED` unless evidenced |

## Routing

| If you are changing | Open |
|---|---|
| anything | `map/CONTEXT.md` first, then `runbook/RUNBOOK-MANIFEST.md` |
| HES/HPS/HSP plane code | its dir + `policy/anti-hallucination-guardrails.md` |
| production-facing behaviour | mutation-funnel + fail-closed rules in `map/CONTEXT.md` are contractual |
| secrets handling | `config/secret-contract.yaml` — names only in Git |

## Twins

`map/AGENTS.md` and `map/routing.md` are byte-identical twins of this catalog. Never hand-edit the twins; regenerate from `CLAUDE.md`.
