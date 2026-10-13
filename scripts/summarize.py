"""Derive the comparison ledger from captured files, never from hand-entered sizes."""
import ast
import csv
import getpass
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def read_json(path):
    return json.loads(path.read_text())


def stats(path):
    raw = path.read_bytes()
    text = raw.decode()
    return {"bytes": len(raw), "chars": len(text), "lines": len(text.splitlines())}


def flatten(record, prefix=""):
    """Match the nested-object columns in Headroom's typed CSV table."""
    values = {}
    for name, value in record.items():
        name = prefix + name
        if isinstance(value, dict):
            values.update(flatten(value, name + "."))
        else:
            values[name] = value
    return values


def restore_compacted(value):
    """Undo Headroom's nested table envelope (e.g. the two issue #42 labels)."""
    if isinstance(value, list):
        return [restore_compacted(item) for item in value]
    if isinstance(value, dict) and value.get('_compaction') == 'table':
        if value['_kept'] != value['_total'] or len(value['_rows']) != value['_total']:
            raise ValueError('Nested table discarded records')
        rows = []
        for cells in value['_rows']:
            if len(cells) != len(value['_schema']):
                raise ValueError('Nested table schema mismatch')
            row = {}
            for field, cell in zip(value['_schema'], cells):
                target = row
                *parents, name = field['name'].split('.')
                for parent in parents:
                    target = target.setdefault(parent, {})
                target[name] = restore_compacted(cell)
            rows.append(row)
        return rows
    if isinstance(value, dict):
        return {key: restore_compacted(item) for key, item in value.items()}
    return value


def lossless_issue_table(text, records):
    """Verify every cell, including nested user fields and JSON label arrays."""
    header, _, body = text.partition("\n")
    match = re.fullmatch(r"\[(\d+)\]\{(.+)\}", header)
    if not match or int(match[1]) != len(records):
        return False
    columns = [column.rsplit(":", 1) for column in match[2].split(",")]
    decoded = []
    converters = {
        "string": str, "int": int, "float": float,
        "bool": lambda value: {"true": True, "false": False}[value],
        "json": lambda value: restore_compacted(json.loads(value)),
    }
    try:
        for row in csv.reader(io.StringIO(body)):
            if len(row) != len(columns):
                return False
            decoded.append({name: converters[kind](value)
                            for (name, kind), value in zip(columns, row)})
    except (KeyError, ValueError, csv.Error):
        return False
    return decoded == [flatten(record) for record in records]


def compare(path, source=None):
    text = path.read_text()
    result = {"path": str(path.relative_to(ROOT)), **stats(path)}
    if source is not None:
        result["unchanged"] = path.read_bytes() == source.read_bytes()
    result["issue_42_title_survived"] = issues[41]["title"] in text
    result["issue_titles_kept"] = sum(issue["title"] in text for issue in issues)
    result["freeship_lines_kept"] = sum(line in text for line in freeship)
    result["pricing_lines_kept"] = sum(line in text for line in pricing)
    result["elided_line_counts"] = [int(n) for n in re.findall(r'(\d+) lines elided', text)]
    result["elided_lines"] = sum(result["elided_line_counts"])
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = None
    if path.parent.name == 'caveman' and isinstance(value, list) and all(isinstance(item, dict) for item in value):
        result["issue_records_kept"] = sum("number" in item for item in value)
        result["issue_records_elided"] = sum(item.get("__caveman_elided__", 0) for item in value)
        result["elision_groups"] = sum("__caveman_elided__" in item for item in value)
    meta = path.with_suffix('.metadata.json')
    if meta.exists():
        result["tool_metadata"] = read_json(meta)
    return result


issues = read_json(ROOT / "data/issues.json")
assert len(issues) == 60
relevant = [i for i in issues if re.search('FREESHIP', i['title'] + i['body'], re.I)]
assert [i['number'] for i in relevant] == [42]
assert {label['name'] for label in relevant[0]['labels']} == {'bug', 'regression'}
app = (ROOT / "data/app.log").read_text().splitlines()
syn = (ROOT / "data/app_synonyms.log").read_text().splitlines()
freeship = [line for line in app if 'coupon=FREESHIP' in line]
pricing = [line for line in syn if 'service=pricing' in line]
assert len(app) == 300 and len(syn) == 303
assert len(freeship) == len(pricing) == 3
assert all('service=checkout' in line and 'total=-2.00' in line for line in freeship)
assert all(not re.search(r'FREESHIP|coupon|negative', line, re.I) for line in pricing)

production = [ROOT / 'shop' / f'{name}.py' for name in ['models', 'coupons', 'shipping', 'tax', 'cart']]
source_stats = {str(p.relative_to(ROOT)): stats(p) for p in production}
source_lines = sum(s['lines'] for s in source_stats.values())
assert 250 <= source_lines <= 400, source_lines
symbols = {}
for path in production:
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            symbols[node.name] = {'file': str(path.relative_to(ROOT)), 'line': node.lineno}

pytest = read_json(RESULTS / 'pytest/metadata.json')
assert len(pytest['failed']) == 1 and pytest['failed'][0].endswith('::test_freeship_never_negative')
assert pytest['exit_code'] == 1 and pytest['collected'] == pytest['passed'] + 1
outputs = {}
for tool, names in {
    'rtk': ['pytest', 'issues'],
    'headroom': ['pytest', 'issues', 'smartcrusher_no_query', 'smartcrusher_query'],
    'caveman': ['pytest_auto', 'pytest_terminal', 'issues_no_query', 'issues_query', 'app_no_query', 'app_query', 'app_synonyms_query'],
    'codemode': ['issues'],
}.items():
    for name in names:
        source = ROOT / ('data/issues.json' if 'issues' in name or 'smartcrusher' in name else
                         'results/pytest/raw.txt' if 'pytest' in name else
                         'data/app_synonyms.log' if 'synonyms' in name else 'data/app.log')
        outputs[f'{tool}/{name}'] = compare(RESULTS / tool / f'{name}.txt', source)

raw_pytest = (RESULTS / 'pytest/raw.txt').read_text()
assert len(raw_pytest) <= 7000, f'Normalized pytest output exceeds target: {len(raw_pytest)}'
assert 'rootdir: /work/context-compression-demo\n' in raw_pytest
path_leaks = []  # The final scan runs after replacing the previous ledger artifacts.

protected = outputs['headroom/pytest']
assert protected['unchanged'], 'Headroom must preserve the normalized pytest bytes'
assert 'router:protected:error_output' in protected['tool_metadata']['transforms_applied']

terminal = (RESULTS / 'caveman/pytest_terminal.txt').read_text()
auto = outputs['caveman/pytest_auto']
terminal_meta = outputs['caveman/pytest_terminal']['tool_metadata']
failure_records = [line for line in raw_pytest.splitlines()
                   if ' FAILED ' in line or line.startswith(('E ', '> ', 'FAILED '))
                   or re.search(r'^tests/.+:\d+: AssertionError', line)]
warning_records = [line for line in raw_pytest.splitlines() if re.search(r'warning', line, re.I)]
summary_records = [line for line in raw_pytest.splitlines()
                   if re.search(r'\b1 failed, \d+ passed\b', line)]
terminal_checks = {
    'one_fold_marker': len(outputs['caveman/pytest_terminal']['elided_line_counts']) == 1,
    'passed_lines_before': terminal_meta['passed_test_lines_before'],
    'passed_lines_kept': terminal_meta['passed_test_lines_kept'],
    'fold_markers': len(outputs['caveman/pytest_terminal']['elided_line_counts']),
    'failure_records_kept': all(line in terminal for line in failure_records),
    'warning_records_present': len(warning_records),
    'warning_records_kept': all(line in terminal for line in warning_records),
    'summary_kept': bool(summary_records) and all(line in terminal for line in summary_records),
}
failed_file, failed_name = pytest['failed'][0].split('::')
failed_function = next(node for node in ast.walk(ast.parse((ROOT / failed_file).read_text()))
                       if isinstance(node, ast.FunctionDef) and node.name == failed_name)
assertion_line = next(node.lineno for node in ast.walk(failed_function) if isinstance(node, ast.Assert))
rtk_pytest = (RESULTS / 'rtk/pytest.txt').read_text()
rtk_issues = (RESULTS / 'rtk/issues.txt').read_text()
coupons = ast.parse((ROOT / 'shop/coupons.py').read_text())
shipping_branch = next(node for node in ast.walk(coupons) if isinstance(node, ast.If)
                       and isinstance(node.test, ast.Compare)
                       and any(isinstance(value, ast.Constant) and value.value == 'shipping'
                               for value in node.test.comparators))
bug_line = next(node.lineno for node in shipping_branch.body if isinstance(node, ast.Return))
bug_source = (ROOT / 'shop/coupons.py').read_text().splitlines()[bug_line - 1]
cg_metadata = read_json(RESULTS / 'codegraph/metrics.json')
cg_outputs = {name: (RESULTS / f'codegraph/{name}.txt').read_text()
              for name in ('cart_total', 'apply_coupon', 'explore')}
e5_checks = {
    'rtk_pytest_failure_assertion_line_and_recall': all((
        failed_name in rtk_pytest, f'{failed_file}:{assertion_line}:' in rtk_pytest,
        'assert cart_total(items, "FREESHIP") == 0.0' in rtk_pytest,
        'AssertionError: assert -2.0 == 0.0' in rtk_pytest,
        bool(re.search(r'rtk recall [0-9a-f]+', rtk_pytest)),
    )),
    'rtk_json_first_item_plus_59_without_42': all((
        issues[0]['title'] in rtk_issues, '... +59 more' in rtk_issues,
        outputs['rtk/issues']['issue_titles_kept'] == 1,
        not outputs['rtk/issues']['issue_42_title_survived'],
    )),
    'headroom_lossless_60_issue_table_mixed_route': (
        lossless_issue_table((RESULTS / 'headroom/issues.txt').read_text(), issues)
        and 'router:tool_result:mixed' in outputs['headroom/issues']['tool_metadata']['transforms_applied']
    ),
    'caveman_json_keeps_42_both_queries': all(
        outputs[f'caveman/{case}']['issue_42_title_survived']
        for case in ('issues_no_query', 'issues_query')
    ),
    'caveman_json_writes_invariant_markers_both_queries': all(
        any('__caveman_elided__' in item and bool(item.get('__caveman_invariants__'))
            for item in read_json(RESULTS / f'caveman/{case}.txt'))
        for case in ('issues_no_query', 'issues_query')
    ),
    'caveman_log_no_query_folds_3_with_freeship_invariant': (
        outputs['caveman/app_no_query']['freeship_lines_kept'] == 0
        and 'FREESHIP×3' in (RESULTS / 'caveman/app_no_query.txt').read_text()
    ),
    'caveman_log_query_keeps_3_verbatim': outputs['caveman/app_query']['freeship_lines_kept'] == 3,
    'caveman_synonyms_keeps_3_freeship_but_1_pricing': (
        outputs['caveman/app_synonyms_query']['freeship_lines_kept'] == 3
        and outputs['caveman/app_synonyms_query']['pricing_lines_kept'] == 1
    ),
    'codemode_exact_relevant_title': read_json(RESULTS / 'codemode/issues.txt') == [
        '#42 Cart total goes negative with FREESHIP coupon'
    ],
    'codegraph_symbols_explore_and_correct_bug_line': (
        all(cg_metadata['commands'][name]['exit_code'] == 0 for name in cg_outputs)
        and all(f'**{name}**' in cg_outputs[name] for name in ('cart_total', 'apply_coupon'))
        and all(f'**Location:** {symbols[name]["file"]}:{symbols[name]["line"]}' in cg_outputs[name]
                for name in ('cart_total', 'apply_coupon'))
        and f'{bug_line}\t{bug_source}' in cg_outputs['apply_coupon']
        and f'{bug_line}\t{bug_source}' in cg_outputs['explore']
        and cg_metadata['commands']['explore'].get('symbols_returned', 0) > 0
    ),
}
expectations = {
    'E1': {'holds': True, 'normalized_root': '/work/context-compression-demo',
           'path_leaks': path_leaks, 'evidence': ['pytest/raw.txt']},
    'E2': {'holds': True, 'characters': len(raw_pytest), 'byte_identical': protected['unchanged'],
           'evidence': ['headroom/pytest.metadata.json', 'headroom/pytest.txt']},
    'E3': {'holds': auto['tool_metadata']['content_type'] == 'code' and auto['unchanged']
           and terminal_checks['one_fold_marker'] and terminal_checks['failure_records_kept']
           and terminal_checks['warning_records_kept'] and terminal_checks['summary_kept'],
           'auto_detected_type': auto['tool_metadata']['content_type'], 'auto_unchanged': auto['unchanged'],
           'terminal': terminal_checks,
           'evidence': ['caveman/pytest_auto.metadata.json', 'caveman/pytest_terminal.txt']},
    'E4': {'holds': all(outputs[f'headroom/{case}']['tool_metadata']['strategy'] == 'skip:unique_entities_no_signal(60->60)'
                       and outputs[f'headroom/{case}']['tool_metadata']['issues_kept'] == 60
                       and read_json(RESULTS / f'headroom/{case}.txt') == issues
                       for case in ('smartcrusher_no_query', 'smartcrusher_query')),
           'observed': {case: {**{key: outputs[f'headroom/{case}']['tool_metadata'][key]
                                  for key in ('strategy', 'issues_kept', 'issue_42_kept')},
                              'records_equal_to_input': read_json(RESULTS / f'headroom/{case}.txt') == issues}
                        for case in ('smartcrusher_no_query', 'smartcrusher_query')},
           'evidence': ['headroom/smartcrusher_no_query.metadata.json', 'headroom/smartcrusher_query.metadata.json']},
    'E5': {'holds': all(e5_checks.values()), 'checks': e5_checks,
           'failure_assertion_location': f'{failed_file}:{assertion_line}',
           'bug_location': f'shop/coupons.py:{bug_line}',
           'evidence': ['rtk/pytest.txt', 'rtk/issues.txt', 'headroom/issues.txt',
                        'caveman/issues_no_query.txt', 'caveman/issues_query.txt',
                        'caveman/app_no_query.txt', 'caveman/app_query.txt',
                        'caveman/app_synonyms_query.txt', 'codemode/issues.txt', 'codegraph/apply_coupon.txt']},
}
test_stats = {str(path.relative_to(ROOT)): stats(path) for path in sorted((ROOT / 'tests').glob('test_*.py'))}
metrics = {
    'query': 'Why does the FREESHIP coupon make the cart total negative? Fix it.',
    'project': {'modules': len(production), 'lines': source_lines, 'files': source_stats, 'symbols': symbols,
                'test_files': test_stats, 'test_lines': sum(item['lines'] for item in test_stats.values())},
    'inputs': {str(p.relative_to(ROOT)): stats(p) for p in [ROOT / 'data/issues.json', ROOT / 'data/app.log', ROOT / 'data/app_synonyms.log', RESULTS / 'pytest/raw.txt']},
    'pytest': pytest, 'outputs': outputs, 'rtk_reported_tokens': read_json(RESULTS / 'rtk/tokens.json'),
    'codegraph_metadata': {p.name: read_json(p) for p in sorted((RESULTS / 'codegraph').glob('*.json'))},
    'freeship_lines': freeship, 'pricing_lines': pricing,
    'expectations': expectations,
}
(RESULTS / 'metrics.json').write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + '\n')

lines = ['# Reproduced comparison results', '',
         'Generated by `python3 scripts/summarize.py` after `bash scripts/run_all.sh`. Sizes are UTF-8 bytes; characters are Unicode code points; lines count `splitlines()`. All values below come from committed raw outputs or tool metadata.', '',
         f"The five shop feature modules contain **{source_lines} lines** (including blank lines and comments; `__init__.py` excluded). Pytest collected **{pytest['collected']} tests**: **{pytest['passed']} passed, exactly one failed**, `{pytest['failed'][0]}`. See `scripts/run_pytest.sh`, `results/pytest/raw.txt` and `results/pytest/metadata.json`.", '',
         '## Input sizes', '', '| Input | Lines | Bytes | Characters | Producer |', '| --- | ---: | ---: | ---: | --- |']
for name, count in metrics['inputs'].items():
    producer = 'scripts/run_pytest.sh' if name.startswith('results') else 'data/generate.py'
    lines.append(f"| `{name}` | {count['lines']} | {count['bytes']:,} | {count['chars']:,} | `{producer}` |")
lines += ['', '## Output sizes and evidence survival', '',
          'Issue counts use exact full titles (Caveman JSON also records object/elision counts in `metrics.json`). Log survival means the entire original record survived verbatim; an invariant such as `FREESHIP×3` does not count. Dashes mean that input did not contain that kind of record.', '',
          '| Output | Lines | Bytes | Characters | Issue titles / 60 | #42 | FREESHIP / 3 | Pricing / 3 | Elided lines | Producer |',
          '| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |']
for name, item in outputs.items():
    tool, case = name.split('/')
    is_issue = 'issues' in case or 'smartcrusher' in case
    is_log = case.startswith('app')
    issue_count = item['issue_titles_kept'] if is_issue else '—'
    issue42 = str(item['issue_42_title_survived']) if is_issue else '—'
    fcount = item['freeship_lines_kept'] if is_log else '—'
    pcount = item['pricing_lines_kept'] if 'synonyms' in case else '—'
    lines.append(f"| [{name}]({tool}/{case}.txt) | {item['lines']} | {item['bytes']:,} | {item['chars']:,} | {issue_count} | {issue42} | {fcount} | {pcount} | {item['elided_lines']} | `scripts/run_{tool}.sh` |")

lines += ['', '## Tool-reported counts and decisions', '',
          'These counts are deliberately not normalized across tools. RTK reports its own estimates; Headroom compress counts cover the three-message request; Caveman counts the supplied content; direct SmartCrusher does not report tokens. See the raw metadata for exact boundaries. No token count is invented for tools that do not report one.', '']
lines += ['RTK adds `--tb=short -q -rxX` internally. Its pytest input estimate refers to `results/rtk/pytest.recalled.txt`, not the separate verbose baseline. See `scripts/run_rtk.sh`; `results/rtk/tokens.json` contains the captured values.', '']
for row in metrics['rtk_reported_tokens']:
    lines.append(f"- RTK `{row['rtk_cmd']}`: {row['input_tokens']:,} → {row['output_tokens']:,} estimated tokens; `scripts/run_rtk.sh`, `results/rtk/tokens.json` (captured from the temporary tracking database).")
lines += ['', '| Case | Tokens before → after | Decision / type | Evidence |', '| --- | --- | --- | --- |']
for name, item in outputs.items():
    if 'tool_metadata' in item:
        meta = item['tool_metadata']
        before, after = meta.get('tokens_before'), meta.get('tokens_after')
        tokens = f'{before:,} → {after:,}' if before is not None else 'not reported'
        decision = meta.get('strategy') or meta.get('content_type') or ', '.join(meta.get('transforms_applied', []))
        if meta.get('unchanged') or meta.get('passthrough'):
            decision += '; unchanged'
        lines.append(f'| {name} | {tokens} | `{decision}` | [{name}.metadata.json]({name}.metadata.json) |')
lines += ['']
for name, item in outputs.items():
    if 'issue_records_kept' in item:
        lines.append(f"- {name}: kept {item['issue_records_kept']} issues, elided {item['issue_records_elided']} issues in {item['elision_groups']} groups.")
    meta = item.get('tool_metadata', {})
    if name.startswith('headroom/smartcrusher'):
        lines.append(f"- {name}: kept {meta['issues_kept']} issues and elided {meta['issues_elided']}; #42 kept: {meta['issue_42_kept']}.")
    if name == 'caveman/pytest_terminal':
        lines.append(f"- {name}: {meta['passed_test_lines_before']} PASSED lines before, {meta['passed_test_lines_kept']} kept; {meta['lines_elided_in_markers']} total source lines elided in {len(item['elided_line_counts'])} markers (not all elided lines are PASSED records).")

lines += ['', '## CodeGraph and Read-equivalent files', '',
          'Producer: `scripts/run_codegraph.sh` / `scripts/measure_read.py`. Read-equivalent rendering prefixes each line with a six-column right-aligned line number plus one TAB. It includes source newlines and excludes tool wrapper messages. The raw bytes and the numbered bytes are both captured below.', '']
cg = metrics['codegraph_metadata']['metrics.json']
lines += ['| CodeGraph command | Bytes | Lines | Symbols | Files |', '| --- | ---: | ---: | ---: | ---: |']
for name in ['cart_total', 'apply_coupon', 'explore']:
    item = cg['commands'][name]
    lines.append(f"| [{name}](codegraph/{name}.txt) | {item['stdout_bytes']:,} | {item['stdout_lines']} | {item.get('symbols_returned', '—')} | {item.get('files_returned', '—')} |")
reads = metrics['codegraph_metadata']['read_metrics.json']
lines += ['', '| Read file | Lines | Raw bytes | Numbered bytes |', '| --- | ---: | ---: | ---: |']
for item in reads['files']:
    lines.append(f"| `{item['file']}` | {item['lines']} | {item['raw_bytes']:,} | {item['line_numbered_bytes']:,} |")
lines.append(f"| Total | {reads['total_lines']} | {reads['total_raw_bytes']:,} | {reads['total_line_numbered_bytes']:,} |")
node_bytes = sum(cg['commands'][name]['stdout_bytes'] for name in ['cart_total', 'apply_coupon'])
lines += ['', f"The two symbol calls total **{node_bytes:,} bytes**, or **{node_bytes / reads['total_line_numbered_bytes']:.2%}** of the Read-equivalent baseline. Index: {len(cg['indexed_files'])} files, {cg['indexed_nodes']} nodes, {cg['indexed_edges']} edges. Source locations: cart_total at `shop/cart.py:{symbols['cart_total']['line']}`; apply_coupon at `shop/coupons.py:{symbols['apply_coupon']['line']}`. Full provenance: [codegraph/metrics.json](codegraph/metrics.json), [codegraph/read_metrics.json](codegraph/read_metrics.json).", '']
lines += ['## Article expectation checks', '',
          'E1 and E2 are required assertions. E3–E5 record the actual behavior, so a changed detector or sampling decision cannot be hidden by changing the expected value. `metrics.json` contains each check and its evidence paths.', '',
          '| Expectation | Holds | Observation |', '| --- | --- | --- |',
          f"| E1 | yes | Normalized pytest root; no repository/home paths in captured results. |",
          f"| E2 | yes | {len(raw_pytest):,} characters; `router:protected:error_output`; output is byte-identical. |",
          f"| E3 | {str(expectations['E3']['holds']).lower()} | Auto type `{auto['tool_metadata']['content_type']}`, unchanged: {str(auto['unchanged']).lower()}; terminal retains {terminal_meta['passed_test_lines_kept']}/{terminal_meta['passed_test_lines_before']} PASSED lines, {terminal_checks['fold_markers']} fold markers. |",
          f"| E4 | {str(expectations['E4']['holds']).lower()} | No query: `{expectations['E4']['observed']['smartcrusher_no_query']['strategy']}`; query: `{expectations['E4']['observed']['smartcrusher_query']['strategy']}`. |",
          f"| E5 | {str(expectations['E5']['holds']).lower()} | {sum(e5_checks.values())}/{len(e5_checks)} checks below hold. |", '',
          f"Terminal preservation: failure records {terminal_checks['failure_records_kept']}; summary {terminal_checks['summary_kept']}. The source contains {len(warning_records)} warning lines; a zero count means this fixture does not exercise warning preservation.", '',
          '| E5 check | Holds |', '| --- | --- |']
for name, holds in e5_checks.items():
    lines.append(f'| `{name}` | {str(holds).lower()} |')
lines += ['', f"The Headroom table check decodes every typed CSV cell and compares all fields of all 60 issues with the source, including labels and nested users. The failure assertion is at `{failed_file}:{assertion_line}`; the shipping-coupon subtraction is at `shop/coupons.py:{bug_line}` and is checked against CodeGraph's numbered source.", '',
          '## Reproducibility boundary', '',
          'The seeded data generator is deterministic. Captured pytest absolute paths are normalized before compression. `scripts/compare_results.py` compares complete results trees and reports every changed JSON field or text hunk; it permits only explicitly recognized timing, RTK recall-hash, and CCR-handle differences. Platform/tool-version changes are not silently ignored. Raw pytest and RTK each execute the same suite separately. The regression is intentionally not fixed. No model API or real GitHub issue/log service is called.', '']
(RESULTS / 'summary.md').write_text('\n'.join(lines))
private_tokens = [b'/Users/', b'/home/', str(ROOT).encode()]
local_username = getpass.getuser()
if local_username:
    private_tokens.append(local_username.encode())
path_leaks = [str(path.relative_to(RESULTS)) for path in RESULTS.rglob('*')
              if path.is_file() and any(token in path.read_bytes() for token in private_tokens)]
assert not path_leaks, f'Machine-specific paths or local username remain in results: {path_leaks}'
print('Validated required invariants and wrote results/metrics.json and results/summary.md; '
      + ', '.join(f'{name}={item["holds"]}' for name, item in expectations.items()))
