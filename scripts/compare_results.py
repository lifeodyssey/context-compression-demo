#!/usr/bin/env python3
"""Audit two complete results trees without hiding unexplained differences.

JSON differences are reported as individual leaf fields; other files are
reported as changed line ranges. Exit status is 1 if any difference is outside
the small, documented nondeterminism rules below. Neither tree is modified.
"""

import argparse
import difflib
import json
import re
from pathlib import Path


PYTEST_TEXT_FILES = {
    'pytest/raw.txt', 'rtk/pytest.txt', 'rtk/pytest.recalled.txt',
    'headroom/pytest.txt', 'headroom/pytest.messages.json',
    'caveman/pytest_auto.txt', 'caveman/pytest_terminal.txt',
}


def canonical_text(filename, text):
    """Replace only measured volatile fields, never general paths or numbers."""
    rules = []
    if filename in PYTEST_TEXT_FILES:
        rules.append(('pytest elapsed seconds', r'(?<= in )\d+(?:\.\d+)?s\b', '<pytest-time>'))
    if filename == 'rtk/pytest.txt':
        rules.append(('RTK recall hash', r'(?<=rtk recall )[0-9a-f]{12}\b', '<recall-hash>'))
    if filename == 'codegraph/init.txt':
        rules.append(('CodeGraph index elapsed seconds',
                      r'(?<= edges in )\d+(?:\.\d+)?s\b', '<index-time>'))
    if filename == 'headroom/routing.log':
        rules.extend([
            ('SmartCrusher elapsed nanoseconds', r'(?<=elapsed_ns=)\d+\b', '<elapsed-ns>'),
            ('Headroom transform elapsed milliseconds', r'\[\d+(?:\.\d+)?ms\]', '[<elapsed-ms>]'),
            ('Headroom pipeline stage milliseconds',
             r'(?<==)\d+(?:\.\d+)?ms\b', '<stage-ms>'),
            ('Headroom cache average nanoseconds', r'\b\d+(?:\.\d+)?ns(?= avg\])', '<cache-ns>'),
        ])
    reasons = []
    for reason, pattern, replacement in rules:
        text, count = re.subn(pattern, replacement, text)
        if count:
            reasons.append(reason)
    return text, reasons


def allowed_json_difference(filename, field, before, after):
    if (filename == 'rtk/gain.json' and field in
            ('$.summary.total_time_ms', '$.summary.avg_time_ms')
            and type(before) is int and type(after) is int):
        return ['RTK measured command milliseconds']
    is_caveman_metadata = filename.startswith('caveman/') and filename.endswith('.metadata.json')
    is_embedded_caveman = filename == 'metrics.json' and field.startswith('$.outputs.caveman/')
    if (field.endswith('.recovery_handle') and (is_caveman_metadata or is_embedded_caveman)
            and isinstance(before, str) and isinstance(after, str)
            and re.fullmatch(r'ccr_[0-9a-f]{32}', before)
            and re.fullmatch(r'ccr_[0-9a-f]{32}', after)):
        return ['Caveman ephemeral CCR handle']
    if isinstance(before, str) and isinstance(after, str):
        old, old_reasons = canonical_text(filename, before)
        new, new_reasons = canonical_text(filename, after)
        if old == new:
            return sorted(set(old_reasons + new_reasons))
    return []


def json_changes(filename, before, after, field='$'):
    if type(before) is dict and type(after) is dict:
        for key in sorted(before.keys() | after.keys()):
            location = f'{field}.{key}'
            if key not in before or key not in after:
                yield {'field': location, 'before': before.get(key), 'after': after.get(key),
                       'accepted': False, 'reason': ['JSON key added or removed']}
            else:
                yield from json_changes(filename, before[key], after[key], location)
    elif type(before) is list and type(after) is list and len(before) == len(after):
        for index, (old, new) in enumerate(zip(before, after)):
            yield from json_changes(filename, old, new, f'{field}[{index}]')
    elif type(before) is not type(after) or before != after:
        reasons = allowed_json_difference(filename, field, before, after)
        yield {'field': field, 'before': before, 'after': after,
               'accepted': bool(reasons), 'reason': reasons or ['unexplained value change']}


def text_changes(filename, before, after):
    old_lines, new_lines = before.splitlines(keepends=True), after.splitlines(keepends=True)
    for tag, start_old, end_old, start_new, end_new in difflib.SequenceMatcher(
            a=old_lines, b=new_lines, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        old = ''.join(old_lines[start_old:end_old])
        new = ''.join(new_lines[start_new:end_new])
        old_clean, old_reasons = canonical_text(filename, old)
        new_clean, new_reasons = canonical_text(filename, new)
        reasons = sorted(set(old_reasons + new_reasons)) if old_clean == new_clean else []
        yield {'old_lines': [start_old + 1, end_old], 'new_lines': [start_new + 1, end_new],
               'before': old, 'after': new, 'accepted': bool(reasons),
               'reason': reasons or ['unexplained text change']}


def compare_trees(left, right):
    left_files = {str(path.relative_to(left)): path for path in left.rglob('*') if path.is_file()}
    right_files = {str(path.relative_to(right)): path for path in right.rglob('*') if path.is_file()}
    differences = []
    identical = []
    for name in sorted(left_files.keys() | right_files.keys()):
        if name not in left_files or name not in right_files:
            differences.append({'file': name, 'accepted': False, 'reason': ['file added or removed'],
                                'before': name in left_files, 'after': name in right_files})
            continue
        before, after = left_files[name].read_bytes(), right_files[name].read_bytes()
        if before == after:
            identical.append(name)
            continue
        try:
            old_text, new_text = before.decode('utf-8'), after.decode('utf-8')
        except UnicodeDecodeError:
            changes = [{'accepted': False, 'reason': ['binary content differs']}]
        else:
            if name.endswith('.json'):
                try:
                    changes = list(json_changes(name, json.loads(old_text), json.loads(new_text)))
                except json.JSONDecodeError:
                    changes = list(text_changes(name, old_text, new_text))
                if not changes:
                    changes = [{'accepted': False, 'reason': ['JSON formatting differs']}]
            else:
                changes = list(text_changes(name, old_text, new_text))
        differences.extend({'file': name, **change} for change in changes)
    return {
        'compared_files': len(left_files.keys() | right_files.keys()),
        'identical_files': identical,
        'differing_files': sorted({change['file'] for change in differences}),
        'accepted_differences': sum(change['accepted'] for change in differences),
        'unexpected_differences': sum(not change['accepted'] for change in differences),
        'differences': differences,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('left', type=Path)
    parser.add_argument('right', type=Path)
    parser.add_argument('--json-output', type=Path, help='Optional complete audit JSON outside the compared trees')
    args = parser.parse_args()
    for tree in (args.left, args.right):
        if not tree.is_dir():
            parser.error(f'Not a results directory: {tree}')
    if args.json_output:
        output = args.json_output.resolve()
        if any(output.is_relative_to(tree.resolve()) for tree in (args.left, args.right)):
            parser.error('Audit output must be outside both compared results trees')
    report = compare_trees(args.left, args.right)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if args.json_output:
        args.json_output.write_text(rendered)
    print(rendered, end='')
    raise SystemExit(bool(report['unexpected_differences']))


if __name__ == '__main__':
    main()
