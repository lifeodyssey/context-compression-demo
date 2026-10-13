#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
task_home=$(mktemp -d "${TMPDIR:-/tmp}/shop-rtk.XXXXXX")
trap 'rm -rf "$task_home"' EXIT
export HOME="$task_home" XDG_CONFIG_HOME="$task_home/.config" XDG_CACHE_HOME="$task_home/.cache" XDG_DATA_HOME="$task_home/.local/share"
export PATH="${PYTEST_BIN_DIR:-/tmp/hrenv/bin}:$PATH"
export RTK_TELEMETRY_DISABLED=1 DO_NOT_TRACK=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 TERM=dumb NO_COLOR=1
export RTK_DB_PATH="$task_home/tracking.db"
unset PYTEST_ADDOPTS
rtk_bin=${RTK_BIN:-/tmp/ctxsrc/rtk/target/release/rtk}
mkdir -p results/rtk
"$rtk_bin" --version > results/rtk/version.txt
git -C "${RTK_SOURCE_DIR:-/tmp/ctxsrc/rtk}" rev-parse HEAD > results/rtk/source_commit.txt
[[ "$(cat results/rtk/version.txt)" == 'rtk 0.49.0' ]]
[[ "$(cat results/rtk/source_commit.txt)" == 'a4cddfc5ce6e6412c66e9729c4200792d822a964' ]]
set +e
"$rtk_bin" pytest -v > results/rtk/pytest.txt 2> results/rtk/pytest.stderr.txt
status=$?
set -e
printf '%s\n' "$status" > results/rtk/pytest.exit_code.txt
[[ "$status" == 1 ]]
"$rtk_bin" json data/issues.json > results/rtk/issues.txt 2> results/rtk/issues.stderr.txt
python3 - <<'PY' > "$task_home/recall-hash"
import re
from pathlib import Path
text = Path('results/rtk/pytest.txt').read_text()
assert '1 failed' in text and 'test_freeship_never_negative' in text, text
match = re.search(r'rtk recall ([0-9a-f]+)', text)
assert match, text
print(match[1])
PY
"$rtk_bin" recall "$(cat "$task_home/recall-hash")" > results/rtk/pytest.recalled.txt 2> results/rtk/recall.stderr.txt
"$rtk_bin" gain --format json > results/rtk/gain.json 2> results/rtk/gain.stderr.txt
python3 - <<'PY'
import json, os, sqlite3
from pathlib import Path
databases = list(Path(os.environ['HOME']).rglob('tracking.db'))
assert len(databases) == 1, databases
with sqlite3.connect(f'file:{databases[0]}?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    rows = [dict(row) for row in db.execute(
        'SELECT rtk_cmd, input_tokens, output_tokens, saved_tokens FROM commands ORDER BY id'
    )]
Path('results/rtk/tokens.json').write_text(json.dumps(rows, indent=2) + '\n')
PY
