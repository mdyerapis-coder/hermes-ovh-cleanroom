# Service inventory

See `config/services.yaml` for machine-readable intended state.

| Component | Required | Supervision | Notes |
|-----------|----------|-------------|-------|
| hermes-agent | yes | systemd | Planned runtime |
| hermes-gateway | yes | systemd | Polling disabled until cutover |
| hsp | yes | local | Fail-closed secrets |
| hps | yes | cli | Idempotent provisioner |
| hes | yes | cli | Clean-room operator UI/CLI |
| postgres | no | compose | Profile `datastores` |
| qdrant | no | compose | Profile `datastores` |
| n8n | no | compose | Optional |
| HADA | no | n/a | NOT_DEPLOYED |
