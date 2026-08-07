# POST-COMPLETION EVOLUTION POLICY
## Additive Expansion Only — Never Remove the Proven Baseline

**Applies:** After the clean-room implementation first reaches its accepted completion state.

---

# 1. CORE RULE

After baseline completion, Grok is authorised and encouraged to continue improving the system autonomously.

Grok may:

- add new capabilities;
- add integrations;
- improve reliability;
- improve observability;
- improve performance;
- add automation;
- add tests;
- add security controls;
- add recovery mechanisms;
- add documentation;
- add providers/models;
- add HPS/HES/HSP functionality;
- extend Hermes;
- extend CI/auditing;
- replace an implementation with a proven successor;
- refactor internally where externally observable capabilities and recovery guarantees are preserved.

Grok must **never reduce or silently remove the accepted baseline**.

The completed baseline is a permanent preservation floor.

---

# 2. NEVER-REMOVE RULE

Once a capability, control, test, evidence stream, documented interface, recovery path, deployment safeguard, audit gate, service contract, backup path, fault record, or accepted integration forms part of the completed baseline, Grok must not delete it or make it unavailable merely to simplify future work.

This includes, at minimum:

- Hermes capabilities;
- HPS capabilities;
- HES capabilities;
- HSP controls;
- GitHub CI audit controls;
- `AUDIT-GATE`;
- fault/repair history;
- tests;
- health checks;
- backup/restore mechanisms;
- rollback paths;
- service inventory history;
- network/port contracts;
- secret contracts;
- release evidence;
- acceptance evidence;
- runbooks;
- operational documentation;
- known-good release records;
- migration records;
- compatibility interfaces that are still required by the accepted baseline.

A replacement is not permission to erase the predecessor immediately.

---

# 3. SUPERSEDE, DO NOT ERASE

When Grok introduces a superior replacement:

1. add the successor;
2. test it independently;
3. run both old and new compatibility/acceptance tests where practical;
4. prove migration and rollback;
5. mark the older implementation `SUPERSEDED`;
6. preserve its source/configuration/evidence and recovery path;
7. switch the preferred/default path only after the new implementation passes `AUDIT-GATE`;
8. retain enough of the predecessor to restore or understand the former known-good state.

The historical artefact must remain traceable in Git and release evidence.

---

# 4. SECURITY EXCEPTION — QUARANTINE, NOT SILENT REMOVAL

If a baseline component becomes unsafe, vulnerable, compromised, legally unusable, or incompatible with a mandatory upstream requirement, Grok may disable or isolate it to protect the system.

In that case Grok must:

- log a fault;
- record the reason;
- preserve historical configuration/source/evidence;
- mark it `QUARANTINED` or `DISABLED_FOR_SECURITY`;
- provide a replacement or compatibility path where possible;
- preserve rollback information where safe;
- never pretend the capability still operates if it has been disabled.

Security does not justify deleting the historical record.

---

# 5. BASELINE MANIFEST

At first accepted completion Grok must generate and commit:

```text
evidence/baseline/baseline-manifest.json
```

The manifest must include at minimum:

- completion Git SHA;
- completion timestamp;
- accepted services;
- accepted commands/interfaces;
- accepted HES/HPS/HSP capabilities;
- required CI jobs;
- required tests;
- required health checks;
- backup/restore controls;
- recovery controls;
- network exposure contract;
- secret contract names;
- evidence streams;
- documentation set;
- fault-ledger location;
- known-good deployment release;
- hashes of critical governance files.

This manifest becomes the minimum future capability set.

---

# 6. CI ENFORCEMENT

After baseline completion, add a mandatory PR job named:

```text
baseline-preservation
```

`AUDIT-GATE` must require `baseline-preservation=success`.

The job must compare the PR against the committed baseline manifest and fail when the change attempts to remove or regress a protected baseline item without an additive compatible successor.

At minimum it must detect:

- deleted protected files;
- removed required CI jobs;
- removed required tests;
- removed accepted commands/interfaces;
- removed backup/restore controls;
- removed health checks;
- removed recovery controls;
- removed evidence streams;
- loss of a required service without a declared successor state;
- reduction of the fault ledger/history;
- removal of required documentation;
- weakening of `AUDIT-GATE`;
- weakening of branch/ruleset protections;
- removal of secret-handling controls;
- removal of rollback guarantees.

Mandatory preservation failures must not be marked `continue-on-error` and must not be skipped.

---

# 7. APPEND-ONLY HISTORY

The following are append-only or historically immutable:

- fault ledger;
- repair attempts;
- release manifests;
- acceptance evidence;
- backup/restore evidence;
- audit history;
- supersession records;
- baseline manifests.

Corrections must be represented by a new record referencing the old record, not deletion of the old evidence.

---

# 8. AUTONOMOUS EXPANSION LOOP

After the system reaches `COMPLETE_CLEANROOM` or `COMPLETE_READY_FOR_EXCLUSIVE_CUTOVER`, Grok may continue autonomously using this loop:

```text
identify improvement
  ↓
create branch
  ↓
implement additive change
  ↓
run tests
  ↓
open PR
  ↓
baseline-preservation
  ↓
all other required CI
  ↓
AUDIT-GATE exact success
  ↓
auto-merge
  ↓
auto-deploy
  ↓
post-deploy acceptance
  ├── PASS → retain expansion
  └── FAIL → rollback + fault/repair PR
```

No routine human approval is required.

---

# 9. EXPANSION PRIORITIES

Once baseline completion is achieved, Grok should preferentially expand in this order unless evidence indicates a higher-value priority:

1. reliability and self-recovery;
2. observability and fault diagnosis;
3. security hardening;
4. backup/recovery depth;
5. test coverage;
6. HES operator visibility;
7. HPS reproducibility/idempotence;
8. HSP resilience;
9. Hermes capabilities and integrations;
10. performance/resource optimisation;
11. developer/agent ergonomics;
12. optional experimental functionality.

Expansion must not reduce the baseline to gain performance, simplicity or lower cost.

---

# 10. NO CLEANUP BY DELETION

Grok must not interpret requests such as:

- clean up;
- simplify;
- refactor;
- optimise;
- modernise;
- consolidate;
- deduplicate;

as permission to permanently remove accepted baseline capabilities or evidence.

Cleanup should mean organisation, consolidation, supersession, archiving, quarantine, compatibility wrappers, or reduction of duplication **without loss of the accepted capability floor**.

---

# 11. FINAL GOVERNANCE STATEMENT

**Build forward, never backward.**

Once the clean-room baseline is proven, every autonomous generation should be equal to or more capable, more observable, more recoverable, or more secure than the accepted baseline.

Grok may expand indefinitely through audited green PRs.

Grok may supersede.

Grok may quarantine unsafe legacy implementations.

Grok must never silently erase the proven baseline, its evidence, or its recovery history.
