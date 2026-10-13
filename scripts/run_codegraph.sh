#!/usr/bin/env bash
set -euo pipefail

# Use the selected nvm runtime when a login shell has put another Node first.
NODE_BIN_DIR=${CODEGRAPH_NODE_BIN_DIR:-${NVM_BIN:-}}
if [[ -n "$NODE_BIN_DIR" ]]; then
  export PATH="$NODE_BIN_DIR:$PATH"
fi

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
OUTPUT="$ROOT/results/codegraph"
mkdir -p "$OUTPUT"
RUN_TEMP=$(mktemp -d "${TMPDIR:-/tmp}/ctx-codegraph.XXXXXX")
export HOME="$RUN_TEMP/home"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_DATA_HOME="$HOME/.local/share"
export npm_config_cache="$RUN_TEMP/npm-cache"
export npm_config_userconfig="$HOME/.npmrc"
export npm_config_globalconfig="$HOME/npm-globalrc"
export npm_config_prefer_offline=true
export npm_config_update_notifier=false
export CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1 NO_COLOR=1
export HEADROOM_TELEMETRY=0 RTK_TELEMETRY_DISABLED=1 PYTHONDONTWRITEBYTECODE=1
# Prevent init's watch-disabled fallback from offering/installing Git hooks.
unset CODEGRAPH_NO_WATCH
export CODEGRAPH_FORCE_WATCH=1
export CODEGRAPH_DIR=".codegraph-demo-$(basename "$RUN_TEMP")"
mkdir -p "$HOME" "$npm_config_cache"
cleanup() {
  rm -rf "$ROOT/$CODEGRAPH_DIR" "$RUN_TEMP"
}
trap cleanup EXIT

# Reuse only the supplied experiment's temporary npm cache, never ~/.npm.
# On a new machine, npx downloads the pinned package into the isolated cache.
CACHE_SEED=${CODEGRAPH_NPM_CACHE_SEED:-/tmp/ctxlab/cg-home/.npm}
if [[ -d "$CACHE_SEED/_cacache" ]]; then
  cp -R "$CACHE_SEED/_cacache" "$npm_config_cache/"
fi
if [[ -d "$CACHE_SEED/_npx" ]]; then
  cp -R "$CACHE_SEED/_npx" "$npm_config_cache/"
fi

capture() {
  local name=$1
  shift
  local status=0
  npx -y @colbymchenry/codegraph@1.6.2 "$@" \
    >"$RUN_TEMP/$name.txt" 2>"$RUN_TEMP/$name.stderr.txt" </dev/null || status=$?
  python3 scripts/normalize_paths.py "$RUN_TEMP/$name.txt" > "$OUTPUT/$name.txt"
  python3 scripts/normalize_paths.py "$RUN_TEMP/$name.stderr.txt" > "$OUTPUT/$name.stderr.txt"
  printf '%s\n' "$status" >"$OUTPUT/$name.exit.txt"
  return "$status"
}

capture version --version
capture init init --yes "$ROOT"
capture cart_total node cart_total
capture apply_coupon node apply_coupon
capture explore explore "why can the cart total become negative"
python3 scripts/measure_read.py

python3 - "$ROOT" "$ROOT/$CODEGRAPH_DIR/codegraph.db" <<'PY'
import json
import re
import sqlite3
import sys
from pathlib import Path

root = Path(sys.argv[1])
output = root / "results" / "codegraph"
commands = {}
for name, arguments in (
    ("version", ["--version"]),
    ("init", ["init", "--yes", "."]),
    ("cart_total", ["node", "cart_total"]),
    ("apply_coupon", ["node", "apply_coupon"]),
    ("explore", ["explore", "why can the cart total become negative"]),
):
    raw = (output / f"{name}.txt").read_bytes()
    rendered = raw.decode("utf-8")
    commands[name] = {
        "command": ["npx", "-y", "@colbymchenry/codegraph@1.6.2", *arguments],
        "stdout": f"results/codegraph/{name}.txt",
        "stderr": f"results/codegraph/{name}.stderr.txt",
        "exit_code": int((output / f"{name}.exit.txt").read_text()),
        "stdout_bytes": len(raw),
        "stdout_characters": len(rendered),
        "stdout_lines": len(rendered.splitlines()),
        "tokens": None,
        "tokens_note": "The CLI does not report a token count for this output.",
    }
    found = re.search(r"Found (\d+) symbols across (\d+) files", rendered)
    if found:
        commands[name]["symbols_returned"] = int(found[1])
        commands[name]["files_returned"] = int(found[2])

with sqlite3.connect(sys.argv[2]) as database:
    indexed_files = [row[0] for row in database.execute("SELECT path FROM files ORDER BY path")]
    indexed_nodes = database.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    indexed_edges = database.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
result = {
    "script": "scripts/run_codegraph.sh",
    "package": "@colbymchenry/codegraph@1.6.2",
    "user_question": "Why does the FREESHIP coupon make the cart total negative? Fix it.",
    "explore_query": "why can the cart total become negative",
    "scope": "Repository root, with codegraph.json excluding data/, scripts/, tools/, results/, and docs/. Shop source and tests are included.",
    "indexed_files": indexed_files,
    "indexed_nodes": indexed_nodes,
    "indexed_edges": indexed_edges,
    "commands": commands,
}
(output / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
PY
