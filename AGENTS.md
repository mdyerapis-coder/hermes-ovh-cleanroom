# Mandatory Grok Operating Rules — Hermes OVH Clean-room

These instructions are authoritative for every Grok session in this repository.

1. Read `runbook/RUNBOOK-MANIFEST.md` first and then every file it marks authoritative, in order, before implementation work.
2. Execute the runbook; do not merely restate, plan, or hand work back to the user.
3. No routine human approvals are required. Use branches, PRs, CI, exact-success gates, auto-merge, automatic deployment, verification, and rollback.
4. The existing Hermes production environment is READ-ONLY reference material. Never mutate it except when the authoritative post-baseline cutover phase has reached its explicit armed production transaction.
5. Never run a second live polling gateway using the existing production Telegram bot token.
6. Log every observed fault when it occurs and every repair attempt, including failed attempts. Never erase fault history.
7. Obey `policy/anti-hallucination-guardrails.md`. Unsupported claims are prohibited. Unknown facts are `PENDING_VERIFICATION`.
8. Obey `runbook/part-99-post-completion-evolution-policy.md`. After baseline completion you may add, improve, automate, optimise, or supersede, but never silently remove or regress preserved baseline capability/evidence/recovery.
9. Never weaken, skip, rename, bypass, or administratively override a failing required audit gate to obtain a merge.
10. Never store plaintext credentials, tokens, private keys, bot tokens, API keys, or real `.env` values in Git or evidence.
11. HADA status must be evidence-backed. If no genuine HADA runtime exists, report `HADA_RUNTIME=NOT_DEPLOYED`.
12. A command you propose is not an executed command. A deployment attempt is not a successful deployment. A planned test is not a passed test.
13. The exact current PR head SHA must be the SHA that passed its required gates.
14. Continue independent work when one integration is externally blocked. Classify the blocker precisely.
15. Create `evidence/control/AUTONOMY_DONE.json` only under the clean-room completion rules in `runbook/RUNBOOK-MANIFEST.md`. Preserve an existing valid marker as baseline evidence.
16. Bootstrap auto-merge MUST remain disabled during the first governance/CI PR. `BOOTSTRAP-GATE` by itself is never sufficient to merge implementation work.
17. On the first governance PR, build the full `AUDIT-GATE`, let BOTH `BOOTSTRAP-GATE` and `AUDIT-GATE` reach exact `success` on the exact current head SHA, then update `main` protection to require BOTH gates and read the protection back to prove both are enforced. Only after that proof may repository auto-merge be enabled and used.
18. Never use administrator bypass, direct push to protected `main`, or temporary removal of a required check to activate or satisfy `AUDIT-GATE`.
19. If the GitHub plan/account cannot enforce required protection, record the external governance blocker and stop implementation merges rather than weakening the design.
20. After the verified clean-room baseline, obey `runbook/part-100-hps-hes-platform-completion.md` for HPS v1, HES v1, integration and cutover evolution.
21. The existing `AUTONOMY_DONE.json` does not stop the post-baseline platform controller. That phase may stop only on a valid evidence-backed `evidence/control/PLATFORM_COMPLETION.json`.
22. HPS is the sole infrastructure/runtime mutation authority in the completed architecture. HES may orchestrate and display HPS operations but must not become a separate mutation engine.
23. Production host mutation is prohibited until HPS cutover readiness is proven and an explicit local arm transaction is valid. Read-only production discovery remains permitted when access is authorised.
24. Telegram cutover must be exclusive: prove the old production poller is fenced before starting the new one, and prove the new poller is dead before rollback re-enables the old one.
25. Maximum autonomous repair attempts per distinct fault is 12. After that record `BLOCKED_AUTONOMOUS_REPAIR_LIMIT` and continue independent work.
26. Do not write `PLATFORM_COMPLETION.json` merely because HPS/HES code exists or CI is green. Reconcile host deployment, acceptance, fault, claim, cutover and blocker evidence first.

The GitHub repository is the control plane and audit record. The default mutation host remains `hermes-ovh-cleanroom`. `hermes-station-1` remains read-only except during an explicitly armed HPS production cutover transaction governed by Part 100.
