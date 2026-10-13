#!/usr/bin/env python3
"""Save exact Read-tool-equivalent text and its UTF-8 byte measurements."""

import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "results" / "codegraph"
    output.mkdir(parents=True, exist_ok=True)
    measurements = []
    for relative in ("shop/cart.py", "shop/coupons.py"):
        source = root / relative
        raw = source.read_bytes()
        lines = raw.decode("utf-8").splitlines(keepends=True)
        rendered = "".join(f"{number:6d}\t{line}" for number, line in enumerate(lines, 1))
        destination = output / f"read_{source.name}.txt"
        destination.write_bytes(rendered.encode("utf-8"))
        measurements.append({
            "file": relative,
            "lines": len(lines),
            "raw_bytes": len(raw),
            "line_numbered_bytes": len(rendered.encode("utf-8")),
            "line_numbered_output": destination.relative_to(root).as_posix(),
        })
    result = {
        "script": "scripts/measure_read.py",
        "format": "Each source line prefixed with its right-aligned width-6 line number and a TAB; source line endings preserved; no wrapper text.",
        "files": measurements,
        "total_raw_bytes": sum(item["raw_bytes"] for item in measurements),
        "total_line_numbered_bytes": sum(item["line_numbered_bytes"] for item in measurements),
        "total_lines": sum(item["lines"] for item in measurements),
    }
    (output / "read_metrics.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
