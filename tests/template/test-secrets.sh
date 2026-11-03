#!/usr/bin/env bash
# shellcheck source=tests/template/harness.sh
. "$(dirname "${BASH_SOURCE[0]}")/harness.sh"

X="$SCRIPTS/secrets.sh"

new_repo
printf 'API_KEY=REPLACE_ME\nTOKEN=REPLACE_ME\n' > .env.example

assert_fail "check fails without .env" "$X" check

assert_ok "init creates .env" "$X" init
# GNU stat may print filesystem information before its BSD-style probe fails.
mode="$(stat -f '%Lp' .env 2>/dev/null)" || mode="$(stat -c '%a' .env)"
assert_eq "600" "$mode" ".env is mode 600"
assert_ok "check passes for a fresh copy" "$X" check

printf 'API_KEY=hunter2\n' > .env
assert_fail "check fails when a key is missing" "$X" check

printf 'API_KEY=a\nTOKEN=b\nEXTRA=c\n' > .env
assert_ok "undocumented extra keys only warn" "$X" check
out="$("$X" check 2>&1)"
assert_contains "$out" "EXTRA" "extra key is reported"
assert_not_contains "$out" "hunter2" "values never printed"

echo "KEEP=1" >> .env
"$X" init >/dev/null 2>&1
assert_contains "$(cat .env)" "KEEP=1" "init never overwrites"

assert_fail "push refuses a tracked env file" bash -c "
  cd '$PWD' && git add -f .env && ENV_FILE=.env YES=1 '$X' push"

finish
