Every unit must define where appropriate:

- dedicated user;
- working directory;
- environment source;
- restart policy;
- startup dependency;
- timeout;
- hardening options;
- logging;
- health/recovery relationship.

Run:

```bash
systemd-analyze verify <unit-files>
```

Inspect:

```bash
systemctl status
journalctl
```

Any crash/restart loop is a fault and blocks acceptance.

---

# 31. PHASE 23 — CONTAINER SECURITY

For containerised services:

- pin image version/digest;
- no `latest` in production;
- run non-root where supported;
- drop unnecessary capabilities;
- `no-new-privileges` where compatible;
- read-only root filesystem where compatible;
- bounded memory/CPU where sensible;
- private networks;
- explicit volumes;
- health checks;
- no broad host mounts;
- no Docker socket unless demonstrably required.

Generate SBOM for deployed images.

Scan candidate images before merge/deploy.

---

# 32. PHASE 24 — BACKUPS

Implement backups before declaring the host complete.

Required targets based on deployed components:

- Hermes memory/state;
- HSP metadata where backup-safe;
- PostgreSQL;
- n8n state;
- Qdrant snapshots;
- HES/HPS configuration;
- deployment manifests;
- service configs;
- evidence.

Use encrypted off-host backup where current architecture provides a destination.

Never rely only on the same OVH disk.

## 32.1 Restore testing

A backup is not accepted until restore is tested.

Use an isolated temporary restore target.

Verify:

- backup can decrypt;
- files/databases restore;
- expected record counts/checksums;
- restored services can start in isolation;
- no external production action fires from restored test state.

Record:

```text
evidence/backups/restore-test-<timestamp>.md
```

---

# 33. PHASE 25 — RELEASE MODEL

Every merged commit becomes an immutable release.

Release identity:

```text
Git commit SHA
```

Images:

```text
ghcr.io/<owner>/<image>:sha-<sha>
```

or canonical equivalent.

Do not deploy `latest`.

Each release evidence bundle includes:

- Git SHA;
- PR number;
- AUDIT-GATE result;
- image digest;
- dependency lock hashes;
- SBOM;
- vulnerability result;
- migration plan/result;
- configuration checksum;
- timestamp;
- fault summary.

---

# 34. PHASE 26 — AUTOMATIC DEPLOYMENT WORKFLOW

Create:

```text
.github/workflows/deploy-production.yml
```

Trigger:

```yaml
on:
  push:
    branches:
      - main
```

Use a `production` GitHub environment with:

- no required human reviewers;
- only protected `main` permitted;
- environment-scoped bootstrap/deployment secrets;
- no administrator bypass requirement.

Use concurrency:

```yaml
concurrency:
  group: hermes-ovh-production
  cancel-in-progress: false
```

## 34.1 Deployment sequence

1. checkout exact merged SHA;
2. authenticate Tailscale using workload identity federation where available;
3. verify target host identity;
4. verify target is the clean-room OVH host;
5. verify free disk/RAM;
6. verify backup destination;
7. acquire deployment lock;
8. identify previous known-good release;
9. create pre-deploy backup;
10. validate migrations;
11. transfer/pull immutable release;
12. stage configuration;
13. resolve secrets on target;
14. start candidate;
15. run health checks;
16. run acceptance suite;
17. mark candidate known-good on success;
18. archive deployment evidence;
19. release lock.

On any failure after mutation begins:

1. log fault;
2. capture logs;
3. run rollback;
4. restore previous configuration/data if migration contract requires;
5. restart previous known-good;
6. prove previous release healthy;
7. mark failed release;
8. open/continue autonomous repair PR.

---

# 35. PHASE 27 — SERVER RELEASE LAYOUT

Use an atomic release structure such as:

```text
/opt/hermes-cleanroom/
  releases/
    <sha-1>/
    <sha-2>/
  current -> releases/<known-good-sha>
  previous -> releases/<previous-sha>
  shared/
    data/
    models/
    backups/
    logs/
    secrets-runtime/
```

Activation should be atomic where possible:

```text
stage → validate → switch current symlink → restart → verify
```

Keep enough historical releases for rollback.

Do not mix mutable source checkout state directly into `current`.

---

# 36. PHASE 28 — DATABASE MIGRATION SAFETY

Every schema/data migration must be classified:

```text
NONE
BACKWARD_COMPATIBLE
REQUIRES_DOWNTIME
IRREVERSIBLE
```

CI must dry-run or validate migrations before merge.

For irreversible migrations:

- require a tested pre-migration backup;
- require explicit rollback/recovery path;
- if no safe autonomous rollback is possible, do not execute destructive migration automatically;
- mark:
  `BLOCKED_UNSAFE_IRREVERSIBLE_MIGRATION`.

This is a safety boundary, not a routine approval request.

---

# 37. PHASE 29 — ACCEPTANCE TEST SUITE

Create deterministic acceptance tests.

## 37.1 Host

Pass criteria:

- intended OS;
- expected CPU/RAM/storage;
- time sync;
- Tailscale connected;
- firewall active;
- no unexpected public listeners;
- SSH hardened;
- no failed systemd units.

## 37.2 Hermes

Pass criteria:

- service active;
- health command/endpoint healthy;
- profiles load;
- skills enumerate;
- memory write/read test;
- provider routing test;
- fallback test where configured;
- logs free of secret values;
- no restart loop.

## 37.3 HSP

Pass criteria:

- required secret names resolve;
- values never printed;
- missing mandatory secret fails closed;
- runtime secret files permissioned correctly.

## 37.4 HPS

Pass criteria:

- plan succeeds;
- second apply is idempotent;
- verify succeeds;
- resume/checkpoint behaviour works;
- evidence produced.

## 37.5 HES

Pass criteria:

- starts;
- identifies clean-room host;
- reports real service state;
- audit view reads actual evidence;
- recovery state works;
- `/hada` is truthful.

## 37.6 Supporting services

For every deployed service:

- process/container healthy;
- intended bind only;
- persistent storage mounted;
- functional smoke test;
- backup target included where needed.

## 37.7 Reboot test

Reboot the clean-room OVH host only.

After reboot:

- Tailscale returns;
- core services return;
- no duplicate services appear;
- persistent state remains;
- health suite passes.

A host that only works before reboot is not complete.

---

# 38. PHASE 30 — CHAOS / RECOVERY TESTS

Perform bounded recovery tests against the clean-room host.

Examples:

- stop Hermes service → verify supervisor/recovery behaviour;
- kill supporting container → verify restart;
- temporarily make optional provider unavailable → verify fallback;
- deliberately fail a candidate deployment health check → prove rollback;
- restore backup into isolated test target.

Do not deliberately corrupt the production reference host.

Every induced test fault must still be recorded, classified as:

`test-induced`

and resolved.

---

# 39. PHASE 31 — SCHEDULED HEALTH AUDIT

Create:

```text
.github/workflows/scheduled-health.yml
```

At a reasonable cadence, e.g. daily.

It should:

- connect privately;
- run read-only health;
- verify listener contract;
- verify backup freshness;
- verify disk/RAM thresholds;
- verify core services;
- verify deployed SHA equals recorded release;
- emit evidence.

If a repair is required:

- create an issue/branch/PR automatically;
- run normal CI;
- auto-merge only through `AUDIT-GATE`;
- deploy normally.

Do not mutate production directly from the health check.

---

# 40. PHASE 32 — AUTOMATIC DEPENDENCY MAINTENANCE

Configure Dependabot/Renovate or canonical equivalent for:

- GitHub Actions;
- containers;
- language dependencies.
