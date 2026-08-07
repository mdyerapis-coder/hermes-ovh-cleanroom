#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="mdyerapis-coder/hermes-ovh-cleanroom"
BRANCH="main"
BOOT_LEDGER="/home/ubuntu/hermes-bootstrap/evidence/faults/fault-ledger.jsonl"

log_failure() {
  local rc="$1"
  local cmd="$2"
  mkdir -p "$(dirname "$BOOT_LEDGER")"
  python3 - "$BOOT_LEDGER" "$rc" "$cmd" <<'PY'
import datetime, json, pathlib, sys, uuid
from zoneinfo import ZoneInfo
path, rc, cmd = sys.argv[1:4]
now = datetime.datetime.now(datetime.timezone.utc)
rec = {
    "fault_id": "FLT-" + now.strftime("%Y%m%d-") + uuid.uuid4().hex[:8].upper(),
    "timestamp_utc": now.isoformat(),
    "timestamp_melbourne": now.astimezone(ZoneInfo("Australia/Melbourne")).isoformat(),
    "phase": "github-governance-bootstrap",
    "host": "hermes-ovh-cleanroom",
    "repository": "mdyerapis-coder/hermes-ovh-cleanroom",
    "branch": "main",
    "command": cmd,
    "exit_code": int(rc),
    "symptom": "GitHub governance bootstrap command failed",
    "classification": "configuration",
    "severity": "critical",
    "repair_status": "blocked"
}
with pathlib.Path(path).open("a", encoding="utf-8") as f:
    f.write(json.dumps(rec, separators=(",", ":")) + "\n")
PY
}
trap 'rc=$?; log_failure "$rc" "$BASH_COMMAND"; exit "$rc"' ERR

command -v gh >/dev/null
gh auth status --hostname github.com >/dev/null

LOGIN="$(gh api user --jq .login)"
PLAN="$(gh api user --jq '.plan.name // "unknown"')"

if [[ "$LOGIN" != "mdyerapis-coder" ]]; then
  echo "Unexpected GitHub identity: $LOGIN" >&2
  exit 64
fi

echo "GitHub identity: $LOGIN"
echo "GitHub plan: $PLAN"

# PR #2 exercised the final hardened trusted bootstrap auditor.
SMOKE_SHA="$(gh pr view 2 --repo "$REPO" --json headRefOid --jq .headRefOid)"
SMOKE_STATE="$(gh api "repos/$REPO/commits/$SMOKE_SHA/status" --jq '[.statuses[] | select(.context=="BOOTSTRAP-GATE")][0].state // "missing"')"

if [[ "$SMOKE_STATE" != "success" ]]; then
  echo "Refusing governance activation: proven final BOOTSTRAP-GATE smoke status is $SMOKE_STATE" >&2
  exit 65
fi

echo "FINAL BOOTSTRAP-GATE smoke proof: success ($SMOKE_SHA)"

# Bootstrap merge policy is squash-only, but auto-merge stays OFF until Grok's first
# governance PR has created and exact-success-passed the full AUDIT-GATE. This prevents
# BOOTSTRAP-GATE alone from racing and merging that first PR before the full auditor is live.
gh api --method PATCH "repos/$REPO" --input - <<'JSON' >/dev/null
{
  "allow_auto_merge": false,
  "allow_squash_merge": true,
  "allow_merge_commit": false,
  "allow_rebase_merge": false,
  "delete_branch_on_merge": true,
  "allow_update_branch": true
}
JSON

# GitHub Actions token is read-only by default. Individual audited jobs must request any narrowly needed writes.
gh api --method PUT "repos/$REPO/actions/permissions/workflow" --input - <<'JSON' >/dev/null
{
  "default_workflow_permissions": "read",
  "can_approve_pull_request_reviews": false
}
JSON

# Require a PR but deliberately require zero human approvals. Bootstrap requires strict
# current-head BOOTSTRAP-GATE. Grok must later add exact-success AUDIT-GATE to this required
# list BEFORE enabling repository auto-merge.
protection_err="$(mktemp)"
if ! gh api --method PUT "repos/$REPO/branches/$BRANCH/protection" --input - 2>"$protection_err" <<'JSON' >/dev/null
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["BOOTSTRAP-GATE"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "allow_fork_syncing": false
}
JSON
then
  echo "Failed to enable branch protection on private repository." >&2
  cat "$protection_err" >&2
  if [[ "$PLAN" == "free" ]]; then
    echo "GitHub Free does not provide protected branches for private repositories. Keep this repo private and upgrade the account to GitHub Pro, or explicitly choose a public repository. The autonomous controller has NOT been started." >&2
  fi
  rm -f "$protection_err"
  exit 78
fi
rm -f "$protection_err"

echo "=== VERIFIED REPOSITORY SETTINGS ==="
gh api "repos/$REPO" --jq '{private:.private,allow_auto_merge:.allow_auto_merge,allow_squash_merge:.allow_squash_merge,allow_merge_commit:.allow_merge_commit,allow_rebase_merge:.allow_rebase_merge,delete_branch_on_merge:.delete_branch_on_merge,allow_update_branch:.allow_update_branch}'

echo
echo "=== VERIFIED MAIN PROTECTION ==="
gh api "repos/$REPO/branches/$BRANCH/protection" --jq '{enforce_admins:.enforce_admins.enabled,required_status_checks:.required_status_checks.contexts,strict:.required_status_checks.strict,required_approvals:.required_pull_request_reviews.required_approving_review_count,force_pushes:.allow_force_pushes.enabled,deletions:.allow_deletions.enabled,linear_history:.required_linear_history.enabled}'

echo
echo "Bootstrap auto-merge intentionally remains disabled until full AUDIT-GATE activation."
echo "GITHUB_GOVERNANCE_BOOTSTRAP=PASS"
