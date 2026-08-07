`DENY`

Create:

```text
config/ports.yaml
```

Every listener must declare:

```yaml
component:
port:
protocol:
bind:
exposure:
health_probe:
reason:
```

Allowed exposure classes:

```text
loopback
container-private
tailscale
public
```

Databases and internal services should normally be loopback/container-private/Tailscale only.

PostgreSQL, Qdrant, local LLM endpoint, internal Hermes API and admin panels must not become publicly reachable accidentally.

Acceptance compares real listeners with the contract.

Unexpected public listeners fail deployment acceptance.

---

# 21. PHASE 13 — HSP

Implement the current authoritative Hermes Secrets Plane.

Core rules:

- secret values never committed;
- bootstrap credential only outside HSP where unavoidable;
- GitHub variables only for non-secret data;
- GitHub environment secrets only for bootstrap/deployment identities;
- application/provider credentials live in the selected secret backend;
- generated secret files mode `0600`;
- temporary secret files removed;
- logs redact values;
- shell secret-handling scripts prohibit `set -x`.

Create:

```text
config/secret-contract.yaml
```

It records names and purpose only.

Example structure:

```yaml
secrets:
  SOME_SECRET_NAME:
    owner: component
    required: true
    external_exclusive: false
```

Generate real names from source.

Do not copy example names blindly.

## 21.1 Secret health

Implement a secret validation command that returns:

- available;
- missing;
- expired/invalid where detectable;
- inaccessible;
- optional.

Never print values.

Mandatory missing secrets cause the affected service to fail closed.

---

# 22. PHASE 14 — HPS

Use authoritative HPS source if it exists.

If implementation gaps exist, complete them through audited PRs.

HPS must provide:

- preflight;
- plan;
- apply;
- verify;
- resume;
- evidence.

Properties:

- idempotent;
- rerunnable;
- dry-run/check mode;
- phase checkpoints;
- mutation log;
- rollback where practical;
- no destructive repartitioning;
- no access to the production host as a mutation target.

Every HPS mutation must be attributable to:

- run ID;
- phase;
- Git SHA;
- host;
- timestamp.

HPS faults use the central fault ledger.

---

# 23. PHASE 15 — HERMES RUNTIME

Discover the exact current Hermes install method from authoritative source.

Implement the runtime so that:

- exactly one main Hermes Agent/runtime is active;
- API binds only to intended interfaces;
- profiles load;
- skills load;
- memory/state initialises;
- configured providers validate;
- tool discovery completes;
- background/scheduled jobs are installed;
- external-action jobs remain isolated during clean-room tests;
- health checks exist;
- service logs rotate;
- secrets are redacted.

Use systemd for host-level lifecycle management unless authoritative source specifies a stronger current approach.

Avoid duplicate system and user services for the same gateway.

---

# 24. PHASE 16 — HERMES PROFILES, SKILLS AND MEMORY

Inventory current profiles from source and the existing read-only host.

For each profile:

- name;
- role;
- provider;
- model;
- fallback chain;
- tool permissions;
- memory namespace;
- status;
- source of truth.

Install only current profiles.

For skills:

- inventory installed/enabled skills;
- verify source/trust classification;
- validate skill dependencies;
- disable broken skills rather than pretending they are healthy;
- record skill faults in the ledger.

For memory/state:

- initialise empty clean-room state;
- run schema validation;
- restore only deliberately selected state that cannot cause duplicated external side effects;
- verify backup/restore before accepting migration readiness.

---

# 25. PHASE 17 — PROVIDER CHAIN

Build provider configuration from current accepted source.

Validate each configured provider with:

- credential presence;
- endpoint;
- model availability where safely testable;
- basic completion request;
- timeout;
- rate-limit handling;
- fallback behaviour.

Do not treat an exhausted quota as an application defect.

Classify it:

`external/quota`

and test fallback behaviour.

Do not commit API keys.

---

# 26. PHASE 18 — LOCAL FALLBACK INFERENCE

If still part of the accepted architecture and host resources permit:

- install llama.cpp or canonical local inference server;
- bind to loopback only;
- install approved quantised fallback model;
- verify model checksum;
- store model outside Git;
- configure service resource limits;
- run deterministic smoke inference;
- verify Hermes fallback path.

Do not substitute models silently.

Any substitution requires:

- reason;
- source;
- benchmark/smoke evidence;
- explicit record in `source-of-truth.md`.

---

# 27. PHASE 19 — TELEGRAM GATEWAY

Install the canonical current gateway once.

Acceptance:

1. unit config validates;
2. service can start safely in test/no-poll mode if supported;
3. Telegram credential can be resolved from HSP;
4. synthetic update reaches routing;
5. provider/model path returns a response;
6. reply formatting passes;
7. shutdown/restart lifecycle passes;
8. no duplicate gateway unit is enabled.

If a separate test bot exists, perform end-to-end live test with it.

Otherwise:

- do not start the production bot poller;
- leave gateway installed and disabled from live polling;
- set:

`TELEGRAM_STATE=READY_FOR_EXCLUSIVE_CUTOVER`

---

# 28. PHASE 20 — SUPPORTING SERVICES

Deploy only if current source confirms they belong on this host.

## 28.1 PostgreSQL

Requirements:

- private network only;
- persistent storage;
- HSP-generated credential;
- version pinned;
- health check;
- backup;
- restore test.

## 28.2 n8n

Requirements:

- pinned version;
- PostgreSQL backing where current architecture requires;
- persistent configuration;
- private/Tailscale access;
- migration check;
- health check;
- backup/restore verification.

## 28.3 Qdrant

Requirements:

- pinned version;
- private binding;
- persistent storage;
- health check;
- snapshot/restore test.

## 28.4 Crawl4AI

Requirements:

- internal exposure only;
- resource limits;
- safe public test crawl;
- timeout behaviour;
- health check.

## 28.5 Stirling PDF

Requirements:

- internal/Tailscale access only;
- pinned image;
- health check;
- PDF operation smoke test.

## 28.6 OCR

Treat OCR as a separate resource-heavy stage.

Acceptance:

- service/tool starts;
- representative document fixture processed;
- timeout enforced;
- fault logged if OCR engine hangs;
- OCR failure cannot take down Hermes core.

## 28.7 ntfy

Only if still current.

Requirements:

- authenticated/restricted access;
- health check;
- synthetic notification;
- no secret leakage.

---

# 29. PHASE 21 — HES CLI/TUI

Use the authoritative HES implementation if present.

Complete missing functionality through PRs.

HES must expose real state.

Expected capabilities where source supports them:

```text
hes status
hes inventory
hes health
hes deploy status
hes recovery status
hes audit
hes logs
```

The host identity must be visually unmistakable:

```text
HERMES OVH CLEANROOM
```

or equivalent.

Do not make the new server look like the existing Hermes station.

## 29.1 `/hada`

If a genuine HADA integration exists:

- show live HADA state.

If not:

- show evidence-backed CI/HADA integration state;
- display:
  `HADA_RUNTIME=NOT_DEPLOYED`
  where appropriate.

Never fabricate a running controller.

---

# 30. PHASE 22 — SERVICE SUPERVISION

Create or install canonical systemd units for host services.
