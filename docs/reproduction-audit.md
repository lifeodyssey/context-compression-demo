# Reproduction audit against cfe3ee2

The production bug remains intentional. The project still has five feature
modules / 288 physical lines (289 including `shop/__init__.py`). Four test
modules / 300 lines collect 67 cases: 66 pass and only
`test_freeship_never_negative` fails. Its assertion and the faulty shipping
coupon subtraction both happen to be at line 52, in `tests/test_cart.py` and
`shop/coupons.py` respectively. No article draft was edited.

See [the complete numeric comparison](article-number-changes.md),
[the generated summary](../results/summary.md), and
[the machine-readable checks](../results/metrics.json).

## E1: normalize paths before compression

`scripts/run_pytest.sh` captures into its disposable HOME, normalizes stdout
and stderr with `scripts/normalize_paths.py`, then writes `results/pytest/`.
Repository paths become `/work/context-compression-demo`, preserving relative
suffixes; the interpreter becomes `/work/toolchain/python`; other absolute
paths become `/work/external`. Quoted paths and absolute cachedir/configfile
headers are handled too. Timings are retained, not fabricated.

Headroom and Caveman receive those identical normalized bytes. RTK's actual
pytest child uses its own arguments, so a temporary wrapper applies the same
normalization before RTK reads or stores that output. CodeGraph stdout/stderr
are normalized before their metrics are measured. No compressor implementation
is patched. The summary checks all final result files for home paths, the real
repository path and the local username.

## E2: error protection is a conditional gate

Headroom 0.40.0 defaults `protect_error_outputs=True` and
`error_protection_max_chars=8000` at
`headroom/transforms/content_router.py:1870-1871`. The current Anthropic
`tool_result` branch (`content_router.py:7223-7236`) requires protection enabled,
a string, Python `len(text) <= 8000`, and either `is_error is True` or strong
error indicators. This fixture does not set `is_error`.

`headroom/transforms/error_detection.py:241-247,276-283` removes zero-error and
zero-failure phrases, lowercases the remaining text, then requires at least two
distinct substring hits from `error`, `fail`, `exception`, `traceback`, `fatal`,
`panic`, `crash`. Here `AssertionError` supplies `error` and `FAILED`/`FAILURES`
supplies `fail`. These are substring matches, not a requirement for an ERROR
severity record. Python characters and UTF-8 bytes are different measures;
this fixture is ASCII so its two counts coincide.

The normalized 6,426-character fixture now records
`router:protected:error_output` and is byte-identical after compression.
The OpenAI `role=tool` branch (`content_router.py:6128-6140`) requires strong
indicators without the Anthropic `is_error` alternative. Other earlier
protection branches can also return first.

Above 8,000 characters the gate is skipped and ordinary routing decides what
happens; it does **not** unconditionally invoke a log compressor. In cfe3ee2,
the 8,087-character pytest input was classified as `text`, selected
`KompressCompressor`, and stayed unchanged because Kompress was disabled.
Its byte identity therefore did not demonstrate error protection.

## E3: actual Caveman detection and folding

References below use Caveman commit
`2e08b9177c07bb7249a8a2d1a6758e5db281d002`.

`engine/detect.go:35-36,120-141` requires at least three code-keyword matches
plus structural syntax (unless a shebang already identifies code). Only
`def` matches in the normalized pytest text. The `::` node-ID separators supply
structural syntax but do not make up the missing keyword count. The old
interpreter path contained `private`; a clone rooted under `/private/tmp`
added another `private`, accidentally reaching three matches. Removing path
dependence correctly yields `text`, not `code`.

`engine/detect.go:81-105` falls back to text; terminal auto-detection requires
ANSI or at least three bare carriage returns, absent here. The text compressor
keeps five blank-line-delimited sections unchanged because its early return
threshold is six (`engine/compressors/text.go:34,55-57`). Thus “code parsing
failed” is not the explanation for this output.

Forced terminal mode retains 59/66 PASSED lines, with seven markers eliding
eleven lines: seven PASSED records and four blank lines. The failure, assertion,
line number and summary survive. There are no warning records in this fixture;
warning handling is source-confirmed, not demonstrated by this run.

`engine/compressors/terminal.go:30,53,124-148` preserves the first/last three
lines and important error/warning/stack records, then calls the global
`keepNonRedundant` pass. `engine/compressors/redundancy.go:39-85,109,142-161`
requires 90% of a candidate vocabulary to be covered by one retained vocabulary.
It does not compare only adjacent lines. Tokenization lowercases and masks
numeric runs, but preserves letters and underscores in test function names
(`redundancy.go:175-181,209-225`). Distinct tests therefore remain representative
records. Only consecutive deleted lines share a marker. File prefixes and the
failure can split groups, but reordering a realistic suite cannot eliminate
the distinct test vocabularies.

The implementation samples at most 64 initially retained categories, promotes
at most 128 new representatives, and considers at most 128 vocabulary entries
per unit; reaching the promotion limit preserves the remaining units
(`redundancy.go:68-74,109-121`). This suite does not reach that limit. Terminal
does not implement query-aware compression (`engine/engine.go:208-222`). The
four domain files were retained; closely related boundary checks were grouped
and redundant arithmetic/delivery examples removed instead of arranging the
suite to manufacture one fold.

## E4: labels supply the structural signal

Headroom references use release tag v0.40.0, commit
[`855390d6110e0bbb199d9b97025baac16c2f5cf3`](https://github.com/headroomlabs-ai/headroom/tree/855390d6110e0bbb199d9b97025baac16c2f5cf3).
The installed Python `content_router.py` matches that tag's git blob
`848cb81fe4a407fdda8c0b462861aee052bf483a`. The native `_core.abi3.so` is bundled
inside the `headroom-ai==0.40.0` wheel, and its RECORD checksum was verified.
It exposes no independent native commit/version; a source rebuild was not done.

The exact causal difference was the distribution of the **entire labels array**:

| Dataset | Label-value frequencies, descending | Smallest K covering 48/60 | Actual strategy, either query |
| --- | --- | ---: | --- |
| Original `/tmp/ctxlab/inputs/issues.json` | 8,8,8,7,7,7,7,7,1 | 7 | `skip:unique_entities_no_signal(60->60)` |
| cfe3ee2 | 26,20,13,1 | 3 | `smart_sample(60->15)` |
| Revised | 10,10,10,7,7,7,6,2,1 | 6 | `skip:unique_entities_no_signal(60->60)` |

All following Rust files are under
`crates/headroom-core/src/transforms/smart_crusher/`:

- `outliers.rs:133-170` serializes full field values, including nested arrays,
  and considers cardinalities 2 through 50. `outliers.rs:188-229` finds the
  smallest top-K set covering at least 80%; when K <= 5, other values become
  structural outliers. cfe3ee2's enhancement/question/docs labels cover 59/60,
  leaving #42's `[bug,regression]` value outside that set.
- `analyzer.rs:435-478,544,604-623` combines unique IDs (`id_uniqueness=1`) with
  the structural signal. Unique entities with no signal skip; with a signal
  they can be sampled. No numeric anomaly, numeric change point, score-field
  or error-keyword signal explains these fixtures. `analyzer.rs:666-695` falls
  through to SmartSample, whose default target is 15 (`config.rs:143`).
- `planning.rs:191-192` and `orchestration.rs:183-195` preserve structural
  outliers independently of query relevance. This is why cfe3ee2 kept #42 even
  **without a query**. It does not demonstrate semantic diagnosis.
- `crusher.rs:947-973` returns the no-signal skip before passing a query into
  the planner. Adding a query therefore does not override that decision.

Single-field swaps between the original ctxlab and cfe3ee2 inputs flipped the
decision in both directions **only for labels**. Swapping id, number, title,
state, user, comments, timestamps or body individually did not. Repeated text
and numeric patterns were not the direct cause. The evidence snapshot is
[headroom-field-probe.json](headroom-field-probe.json); actual strategies come
from installed SmartCrusher, while diagnostic signal calculations reproduce
the cited Rust rules.

The generator still needed a realism fix: ten repeated topics with numeric
suffixes, unrelated random labels and inconsistent author IDs became sixty
individually written reports with topic labels, coherent authors and ordered
dates. The date window ends before the run date. Only #42 mentions FREESHIP;
the #37 refactor it references is now an actual refactoring report. Both log
fixtures remain byte-identical. The revised top five label categories cover
44/60 and the top six cover 51/60, so no label outlier signal is produced.
This dataset happens to skip; this is not a universal property of issue lists.
“Skip” retains all records and fields but still serializes compact JSON; it
does not mean byte identity.

## E5: preserved evidence and one honest incompatibility

Nine of ten measured subchecks hold. RTK keeps the failure, assertion, line 52
and recall pointer; `rtk json` keeps only the first issue plus `... +59 more`.
Headroom uses `router:tool_result:mixed` and keeps a lossless 60-row table;
the checker reconstructs every field, including nested labels and user objects.
The codemode result is exactly
`["#42 Cart total goes negative with FREESHIP coupon"]`.

Caveman's logs behave as before: without a query all three FREESHIP records
are folded but `FREESHIP×3` survives in a marker; with the query all three
records survive verbatim. The synonym case keeps all three FREESHIP records
and one of three `service=pricing` cause lines. CodeGraph's two symbol calls
and explore succeed and include the faulty subtraction at `shop/coupons.py:52`.

The revised **JSON** no longer produces invariant fold markers. Caveman keeps
all sixty records, including #42, byte-identically with either query.
`engine/compressors/json.go:232` calls `keepNonRedundant` after anchor/error/
anomaly/query selection. None of the sixty distinct row vocabularies can cover
90% of another, so all rows are retained. The query-relevance limit of 50 is
not a hard cap on this final set. Markers require an actually deleted run
(`json.go:238-249`); when no array collapses, `json.go:94-98` returns the original
input rather than merely reserializing it. Manufacturing duplicates to retain
the old marker claim would undermine the data realism correction.

## Cross-path verification

The final cross-path report is recorded after cloning the implementation
commit, running `scripts/run_all.sh` in that clone, and comparing the complete
`results/` trees. The clone is then deleted. Only explicitly enumerated timing,
recall-hash and CCR-handle differences are allowed; none of the result files
are post-edited to make them match.
