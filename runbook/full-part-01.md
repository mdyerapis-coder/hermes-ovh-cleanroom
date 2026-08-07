- profiles;
- skills;
- memory/state;
- provider configuration;
- tool integrations;
- scheduled jobs;
- recovery tooling;
- local inference fallback where hardware permits.

## 5.2 HSP — Hermes Secrets Plane

Expected:

- current authoritative secret backend;
- Bitwarden-backed design if that remains canonical;
- bootstrap-only external credential where unavoidable;
- no plaintext application secrets in Git;
- fail-closed secret validation;
- transient secret cleanup;
- logged secret access failures with redacted evidence.

## 5.3 HPS — Hermes Provisioning System

Expected:

- reproducible provisioning;
- idempotent application;
- dry-run/check mode;
- resume capability;
- phase logging;
- evidence capture;
- machine inventory;
- package/runtime provisioning;
- recovery handoff.

## 5.4 HES — Hermes Environment / Execution System

Expected:

- HES CLI/TUI;
- system status;
- inventory;
- health;
- recovery state;
- deployment state;
- audit/evidence view;
- HADA view/integration where genuine source exists;
- clearly identified clean-room host.

## 5.5 Supporting services

Deploy when confirmed current by authoritative source:

- n8n;
- PostgreSQL;
- Qdrant;
- Crawl4AI;
- Stirling PDF;
- OCR pipeline;
- ntfy;
- Tailscale;
- logging/health monitoring;
- encrypted backup tooling.

If a listed service has been superseded, record that fact instead of installing obsolete software.

---

# 6. TARGET HOST BASELINE

Preferred minimum:

```text
CPU:      4 vCPU
RAM:      16 GB
Storage:  120 GB SSD/NVMe usable
Swap:     8 GB
OS:       Ubuntu Server 24.04 LTS
Network:  OVH IPv4/IPv6 + Tailscale
```

A larger host is acceptable.

If the actual host is smaller:

1. continue discovery and CI implementation;
2. calculate service resource requirements;
3. deploy mandatory core components only if safe;
4. mark constrained components:
   `BLOCKED_RESOURCE_FLOOR`;
5. do not falsify acceptance.

---

# 7. SOURCE OF TRUTH

Resolve conflicting data in this order:

1. protected default branch of authoritative repository;
2. current release tag;
3. current committed deployment manifests;
4. current running production configuration inspected read-only;
5. verified backup/restore manifests;
6. current project documentation;
7. historical notes.

Never guess.

Create:

```text
evidence/discovery/source-of-truth.md
```

For every conflict record:

- component;
- candidate value;
- source;
- source date;
- commit SHA/version;
- chosen value;
- reason;
- superseded value if any.

---

# 8. PHASE 0 — CREATE EXECUTION WORKSPACE

On the Grok control machine:

```bash
set -Eeuo pipefail
umask 077

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
WORK_ROOT="$HOME/hermes-ovh-cleanroom-$RUN_ID"

mkdir -p "$WORK_ROOT"/{
  evidence/discovery,
  evidence/faults/repair-attempts,
  evidence/ci,
  evidence/host,
  evidence/deploy,
  evidence/acceptance,
  evidence/backups,
  logs
}

cd "$WORK_ROOT"
```

Create initial metadata:

```bash
{
  echo "run_id=$RUN_ID"
  echo "started_utc=$(date -u --iso-8601=seconds)"
  echo "timezone=Australia/Melbourne"
  echo "target=separate-ovh-cleanroom"
} > evidence/run.meta
```

Initialise the fault ledger before any other operational command.

---

# 9. PHASE 1 — DISCOVER AUTHORITATIVE REPOSITORIES

## 9.1 Git/GitHub identity

Run and capture:

```bash
gh auth status
git --version
gh --version
```

Do not print tokens.

If inside known Hermes/HPS/HES checkouts:

```bash
git status --short
git remote -v
git branch --show-current
git rev-parse HEAD
git tag --sort=-creatordate | head -30
```

## 9.2 Repository inventory

Find authoritative repositories using:

- existing `git remote -v`;
- GitHub account/organisation repository listing;
- known project references;
- existing deployment manifests.

Do not invent repository names.

Create:

```text
evidence/discovery/repositories.tsv
```

Fields:

```text
role
owner_repo
default_branch
remote_url
head_sha
release_tag
evidence_source
status
```

Status must be one of:

```text
CURRENT
SUPERSEDED
REPLACED
TRIALLED
PENDING_VERIFICATION
```

---

# 10. PHASE 2 — READ-ONLY CURRENT HOST INVENTORY

Only if current host access exists.

Collect:

```bash
hostnamectl
cat /etc/os-release
uname -a
df -hT
free -h
systemctl --no-pager --type=service --state=running
systemctl list-unit-files --no-pager
ss -lntup
tailscale status 2>/dev/null || true
docker ps --format '{{json .}}' 2>/dev/null || true
podman ps --format json 2>/dev/null || true
```

Inspect relevant units:

```bash
systemctl cat <relevant-unit>
systemctl show <relevant-unit>
```

Inspect safe configs.

For env files, output **names only**:

```bash
sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' <envfile>
```

Never copy secret values to Git or logs.

## 10.1 Known existing-state checks

Specifically verify rather than assume:

- which Hermes system gateway unit is canonical;
- whether any duplicate user gateway unit exists;
- current Hermes version;
- current model/provider order;
- current local fallback model;
- current memory/state DB paths;
- current profiles;
- current installed/enabled skills;
- current n8n/Postgres/Qdrant/Crawl4AI/Stirling state;
- current Tailscale node state;
- current backup mechanism;
- HPS/HES source locations;
- whether HADA is runtime-deployed or source-only.

---

# 11. PHASE 3 — PERSISTENT STATE INVENTORY

Identify, without mutating:

- Hermes memory database;
- Hermes state/session database;
- profile configuration;
- skill configuration;
- scheduled jobs;
- n8n database/config;
- PostgreSQL databases;
- Qdrant collections/snapshots;
- crawl/document indexes;
- HSP metadata;
- backup manifests.

Create:

```text
evidence/discovery/persistent-state.md
```

For each item:

- source host;
- path/database;
- owner;
- format;
- size;
- service dependency;
- backup method;
- migration method;
- whether safe to copy during clean-room testing;
- checksum if safe;
- migration status.

Do not migrate state that can cause duplicate external actions until the receiving service is isolated.

---

# 12. PHASE 4 — CLEAN-ROOM GITOPS REPOSITORY

Use an existing isolated repository if one already exists and is clearly intended for this build.

Otherwise create a private repository:

```text
hermes-ovh-cleanroom
```

The repository owns host/deployment automation.

Application source repositories remain canonical upstreams unless current architecture says otherwise.

Suggested layout:

```text
.github/
  workflows/
    pr-audit.yml
    deploy-production.yml
    scheduled-health.yml
    backup-restore-test.yml
  dependabot.yml

ansible/
  inventory/
  roles/
  playbooks/

compose/
  compose.yaml
  compose.production.yaml

config/
  versions.lock
  services.yaml
  ports.yaml
  secret-contract.yaml

hsp/
hps/
hes/

scripts/
  fault-log.sh
  preflight.sh
  validate-config.sh
  backup.sh
  restore-test.sh
  deploy.sh
  healthcheck.sh
  acceptance.sh
  rollback.sh

systemd/
tests/
  unit/
  integration/
  smoke/
  acceptance/

evidence/
docs/
  architecture.md
  service-inventory.md
  operations.md
  recovery.md
  secrets-contract.md

