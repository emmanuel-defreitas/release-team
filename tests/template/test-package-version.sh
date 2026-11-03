#!/usr/bin/env bash
# shellcheck source=tests/template/harness.sh
. "$(dirname "${BASH_SOURCE[0]}")/harness.sh"

new_repo
mkdir scripts
cp "$SCRIPTS/version.sh" "$SCRIPTS/lib.sh" "$SCRIPTS/check-package-version.sh" scripts/
printf '1.2.3\n' > VERSION
for value in '' '1.2.4' 'v1.2.3' '1.2' '1.2.3;echo unsafe'; do
  assert_fail "rejects unapproved version: $value" env PACKAGE_VERSION="$value" bash scripts/check-package-version.sh
done
assert_ok "accepts exact committed version" env PACKAGE_VERSION=1.2.3 bash scripts/check-package-version.sh
printf '0.0.0\n' > VERSION
assert_fail "rejects matching scaffold placeholder" env PACKAGE_VERSION=0.0.0 bash scripts/check-package-version.sh
finish
