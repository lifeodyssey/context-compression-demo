#!/usr/bin/env python3
"""Run Headroom's offline pipeline and SmartCrusher on the shared fixtures."""

import dataclasses
import importlib.metadata
import json
import logging
import os
from pathlib import Path

# The shell wrapper supplies an isolated HOME. No provider client is constructed.
os.environ["HEADROOM_TELEMETRY"] = "0"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import headroom
from headroom.transforms.smart_crusher import SmartCrusher


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "headroom"
QUERY = "Why does the FREESHIP coupon make the cart total negative? Fix it."
MODEL = "claude-sonnet-4-5-20250929"
ROUTING_EVENTS = []


class RoutingLogFilter(logging.Filter):
    """Keep route decisions without duplicating entire raw inputs in DEBUG logs."""

    def filter(self, record):
        message = record.getMessage()
        if message.startswith("event=content_router_") and "{" in message:
            prefix, payload = message.split("{", 1)
            event = json.loads("{" + payload)
            selected = {
                key: value
                for key, value in event.items()
                if key in {
                    "event", "chars", "bytes", "detected_content_type",
                    "detection_confidence", "selected_strategy", "selection_reason",
                    "requested_strategy", "actual_strategy", "strategy_chain",
                    "compressor", "reason", "compression_ratio", "tokens_saved",
                }
            }
            ROUTING_EVENTS.append(selected)
            record.msg = prefix + json.dumps(selected)
            record.args = ()
        return True


def dimensions(text):
    return {
        "bytes": len(text.encode("utf-8")),
        "characters": len(text),
        "lines": len(text.splitlines()),
    }


def issue_preservation(source, output):
    issues = json.loads(source)
    kept = [issue["number"] for issue in issues if issue["title"] in output]
    return {
        "issues_before": len(issues),
        "issues_kept": len(kept),
        "issues_elided": len(issues) - len(kept),
        "kept_issue_numbers": kept,
        "issue_42_kept": 42 in kept,
        "preservation_basis": "original unique issue title present in output",
    }


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def pipeline_case(name, input_path, command):
    original = input_path.read_text()
    first_event = len(ROUTING_EVENTS)
    messages = [
        {"role": "user", "content": QUERY},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_demo",
                    "name": "Bash",
                    "input": {"command": command},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "tool_demo", "content": original}
            ],
        },
    ]
    result = headroom.compress(
        messages,
        model=MODEL,
        kompress_model="disabled",
        protect_recent=0,
        diagnostics=True,
    )
    # Preserve the actual model-visible tool result independently of its envelope.
    blocks = [
        block
        for message in result.messages
        if isinstance(message.get("content"), list)
        for block in message["content"]
        if block.get("type") == "tool_result"
        and block.get("tool_use_id") == "tool_demo"
    ]
    if len(blocks) != 1 or not isinstance(blocks[0]["content"], str):
        raise RuntimeError("Unexpected Headroom result shape; inspect messages output")
    output = blocks[0]["content"]
    (OUT / f"{name}.txt").write_text(output)
    write_json(OUT / f"{name}.messages.json", result.messages)
    metadata = {
        "script": "scripts/run_headroom.sh",
        "input": str(input_path.relative_to(ROOT)),
        "version": importlib.metadata.version("headroom-ai"),
        "model_for_token_counting": MODEL,
        "query": QUERY,
        "options": {"kompress_model": "disabled", "protect_recent": 0},
        "input_dimensions": dimensions(original),
        "output_dimensions": dimensions(output),
        "unchanged": output == original,
        "tokens_before": result.tokens_before,
        "tokens_after": result.tokens_after,
        "tokens_saved": result.tokens_saved,
        "token_count_basis": "Headroom local estimator; complete three-message conversation, not provider usage",
        "transforms_applied": result.transforms_applied,
        "routing_events": ROUTING_EVENTS[first_event:],
        "diagnostics": [dataclasses.asdict(item) for item in result.diagnostics or []],
    }
    if name == "issues":
        metadata.update(issue_preservation(original, output))
    write_json(OUT / f"{name}.metadata.json", metadata)


def smartcrusher_case(name, query):
    source_path = ROOT / "data" / "issues.json"
    original = source_path.read_text()
    result = SmartCrusher(with_compaction=False, lossless_only=False).crush(original, query)
    (OUT / f"{name}.txt").write_text(result.compressed)
    metadata = {
        "script": "scripts/run_headroom.sh",
        "input": "data/issues.json",
        "version": importlib.metadata.version("headroom-ai"),
        "query": query,
        "options": {"with_compaction": False, "lossless_only": False},
        "input_dimensions": dimensions(original),
        "output_dimensions": dimensions(result.compressed),
        "was_modified": result.was_modified,
        "strategy": result.strategy,
        "tokens_before": None,
        "tokens_after": None,
        "token_count_basis": "SmartCrusher.crush does not report token counts",
        **issue_preservation(original, result.compressed),
    }
    write_json(OUT / f"{name}.metadata.json", metadata)


def main():
    if importlib.metadata.version("headroom-ai") != "0.40.0":
        raise RuntimeError("This comparison requires headroom-ai 0.40.0")
    OUT.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(OUT / "routing.log", mode="w")
    handler.addFilter(RoutingLogFilter())
    logging.basicConfig(level=logging.DEBUG, handlers=[handler],
                        format="%(name)s %(levelname)s %(message)s")
    pipeline_case("pytest", ROOT / "results" / "pytest" / "raw.txt", "pytest -v")
    pipeline_case("issues", ROOT / "data" / "issues.json", "cat data/issues.json")
    smartcrusher_case("smartcrusher_no_query", "")
    smartcrusher_case("smartcrusher_query", QUERY)


if __name__ == "__main__":
    main()
