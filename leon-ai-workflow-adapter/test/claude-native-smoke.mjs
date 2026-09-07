import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const testDir = dirname(fileURLToPath(import.meta.url));
const projectDir = resolve(testDir, '..');
const workflowPath = resolve(projectDir, '../workflows/leon-ai-wf-adapted.js');
const source = await readFile(workflowPath, 'utf8');

assert.match(source, /^\/\/[\s\S]*?export const meta\s*=\s*\{/);
assert.match(source, /name:\s*'leon-ai-wf-adapted'/);
assert.doesNotMatch(source, /^\s*import\s/m);
assert.doesNotMatch(source, /\bimport\s*\(/);

const executable = source.replace('export const meta =', 'const meta =');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

const phases = [];
const logs = [];
const agentLabels = [];

const fakeAgent = async (_prompt, options = {}) => {
  agentLabels.push(options.label);

  if (options.label === 'analyze:project') {
    return {
      projectType: 'frontend SPA',
      langFramework: 'JavaScript',
      buildCommands: {
        install: 'npm install',
        dev: 'npm run dev',
        build: 'npm run build',
        test: 'npm test',
        lint: 'npm run lint',
      },
      modules: [],
      existingClaudeDir: false,
      hasClaudeMd: false,
      existingRules: [],
    };
  }

  if (options.label === 'plan:feature') {
    return {
      featureName: 'smoke feature',
      tasks: [
        {
          id: 'T1',
          desc: 'exercise the full workflow path',
          role: 'other',
          deps: [],
          done: false,
        },
      ],
      groups: [['T1']],
    };
  }

  if (options.label === 'task:T1:other') {
    return {
      taskId: 'T1',
      files: ['src/example.js'],
      verification: 'smoke-test',
      blockers: [],
    };
  }

  if (options.label === 'review:T1') {
    return {
      taskId: 'T1',
      verdict: 'pass',
      issues: [],
      p0Issues: [],
      summary: 'passed',
    };
  }

  if (options.label === 'mark:T1') {
    return {
      taskId: 'T1',
      marked: true,
      note: 'marked',
    };
  }

  if (options.label === 'learn:T1') {
    return {
      taskId: 'T1',
      appended: false,
      lessons: [],
    };
  }

  return {
    path: `/tmp/${options.label ?? 'unknown'}`,
    action: 'created',
    note: 'smoke-test',
  };
};

const fakeFunction = new AsyncFunction(
  'args',
  'agent',
  'parallel',
  'pipeline',
  'phase',
  'log',
  executable,
);

const result = await fakeFunction(
  { projectDir: '/tmp/example-project' },
  fakeAgent,
  tasks => Promise.all(tasks.map(task => task())),
  async () => {
    throw new Error('init-only smoke test must not enter pipeline');
  },
  name => phases.push(name),
  message => logs.push(message),
);

assert.equal(result.mode, 'init-only');
assert.equal(result.projectDir, '/tmp/example-project');
assert.deepEqual(phases, ['Init', 'Collect']);
assert.ok(agentLabels.includes('analyze:project'));
assert.ok(agentLabels.includes('write:CLAUDE.md'));
assert.ok(logs.length >= 2);

console.log('claude-native smoke test passed');

const fullPhases = [];
const fullResult = await fakeFunction(
  {
    projectDir: '/tmp/example-project',
    feature: '1.smoke',
  },
  fakeAgent,
  tasks => Promise.all(tasks.map(task => task())),
  (items, ...stages) => Promise.all(
    items.map(async (original, index) => {
      let value = original;
      for (const stage of stages) {
        value = await stage(value, original, index);
      }
      return value;
    }),
  ),
  name => fullPhases.push(name),
  () => {},
);

assert.equal(fullResult.mode, 'init+dev');
assert.equal(fullResult.executedTasks, 1);
assert.equal(fullResult.results[0].taskId, 'T1');
assert.equal(fullResult.reviews[0].verdict, 'pass');
assert.deepEqual(
  fullPhases,
  ['Init', 'Plan', 'Execute', 'Review', 'Collect'],
);

console.log('claude-native full-path smoke test passed');

const completeLabels = [];
const completeAgent = async (_prompt, options = {}) => {
  completeLabels.push(options.label);

  if (options.label !== 'analyze:project') {
    throw new Error(`complete Init must not dispatch ${options.label}`);
  }

  return {
    projectType: 'frontend SPA',
    langFramework: 'JavaScript',
    buildCommands: {
      install: 'npm install',
      dev: 'npm run dev',
      build: 'npm run build',
      test: 'npm test',
      lint: 'npm run lint',
    },
    modules: [],
    existingClaudeDir: true,
    hasClaudeMd: true,
    existingRules: [
      'coding-style.md',
      'testing.md',
      'security.md',
      'git-workflow.md',
    ],
  };
};

const completeResult = await fakeFunction(
  { projectDir: '/tmp/complete-project' },
  completeAgent,
  tasks => Promise.all(tasks.map(task => task())),
  async () => {
    throw new Error('complete init-only test must not enter pipeline');
  },
  () => {},
  () => {},
);

assert.equal(completeResult.init.mode, 'skipped-complete');
assert.deepEqual(completeLabels, ['analyze:project']);

console.log('claude-native complete-init fast path passed');
