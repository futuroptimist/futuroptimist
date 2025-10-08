import { readFileSync, readdirSync, statSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createLinter } from 'actionlint';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..', '..');

function listMarkdownFiles(dir) {
  const entries = readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...listMarkdownFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }
  return files;
}

function checkTrailingWhitespace() {
  const targetsDir = path.join(repoRoot, 'docs', 'prompts', 'codex');
  if (!statSync(targetsDir, { throwIfNoEntry: false })) {
    return true;
  }
  let ok = true;
  const files = listMarkdownFiles(targetsDir);
  for (const file of files) {
    const lines = readFileSync(file, 'utf8').split(/\r?\n/);
    lines.forEach((line, idx) => {
      if (line && line !== line.trimEnd()) {
        console.error(`Trailing whitespace in ${path.relative(repoRoot, file)}:${idx + 1}`);
        ok = false;
      }
    });
  }
  return ok;
}

function checkPackageJsonFormat() {
  const pkgPath = path.join(repoRoot, 'package.json');
  let data;
  try {
    const raw = readFileSync(pkgPath, 'utf8');
    data = JSON.parse(raw);
    const normalized = `${JSON.stringify(data, null, 2)}\n`;
    if (normalized !== raw) {
      console.error('package.json is not formatted with 2-space indentation.');
      return false;
    }
  } catch (error) {
    console.error(`Failed to read package.json: ${error.message}`);
    return false;
  }
  if (!data || typeof data !== 'object') {
    console.error('package.json did not parse into an object.');
    return false;
  }
  return true;
}

function checkPromptDocsSummary() {
  const summaryPath = path.join(repoRoot, 'docs', 'prompt-docs-summary.md');
  let raw;
  try {
    raw = readFileSync(summaryPath, 'utf8');
  } catch (error) {
    console.error(`Failed to read docs/prompt-docs-summary.md: ${error.message}`);
    return false;
  }
  const lines = raw.split(/\r?\n/);
  const startIndex = lines.findIndex((line) => line.startsWith('|------'));
  const dataLines = startIndex >= 0 ? lines.slice(startIndex + 1) : [];
  const pattern = /^\| \[[^\]]+\]\([^)]+\) \|[^|]+\|$/;
  let ok = true;
  let rowCount = 0;
  for (const line of dataLines) {
    if (!line.startsWith('|')) {
      continue;
    }
    const trimmed = line.trimEnd();
    if (!trimmed) {
      continue;
    }
    rowCount += 1;
    if (!pattern.test(trimmed)) {
      console.error(
        `docs/prompt-docs-summary.md row ${rowCount} is not a two-column Markdown table: ${trimmed}`,
      );
      ok = false;
    }
  }
  if (rowCount === 0) {
    console.error('docs/prompt-docs-summary.md contains no table rows after the header.');
    ok = false;
  }
  return ok;
}

let cachedActionlint;

async function runActionlint() {
  try {
    if (!cachedActionlint) {
      cachedActionlint = await createLinter();
    }
  } catch (error) {
    console.error(`Failed to initialise actionlint: ${error.message}`);
    console.error('Install dependencies with `npm ci` and try again.');
    return false;
  }

  const workflowsDir = path.join(repoRoot, '.github', 'workflows');
  let entries = [];
  try {
    entries = readdirSync(workflowsDir, { withFileTypes: true });
  } catch (error) {
    console.error(`Unable to read ${workflowsDir}: ${error.message}`);
    return false;
  }

  let ok = true;
  for (const entry of entries) {
    if (!entry.isFile() || !/\.ya?ml$/i.test(entry.name)) {
      continue;
    }
    const fullPath = path.join(workflowsDir, entry.name);
    const relPath = path.relative(repoRoot, fullPath).replace(/\\/g, '/');
    let content;
    try {
      content = readFileSync(fullPath, 'utf8');
    } catch (error) {
      console.error(`Failed to read ${relPath}: ${error.message}`);
      ok = false;
      continue;
    }
    try {
      const results = await cachedActionlint.lintText(content, relPath);
      for (const result of results) {
        ok = false;
        console.error(
          `${result.file}:${result.line}:${result.column} ${result.kind} ${result.message}`,
        );
      }
    } catch (error) {
      console.error(`actionlint threw while analysing ${relPath}: ${error.message}`);
      ok = false;
    }
  }

  if (!ok) {
    console.error('actionlint found workflow issues.');
  }
  return ok;
}

function lintDocs() {
  const summaryOk = checkPromptDocsSummary();
  const whitespaceOk = checkTrailingWhitespace();
  return summaryOk && whitespaceOk;
}

async function runCiChecks() {
  const summaryOk = checkPromptDocsSummary();
  const actionlintOk = await runActionlint();
  return summaryOk && actionlintOk;
}

const commands = {
  lint: checkTrailingWhitespace,
  format: checkPackageJsonFormat,
  test: runCiChecks,
  docs: lintDocs,
  'docs-lint': lintDocs,
};

const command = process.argv[2] ?? 'test';
const runner = commands[command];

if (!runner) {
  console.error(`Unknown command '${command}'. Use one of: ${Object.keys(commands).join(', ')}.`);
  process.exit(1);
}

try {
  const result = runner();
  if (result && typeof result.then === 'function') {
    result
      .then((ok) => process.exit(ok ? 0 : 1))
      .catch((error) => {
        console.error(error);
        process.exit(1);
      });
  } else {
    process.exit(result ? 0 : 1);
  }
} catch (error) {
  console.error(error);
  process.exit(1);
}
