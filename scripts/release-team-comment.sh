#!/usr/bin/env bash
# Turn `release-team workflow` results into a Markdown comment for a PR or run summary.
#
#   scripts/release-team-comment.sh results.json [run-url] > comment.md
#
# Draft text comes from a model, so treat it as untrusted: @mentions are broken up
# so a draft cannot ping people, and the body is capped below GitHub's comment limit.
# The first line is a hidden marker the workflow uses to update its own comment.

set -euo pipefail

results="${1:?usage: release-team-comment.sh results.json [run-url]}"
run_url="${2:-}"
marker='<!-- release-team-drafts -->'
limit=60000

body="$(
  echo "$marker"
  echo "## Release Team drafts"
  echo
  if ! jq -e 'type == "array" and length > 0' "$results" >/dev/null 2>&1; then
    echo "The team returned no results. Check the workflow log${run_url:+: $run_url}."
  else
    jq -r '
      def safe: gsub("@"; "@\u200b");
      def cell: safe | gsub("\\|"; "\\|") | gsub("\\s*\n\\s*"; " ");
      def icon: if . == "completed" then "✅" elif . == "failed" then "❌" else "⚠️" end;
      "> Drafts for review only. Nothing was published or changed. Runtime: `\(.[0].runtime)`.",
      "",
      "| Agent | Status | Summary |",
      "| --- | --- | --- |",
      (.[] | "| `\(.agent)` | \(.status | icon) \(.status) | \(.summary | cell) |"),
      "",
      (.[] |
        "<details><summary><b>\(.agent)</b>: \(.summary | cell)</summary>",
        "",
        (.artifacts[] | (.content | safe), ""),
        (if (.warnings | length) > 0 then "**Warnings**", (.warnings[] | "- " + (. | cell)), "" else empty end),
        (if (.errors | length) > 0 then "**Errors**", (.errors[] | "- " + (. | cell)), "" else empty end),
        "</details>",
        "")
    ' "$results"
  fi
  if [ -n "$run_url" ]; then echo "<sub>[Workflow run]($run_url)</sub>"; fi
)"

if [ "${#body}" -gt "$limit" ]; then
  printf '%s\n\n_Truncated. Download the full drafts from the workflow run._\n' "${body:0:$limit}"
else
  printf '%s\n' "$body"
fi
