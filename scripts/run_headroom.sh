#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
task_home=$(mktemp -d "${TMPDIR:-/tmp}/context-demo-headroom.XXXXXX")
trap 'rm -rf "$task_home"' EXIT
export HOME="$task_home" HEADROOM_TELEMETRY=0 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CONFIG_HOME="$task_home/.config" XDG_CACHE_HOME="$task_home/.cache"
export XDG_DATA_HOME="$task_home/.local/share" PYTHONDONTWRITEBYTECODE=1
unset ANTHROPIC_API_KEY OPENAI_API_KEY HEADROOM_API_KEY
mkdir -p results/headroom
"${HEADROOM_PYTHON:-/tmp/hrenv/bin/python}" scripts/run_headroom.py \
  > results/headroom/run.stdout.txt 2> results/headroom/run.stderr.txt
