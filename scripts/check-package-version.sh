#!/usr/bin/env bash
# Fail closed before uploading a placeholder, mismatched or malformed version.
set -euo pipefail
version="$(bash scripts/version.sh get)"
if [[ ! "${PACKAGE_VERSION:-}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] ||
   [[ "$PACKAGE_VERSION" == "0.0.0" ]] || [[ "$PACKAGE_VERSION" != "$version" ]]; then
  echo "Choose the exact committed X.Y.Z version; 0.0.0 cannot be published." >&2
  exit 1
fi
printf 'Publication version checked: %s\n' "$version"
