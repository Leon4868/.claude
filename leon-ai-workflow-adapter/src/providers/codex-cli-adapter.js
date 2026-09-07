import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { createInjectedAgentAdapter } from './injected-agent-adapter.js';
import { RuntimeUnavailableError } from '../runtime/errors.js';

function runProcess(binary, argv, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(binary, argv, {
      cwd: options.cwd,
      env: options.env,
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: options.timeoutMs,
    });
    let stdout = '';
    let stderr = '';
    const appendLimited = (current, chunk) => `${current}${chunk}`.slice(-20_000);
    child.stdout.on('data', (chunk) => { stdout = appendLimited(stdout, chunk); });
    child.stderr.on('data', (chunk) => { stderr = appendLimited(stderr, chunk); });
    child.on('error', reject);
    child.on('close', (code, signal) => resolve({ code, signal, stdout, stderr }));
  });
}

export function buildCodexExecArgs({
  projectDir,
  prompt,
  schemaPath,
  outputPath,
  model,
  sandbox = 'workspace-write',
  approveForMe = true,
  extraArgs = [],
}) {
  const argv = [
    'exec',
    '--ephemeral',
    '--color', 'never',
    '--cd', projectDir,
    '--sandbox', sandbox,
    '--skip-git-repo-check',
  ];
  if (approveForMe) argv.push('--approve-for-me');
  if (model) argv.push('--model', model);
  if (schemaPath) argv.push('--output-schema', schemaPath);
  if (outputPath) argv.push('--output-last-message', outputPath);
  argv.push(...extraArgs, prompt);
  return argv;
}

export async function probeCodexCli({
  binary = 'codex',
  spawnProcess = runProcess,
  env = process.env,
} = {}) {
  try {
    const result = await spawnProcess(binary, ['--version'], { env, timeoutMs: 10_000 });
    return result.code === 0;
  } catch (error) {
    if (error && error.code === 'ENOENT') return false;
    throw error;
  }
}

export function createCodexCliAdapter({
  binary = 'codex',
  model,
  sandbox = 'workspace-write',
  approveForMe = true,
  timeoutMs = 30 * 60 * 1000,
  extraArgs = [],
  env = process.env,
  spawnProcess = runProcess,
} = {}) {
  const executeAgent = async (prompt, options = {}, context = {}) => {
    const projectDir = context.args && context.args.projectDir;
    if (!projectDir) throw new TypeError('Codex CLI executor 缺少 args.projectDir');

    const tempDir = await mkdtemp(join(tmpdir(), 'leon-ai-codex-'));
    const schemaPath = options.schema ? join(tempDir, 'schema.json') : undefined;
    const outputPath = join(tempDir, 'last-message.txt');
    try {
      if (schemaPath) await writeFile(schemaPath, JSON.stringify(options.schema), 'utf8');
      const rolePrefix = options.agentType
        ? `以 ${options.agentType} 角色执行。\n\n`
        : '';
      const argv = buildCodexExecArgs({
        projectDir,
        prompt: `${rolePrefix}${prompt}`,
        schemaPath,
        outputPath,
        model,
        sandbox,
        approveForMe,
        extraArgs,
      });
      const result = await spawnProcess(binary, argv, { cwd: projectDir, env, timeoutMs });
      if (result.code !== 0) {
        const detail = (result.stderr.trim() || result.stdout.trim() || `signal=${result.signal || 'none'}`).slice(-4_000);
        throw new Error(`Codex CLI Agent 执行失败(code=${result.code}): ${detail}`);
      }

      const output = (await readFile(outputPath, 'utf8')).trim();
      if (!options.schema) return output;
      try {
        return JSON.parse(output);
      } catch (error) {
        throw new Error(`Codex CLI 未返回合法 JSON: ${error.message}`, { cause: error });
      }
    } finally {
      await rm(tempDir, { recursive: true, force: true });
    }
  };

  const adapter = createInjectedAgentAdapter({
    id: 'gpt',
    aliases: ['openai', 'chatgpt', 'codex'],
    isAvailable: async () => probeCodexCli({ binary, spawnProcess, env }),
    executeAgent,
  });

  return {
    ...adapter,
    async probe(context) {
      try {
        await adapter.probe(context);
      } catch (error) {
        if (error instanceof RuntimeUnavailableError) {
          throw new RuntimeUnavailableError(`找不到可用的 Codex CLI: ${binary}`, { cause: error });
        }
        throw error;
      }
    },
  };
}
