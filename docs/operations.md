# Operations

## Common commands

```bash
./hes/bin/hes status
./hes/bin/hes health
./hes/bin/hes hosts
./hes/bin/hes releases
./hes/bin/hes deploy status
./hes/bin/hes cutover status
./hes/bin/hes secrets
./hes/bin/hes hada
./hsp/bin/hsp status
./hps/bin/hps inventory
./hps/bin/hps plan -e cleanroom
./hps/bin/hps verify
./hps/bin/hps protect -e production
./hps/bin/hps cutover status
./scripts/healthcheck.sh
./scripts/acceptance.sh
```

HES always prints `environment` and `target_host`. Mutations go through HPS only.
Production mutation requires local arm (`hps cutover arm`) and cutover `ARMED+`.

## Deployment

Green merges to `main` trigger automatic deploy to `hermes-ovh-cleanroom` only.

Release layout:

```text
/opt/hermes-cleanroom/releases/<sha>
/opt/hermes-cleanroom/current -> releases/<known-good>
/opt/hermes-cleanroom/previous -> releases/<prior>
```
