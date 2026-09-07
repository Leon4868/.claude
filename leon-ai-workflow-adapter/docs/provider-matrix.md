# Provider Adapter 矩阵

工作流业务层只依赖统一的 `AgentRuntime`。各厂商 Adapter 负责把一次
`agent(prompt, options)` 转换成对应 Agent Harness 的执行调用；模型 API 本身不等于
Agent Runtime，宿主仍需提供文件、Shell、结构化输出和工具循环。

| Provider | 首选协议/入口 | 当前适配状态 |
| --- | --- | --- |
| Claude | Dynamic Workflow 注入的 `agent/parallel/pipeline/phase/log` | 已实现并通过模拟测试 |
| GPT | OpenAI Responses，`client.responses.create(...)`；本机桥接可用 Codex CLI | Codex CLI executor 已实现，真实付费 Agent 调用待验证 |
| DeepSeek | OpenAI 兼容 Chat Completions，`client.chat.completions.create(...)` | 已注册；等待接入宿主 Agent executor |
| Kimi | Kimi/OpenAI 兼容协议 | 已注册；等待接入宿主 Agent executor |
| GLM | OpenAI 或 Anthropic 兼容协议 | 已注册；等待接入宿主 Agent executor |
| Qwen | OpenAI Responses；Chat Completions 可作为兼容路径 | 已注册；等待接入宿主 Agent executor |
| 豆包 | 火山方舟 Responses，`client.responses.create(...)` | 已注册；等待接入宿主 Agent executor |

## 回退规则

1. 主 Adapter 先执行 `probe()`，确认运行时函数与 executor 可用。
2. 只有 `probe()` 或创建 Runtime 阶段报告“不可用/缺能力”，且尚未发出任何 Agent
   调用时，才允许通过宿主提供的 `invokeWorkflow` 回退原始 `leon-ai-workflow`。
3. 一旦 `agent()` 已开始调用，后续失败原样抛出，不自动重跑旧工作流，避免重复写文件、
   重复提交或重复产生其他副作用。

## 官方协议依据

- OpenAI Responses：https://platform.openai.com/docs/quickstart/make-your-first-api-request
- DeepSeek Chat Completions：https://api-docs.deepseek.com/api/create-chat-completion/
- Kimi Code Provider：https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/configuration/providers.md
- GLM OpenAI/Anthropic 兼容入口：https://open.bigmodel.cn/glm-coding
- Qwen Responses：https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-responses
- 火山方舟 Responses：https://www.volcengine.com/docs/82379/1795150
