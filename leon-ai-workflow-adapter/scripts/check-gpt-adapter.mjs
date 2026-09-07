import { probeCodexCli } from '../src/providers/codex-cli-adapter.js';

const available = await probeCodexCli();
console.log(JSON.stringify({ provider: 'gpt', executor: 'codex-cli', available }));
if (!available) process.exitCode = 1;
