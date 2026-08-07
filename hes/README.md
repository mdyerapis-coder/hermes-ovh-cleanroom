# HES — Hermes Operator Shell (v1)

Terminal-emulator agnostic operator interface. Plain text is fully usable; dark/blue high-contrast styling is a progressive enhancement when the terminal supports it.

## Authority

- **HES** = operator views and command routing
- **HPS** = sole infrastructure/runtime mutation authority
- **HSP** = secrets plane (presence only; never values)

HES never independently mutates managed infrastructure. Deploy/rollback/backup/restore/cutover mutations are delegated to HPS and success is reported only after HPS verification.

## Commands

```text
hes status|health|hosts|host|services|service|releases
hes deploy [status|plan|apply]
hes rollback|backup|restore|drift
hes faults|repairs|audit|github|secrets
hes cutover [status|transition|arm|disarm]
hes hada|help|inventory|recovery|logs
```

Environment context is always printed:

- `HES_ENVIRONMENT` / `HPS_ENVIRONMENT` (default `cleanroom`)
- `HES_TARGET_HOST` / `HPS_TARGET_HOST` (default `hermes-ovh-cleanroom`)

`/hada` always reports `HADA_RUNTIME=NOT_DEPLOYED` unless genuine runtime evidence exists.
