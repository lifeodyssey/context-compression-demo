import { readFileSync } from 'node:fs';

const issues = JSON.parse(readFileSync(new URL('../data/issues.json', import.meta.url), 'utf8'));
const result = issues
  .filter((issue) => /FREESHIP/i.test(issue.title + issue.body))
  .map((issue) => `#${issue.number} ${issue.title}`);
// This is the serialized return value; omit a terminal-only trailing newline.
process.stdout.write(JSON.stringify(result));
