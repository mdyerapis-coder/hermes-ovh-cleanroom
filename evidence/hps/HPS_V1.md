# HPS v1 Evidence

**Result:** `PASS`  
**Host:** `hermes-ovh-cleanroom`  
**Verified commit:** `0ff5f4a4ba0c6e6828dd1663e6fac7de3a4b4d2f`  
**Deployed release:** `/opt/hermes-cleanroom/releases/0ff5f4a4ba0c6e6828dd1663e6fac7de3a4b4d2f`  
**Timestamp (UTC):** `2026-08-07T11:42:35.063665+00:00`

## Capabilities

| Capability | Result |
|---|---|
| inventory | PASS |
| target_resolution | PASS |
| plan | PASS |
| apply | PASS |
| verify | PASS |
| rollback | PASS |
| backup | PASS |
| restore_test | PASS |
| restore | PASS |
| drift | PASS |
| release_management | PASS |
| secret_references | PASS |
| production_protection | PASS |
| fault_ledger | PASS |
| evidence_output | PASS |
| github_governance | PASS |
| reboot_persistence | PASS |
| cutover_state_machine | PASS |

## Notes

- Production mutation protection verified (blocked without arm).
- Plan digest / apply / verify / rollback cycle proven on clean-room.
- Backup + restore-test proven.
- Cutover state machine illegal transitions fail closed.
- Evidence artefacts under `evidence/hps/`.
- PATH note: `/usr/local/bin/hps` is a different unrelated binary; repo authority is `./hps/bin/hps`.

## Evidence files

- `evidence/hps/apply-plan-20260807T114004Z-1cacf0b03118.json`
- `evidence/hps/apply-plan-20260807T114127Z-9cee7f05ff9c.json`
- `evidence/hps/apply-post-merge.out`
- `evidence/hps/backup-cmd-20260807T114111Z.json`
- `evidence/hps/backup-host-20260807T114110Z.out`
- `evidence/hps/cutover-illegal-20260807T114110Z.out`
- `evidence/hps/cutover-status-20260807T114110Z.json`
- `evidence/hps/drift-20260807T114111Z.json`
- `evidence/hps/drift-host-20260807T114110Z.out`
- `evidence/hps/host-proof-suite-20260807T114110Z.log`
- `evidence/hps/inventory-20260807T114004Z.json`
- `evidence/hps/inventory-20260807T114111Z.json`
- `evidence/hps/plan-20260807T114004Z-1cacf0b03118.json`
- `evidence/hps/plan-20260807T114112Z-9598bc939056.json`
- `evidence/hps/plan-20260807T114127Z-9cee7f05ff9c.json`
- `evidence/hps/plan-post-merge.out`
- `evidence/hps/protect-production-20260807T114110Z.json`
- `evidence/hps/reapply-after-rollback-20260807T114126Z.out`
- `evidence/hps/reboot-persistence-20260807T114110Z.out`
- `evidence/hps/reboot-persistence-20260807T114111Z.json`
- `evidence/hps/releases-20260807T114110Z.json`
- `evidence/hps/replan-after-rollback-20260807T114126Z.out`
- `evidence/hps/restore-test-20260807T114111Z.json`
- `evidence/hps/restore-test-host-20260807T114110Z.out`
- `evidence/hps/rollback-20260807T114126Z.json`
- `evidence/hps/rollback-cycle-20260807T114126Z.log`
- `evidence/hps/rollback-test-20260807T114126Z.out`
- `evidence/hps/secrets-refs-20260807T114110Z.json`
- `evidence/hps/target-cleanroom-20260807T114110Z.json`
- `evidence/hps/verify-20260807T114110Z.json`
- `evidence/hps/verify-host-20260807T114110Z.out`
