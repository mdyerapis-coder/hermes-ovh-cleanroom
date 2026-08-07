# Mandatory Grok Operating Rules — Hermes OVH Clean-room

These instructions are authoritative for every Grok session in this repository.

1. Read `runbook/RUNBOOK-MANIFEST.md` first and then every file it marks authoritative, in order, before implementation work.
2. Execute the runbook; do not merely restate, plan, or hand work back to the user.
3. No routine human approvals are required. Use branches, PRs, CI, exact-success gates, auto-merge, automatic deployment, verification, and rollback.
4. The existing Hermes production environment is READ-ONLY reference material. Never mutate it.
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
15. Create `evidence/control/AUTONOMY_DONE.json` only under the completion rules in `runbook/RUNBOOK-MANIFEST.md`.

The GitHub repository is the control plane and audit record. The target mutation host is `hermes-ovh-cleanroom` only unless an authoritative runbook step explicitly uses another system read-only.
