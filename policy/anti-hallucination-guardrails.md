# Anti-Hallucination Guardrails

**Applies to:** Grok, automation agents, CI-generated reports, deployment reports, repair agents, HES/HPS/HSP status output, and final acceptance reports.

**Mode:** Fail closed on unsupported factual claims.

---

## 1. Core rule

Never present an inferred, assumed, remembered, planned, attempted, or probable state as an observed fact.

Every operational claim must be one of:

- `VERIFIED`
- `PENDING_VERIFICATION`
- `BLOCKED`
- `NOT_APPLICABLE`
- `SUPERSEDED`
- `REPLACED`
- `TRIALLED`

A claim may be marked `VERIFIED` only when evidence exists from an accepted source of truth.

---

## 2. Evidence hierarchy

Resolve facts in this order:

1. protected default branch of the authoritative repository;
2. current immutable release/tag/commit;
3. current committed deployment manifest;
4. current runtime state observed directly on the clean-room OVH host;
5. current production state inspected read-only;
6. verified backup/restore metadata;
7. current project documentation;
8. historical notes.

If two sources disagree, do not choose silently. Record the conflict and mark the claim `PENDING_VERIFICATION` until resolved.

---

## 3. Prohibited unsupported claims

Grok must never state or imply any of the following without evidence:

- a repository exists;
- a path exists;
- a file exists;
- a service exists;
- a systemd unit exists;
- a container exists;
- a port is open or closed;
- a dependency is installed;
- a configuration is active;
- a secret exists;
- a credential is valid;
- a provider/model is available;
- a database/schema migration succeeded;
- a backup completed;
- a restore succeeded;
- CI passed;
- a PR merged;
- a deployment completed;
- a rollback completed;
- a health check passed;
- a Telegram message was delivered;
- HADA is deployed or running;
- HPS/HES/HSP is operational;
- a feature is complete;
- an existing component is obsolete or safe to remove.

If the required evidence is absent, the only acceptable state is `PENDING_VERIFICATION` or an appropriate blocker.

---

## 4. No invented infrastructure

Never invent:

- repository names;
- branch names;
- hostnames;
- IP addresses;
- Tailscale node names;
- paths;
- ports;
- environment variable names;
- secret names;
- API endpoints;
- GitHub Actions workflow names;
- systemd unit names;
- container/image names;
- database names;
- profile names;
- model/provider names;
- migration identifiers;
- user accounts;
- backup destinations.

Discover them from source or runtime first.

---

## 5. Command evidence

Any command used as evidence must record, where relevant:

- exact command with secrets redacted;
- target host/context;
- timestamp;
- exit code;
- stdout/stderr evidence path;
- Git commit SHA;
- PR/workflow/run identifier if applicable.

A command that was only proposed or printed is not evidence that it was executed.

A command returning non-zero cannot be reported as successful.

---

## 6. CI evidence

A CI claim is valid only when tied to the current PR head/merge candidate SHA.

Never reuse a green result from an earlier commit after the branch changes.

For mandatory jobs, only exact `success` is accepted.

The following do not count as success:

- skipped;
- neutral;
- cancelled;
- stale;
- missing;
- timed_out;
- action_required;
- failure.

`AUDIT-GATE` must validate this explicitly.

---

## 7. Runtime evidence

A runtime claim requires direct observation from the correct target host.

Before mutating or validating a host, verify identity using multiple independent signals where practical, such as:

- `hostname`;
- machine ID;
- Tailscale IP/name;
- expected Git/deployment marker;
- expected target metadata.

If target identity is ambiguous, stop the mutation and mark the operation `BLOCKED_TARGET_IDENTITY_UNVERIFIED`.

---

## 8. Completion claims

Terms such as:

- complete;
- implemented;
- deployed;
- operational;
- healthy;
- fixed;
- resolved;
- restored;
- migrated;
- verified;
- production-ready;

must have mapped evidence.

Create and maintain:

```text
evidence/claims/claim-evidence-map.jsonl
```

Each record must include:

```json
{
  "claim_id": "CLM-YYYYMMDD-NNNN",
  "claim": "human-readable claim",
  "status": "VERIFIED|PENDING_VERIFICATION|BLOCKED|NOT_APPLICABLE|SUPERSEDED|REPLACED|TRIALLED",
  "component": "component name",
  "commit_sha": "sha or null",
  "host": "host or null",
  "evidence": ["path/url/run-id/etc"],
  "verified_at": "ISO-8601 or null"
}
```

No final report may contain a `VERIFIED` completion claim that is absent from this map.

---

## 9. Fault/repair truthfulness

A repair is not `RESOLVED` because code was changed.

It becomes `RESOLVED` only after:

1. the repair is applied;
2. the original failure condition is re-tested;
3. the re-test passes;
4. the evidence is recorded;
5. any regression/acceptance tests required by scope also pass.

Failed repair attempts remain permanently recorded.

---

## 10. Historical-state protection

Do not rewrite history to make the final state look cleaner.

Never delete or alter prior fault evidence merely because a later repair succeeds.

Never remove previous release manifests, rollback evidence, or historical incident records to make a current build appear successful.

Corrections must be additive and traceable.

---

## 11. Source conflicts

When conflicting facts are found, create a conflict record containing:

- subject;
- candidate values;
- source for each value;
- timestamp/date;
- relevant commit/version;
- current disposition.

Until resolved, consumers must see:

`PENDING_VERIFICATION_SOURCE_CONFLICT`

not a guessed value.

---

## 12. External documentation

When implementation depends on an external product/API/CLI:

- prefer official documentation;
- record the source URL and retrieval date;
- pin versions/commit SHAs where supported;
- do not assume command-line flags from memory when the installed version can be inspected;
- validate help/version output before relying on flags for unattended execution.

If external behaviour cannot be verified, mark it pending rather than inventing compatibility.

---

## 13. Model/provider availability

Never infer provider/model availability from documentation or historical config alone.

Validate availability against the currently configured provider when safely possible.

Classify failures correctly:

- authentication;
- quota/rate limit;
- model unavailable;
- endpoint unavailable;
- network;
- application defect;
- unknown.

Do not mislabel external quota exhaustion as a Hermes defect.

---

## 14. HADA-specific rule

Never state that HADA is deployed, operational, controlling, monitoring, approving, or repairing unless a real current runtime is observed and evidenced.

Source files, staged directories, UI placeholders, historical notes, or a `/hada` command are not sufficient evidence of a running HADA controller.

When runtime evidence is absent, report exactly:

`HADA_RUNTIME=NOT_DEPLOYED`

or `PENDING_VERIFICATION` if evidence is incomplete.

---

## 15. Telegram-specific rule

Never report Telegram end-to-end success unless an actual permitted E2E transaction is observed.

Synthetic/configuration tests must be labelled as such.

Without a separate test bot or exclusive production cutover, use:

`TELEGRAM_STATE=READY_FOR_EXCLUSIVE_CUTOVER`

not `LIVE`.

---

## 16. Destructive decisions

Absence of evidence is never evidence that a component is obsolete or safe to delete.

A component may not be removed merely because Grok cannot find a reference quickly.

Under the additive-only evolution policy, components may be disabled/quarantined when unsafe, but historical configuration, evidence, rollback artefacts and documented capability must remain recoverable.

---

## 17. Required CI guard

The repository must implement a mandatory job named:

`claim-evidence-validation`

It must fail when:

- claim-evidence JSONL is invalid;
- a claim marked `VERIFIED` has no evidence;
- a completion/health/deployment claim in generated final status lacks a corresponding verified claim record;
- referenced commit SHA does not match the candidate/current release where required;
- a claim references a missing evidence artifact;
- unresolved source conflicts are represented as verified facts;
- HADA is represented as deployed without runtime evidence;
- Telegram is represented as live without permitted E2E evidence;
- required evidence history was deleted.

`claim-evidence-validation` must be a mandatory dependency of `AUDIT-GATE`.

---

## 18. Final reporting rule

Final reports must clearly separate:

### Verified facts
Directly supported by evidence.

### Pending verification
Information not proven yet.

### External blockers
Credentials, entitlements, quotas, unavailable third-party systems, or other external conditions.

### Superseded/replaced/trialled
Historical architecture states supported by evidence.

### Faults and repairs
Full trace of observed faults and all repair attempts.

Never blend these categories to make the implementation appear more complete than it is.

---

# Enforcement principle

When there is a choice between:

- making progress using an assumption; or
- stopping that specific action and recording uncertainty;

choose evidence and uncertainty.

Continue independent safe work, but never convert an unknown into a fact.
