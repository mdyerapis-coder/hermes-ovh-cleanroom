# Unresolved blockers

## BLOCKED_EXTERNAL_PERMISSION
- **FLT-20260807-PRODSSH01**: Read-only SSH inventory of production `hermes-station-1` denied by Tailscale ACL for user `ubuntu`.
- Impact: production runtime inventory incomplete; clean-room used upstream public clones instead.
- Production host remains unmutated.

## BLOCKED_EXTERNAL_SECRET (optional integrations)
- Optional provider secrets not present on clean-room: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, `TELEGRAM_BOT_TOKEN`.
- Impact: live provider completion tests and Telegram E2E not performed.
- Telegram remains `READY_FOR_EXCLUSIVE_CUTOVER` (no duplicate production poller).

## HADA
- `HADA_RUNTIME=NOT_DEPLOYED` — no genuine HADA runtime observed on clean-room.

## Hermes agent tag pin
- Requested tag `v2026.8.3` was not present on `mdyerapis-coder/hermes-agent` remote; installed from default branch at commit `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012` (package 0.19.0). Recorded as PENDING_VERIFICATION for exact tag alignment.
