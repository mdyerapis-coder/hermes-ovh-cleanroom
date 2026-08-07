# Architecture — Hermes OVH Clean-room

This repository controls an isolated **clean-room** deployment of Hermes / HPS / HES on a separate OVH host.

## Identity

- Host: `hermes-ovh-cleanroom`
- Control plane: GitHub PR + CI (`BOOTSTRAP-GATE` + `AUDIT-GATE`)
- Existing production Hermes: **read-only reference only**

## Layers

1. **Governance** — branch protection, exact-success gates, auto-merge after dual green
2. **HSP** — secrets plane (names in Git, values never in Git)
3. **HPS** — idempotent provisioning for the clean-room host only
4. **Hermes runtime** — agent + gateway (Telegram polling disabled until exclusive cutover)
5. **HES** — operator CLI with unmistakable clean-room banner
6. **Supporting services** — optional compose profiles (Postgres, Qdrant, …) on loopback

## HADA

`HADA_RUNTIME=NOT_DEPLOYED` on this host unless a genuine runtime is later evidenced.

## Telegram

`TELEGRAM_STATE=READY_FOR_EXCLUSIVE_CUTOVER` — no duplicate production poller.
