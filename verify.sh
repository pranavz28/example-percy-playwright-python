#!/usr/bin/env bash
# Verify a Percy build's CI detection fields.
#
# Usage: ./verify.sh <build_id_or_url> <expected_ci> [expected_branch] [expected_commit] [expected_pr] [expected_nonce]
#
# Requires: PERCY_TOKEN exported with admin-scope (run `admin-t` first).
# Any field passed as "-" is skipped. expected_nonce supports "regex:<pattern>".
#
# ci is parsed from user_agent — specifically the last token inside the final parenthetical group,
# e.g. "Percy/v1 ... (node/vX; playwright/Y; python/Z; teamcity)" → ci=teamcity.

set -u

usage() {
  echo "Usage: $0 <build_id_or_url> <expected_ci> [branch] [commit] [pr] [nonce]"
  echo "  Pass '-' to skip. Prefix nonce/commit with 'regex:' to pattern-match."
  exit 2
}

[ $# -lt 2 ] && usage

RAW="$1"
EXP_CI="$2"
EXP_BRANCH="${3:--}"
EXP_COMMIT="${4:--}"
EXP_PR="${5:--}"
EXP_NONCE="${6:--}"

if [ -z "${PERCY_TOKEN:-}" ]; then
  echo "ERROR: PERCY_TOKEN not set. Run 'admin-t' first." >&2
  exit 2
fi

BUILD_ID="$(echo "$RAW" | grep -oE '[0-9]+' | tail -1)"
if [ -z "$BUILD_ID" ]; then
  echo "ERROR: could not parse build ID from '$RAW'" >&2
  exit 2
fi

API="https://percy.io/api/v1/builds/${BUILD_ID}?include=commit"
RESP="$(curl -sS -H "Authorization: Token token=${PERCY_TOKEN}" "$API")"

if ! echo "$RESP" | jq -e .data >/dev/null 2>&1; then
  echo "ERROR: build lookup failed for id=$BUILD_ID" >&2
  echo "$RESP" | head -20 >&2
  exit 2
fi

UA="$(echo "$RESP" | jq -r '.data.attributes."user-agent" // ""')"
# Extract the last parenthesized group, then take the last `;`-delimited token.
# Examples:
#   "Percy/v1 @percy/cli/1.31.12 (node/v20; python/3.9; teamcity)"  → teamcity
#   "Percy/v1 @percy/cli/1.31.12 (node/v20; darwin)"                 → darwin (fallback — no CI)
ACT_CI="$(echo "$UA" | awk -F'[()]' '{print $(NF-1)}' | awk -F';' '{gsub(/^ +| +$/,"",$NF); print $NF}')"
# Normalize: if the last token is a pure platform like 'darwin', 'linux', 'win32', treat as null.
case "$ACT_CI" in
  darwin|linux|win32|freebsd|openbsd|"") ACT_CI="null" ;;
esac

ACT_BRANCH="$(echo "$RESP" | jq -r '.data.attributes.branch // "null"')"
ACT_COMMIT="$(echo "$RESP" | jq -r '(.included // [])[] | select(.type=="commits") | .attributes.sha' | head -1)"
[ -z "$ACT_COMMIT" ] && ACT_COMMIT="null"
ACT_PR="$(echo "$RESP" | jq -r '.data.attributes."pull-request-number" // "null"')"
ACT_NONCE="$(echo "$RESP" | jq -r '.data.attributes."parallel-nonce" // "null"')"
ACT_PROJECT="$(echo "$RESP" | jq -r '.data.relationships.project.data.id // "null"')"

RC=0
check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "-" ]; then
    printf "  %-22s %s  (skipped)\n" "$label:" "$actual"
    return
  fi
  local ok="FAIL" match=0
  if [[ "$expected" == regex:* ]]; then
    if [[ "$actual" =~ ${expected#regex:} ]]; then match=1; fi
  else
    [ "$expected" = "$actual" ] && match=1
  fi
  if [ "$match" -eq 1 ]; then ok="pass"; else RC=1; fi
  printf "  %-22s %-50s  expected=%s  [%s]\n" "$label:" "$actual" "$expected" "$ok"
}

echo "Build #$BUILD_ID (project $ACT_PROJECT)"
echo "  user-agent: $UA"
check "ci"                  "$EXP_CI"     "$ACT_CI"
check "branch"              "$EXP_BRANCH" "$ACT_BRANCH"
check "commit-sha"          "$EXP_COMMIT" "$ACT_COMMIT"
check "pull-request-number" "$EXP_PR"     "$ACT_PR"
check "parallel-nonce"      "$EXP_NONCE"  "$ACT_NONCE"

if [ $RC -eq 0 ]; then
  echo "  -> ALL PASS"
else
  echo "  -> FAIL"
fi
exit $RC
