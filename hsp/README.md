# HSP — Hermes Secrets Plane (clean-room)

Fail-closed secret resolution for hermes-ovh-cleanroom.

- Secret **values** never enter Git.
- Contract of names lives in `config/secret-contract.yaml`.
- Runtime material is resolved from environment or a local secrets directory with mode 0600.
