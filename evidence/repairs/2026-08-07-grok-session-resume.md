# Repair Note — Grok stale named-session collision

Date: 2026-08-07 (Australia/Melbourne)
Host: `hermes-ovh-cleanroom`
Component: `hermes-grok-controller.service`
Session: `cef6bfc1-afb3-4f58-8829-72f2fa0abf32`

## Observed fault

The autonomous controller repeatedly exited with rc=1 and retried every 300 seconds. Journal evidence showed repeated errors of the form:

`Session ID cef6bfc1-afb3-4f58-8829-72f2fa0abf32 is already in use.`

Observed retry timestamps included 17:08:21, 17:13:22, and 17:18:23 Melbourne time.

## Root cause

`ops/grok-controller.sh` used `--session-id <UUID>` for every controller turn, including retries after the first named session had already been created. Current Grok CLI semantics distinguish a specific new session ID from explicitly resuming an existing session with `--resume <ID>`.

## Repair

Preserve the existing session UUID and session history. Do not delete the session. Use:

- `--session-id <UUID>` only for the first controller launch;
- `--resume <UUID>` for all subsequent controller turns and service restarts after the `started` marker exists.

This repair is additive and preserves the original session state.

## Required validation

1. Merge only after `BOOTSTRAP-GATE` succeeds on the exact repair PR head SHA.
2. Pull `main` on `hermes-ovh-cleanroom`.
3. Stop the controller before replacing the installed `/usr/local/libexec/hermes-grok-controller` binary.
4. Reinstall from the audited repository source and restart the service.
5. Confirm the repeated `Session ID ... is already in use` error no longer occurs.
6. Confirm the controller remains active and Grok progresses far enough to create the first governance/implementation PR.
7. Preserve controller fault history and this repair note permanently.

## Source evidence

xAI Grok CLI reference, current as of 2026-08-07, documents `--resume <ID>` for an existing session and `--session-id <UUID>` for a specific named session. The headless scripting documentation likewise exposes both session mechanisms.
