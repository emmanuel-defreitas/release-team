#!/usr/bin/env bash
# Run the release-team agents in CI (.github/workflows/release-team.yml) or locally.
#
#   scripts/release-team-ci.sh runtime   print the runtime to use: offline or openai
#   scripts/release-team-ci.sh run       plan + run the five-agent draft workflow into OUT_DIR
#
# Runtime selection (REQUESTED_RUNTIME, default auto):
#   auto     openai when OPENAI_API_KEY is set (OPENAI_MODEL is then required), otherwise offline
#   offline  always offline; the key is removed from the environment before the CLI runs
#   openai   require OPENAI_API_KEY and OPENAI_MODEL, fail otherwise
#
# Other inputs: OBJECTIVE (required for run), OUT_DIR (default release-team-out),
# EVIDENCE_RANGE (git range for commit-subject evidence, default: since the latest tag;
# "none" disables it), RELEASE_TEAM_CMD (default: uv run --no-sync release-team).
#
# Output is drafts only: workflow.json, results.json and summary.md in OUT_DIR. Nothing is
# posted, published, tagged or released. Draft text is never printed to the log.

set -euo pipefail

# shellcheck source=scripts/lib.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

notice() {
  if [ -n "${GITHUB_ACTIONS:-}" ]; then printf '::notice::%s\n' "$*" >&2; else info "$*"; fi
}

select_runtime() {
  local requested="${REQUESTED_RUNTIME:-auto}" key="${OPENAI_API_KEY:-}" model="${OPENAI_MODEL:-}"
  case "$requested" in
    offline) echo offline ;;
    auto | openai)
      if [ -z "$key" ]; then
        [ "$requested" = auto ] || die "runtime openai requested but the OPENAI_API_KEY secret is not set"
        echo offline
        return 0
      fi
      [ -n "$model" ] || die "OPENAI_API_KEY is set but OPENAI_MODEL is not; set the OPENAI_MODEL repository variable"
      echo openai
      ;;
    *) die "unknown runtime '$requested' (expected auto, offline or openai)" ;;
  esac
}

# Commit subjects as evidence, as a JSON array (untrusted data for the agents).
evidence_json() {
  local range="${EVIDENCE_RANGE:-}"
  if [ "$range" = none ]; then echo '[]'; return 0; fi
  [ -n "$range" ] || range="$(unreleased_range HEAD)"
  local subjects
  subjects="$(git log --no-merges --format='%h %s' -n 200 "$range" 2>/dev/null)" || subjects=''
  printf '%s' "$subjects" | jq -Rs 'split("\n") | map(select(length > 0))'
}

cmd_run() {
  need jq git
  local runtime objective out status
  local -a rt
  objective="${OBJECTIVE:-}"
  [ -n "${objective//[[:space:]]/}" ] || die "OBJECTIVE is required"
  out="${OUT_DIR:-release-team-out}"
  runtime="$(select_runtime)"
  # shellcheck disable=SC2206  # intentional word splitting of the command override
  rt=(${RELEASE_TEAM_CMD:-uv run --no-sync release-team})
  mkdir -p "$out"

  if [ "$runtime" = offline ]; then
    # Defence in depth: the offline runtime never needs the key, so do not hand it over.
    unset OPENAI_API_KEY
    notice "release-team runtime: offline (placeholder drafts, no model calls)"
  else
    notice "release-team runtime: openai (model ${OPENAI_MODEL})"
  fi

  "${rt[@]}" validate >/dev/null
  "${rt[@]}" plan "$objective" > "$out/plan.json"
  jq --argjson ev "$(evidence_json)" 'map(.evidence = $ev)' "$out/plan.json" > "$out/workflow.json"
  rm -f "$out/plan.json"

  status=0
  if [ "$runtime" = openai ]; then
    "${rt[@]}" workflow "$out/workflow.json" --runtime openai --model "$OPENAI_MODEL" \
      > "$out/results.json" || status=$?
  else
    "${rt[@]}" workflow "$out/workflow.json" --runtime offline > "$out/results.json" || status=$?
  fi

  write_summary "$runtime" "$out" > "$out/summary.md"
  return "$status"
}

# Status table only; draft content stays in results.json.
write_summary() {
  local runtime="$1" out="$2"
  printf '## Release Team drafts\n\n'
  printf 'Runtime: `%s`. Drafts only: nothing was posted, published, tagged or released.\n\n' "$runtime"
  if [ "$runtime" = offline ]; then
    printf 'Offline mode returns placeholder drafts. Add the `OPENAI_API_KEY` secret and the\n'
    printf '`OPENAI_MODEL` variable to switch to OpenAI automatically.\n\n'
  fi
  if jq -e 'type == "array"' "$out/results.json" >/dev/null 2>&1; then
    printf '| Agent | Status | Runtime |\n| --- | --- | --- |\n'
    jq -r '.[] | "| \(.agent) | \(.status) | \(.runtime) |"' "$out/results.json"
    printf '\nDownload the `release-team-drafts` artifact for the full drafts.\n'
  else
    printf 'The workflow did not produce results; see the job log.\n'
  fi
}

main() {
  local cmd="${1:-}"; [ "$#" -gt 0 ] && shift
  case "$cmd" in
    runtime) select_runtime ;;
    run) cmd_run ;;
    *) sed -n '2,19p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; [ -z "$cmd" ] || exit 2 ;;
  esac
}

main "$@"
