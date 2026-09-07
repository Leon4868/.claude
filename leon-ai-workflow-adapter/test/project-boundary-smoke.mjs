import assert from 'node:assert/strict';
import { access, readdir, readFile, realpath } from 'node:fs/promises';
import { dirname, extname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const testDir = dirname(fileURLToPath(import.meta.url));
const adapterDir = resolve(testDir, '..');
const claudeProjectDir = resolve(adapterDir, '..');
const textExtensions = new Set(['.js', '.mjs', '.md', '.json']);
const forbiddenBrand = new RegExp(`(^|[^a-z])${['y', 'd'].join('')}(?=[-_:]|$)`, 'im');
const files = [];

async function collect(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name);
    if (entry.isSymbolicLink()) assert.fail(`项目内禁止符号链接: ${path}`);
    if (entry.isDirectory()) await collect(path);
    else if (textExtensions.has(extname(entry.name))) files.push(path);
  }
}

await collect(adapterDir);

for (const relativePath of [
  'assets/agents/leon-code-reviewer.md',
  'dist/claude-native/leon-ai-wf-adapted.js',
  'scripts/install-claude-native.mjs',
  'src/claude-native/leon-ai-workflow.js',
]) {
  await assert.rejects(access(resolve(adapterDir, relativePath)), `${relativePath} 不应重复保留`);
}

for (const relativePath of [
  'workflows/leon-ai-workflow.js',
  'workflows/leon-ai-wf-adapted.js',
  'agents/leon/leon-code-reviewer.md',
]) {
  const target = await realpath(resolve(claudeProjectDir, relativePath));
  assert.ok(target.startsWith(`${claudeProjectDir}/`), `${relativePath} 越出 .claude 项目`);
}

for (const path of files) {
  const source = await readFile(path, 'utf8');
  assert.doesNotMatch(source, /\/Users\/[^/]+\/Documents\//, `${path} 引用了项目外 Documents 文件`);
  assert.doesNotMatch(source, forbiddenBrand, `${path} 仍包含旧品牌标识`);

  for (const match of source.matchAll(/\bfrom\s+['"](\.[^'"]+)['"]/g)) {
    const target = await realpath(resolve(dirname(path), match[1]));
    assert.ok(
      target === adapterDir || target.startsWith(`${adapterDir}/`),
      `${path} 的本地 import 越出项目: ${match[1]}`,
    );
  }
}

console.log('project boundary smoke test passed');
