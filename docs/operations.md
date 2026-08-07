# Operations

## Common commands

```bash
./hes/bin/hes status
./hes/bin/hes health
./hsp/bin/hsp status
./hps/bin/hps plan
./scripts/healthcheck.sh
./scripts/acceptance.sh
```

## Deployment

Green merges to `main` trigger automatic deploy to `hermes-ovh-cleanroom` only.

Release layout:

```text
/opt/hermes-cleanroom/releases/<sha>
/opt/hermes-cleanroom/current -> releases/<known-good>
/opt/hermes-cleanroom/previous -> releases/<prior>
```
