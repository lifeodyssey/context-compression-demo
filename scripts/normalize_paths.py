"""Remove machine paths from captured output before any compressor sees it.

Keep repository-relative suffixes useful for locating the regression. External
paths are presentation metadata, so replace them with fixed logical locations.
This does not alter test names, assertion text, durations, or compressor output.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
PLACEHOLDER = "/work/context-compression-demo"


def normalize(text: str) -> str:
    # Resolve both spellings for macOS /tmp -> /private/tmp and symlinked clones.
    for root in sorted({str(ROOT), str(ROOT.resolve())}, key=len, reverse=True):
        text = text.replace(root, PLACEHOLDER)
    text = re.sub(r"(?m)^(platform .+ -- )/[^\n]*", r"\1/work/toolchain/python", text)
    # Header paths may contain spaces. Relative configfile/cachedir stay useful.
    text = re.sub(
        r"(?m)^((?:rootdir|cachedir|configfile):\s*)(/[^\n]*)",
        lambda match: match[1] + (match[2] if match[2].startswith(PLACEHOLDER)
                                  else "/work/external"),
        text,
    )
    text = re.sub(
        r'''(["'])(/[^\n]*?)\1''',
        lambda match: match[1] + (match[2] if match[2].startswith("/work/")
                                  else "/work/external") + match[1],
        text,
    )
    # Remaining absolute paths include quoted traceback paths and tool stderr.
    # Relative source paths (shop/coupons.py:58) do not match this boundary.
    return re.sub(
        r'''(?<![\w./])/(?:[^\s"'<>|,;]+)''',
        lambda match: match[0] if match[0].startswith("/work/") else "/work/external",
        text,
    )


if __name__ == "__main__":
    sys.stdout.write(normalize(Path(sys.argv[1]).read_text(encoding="utf-8")))
