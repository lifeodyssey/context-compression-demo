#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export CAVEMAN_MODULE_CACHE="${CAVEMAN_MODULE_CACHE:-${GOMODCACHE:-${GOPATH:-$HOME/go}/pkg/mod}}"
if [[ $(uname -s) == Darwin ]]; then
  export CAVEMAN_BUILD_CACHE="${CAVEMAN_BUILD_CACHE:-$HOME/Library/Caches/go-build}"
else
  export CAVEMAN_BUILD_CACHE="${CAVEMAN_BUILD_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/go-build}"
fi
if [[ -n "${NVM_BIN:-}" ]]; then export PATH="$NVM_BIN:$PATH"; fi
task_home=$(mktemp -d "${TMPDIR:-/tmp}/shop-all.XXXXXX")
trap 'rm -rf "$task_home"' EXIT
export HOME="$task_home" XDG_CONFIG_HOME="$task_home/.config" XDG_CACHE_HOME="$task_home/.cache" XDG_DATA_HOME="$task_home/.local/share"
export PYTHONDONTWRITEBYTECODE=1 HEADROOM_TELEMETRY=0 RTK_TELEMETRY_DISABLED=1 CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1
mkdir -p results
{
  python3 data/generate.py
  for tool in pytest rtk headroom caveman codemode codegraph; do
    printf 'Running %s\n' "$tool"
    bash "scripts/run_${tool}.sh"
  done
  python3 scripts/summarize.py
  printf 'All comparisons completed; see results/summary.md.\n'
} 2>&1 | tee results/run_all.txt
