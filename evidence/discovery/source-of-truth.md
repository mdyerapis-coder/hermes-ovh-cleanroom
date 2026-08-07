# Source of Truth Inventory

Generated during autonomous clean-room execution. Unknowns marked PENDING_VERIFICATION.

## Host (direct observation)

| Fact | Value | Status | Evidence |
|------|-------|--------|----------|
| hostname | hermes-ovh-cleanroom | VERIFIED | evidence/host/preflight.txt |
| OS | Ubuntu 24.04.4 LTS | VERIFIED | evidence/host/preflight.txt |
| Tailscale IPv4 | 100.121.178.125 | VERIFIED | `tailscale ip -4` |
| Public IPv4 | 139.99.221.109 | VERIFIED | evidence/host/preflight.txt |
| vCPU | 8 | VERIFIED | nproc |
| RAM | ~30 GiB | VERIFIED | free -h |
| Disk | ~193G ext4 | VERIFIED | df -hT |
| Docker | 29.7.2 | VERIFIED | docker --version |
| Compose | v5.4.0 | VERIFIED | docker compose version |
| GitHub identity | mdyerapis-coder | VERIFIED | gh auth status |
| Repository visibility | public (API isPrivate=false) | VERIFIED | gh api repos/... |
| Auto-merge at discovery | disabled | VERIFIED | allow_auto_merge=false |
| Required check at discovery | BOOTSTRAP-GATE only | VERIFIED | branch protection API |
| AUDIT-GATE at discovery | not yet present | VERIFIED | no pr-audit.yml on main |

## Production reference

| Fact | Value | Status | Evidence |
|------|-------|--------|----------|
| hermes-station-1 Tailscale | 100.81.157.33 online | VERIFIED | tailscale status |
| Read-only SSH inventory | blocked by Tailscale ACL (ubuntu not permitted) | BLOCKED | evidence/discovery/production-readonly-probe.txt |
| Production mutation | never | POLICY | AGENTS.md / runbook |

## Upstream repositories (cloned shallow for structure)

| Role | Repo | Status | Notes |
|------|------|--------|-------|
| cleanroom-control | mdyerapis-coder/hermes-ovh-cleanroom | CURRENT | this repo |
| hermes-runtime | mdyerapis-coder/hermes-agent | CURRENT | public clone; agent+gateway+docker |
| hps | mdyerapis-coder/hermes-provisioning-system | CURRENT | Go HPS |
| hes | mdyerapis-coder/hes-cli | CURRENT | Python HES CLI |
| hada | mdyerapis-coder/hada | CURRENT | source present; runtime NOT observed on clean-room |
| config | mdyerapis-coder/hermes-config | CURRENT | profiles/skills/config.yaml |

## Conflicts

None resolved by guessing. Production runtime inventory remains PENDING_VERIFICATION due to SSH ACL.
