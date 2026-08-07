# Platform controller Grok PATH repair

- Fault ID: `FLT-20260807-PLATPATH01`
- Host: `hermes-ovh-cleanroom`
- Observed controller failure: 2026-08-07 21:15:25 AEST
- Root cause verified: 2026-08-07 21:23 AEST
- Component: `hermes-platform-controller.service`
- Severity: error
- Status: repair proposed; requires audited merge and host retest

## Observed

The platform controller systemd unit started and exited immediately with status 1. The service environment defined a PATH that omitted the actual Grok installation directory.

Service-user resolution test returned:

```text
GROK=MISSING
GH=/usr/bin/gh
GIT=/usr/bin/git
PYTHON=/usr/bin/python3
```

Normal `ubuntu` shell resolution returned:

```text
/home/ubuntu/.grok/bin/grok
```

The controller script performs `command -v grok` before creating its session-id file, explaining the immediate pre-session exit.

A separate unit warning was also confirmed: `StartLimitIntervalSec` was incorrectly placed in `[Service]`; systemd ignored it.

## SSH finding

The concurrent interactive SSH disconnect was not caused by a host reboot, SSH daemon restart, Tailscale loss, firewall change, or interface failure. Host journal evidence showed the client disconnect as `Normal Shutdown`. The platform controller had already exited two seconds earlier.

## Repair

- Add `/home/ubuntu/.grok/bin` to the service PATH.
- Move `StartLimitIntervalSec=0` into `[Unit]`.
- Make the installer verify that the service-user environment resolves `grok` before installing/enabling the service.
- Add regression tests for the Grok path and systemd directive section.

## Completion requirement

Do not mark this fault resolved until the audited repair merges, the host installs the merged unit, `systemd-analyze verify` is clean, the service-user environment resolves Grok, and the platform controller starts successfully far enough to create its session-id and begin the Grok platform mission.
