# HPS/HES Integration Evidence

**Result:** `PASS`  
**Commit:** `0ff5f4a4ba0c6e6828dd1663e6fac7de3a4b4d2f`  
**Host:** `hermes-ovh-cleanroom`  
**Timestamp:** `2026-08-07T11:42:35.063665+00:00`

## Authority flow

`User/HES -> HPS -> HSP/host/runtime -> evidence -> HES status`

## Proofs

- hes deploy plan invokes hps plan
- hes cutover status invokes hps cutover status
- hes secrets uses hsp + hps secrets-refs
- hes rollback/backup/restore delegate to hps
- hps apply success only after healthcheck verify
