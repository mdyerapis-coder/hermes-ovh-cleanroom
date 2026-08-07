# Architecture — Hermes OVH Clean-room

This repository controls an isolated **clean-room** deployment of Hermes / HPS / HES on a separate OVH host.

## Identity

- Host: `hermes-ovh-cleanroom`
- Control plane: GitHub PR + CI (`BOOTSTRAP-GATE` + `AUDIT-GATE`)
- Existing production Hermes: **read-only reference only**

## Layers

1. **Governance** — branch protection, exact-success gates, auto-merge after dual green
2. **HSP** — secrets plane (names in Git, values never in Git)
3. **HPS** — sole infrastructure/runtime mutation authority (v1: inventory, plan/apply digest, backup/restore, drift, cutover state machine, production arm protection)
4. **Hermes runtime** — agent + gateway (Telegram polling disabled until exclusive cutover)
5. **HES** — operator CLI/TUI; delegates mutations to HPS; environment/target always explicit
6. **Supporting services** — optional compose profiles (Postgres, Qdrant, …) on loopback

Post-baseline evolution is governed by `runbook/part-100-hps-hes-platform-completion.md`. Production Hermes remains read-only until an HPS cutover transaction is ARMED with a valid local arm state.

## HADA

`HADA_RUNTIME=NOT_DEPLOYED` on this host unless a genuine runtime is later evidenced.

## Telegram

`TELEGRAM_STATE=READY_FOR_EXCLUSIVE_CUTOVER` — no duplicate production poller.
