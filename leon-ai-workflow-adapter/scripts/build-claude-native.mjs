import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const projectDir = resolve(scriptDir, '..');
const sourcePath = resolve(projectDir, 'src/leon-ai-workflow.core.js');
const outputPath = resolve(projectDir, '../workflows/leon-ai-wf-adapted.js');

const source = await readFile(sourcePath, 'utf8');
const functionMarker = 'export async function runLeonAiWorkflow(runtime) {';

if (!source.includes(functionMarker)) {
  throw new Error(`Missing core entry: ${functionMarker}`);
}

const bundledCore = source.replace(
  functionMarker,
  'async function runLeonAiWorkflow(runtime) {',
);

const nativeEntry = `

// ---- Claude Dynamic Workflow 原生入口（构建生成，请勿手改） ----
return await runLeonAiWorkflow({
  args: typeof args === 'undefined' ? undefined : args,
  agent: (...callArgs) => agent(...callArgs),
  parallel: (...callArgs) => parallel(...callArgs),
  pipeline: (...callArgs) => pipeline(...callArgs),
  phase: (...callArgs) => phase(...callArgs),
  log: (...callArgs) => log(...callArgs),
});
`;

await mkdir(dirname(outputPath), { recursive: true });
await writeFile(
  outputPath,
  `${bundledCore.trimEnd()}${nativeEntry}`,
  'utf8',
);

console.log(outputPath);
