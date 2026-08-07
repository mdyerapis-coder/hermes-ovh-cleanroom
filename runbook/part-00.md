# GROK AUTONOMOUS RUNBOOK
## Complete Clean-Room Hermes / HPS / HES Implementation on a Separate OVH Server

**Status:** Execution runbook  
**Operating mode:** Hands-free autonomous implementation  
**Primary auditor:** GitHub Pull Request + GitHub Actions CI  
**Merge policy:** Auto-merge when the complete required audit gate is green  
**Deployment policy:** Automatic after merge, with automatic rollback on failure  
**Existing Hermes environment:** Read-only source/reference only  
**Timezone:** Australia/Melbourne  
**Target:** A brand-new, separate OVH server  
**User involvement:** None during normal execution

---

# 1. EXECUTION DIRECTIVE TO GROK

You are the implementation agent.

Execute this runbook from start to finish. Do not merely produce recommendations, plans, shell snippets, or a handoff for somebody else.

Your objective is to deliver a completely implemented, independently audited, reproducible Hermes / HPS / HES installation on a separate OVH server while leaving the existing production Hermes environment untouched.

You are authorised to:

- inspect authoritative Git repositories;
- inspect the current Hermes host read-only where access is available;
- create branches;
- write code and configuration;
- create GitHub Pull Requests;
- inspect GitHub Actions results and logs;
- repair failed CI automatically;
- push repair commits;
- enable PR auto-merge;
- provision and configure the new OVH host;
- deploy automatically after an audited merge;
- run migrations;
- create and test backups;
- run health, smoke, integration and acceptance tests;
- automatically roll back failed deployments;
- retry repair/deployment loops within the limits defined here;
- maintain full evidence and fault/repair logs.

You are **not** required to request routine human approvals.

The user does not want to:

- approve PRs;
- click merge;
- approve deployments;
- approve normal package installation;
- approve normal configuration changes;
- approve routine repairs;
- answer questions that can be resolved from source, evidence or the existing environment.

If a fact can be discovered safely, discover it.

If an external secret, entitlement, account credential, bot token, billing action or provider-side permission genuinely does not exist or is unavailable, do not invent it and do not block unrelated work. Mark the affected integration with a precise blocker and complete everything else.

---

# 2. GOVERNANCE MODEL

The governance chain is:

```text
Grok change
   ↓
feature branch
   ↓
GitHub Pull Request
   ↓
independent CI audit jobs
   ↓
AUDIT-GATE
   ↓ only if exact success
GitHub auto-merge
   ↓
main
   ↓
automatic OVH deployment
   ↓
post-deployment acceptance
   ├── PASS → mark release known-good
   └── FAIL → automatic rollback + fault/repair cycle
```

No routine human review is required.

## 2.1 Definition of green

A PR is eligible to merge only when the final required check named:

`AUDIT-GATE`

has conclusion:

`success`

against the latest valid PR head or merge candidate.

`AUDIT-GATE` must not merely depend on GitHub's visual interpretation of required checks.

It must explicitly verify that every mandatory underlying CI job has result exactly:

`success`

The following are not accepted for mandatory jobs:

- skipped;
- neutral;
- cancelled;
- timed_out;
- stale;
- action_required;
- failure;
- missing.

This requirement exists because skipped and neutral GitHub checks may otherwise be treated as successful for branch protection purposes.

## 2.2 Merge authority

When all repository/ruleset requirements are satisfied and `AUDIT-GATE` is successful:

```bash
gh pr merge --auto --squash
```

or the equivalent GitHub API operation may be used.

Never use an administrator bypass.

Never use:

```bash
gh pr merge --admin
```

Never directly push normal implementation changes to protected `main`.

Never disable a failing required gate to obtain a merge.

## 2.3 Deployment authority

A successful audited merge to `main` authorises automatic deployment to the **new OVH clean-room host only**.

No deployment approval from the user is required.

---

# 3. ABSOLUTE BOUNDARIES

## 3.1 Existing production system is read-only

The existing Hermes station/server may be used to discover:

- repository remotes;
- commit SHAs;
- versions;
- service names;
- systemd definitions;
- container manifests;
- environment variable names;
- profile names;
- skills;
- runtime paths;
- persistence paths;
- current network bindings;
- current backup mechanisms;
- health endpoints;
- migration formats;
- current gateway design.

Do not mutate it during this run.

Specifically, do not:

- install packages;
- restart services;
- stop services;
- edit config;
- edit systemd;
- change Git branches;
- pull or reset code;
- rotate credentials;
- modify DNS;
- enable/disable Telegram polling;
- delete files;
- alter databases;
- change firewall rules;
- change Tailscale ACLs for the production node.

## 3.2 No production cutover

This runbook builds and proves a separate OVH system.

It does not perform the final production cutover unless the new host has a separate, non-conflicting external identity.

The resulting host must be capable of later cutover, but the existing host remains operational.

## 3.3 Telegram single-poller safety

Never run two live polling gateways with the same Telegram bot token.

For the new OVH host:

- fully install the Telegram gateway;
- validate configuration;
- validate secret retrieval;
- run synthetic/integration tests;
- use a separate test bot if available;
- otherwise leave production polling disabled.

Final state without a separate test bot:

`READY_FOR_EXCLUSIVE_CUTOVER`

not:

`LIVE`

## 3.4 HADA truthfulness

Do not declare HADA operational merely because a `/hada` interface or source tree exists.

Current clean-room merge authority is GitHub PR + CI.

If authoritative HADA tooling is available, add it as another independent audit input.

If a genuine HADA runtime is absent, report:

`HADA_RUNTIME=NOT_DEPLOYED`

rather than fabricating success.

## 3.5 Household/application separation

Do not migrate unrelated household application data into this clean-room host unless an authoritative current repository requires that integration.

Keep separate:

- Home Hub household state;
- Firebase household data;
- ADHD-OS user data;
- medication/custody/crisis information.

Interfaces may be tested where appropriate.

---

# 4. REQUIRED FAULT AND REPAIR LOGGING

Fault/repair logging is mandatory from the first command until final acceptance.

Do not reconstruct the history at the end.

Every observed fault must be logged when it occurs.

Create the following append-only files immediately:

```text
evidence/faults/fault-ledger.jsonl
evidence/faults/fault-ledger.md
evidence/faults/repair-attempts/
```

Also create GitHub issue or PR annotations when useful, but the repository ledger remains canonical evidence for this run.

## 4.1 Fault record schema

Every fault record must contain:

```json
{
  "fault_id": "FLT-YYYYMMDD-NNNN",
  "timestamp_utc": "ISO-8601",
  "timestamp_melbourne": "ISO-8601",
  "phase": "discovery|ci|bootstrap|hsp|hps|hermes|hes|deploy|verify|backup|recovery|other",
  "host": "hostname or github-actions",
  "repository": "owner/repo or null",
  "branch": "branch or null",
  "commit_sha": "sha or null",
  "pull_request": "number/url or null",
  "workflow_run": "run id/url or null",
  "job": "job/check name or null",
  "command": "redacted command or null",
  "exit_code": 1,
  "symptom": "what failed",
  "expected": "expected result",
  "observed": "actual result",
  "evidence_paths": [],
  "classification": "configuration|code|dependency|network|secret|permission|resource|data|security|external|unknown",
  "severity": "info|warning|error|critical",
  "root_cause": null,
  "repair_status": "untriaged|repairing|retesting|resolved|blocked|rolled_back",
  "repair_attempts": 0,
  "final_disposition": null
}
```

Never put secret values in the ledger.

## 4.2 Repair attempt schema

Every repair attempt must record:

```json
{
  "fault_id": "FLT-...",
  "attempt": 1,
  "timestamp": "ISO-8601",
  "hypothesis": "suspected root cause",
  "change_summary": "what changed",
  "files_changed": [],
  "commit_sha": "sha",
  "ci_run": "run id/url",
  "verification": "test performed",
  "result": "pass|fail|partial",
  "next_action": "next repair or null"
}
```

## 4.3 Required fault lifecycle

For every fault:

```text
DETECTED
  ↓
LOGGED
  ↓
EVIDENCE CAPTURED
  ↓
TRIAGED
  ↓
ROOT-CAUSE HYPOTHESIS
  ↓
REPAIR
  ↓
COMMIT / CONFIG CHANGE
  ↓
RETEST
  ├── FAIL → log new attempt and repeat
  └── PASS → resolve record
```

Never delete a failed repair record.

A later successful repair does not erase earlier failures.

## 4.4 Automatic repair limit

Maximum autonomous repair attempts per distinct fault:

`12`

At attempt 12, if still unresolved:

- preserve all evidence;
- stop mutating the affected component;
- mark:

`BLOCKED_AUTONOMOUS_REPAIR_LIMIT`

- continue unrelated tasks.

## 4.5 Fault summary generated on every PR

CI must generate:

```text
evidence/faults/current-summary.md
```

containing:

- open faults;
- faults introduced by the PR;
- faults resolved by the PR;
- retry counts;
- blocked items;
- links to evidence.

Unresolved critical faults fail `AUDIT-GATE`.

---

# 5. TARGET ACCEPTANCE SCOPE

The target host is a complete clean-room Hermes platform based on the current authoritative architecture.

Expected components are listed below, but source discovery decides whether an item is current, superseded or replaced.

## 5.1 Hermes runtime

Expected:

- Hermes Agent;
- Hermes API/runtime endpoint;
- one Telegram gateway definition;
