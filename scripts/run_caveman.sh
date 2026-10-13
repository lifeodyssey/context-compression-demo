#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
repo_root=$PWD
source_mod_cache=${CAVEMAN_MODULE_CACHE:-${GOMODCACHE:-${GOPATH:-$HOME/go}/pkg/mod}}
if [[ $(uname -s) == Darwin ]]; then
  source_build_cache=${CAVEMAN_BUILD_CACHE:-$HOME/Library/Caches/go-build}
else
  source_build_cache=${CAVEMAN_BUILD_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/go-build}
fi
task_home=$(mktemp -d "${TMPDIR:-/tmp}/context-demo-caveman.XXXXXX")
cleanup() {
  "${HEADROOM_PYTHON:-/tmp/hrenv/bin/python}" - "$task_home" <<'PY'
import os
from pathlib import Path
import shutil
import stat
import sys

root = Path(sys.argv[1])
if not root.name.startswith("context-demo-caveman."):
    raise RuntimeError("Refusing unexpected cleanup path")
for directory, _, _ in os.walk(root):
    os.chmod(directory, os.stat(directory).st_mode | stat.S_IWUSR)
shutil.rmtree(root)
PY
}
trap cleanup EXIT
export HOME="$task_home" GOPATH="$task_home/go" GOCACHE="$task_home/go-build"
export GOMODCACHE="$task_home/go/pkg/mod" GOENV=off GOPROXY=off GOSUMDB=off
export GOTOOLCHAIN=local GOTELEMETRY=off
export XDG_CONFIG_HOME="$task_home/.config" XDG_CACHE_HOME="$task_home/.cache"
export XDG_DATA_HOME="$task_home/.local/share" TMPDIR="$task_home/tmp"
mkdir -p "$GOPATH/pkg" "$TMPDIR" results/caveman
source_commit=$(git -C /tmp/ctxsrc/caveman rev-parse HEAD)
if [[ "$source_commit" != 2e08b9177c07bb7249a8a2d1a6758e5db281d002 ]]; then
  echo "Expected caveman commit 2e08b9177c07bb7249a8a2d1a6758e5db281d002; found $source_commit" >&2
  exit 1
fi

# Clone required cached dependencies into the temporary HOME before an offline build.
# On APFS cp -c shares unchanged blocks; other systems use a normal copy.
copy_cache() {
  if [[ $(uname -s) == Darwin ]]; then
    cp -cR "$1" "$2"
  else
    cp -R "$1" "$2"
  fi
}
if [[ ! -d "$source_mod_cache" ]]; then
  echo "Missing cached Go modules: $source_mod_cache" >&2
  exit 1
fi
"${HEADROOM_PYTHON:-/tmp/hrenv/bin/python}" - "$source_mod_cache" "$GOMODCACHE" <<'PY'
import platform
from pathlib import Path
import shutil
import subprocess
import sys

source, target = map(Path, sys.argv[1:])
target.mkdir(parents=True, exist_ok=True)
for line in Path("tools/cavrun/go.mod").read_text().splitlines():
    parts = line.split()
    if parts and parts[0] == "require":
        parts = parts[1:]
    if len(parts) < 2 or not parts[1].startswith("v") or parts[1] == "v0.0.0":
        continue
    relative = Path(parts[0] + "@" + parts[1])
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    flags = "-cR" if platform.system() == "Darwin" else "-R"
    subprocess.run(["cp", flags, str(source / relative), str(destination)], check=True)

# Module graph loading needs cached manifests, but not unrelated source archives.
download = source / "cache" / "download"
for pattern in ("*.mod", "*.info", "*.ziphash"):
    for manifest in download.rglob(pattern):
        if not manifest.is_file():
            continue
        destination = target / manifest.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(manifest, destination)
PY
if [[ -d "$source_build_cache" ]]; then
  copy_cache "$source_build_cache" "$GOCACHE"
fi
(
  cd tools/cavrun
  go build -mod=readonly -o "$task_home/cavrun" .
) > results/caveman/build.stdout.txt 2> results/caveman/build.stderr.txt
printf '%s\n' "$source_commit" > results/caveman/source_commit.txt
go version > results/caveman/go_version.txt

query='Why does the FREESHIP coupon make the cart total negative? Fix it.'
run_case() {
  local name=$1 file=$2 forced_type=$3 question=$4
  CAV_TYPE="$forced_type" CAV_METADATA="$repo_root/results/caveman/$name.metadata.json" \
    "$task_home/cavrun" "$file" "$question" \
    > "results/caveman/$name.txt" 2> "results/caveman/$name.stderr.txt"
}
run_case pytest_auto results/pytest/raw.txt '' "$query"
run_case pytest_terminal results/pytest/raw.txt terminal "$query"
run_case issues_no_query data/issues.json '' ''
run_case issues_query data/issues.json '' "$query"
run_case app_no_query data/app.log '' ''
run_case app_query data/app.log '' "$query"
run_case app_synonyms_query data/app_synonyms.log '' "$query"
