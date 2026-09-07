import assert from 'node:assert/strict';

import { createClaudeNativeAdapter } from '../src/providers/claude-native-adapter.js';
import { buildCodexExecArgs } from '../src/providers/codex-cli-adapter.js';
import { createInjectedAgentAdapter } from '../src/providers/injected-agent-adapter.js';
import { createOriginalWorkflowFallback } from '../src/providers/original-workflow-fallback.js';
import { createLeonProviderRegistry } from '../src/providers/provider-adapters.js';
import { RuntimeUnavailableError } from '../src/runtime/errors.js';
import { resolveProviderProfile } from '../src/runtime/provider-catalog.js';
import { createProviderRegistry } from '../src/runtime/provider-registry.js';
import { runWithRuntimeFallback } from '../src/runtime/run-with-fallback.js';

for (const provider of ['claude', 'gpt', 'deepseek', 'kimi', 'glm', 'qwen', 'doubao']) {
  assert.equal(resolveProviderProfile(provider).id, provider);
}
assert.equal(resolveProviderProfile('openai').id, 'gpt');
assert.equal(resolveProviderProfile('moonshot').id, 'kimi');
assert.equal(resolveProviderProfile('ark').id, 'doubao');

const codexArgs = buildCodexExecArgs({
  projectDir: '/tmp/project with spaces',
  prompt: 'do work',
  schemaPath: '/tmp/schema.json',
  outputPath: '/tmp/output.json',
  model: 'gpt-test',
});
assert.deepEqual(codexArgs.slice(0, 2), ['exec', '--ephemeral']);
assert.equal(codexArgs[codexArgs.indexOf('--cd') + 1], '/tmp/project with spaces');
assert.equal(codexArgs[codexArgs.indexOf('--model') + 1], 'gpt-test');
assert.equal(codexArgs.at(-1), 'do work');

const phaseNames = [];
const claude = createClaudeNativeAdapter({
  agent: async (_prompt, options) => ({ label: options.label }),
  phase: (name) => phaseNames.push(name),
  log: () => {},
});
await claude.probe();
const preparedClaude = await claude.createRuntime({ args: { projectDir: '/tmp/demo' } });
preparedClaude.runtime.phase('Init');
assert.deepEqual(await preparedClaude.runtime.agent('hello', { label: 'probe' }), { label: 'probe' });
assert.equal(preparedClaude.state.agentCalls, 1);
assert.deepEqual(phaseNames, ['Init']);

let fallbackCalls = 0;
const unavailable = createInjectedAgentAdapter({
  id: 'gpt',
  executeAgent: async () => ({ provider: 'gpt' }),
  isAvailable: () => false,
});
const fallback = createInjectedAgentAdapter({
  id: 'claude',
  executeAgent: async () => {
    fallbackCalls += 1;
    return { provider: 'claude' };
  },
});

const fallbackResult = await runWithRuntimeFallback({
  workflow: (runtime) => runtime.agent('work', { label: 'work' }),
  primary: unavailable,
  fallback,
});
assert.equal(fallbackResult.fallbackUsed, true);
assert.equal(fallbackResult.provider, 'claude');
assert.equal(fallbackCalls, 1);

let unsafeFallbackCalls = 0;
const failsAfterDispatch = createInjectedAgentAdapter({
  id: 'deepseek',
  executeAgent: async () => {
    throw new RuntimeUnavailableError('request failed after dispatch');
  },
});
const unsafeFallback = createInjectedAgentAdapter({
  id: 'claude',
  executeAgent: async () => {
    unsafeFallbackCalls += 1;
    return {};
  },
});
await assert.rejects(
  runWithRuntimeFallback({
    workflow: (runtime) => runtime.agent('work'),
    primary: failsAfterDispatch,
    fallback: unsafeFallback,
  }),
  /request failed after dispatch/,
);
assert.equal(unsafeFallbackCalls, 0);

let originalInvocation;
const originalFallback = createOriginalWorkflowFallback({
  invokeWorkflow: async (request) => {
    originalInvocation = request;
    return { mode: 'original-workflow' };
  },
});
const originalResult = await runWithRuntimeFallback({
  workflow: (runtime) => runtime.agent('work'),
  args: { projectDir: '/tmp/original' },
  primary: unavailable,
  fallback: originalFallback,
});
assert.equal(originalResult.fallbackUsed, true);
assert.equal(originalResult.provider, 'claude-original');
assert.deepEqual(originalInvocation, {
  name: 'leon-ai-workflow',
  args: { projectDir: '/tmp/original' },
});

const registry = createProviderRegistry([claude, unavailable, fallback]);
assert.equal(registry.resolve('openai'), undefined);
assert.equal(registry.resolve('anthropic').id, 'claude');

const modelRegistry = createLeonProviderRegistry({
  executors: {
    gpt: async () => ({ provider: 'gpt' }),
    claude: async () => ({ provider: 'claude' }),
  },
});
assert.equal(modelRegistry.resolve('openai').id, 'gpt');
assert.equal(modelRegistry.resolve('deep-seek').id, 'deepseek');
assert.equal(modelRegistry.resolve('moonshot').id, 'kimi');
assert.equal(modelRegistry.resolve('bigmodel').id, 'glm');
assert.equal(modelRegistry.resolve('dashscope').id, 'qwen');
assert.equal(modelRegistry.resolve('volcengine').id, 'doubao');
await modelRegistry.resolve('gpt').probe();
await assert.rejects(modelRegistry.resolve('deepseek').probe(), /执行器不可用/);

console.log('runtime adapter smoke test passed');
