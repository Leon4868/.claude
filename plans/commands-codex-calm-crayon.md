# leon agents 权限收紧

## Context

审查 `~/.claude/agents/leon/` 下 6 个 subagent（frontend / backend / database / contract / qa / doc-syncer）。评估结论：设计合理——都是干净的薄委托层（冷启动 → 加载同名 skill → 执行单个 task → 结构化回报），三段式（输入/执行/输出）一致，不重复 skill 正文；上一轮已修好过时节点引用和硬编码模块名。分工自洽：仅可并行/隔离的工种才建 agent，安全扫描按设计留在 N3 inline。

唯一实质问题：6 个 agent 都用 `tools: "*"`（全开），比规范做法宽（对照插件 codex-rescue 用 `tools: Bash`）。全开意味着这些开发 subagent 也持有 `Agent` 工具，可递归再派生 subagent——不必要的口子。

用户已决定：**去掉递归位**（Agent/Task/Artifact），**model 全部保持 sonnet**。

## 实现方式（denylist，比白名单更稳）

Claude Code subagent frontmatter 支持 `disallowedTools` denylist（官方文档确认），并支持 `mcp__<server>__*` 服务级模式。移除 `Agent` 即禁止递归派生（文档："If Agent is omitted from the tools list entirely, the agent can't spawn any subagents"）。

用 denylist 而非我原先提的显式白名单：白名单一旦漏列前端用到的 figma/stitch MCP 工具就会静默破坏设计流；denylist 只减掉递归位，其余开发工具 + 各 MCP 全部照常继承，零误伤，且精确匹配「只去递归」的意图。

## 改动

6 个文件 `agents/leon/*.md`，frontmatter 中：

```yaml
# 删除
tools: "*"
# 替换为
disallowedTools: Agent, Artifact
```

- `Agent`：禁止递归派生 subagent（主要目标）
- `Artifact`：开发 subagent 无需发布网页产物
- 其余全部保持不变：`model: sonnet` 不动、`skills: [...]` 不动、正文不动
- 保留继承的 Read/Write/Edit/Bash/Grep/Glob/TodoWrite/WebFetch/WebSearch 及 figma/stitch 等所有 MCP —— 满足各 skill 开发需要

代表文件：`agents/leon/leon-frontend-engineer.md`（继承 figma/stitch）、`agents/leon/leon-contract-engineer.md`、其余 4 个同样处理。

## 不改

- model 分层：6 个全留 sonnet（用户确认）
- 三段式正文、description、skills 字段：已在合理状态
- agents 目录结构：清理后只剩 leon/，无冗余

## 验证

1. `grep -rn 'tools:' agents/leon/` 确认无 `tools: "*"` 残留、6 个文件均含 `disallowedTools: Agent, Artifact`
2. 6 个文件 frontmatter 用 YAML 解析器校验合法、`model: sonnet` 与 `skills:` 完好
3. 说明：denylist 生效需 Claude Code 版本支持 `disallowedTools`（文档标注为现行字段）；旧版本会忽略该字段（回退为继承全部工具，即当前行为），不会报错
