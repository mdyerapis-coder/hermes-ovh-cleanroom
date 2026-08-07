#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAIL=0
if command -v shellcheck >/dev/null; then
  # run shellcheck on scripts
  while IFS= read -r -d '' f; do
    shellcheck -x "$f" || FAIL=1
  done < <(find "$ROOT/scripts" -type f -name '*.sh' -print0)
else
  echo "shellcheck not installed; performing basic bash -n"
  while IFS= read -r -d '' f; do
    bash -n "$f" || FAIL=1
  done < <(find "$ROOT/scripts" -type f -name '*.sh' -print0)
fi
# python syntax
while IFS= read -r -d '' f; do
  python3 -m py_compile "$f" || FAIL=1
done < <(find "$ROOT/scripts" "$ROOT/tests" "$ROOT/hsp" "$ROOT/hps" "$ROOT/hes" -type f -name '*.py' -print0 2>/dev/null)
if [[ "$FAIL" -ne 0 ]]; then
  echo "FORMAT-LINT FAIL"
  exit 1
fi
echo "FORMAT-LINT PASS"
