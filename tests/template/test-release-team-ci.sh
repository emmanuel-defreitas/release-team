#!/usr/bin/env bash
# shellcheck source=tests/template/harness.sh
. "$(dirname "${BASH_SOURCE[0]}")/harness.sh"

R="$SCRIPTS/release-team-ci.sh"
unset OPENAI_API_KEY OPENAI_MODEL REQUESTED_RUNTIME OBJECTIVE OUT_DIR EVIDENCE_RANGE RELEASE_TEAM_CMD

# ── runtime selection ──
assert_eq offline "$("$R" runtime 2>/dev/null)" "auto without a key falls back to offline"
assert_eq offline "$(OPENAI_API_KEY='' OPENAI_MODEL=m "$R" runtime 2>/dev/null)" "an empty key counts as missing"
assert_eq openai "$(OPENAI_API_KEY=k OPENAI_MODEL=m "$R" runtime 2>/dev/null)" "auto with key and model picks openai"
assert_fail "auto with a key but no model fails loudly" env OPENAI_API_KEY=k "$R" runtime
assert_eq offline "$(REQUESTED_RUNTIME=offline OPENAI_API_KEY=k OPENAI_MODEL=m "$R" runtime 2>/dev/null)" \
  "explicit offline ignores the key"
assert_fail "explicit openai without a key fails" env REQUESTED_RUNTIME=openai OPENAI_MODEL=m "$R" runtime
assert_eq openai "$(REQUESTED_RUNTIME=openai OPENAI_API_KEY=k OPENAI_MODEL=m "$R" runtime 2>/dev/null)" \
  "explicit openai with key and model"
assert_fail "unknown runtime is rejected" env REQUESTED_RUNTIME=bogus "$R" runtime

# ── run, against a stub CLI that records what it received ──
new_repo
commit "feat: first change"
commit "fix: second change"
cat > stub.sh <<'STUB'
#!/usr/bin/env bash
echo "$* key=${OPENAI_API_KEY:-unset}" >> calls.log
case "$1" in
  validate) echo '{"valid": true}' ;;
  plan) echo '[{"agent":"orchestrator","action":"plan","objective":"x"}]' ;;
  workflow)
    [ -z "${STUB_FAIL:-}" ] || { echo '[{"agent":"orchestrator","status":"failed","runtime":"openai"}]'; exit 1; }
    rt=offline; [ "$3" = --runtime ] && rt="$4"
    echo "[{\"agent\":\"orchestrator\",\"status\":\"completed\",\"runtime\":\"$rt\"}]" ;;
esac
STUB
chmod +x stub.sh
export RELEASE_TEAM_CMD="$PWD/stub.sh"

assert_fail "run requires an objective" env OUT_DIR=out "$R" run

rm -f calls.log
assert_ok "offline run succeeds" env REQUESTED_RUNTIME=offline OPENAI_API_KEY=k OBJECTIVE="Ship it" OUT_DIR=out "$R" run
calls="$(cat calls.log)"
assert_contains "$calls" "workflow out/workflow.json --runtime offline key=unset" "offline run never sees the key"
assert_not_contains "$calls" "key=k" "key is stripped from every offline call"
assert_contains "$(cat out/summary.md)" "| orchestrator | completed | offline |" "summary lists agent status"
assert_contains "$(cat out/summary.md)" "nothing was posted, published" "summary states drafts only"
assert_eq 2 "$(jq '.[0].evidence | length' out/workflow.json)" "commit subjects become evidence"
assert_contains "$(jq -r '.[0].evidence[0]' out/workflow.json)" "fix: second change" "newest commit first"

rm -rf out calls.log
assert_ok "openai run succeeds" env OPENAI_API_KEY=k OPENAI_MODEL=m OBJECTIVE="Ship it" OUT_DIR=out EVIDENCE_RANGE=none "$R" run
assert_contains "$(cat calls.log)" "workflow out/workflow.json --runtime openai --model m key=k" "openai run passes runtime and model"
assert_eq 0 "$(jq '.[0].evidence | length' out/workflow.json)" "EVIDENCE_RANGE=none sends no commits"
assert_contains "$(cat out/summary.md)" "| orchestrator | completed | openai |" "summary shows openai runtime"

rm -rf out
assert_fail "a failed agent fails the run" env STUB_FAIL=1 OPENAI_API_KEY=k OPENAI_MODEL=m OBJECTIVE=x OUT_DIR=out "$R" run
assert_contains "$(cat out/summary.md)" "| orchestrator | failed | openai |" "summary is still written on failure"

finish
