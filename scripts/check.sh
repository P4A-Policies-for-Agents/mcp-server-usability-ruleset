#!/usr/bin/env bash
# Test suite for this ruleset. Run from anywhere: scripts/check.sh
# Prints PASS lines; exits 1 with a FAIL line on the first failed assertion.
set -euo pipefail
cd "$(dirname "$0")/.."

# --- per-repo config ---
EXPECTED_AUTHORING_WARNINGS=0   # no known authoring warnings
SIBLING_GOOD=../mcp-server-safety-ruleset/fixtures/good
# -----------------------

RULESET=ruleset.yaml
CLI=anypoint-cli-v4

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }

# Rule IDs listed under a top-level severity key (violation|warning|info).
severity_ids() {
  awk -v key="$1:" '$0 == key { on = 1; next } /^[^ ]/ { on = 0 } on && /^  - / { print $2 }' "$RULESET"
}

# Rule IDs defined directly under `validations:`.
defined_ids() {
  awk '/^validations:/ { on = 1; next } /^[^ ]/ { on = 0 } on && /^  [a-z0-9-]+:$/ { sub(":", "", $1); print $1 }' "$RULESET"
}

# CLI severity label for a rule ID (Violation|Warning|Info); fails if unlisted.
expected_severity() {
  local sev
  for sev in violation warning info; do
    if severity_ids "$sev" | grep -qx "$1"; then
      case $sev in violation) echo Violation ;; warning) echo Warning ;; info) echo Info ;; esac
      return 0
    fi
  done
  return 1
}

# Sorted "<rule-id>:<Severity>" lines for one fixture project.
findings() {
  local out
  out=$("$CLI" governance:api:validate "$1" --rulesets "$RULESET" --no-collectMetrics 2>&1) || true
  grep -q '^Conforms:' <<<"$out" || fail "$1: validator did not run:"$'\n'"$out"
  if grep -q 'example-validation-error' <<<"$out"; then
    fail "$1: manifest fails the MCP schema (example-validation-error):"$'\n'"$out"
  fi
  awk '/^Constraint: / { n = split($2, a, "/"); id = a[n] } /^Severity: / { print id ":" $2 }' <<<"$out" | sort
}

lint() {
  local listed dup
  [ "$(grep -m1 -v '^[[:space:]]*$' "$RULESET")" = '#%Validation Profile 1.0' ] \
    || fail "first non-blank line must be '#%Validation Profile 1.0'"
  grep -qE '^profile: .+' "$RULESET" || fail "missing non-empty 'profile:' name"
  grep -qx '  mcp: http://anypoint.com/vocabs/mcp#' "$RULESET" \
    || fail "missing 'prefixes: mcp: http://anypoint.com/vocabs/mcp#' (validator panics without it)"
  if grep -nE '^ +mcp\.[A-Za-z]+:' "$RULESET"; then
    fail "property paths must use core.*, not mcp.* (lines above)"
  fi
  listed=$({ severity_ids violation; severity_ids warning; severity_ids info; } | sort)
  [ -n "$listed" ] || fail "no rules listed under violation/warning/info"
  dup=$(uniq -d <<<"$listed")
  [ -z "$dup" ] || fail "rules listed more than once: $dup"
  [ "$listed" = "$(defined_ids | sort)" ] || fail "severity lists and validations: keys differ"
  [ "$(wc -c <"$RULESET")" -lt 524288 ] || fail "$RULESET is larger than 512 KB"
  pass "tier-1 lint"
}

echo "CLI: $("$CLI" --version) / $("$CLI" plugins --core | grep governance-plugin)"

lint

out=$("$CLI" governance:ruleset:validate-authoring "$RULESET" 2>&1) || true
# A clean ruleset prints "Ruleset is valid" instead of the error/warning summary.
if grep -qx 'Ruleset is valid' <<<"$out"; then
  summary="0 error(s), 0 warning(s)"
else
  summary=$(grep -E '^[0-9]+ error\(s\), [0-9]+ warning\(s\)' <<<"$out") || fail "validate-authoring did not run:"$'\n'"$out"
fi
[ "$summary" = "0 error(s), $EXPECTED_AUTHORING_WARNINGS warning(s)" ] \
  || fail "validate-authoring: $summary (expected 0 errors, $EXPECTED_AUTHORING_WARNINGS warnings)"$'\n'"$out"
pass "validate-authoring ($summary)"

out=$("$CLI" governance:ruleset:validate "$RULESET" --no-collectMetrics 2>&1) || true
grep -q 'Ruleset conforms with Dialect' <<<"$out" || fail "dialect validation:"$'\n'"$out"
pass "dialect validate"

got=$(findings fixtures/good)
[ -z "$got" ] || fail "fixtures/good should have 0 findings, got:"$'\n'"$got"
pass "fixtures/good: 0 findings"

if [ -d "$SIBLING_GOOD" ]; then
  got=$(findings "$SIBLING_GOOD")
  [ -z "$got" ] || fail "$SIBLING_GOOD should have 0 findings, got:"$'\n'"$got"
  pass "$SIBLING_GOOD: 0 findings"
fi

for id in $(defined_ids); do
  [ -d "fixtures/bad/$id" ] || compgen -G "fixtures/bad/$id.*" >/dev/null \
    || fail "rule $id has no fixtures/bad/$id[.<variant>] fixture"
done

for dir in fixtures/bad/*/; do
  name=$(basename "$dir")
  id=${name%%.*}
  sev=$(expected_severity "$id") || fail "fixtures/bad/$name: no rule named $id in $RULESET"
  got=$(findings "$dir")
  [ "$got" = "$id:$sev" ] || fail "fixtures/bad/$name: expected exactly '$id:$sev', got:"$'\n'"${got:-<none>}"
  pass "fixtures/bad/$name -> $id ($sev)"
done

echo "ALL CHECKS PASSED"
