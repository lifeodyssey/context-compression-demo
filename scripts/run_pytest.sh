#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
task_home=$(mktemp -d "${TMPDIR:-/tmp}/shop-pytest.XXXXXX")
trap 'rm -rf "$task_home"' EXIT
export HOME="$task_home" XDG_CONFIG_HOME="$task_home/.config" XDG_CACHE_HOME="$task_home/.cache"
export PATH="${PYTEST_BIN_DIR:-/tmp/hrenv/bin}:$PATH"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 TERM=dumb NO_COLOR=1
export HEADROOM_TELEMETRY=0 CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1 RTK_TELEMETRY_DISABLED=1
unset PYTEST_ADDOPTS
mkdir -p results/pytest
set +e
pytest -v > "$task_home/raw.txt" 2> "$task_home/stderr.txt"
status=$?
set -e
python3 scripts/normalize_paths.py "$task_home/raw.txt" > results/pytest/raw.txt
python3 scripts/normalize_paths.py "$task_home/stderr.txt" > results/pytest/stderr.txt
printf '%s\n' "$status" > results/pytest/exit_code.txt
python3 - <<'PY'
import json, re
from pathlib import Path
root = Path('results/pytest')
raw = (root / 'raw.txt').read_text()
failed = re.findall(r'^(.+?) FAILED\s+\[', raw, re.M)
passed = re.findall(r'^(.+?) PASSED\s+\[', raw, re.M)
assert (root / 'exit_code.txt').read_text().strip() == '1', raw
assert len(failed) == 1 and failed[0].endswith('::test_freeship_never_negative'), failed
assert re.search(rf'1 failed, {len(passed)} passed', raw), raw
assert len(raw) <= 7000, len(raw)
(root / 'metadata.json').write_text(json.dumps({
    'command': 'pytest -v', 'exit_code': 1, 'failed': failed,
    'passed': len(passed), 'collected': len(failed) + len(passed),
    'lines': len(raw.splitlines()), 'bytes': len(raw.encode()),
    'chars': len(raw), 'tokens': None,
    'path_normalization': 'scripts/normalize_paths.py; repository=/work/context-compression-demo; interpreter=/work/toolchain/python; other absolute paths=/work/external',
}, indent=2) + '\n')
print(f'Confirmed exactly one intended failure; {len(passed)} tests passed.')
PY
