# leon-ai-workflow-adapter

`leon-ai-workflow` 的跨运行时改造工程。原始入口保持可用，改造版使用独立名称 `leon-ai-wf-adapted`，可并存并逐步接入其他模型运行时。

## 当前结构

- `src/leon-ai-workflow.core.js`：显式接收 `args/agent/parallel/pipeline/phase/log` 的工作流核心。
- `src/runtime/`：运行时契约、Provider 注册表和安全回退控制。
- `src/providers/`：Claude 原生、宿主注入式 Provider Adapter，以及原工作流回退适配器。
- `src/providers/codex-cli-adapter.js`：GPT 的首个真实 Agent executor，使用 `codex exec`、工作区沙箱和 JSON Schema 输出。
- `src/run-portable-workflow.js`：按 Provider 选择运行时并执行安全回退的统一入口。
- `docs/provider-matrix.md`：GPT、DeepSeek、Kimi、GLM、Qwen、豆包的协议与接入状态。
- `scripts/build-claude-native.mjs`：生成 Claude 所需的无模块加载单文件。
- `../workflows/leon-ai-workflow.js`：保留的原始 Claude 工作流。
- `../workflows/leon-ai-wf-adapted.js`：由构建脚本直接生成的改造版 Claude 工作流。
- `../agents/leon/leon-code-reviewer.md`：两个 Claude 工作流共用的只读评审 Agent。
- `test/claude-native-smoke.mjs`：用假 Agent 验证入口注入、Init 并发、完整阶段链和完整 Init 快速跳过。

## 使用

```bash
npm test
npm run check:gpt
```

构建完成后，在 Claude Code 中按脚本路径运行：

```text
Workflow({
  scriptPath: "workflows/leon-ai-wf-adapted.js"
}, {
  projectDir: "/abs/project",
  feature: "2.auth"
})
```

Claude Workflow 禁止 `import()`，因此 `workflows/leon-ai-wf-adapted.js` 必须由构建脚本直接生成，不要手工修改。整个 `.claude` 仓库是项目边界，适配工程不会读取该项目之外的本地文件。

## 适配边界

模型接口只负责生成，不天然具备 Claude Dynamic Workflow 注入的 `agent()`。可移植入口要求宿主为各 Provider 注入 `executeAgent(prompt, options, context)`，由宿主负责工具循环、文件操作、Shell 权限和结构化输出。

回退只允许发生在第一次 Agent 调用之前。宿主可用 `createOriginalWorkflowFallback()` 注入调用函数，真正转回原始 `leon-ai-workflow`；只要主 Provider 已经开始执行 Agent，就不会自动回退，以免同一任务产生两次写入等副作用。

```js
import { runPortableLeonWorkflow } from './src/run-portable-workflow.js';
import { createLeonProviderRegistry } from './src/providers/provider-adapters.js';
import { createCodexCliAdapter } from './src/providers/codex-cli-adapter.js';
import { createOriginalWorkflowFallback } from './src/providers/original-workflow-fallback.js';

const registry = createLeonProviderRegistry({
  executors: { deepseek: runDeepSeekAgent },
});
registry.register(createCodexCliAdapter());
registry.register(createOriginalWorkflowFallback({
  invokeWorkflow: runClaudeWorkflow,
}));

await runPortableLeonWorkflow({
  registry,
  provider: 'gpt',
  fallbackProvider: 'original',
  args: { projectDir: '/abs/project', feature: '2.auth' },
});
```

这里的 `runGptAgent`、`runDeepSeekAgent` 与 `runClaudeWorkflow` 由具体宿主提供；适配层不读取或保存 API Key。
