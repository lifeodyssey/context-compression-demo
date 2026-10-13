# Context compression: one shop, one regression

This private demonstration repository puts every comparison on the same small Python shop. The agent's task is:

> Why does the FREESHIP coupon make the cart total negative? Fix it.

The bug is intentionally **not fixed**: `cart_total` calls `apply_coupon`, which treats `FREESHIP` as a flat $5 discount with no lower bound. A $3 merchandise subtotal therefore becomes **-$2.00**. This is the sole failing test. The five feature modules contain 288 physical lines (289 with the package initializer); the suite has 87 collected cases covering cart operations, coupon eligibility, shipping, tax, and model validation.

## Layout

```text
shop/                  models, coupons, shipping, tax, cart
tests/                 86 passing cases and the one intended regression
data/generate.py       deterministic synthetic issue/log generator
data/issues.json       60 GitHub-like issues; only #42 is relevant
data/app.log           300 lines; three FREESHIP checkout totals of -2.00
data/app_synonyms.log  303 lines; adds three INFO pricing explanations
tools/cavrun/          small driver calling the pinned Caveman engine
scripts/run_*.sh       one entry point per comparison, plus run_all.sh
scripts/filter_issues.mjs  local codemode-equivalent filter (not Pi execution)
scripts/measure_read.py    exact numbered Read-equivalent source rendering
scripts/summarize.py       derive and validate the results ledger
results/               captured stdout/stderr, metadata, summary.md, metrics.json
```

The data are fixtures, not real customer records or a live GitHub response. Seed `20261013` fixes both generators. The checkout amounts are computed by this repository's `shop.cart.cart_total`; `total` is merchandise after the coupon and before shipping/tax. The three extra pricing lines use only synonyms for the cause: “discount larger than subtotal, amount went below zero, no lower bound applied”.

## Run the shop and tests

Python 3.10+ is sufficient for the shop. The captured run used Python 3.13.16 and pytest 9.1.1. With pytest available:

```sh
python3 -c 'from shop.cart import cart_total; print(cart_total([{"price": 3.0, "quantity": 1}], "FREESHIP"))'
pytest -v
```

`pytest -v` must exit 1, with exactly `test_freeship_never_negative` failing. `pytest.ini` sets `pythonpath = .`. To install pytest in an isolated environment, use `python3 -m venv .venv` and install `requirements-dev.txt` with that environment's pip and a temporary HOME; nothing requires a global installation.

## Reproduce all comparisons

The supplied research environment already has the pinned tools listed below. From this repository:

```sh
bash scripts/run_all.sh
# equivalently: make reproduce
```

The script generates the fixtures, runs raw pytest, RTK, Headroom, Caveman, the Node filter, and CodeGraph, then validates invariants and writes [results/summary.md](results/summary.md) and [results/metrics.json](results/metrics.json). It accepts the expected pytest exit 1 and requires exactly one failure; other command failures stop the run. Individual `scripts/run_<tool>.sh` files can also be invoked from any directory. Headroom and Caveman consume the previously captured `results/pytest/raw.txt`.

Every runner creates a temporary HOME and redirects tool caches/configuration there. Telemetry is disabled. No global hook setup, `rtk init -g`, `caveman setup`, `codegraph install`, provider/model API calls, or GitHub requests are used. Headroom runs in offline mode with Kompress disabled; its `model` argument selects local token counting, not inference. Pytest plugin autoload is disabled to avoid unrelated installed plugins changing the comparison.

| Tool | Pinned version / source | Default prerequisite or override |
| --- | --- | --- |
| pytest | 9.1.1 | `/tmp/hrenv/bin/pytest`; `PYTEST_BIN_DIR` |
| RTK | 0.49.0, commit `a4cddfc5ce6e6412c66e9729c4200792d822a964` | `/tmp/ctxsrc/rtk/target/release/rtk`; `RTK_BIN` |
| Headroom | `headroom-ai==0.40.0` | `/tmp/hrenv/bin/python`; `HEADROOM_PYTHON` |
| Caveman | commit `2e08b9177c07bb7249a8a2d1a6758e5db281d002` | `/tmp/ctxsrc/caveman` via the Go module replacement |
| CodeGraph | `@colbymchenry/codegraph@1.6.2` | `npx -y` runs the pinned published package |
| CodeGraph source reference | commit `1ce1167e6f647f584220926befd86fd1881d3f70` | Reference checkout for the published 1.6.2 CLI |
| Node | captured with v24.18.0 | Uses `NVM_BIN` if set; CodeGraph supports `CODEGRAPH_NODE_BIN_DIR` |
| Go | 1.26.8 | `go` on PATH, with offline module/build caches |

For a fresh machine, obtain the pinned RTK/Caveman checkouts in the paths above (or change RTK_BIN / the local Go replacement), build RTK, prepare a temporary Python environment with `pytest==9.1.1 headroom-ai==0.40.0`, and populate the pinned Go dependencies in a temporary cache. These prerequisites are explicit; the repository does not silently install or alter tools. Caveman's `CAVEMAN_MODULE_CACHE` and `CAVEMAN_BUILD_CACHE` select cache seeds copied into its disposable HOME, so the originals remain read-only. CodeGraph can reuse `CODEGRAPH_NPM_CACHE_SEED` (default `/tmp/ctxlab/cg-home/.npm`); without that cache npx needs network access to download the pinned package into its temporary cache.

## What is measured

- RTK executes `rtk pytest -v` itself; its internal pytest arguments differ from plain `pytest -v`. [The recalled child output](results/rtk/pytest.recalled.txt) is captured before its temporary store is deleted. RTK's token estimates come from its temporary tracking database, not from counting the separate verbose baseline.
- Headroom receives three Anthropic-format messages: the question, an assistant Bash `tool_use`, and a user `tool_result`. Its pipeline token counts include that envelope. Direct SmartCrusher is run with and without the same query; it does not expose token counts.
- Caveman runs automatic pytest detection and forced `terminal`, JSON with/without query, logs with/without query, and the synonym log with query. It records its `o200k_base` counts, content type, retention and elision counts. Original-content stores are temporary; the committed input files remain the durable originals.
- The Node filter reproduces the codemode filtering logic locally. It emits the serialized array with no terminal newline, and is not a Pi integration test.
- CodeGraph initializes at the repository root and includes the shop and tests. [codegraph.json](codegraph.json) excludes data, tool drivers, scripts and results so generated comparison artifacts do not enter the source index. Symbol callers can therefore include test functions. Its exact `explore` query is `why can the cart total become negative`, as in the article comparison.
- The Read-equivalent baseline numbers every source line using **six right-aligned character columns, then one TAB**, preserving line endings and excluding tool wrapper text. Both raw file bytes and rendered bytes are recorded; CodeGraph does not report output tokens.

Raw timing, platform headers, absolute paths and recall hashes can vary between runs. Byte figures in the article refer to the committed output snapshot; regenerate the ledger for a new run. Compression success is measured here by retained evidence, not by asking a model to fix the bug. Qualitative differences from previous fixtures are recorded in the article as review comments rather than silently changing its argument.
