# HPS — Hermes Provisioning System (v1)

HPS is the **sole** infrastructure/runtime mutation authority for the clean-room platform and for production cutover.

## Capabilities (v1)

- Authoritative host inventory (`hps/inventory/hosts.yaml`)
- Explicit target environments: `cleanroom`, `production`, `rollback`, `test`
- Deterministic `plan` with digest, state digest, secret references, backup/rollback metadata
- `apply` only against an unchanged valid plan digest (state-drift gated)
- Post-apply `verify` and automatic rollback on critical acceptance failure
- `backup`, `restore-test`, controlled `restore`
- Release current/previous management
- Configuration/runtime `drift` detection
- HSP secret-reference consumption without secret disclosure
- Production mutation protection (local arm + cutover state)
- Cutover state machine with illegal-transition fail-closed
- Reboot-persistence observation
- Canonical fault integration via `scripts/fault-log.sh`

## Commands

```text
hps inventory|target|preflight|plan|apply|verify|resume|rollback
hps backup|restore-test|restore|releases|drift|secrets-refs|protect
hps reboot-persistence
hps cutover status|transition|arm|disarm
```

## Production safety

- Production/rollback targets refuse mutation without a valid **local** arm transaction (`HPS_STATE_DIR/arm.json`, never in Git) and an appropriate cutover state.
- Telegram exclusivity and exclusive cutover steps are enforced by the cutover workflow; do not start a second production poller.

## Evidence

Runtime and plan evidence lands under `evidence/hps/` when commands execute.
Completion package: `evidence/hps/HPS_V1.json` + `HPS_V1.md` (only when evidence-backed).
