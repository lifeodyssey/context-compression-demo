#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -n "${NVM_BIN:-}" ]]; then export PATH="$NVM_BIN:$PATH"; fi
task_home=$(mktemp -d "${TMPDIR:-/tmp}/shop-codemode.XXXXXX")
trap 'rm -rf "$task_home"' EXIT
export HOME="$task_home" XDG_CONFIG_HOME="$task_home/.config" XDG_CACHE_HOME="$task_home/.cache"
export HEADROOM_TELEMETRY=0 CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1 RTK_TELEMETRY_DISABLED=1
mkdir -p results/codemode
node scripts/filter_issues.mjs > results/codemode/issues.txt 2> results/codemode/stderr.txt
