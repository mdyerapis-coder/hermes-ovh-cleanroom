# Final Report — Hermes OVH Clean-room Autonomous Execution

## Identity

| Field | Value | Status |
|-------|-------|--------|
| OVH hostname | hermes-ovh-cleanroom | VERIFIED |
| Tailscale IPv4 | 100.121.178.125 | VERIFIED |
| OS | Ubuntu 24.04.4 LTS | VERIFIED |
| Deployed release path | /opt/hermes-cleanroom/releases/15ffd3d6e08f7d6b4cf02a9dd183b498f728c8a1 | VERIFIED |
| Repo SHA (evidence generation) | 15ffd3d6e08f7d6b4cf02a9dd183b498f728c8a1 | VERIFIED |
| Deployment timestamp (Melbourne) | 2026-08-07T18:56:43+10:00 | VERIFIED |
| Reboot | 2026-08-07 16:53 AEST; post-reboot HEALTH=PASS | VERIFIED |

## GitHub governance

| Field | Value | Status |
|-------|-------|--------|
| Repository | mdyerapis-coder/hermes-ovh-cleanroom | VERIFIED |
| Protected branch | main | VERIFIED |
| Required gates | BOOTSTRAP-GATE, AUDIT-GATE | VERIFIED |
| Strict / up-to-date | true | VERIFIED |
| Human approvals | 0 | VERIFIED |
| enforce_admins | true | VERIFIED |
| Force push / deletion | disabled | VERIFIED |
| Auto-merge | enabled | VERIFIED |
| First governance PR | #3 | VERIFIED |
| Host/runtime PR | #6 | VERIFIED |
| Evidence recovery PR | #8 | VERIFIED |
| Protection evidence | evidence/governance/main-protection-after-audit-gate.json | VERIFIED |

## Runtime

| Component | Version | State | Bind/Exposure | Evidence |
|-----------|---------|-------|---------------|----------|
| hermes-agent | 0.19.0 (src d71033a) | active systemd (no prod poll) | private | evidence/deploy/hermes-runtime-install.txt |
| hermes-gateway | cleanroom | active; polling disabled | N/A | systemd/units/hermes-gateway.service |
| HSP | cleanroom | operational; BACKUP key available | local | evidence/acceptance/hsp-status-final.txt |
| HPS | cleanroom | plan/apply/verify OK | cli | evidence/deploy/hps/ |
| HES | cleanroom | operational; clean-room banner | cli | evidence/acceptance/hes-status-final.txt |
| HADA | n/a | NOT_DEPLOYED | n/a | config/services.yaml |
| Telegram | n/a | READY_FOR_EXCLUSIVE_CUTOVER | n/a | config/services.yaml |
| Tailscale | active | connected | 100.121.178.125 | evidence/host/preflight.txt |
| Firewall (ufw) | active | deny in / allow out; SSH+tailscale0 | host | evidence/host/bootstrap-*.txt |
| Swap | 8G | active | /swapfile | evidence/acceptance/persistence-verify.txt |

## Fault/repair summary

| Fault ID | Phase | Severity | Root Cause | Attempts | Final State |
|----------|-------|----------|------------|----------|-------------|
| FLT-20260807-EC1D1A7D | toolchain-bootstrap | error | grok missing early | 0 | resolved |
| FLT-20260807-4C86DBC7 | toolchain-bootstrap | error | grok missing early | 0 | resolved |
| FLT-20260807-053551 | toolchain-bootstrap | warning | SSH drop during bootstrap | 0 | resolved |
| FLT-20260807-PRODSSH01 | discovery | warning | Tailscale ACL | 0 | blocked (external) |
| FLT-20260807-TRIVY001 | ci | error | bad Trivy asset URL | 1 | resolved |
| CTRL-20260807T* (23) | autonomous-controller | warning | session incomplete retries | n/a | resolved (ingested) |

Full ledger: evidence/final/fault-ledger.jsonl

## Backups

- Encrypted backups under /opt/hermes-cleanroom/shared/backups
- Restore tests: PASS (isolated temp targets)
- Evidence: evidence/final/backup-results.md, evidence/final/restore-results.md

## Rollback

- Rollback test 15ffd3d ↔ 54441ed: PASS
- Evidence: evidence/acceptance/rollback-test-*.md

## Reboot / persistence

- Host rebooted 2026-08-07 16:53 AEST
- Post-reboot verify: PASS
- Services active after reboot; hermes src/venv persisted
- Evidence: evidence/acceptance/post-reboot-verify-20260807T065315Z.txt, evidence/acceptance/persistence-verify.txt

## Remaining blockers

See evidence/final/unresolved-blockers.md

- Production SSH inventory: BLOCKED_EXTERNAL_PERMISSION
- Optional provider/Telegram tokens: BLOCKED_EXTERNAL_SECRET (optional)
- Hermes tag v2026.8.3 not on remote: PENDING_VERIFICATION (installed default branch commit)

## Verified facts vs pending

### Verified
- Dual-gate governance active and proven
- Clean-room deploy/health/HSP/HPS/HES
- Backup/restore/rollback/reboot
- HADA not deployed (truthful)
- Telegram not live (truthful)

### Pending verification
- Exact hermes-agent tag alignment with v2026.8.3
- Provider live completion without credentials
- Production host full inventory

### External blockers
- Prod SSH ACL
- Optional API/Telegram secrets absent by design for non-cutover clean-room

## Overall disposition

```
COMPLETE_READY_FOR_EXCLUSIVE_CUTOVER
```

Clean-room platform is implemented, audited, deployed, reboot-proven, backup/restore-proven, and rollback-proven on hermes-ovh-cleanroom only. Exclusive Telegram cutover was not performed (safety). Production Hermes was never mutated.
