// ============================================================
// leon-ai-wf-adapted —— leon:init + leon:ai(编排内核)合并的端到端 workflow
// ------------------------------------------------------------
// 一条链路打通「项目初始化 → 单 feature 并行开发」:
//   Init    : 分析项目 → 生成/增量补齐 .claude/CLAUDE.md + rules/*.md(不覆盖已有)
//   Plan    : 读该 feature 的 tasks/requirements/design,判依赖 → 串/并行分组
//   Execute : 组间串行、组内并行,按工种派 leon-*-engineer subagent 开发
//   Review  : 每个 task 完成后立刻派 review agent 跑 codex review(CLI);报 P0 则另派修复 agent 当场修,
//             非 P0 问题写 blocker 冒泡
//   Collect : 汇总产出 + 把 blockers 冒泡给外层
//
// 设计取舍(沿用拆分时的共识):
//   - 全部 I/O 由 agent 完成,脚本只编排(workflow 沙箱无文件系统)。
//   - 每 task 跑 codex review;开发完即把 tasks.md 标 [x](断点续跑靠它)。
//   - 自学习闭环:每 task 完成把踩的坑/教训追加进项目根 AGENTS.md;后续 task 与 review 开工前都读它,
//     CLAUDE.md 末尾 @AGENTS.md 引入,人类用 Claude Code 时也自动带上。
//   - 重跑:Init 已完整则整段跳过;Plan 读到 [x] 的 task 自动跳过 → 续上次没做完的。
//   - 显式不做:N6 QA / 人工审批 —— 留给外层 command。
//   - 中途不等用户:需人工确认的 blocker 冒泡到返回值。
//   - 若只想初始化:不传 feature → 只做 Init;传了 feature → Init 后继续开发那个 spec。
//
// 目录模型:projectDir 是项目根,代码就在它下面开发;需求拆在 projectDir/specs/ 下,
//           一个子目录 = 一个 feature(spec);记忆/规范统一读 projectDir/.claude/。
//
// 调用:Workflow({ name: 'leon-ai-wf-adapted', args: {
//          projectDir: '/abs/project',  // 必填:项目根(代码在此开发,记忆读 .claude/)
//          feature: '2.auth'            // 可选:specs/ 下要开发的子目录名;不传则只做 Init
//       }})
// ============================================================

export const meta = {
  name: 'leon-ai-wf-adapted',
  description:
    '端到端:先 leon:init 初始化项目 .claude/,再跑 leon:ai 编排内核开发指定 feature(含 review/标记/P0 修复,不做 QA/人工审批,blocker 冒泡)',
  phases: [
    { title: 'Init', detail: '分析项目 + 并行生成/增量补齐 .claude/CLAUDE.md 与 rules/*.md' },
    { title: 'Plan', detail: '读 feature 的 tasks,判依赖 → 串/并行分组' },
    { title: 'Execute', detail: '逐组串行、组内并行,按工种派 subagent' },
    { title: 'Review', detail: '每个完成的 task 派 codex review;P0 当场派 agent 修,非 P0 冒泡 blocker' },
    { title: 'Collect', detail: '汇总产出 + blocker 冒泡' },
  ],
};

// ---- 可移植核心 ----
// Claude 原生入口会在构建时把运行时注入的全局 DSL 显式传入这里；
// 其他模型运行时后续只需提供同形状的 runtime，无需改动下面的业务流程。
export async function runLeonAiWorkflow(runtime) {
const { args, agent, parallel, pipeline, phase, log } = runtime;

const projectDir = (args && args.projectDir) || '';
if (!projectDir) {
  return { error: '缺少 args.projectDir。示例:Workflow({ name: "leon-ai-wf-adapted", args: { projectDir: "/abs/project", feature: "2.auth" } })' };
}
// specs 固定在 projectDir/specs;feature 是其下的子目录名,只传名即可(不传则只做 Init)。
const specsDir = `${projectDir}/specs`;
const feature = (args && args.feature) || null;
const featureDir = feature ? `${specsDir}/${feature}` : null;

// ════════════════════════════════════════════════════════════
// 第一段:Init(原 leon:init)
// ════════════════════════════════════════════════════════════
phase('Init');
log(`【Init】分析项目 ${projectDir} 并初始化 .claude/ …`);

const ANALYSIS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['projectType', 'langFramework', 'buildCommands', 'modules', 'existingClaudeDir', 'hasClaudeMd', 'existingRules'],
  properties: {
    projectType: { type: 'string', description: '如 monorepo / 单体后端 / 前端 SPA / Web3 等' },
    langFramework: { type: 'string', description: '语言 + 框架 + 包管理器' },
    buildCommands: {
      type: 'object',
      additionalProperties: false,
      required: ['install', 'dev', 'build', 'test', 'lint'],
      properties: {
        install: { type: 'string' }, dev: { type: 'string' }, build: { type: 'string' },
        test: { type: 'string' }, lint: { type: 'string' },
      },
    },
    modules: {
      type: 'array',
      description: '从 {frontend, backend, database, app, smart-contract} 中取适用项',
      items: { type: 'string', enum: ['frontend', 'backend', 'database', 'app', 'smart-contract'] },
    },
    existingClaudeDir: { type: 'boolean' },
    hasClaudeMd: { type: 'boolean', description: '项目根 .claude/CLAUDE.md 是否存在' },
    existingRules: { type: 'array', items: { type: 'string' }, description: '已存在的 rules 文件名,没有则空数组' },
  },
};

const analysis = await agent(
  `你在为项目做 leon:init 初始化的「分析」步骤。项目根:${projectDir}

请用 Read/Grep/Bash(ls 等只读命令)调查项目并返回结构化画像:
1. 读 package.json / go.mod / Cargo.toml / pyproject.toml / pom.xml 判断语言、框架、包管理器。
2. 扫目录结构识别模块类型(从 {frontend, backend, database, app, smart-contract} 挑适用项放进 modules)。
3. 从 README / CI / lint 配置 / scripts 提取常用命令(install/dev/build/test/lint)。
4. 检查是否已存在 .claude/;单独判断 .claude/CLAUDE.md 是否存在(hasClaudeMd),并列出 .claude/rules/ 下已有文件名(existingRules)。
只调查、不写任何文件。`,
  { label: 'analyze:project', phase: 'Init', schema: ANALYSIS_SCHEMA, effort: 'low' },
);

const BASE_RULES = ['coding-style', 'testing', 'security', 'git-workflow'];
const MODULE_RULE = { frontend: 'frontend', backend: 'backend-api', database: 'database', app: 'app', 'smart-contract': 'smart-contract' };
const ruleNames = [...BASE_RULES, ...(analysis.modules || []).map((m) => MODULE_RULE[m]).filter(Boolean)];

// ② Init 快速路径:.claude/ 已存在且所有应有 rule 都齐(含 CLAUDE.md)→ 整段跳过写文件,省 token。
//    判据:existingClaudeDir 与 hasClaudeMd 为真,且 ruleNames 里没有一个缺失。
const existingRules = analysis.existingRules || [];
const hasClaudeMd = analysis.hasClaudeMd === true;
const missingRules = ruleNames.filter((r) => !existingRules.some((e) => e === r || e === `${r}.md`));
const initComplete = analysis.existingClaudeDir && hasClaudeMd && missingRules.length === 0;

const WRITE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['path', 'action'],
  properties: {
    path: { type: 'string' },
    action: { type: 'string', enum: ['created', 'appended', 'skipped'] },
    note: { type: 'string' },
  },
};

const INCREMENTAL = analysis.existingClaudeDir
  ? `项目已存在 .claude/(已有 rules: ${(analysis.existingRules || []).join(', ') || '无'})。
严格遵守增量模式:目标已存在且完整 → action=skipped 不动;已存在但缺章节 → 只追加缺失,action=appended;不存在 → 新建,action=created。绝不覆盖用户已有内容。`
  : `项目没有 .claude/,全新初始化,正常新建,action=created。`;

const projectFacts = `项目根:${projectDir}
项目类型:${analysis.projectType}
技术栈:${analysis.langFramework}
常用命令:${JSON.stringify(analysis.buildCommands)}
模块:${(analysis.modules || []).join(', ') || '(未识别)'}`;

const initWriteTasks = [
  () => agent(
    `你在执行 leon:init 文件生成。写/补 ${projectDir}/.claude/CLAUDE.md。

${projectFacts}

${INCREMENTAL}

CLAUDE.md 要求(≤150 行):1.{项目名}+简介 2.技术栈 3.常用命令 4.目录结构(≤20 行) 5.用 @rules/xxx.md 按需引入下面生成的 rules 6.末尾加一行 @AGENTS.md 引入项目踩坑/教训(自学习闭环,开发中会持续追加;若该文件暂不存在也先写引用)。
用 Read 确认现状后再 Write/Edit。返回 {path, action, note}。`,
    { label: 'write:CLAUDE.md', phase: 'Init', schema: WRITE_SCHEMA },
  ),
  ...ruleNames.map((rule) => () => agent(
    `你在执行 leon:init 文件生成。写/补 ${projectDir}/.claude/rules/${rule}.md。

${projectFacts}

${INCREMENTAL}

格式:frontmatter(description: 一句话;可选 globs:)+ # 标题 + 具体规则。内容从项目实际配置推断(${rule} 对应领域规范)。
用 Read 确认现状后再 Write/Edit。返回 {path, action, note}。`,
    { label: `write:${rule}`, phase: 'Init', schema: WRITE_SCHEMA },
  )),
];

let initReport;
if (initComplete) {
  // 重跑且 .claude/ 已完整:整段跳过写文件,不派 agent(省 token),直接当全部 skipped。
  log(`【Init】检测到 .claude/ 已完整(CLAUDE.md + ${ruleNames.length} 个 rules 齐全),跳过 Init 写文件。`);
  initReport = {
    mode: 'skipped-complete',
    created: [],
    appended: [],
    skipped: [`${projectDir}/.claude/CLAUDE.md`, ...ruleNames.map((r) => `${projectDir}/.claude/rules/${r}.md`)],
    writes: [],
  };
} else {
  const initWrites = (await parallel(initWriteTasks)).filter(Boolean);
  initReport = {
    mode: analysis.existingClaudeDir ? 'incremental' : 'fresh',
    created: initWrites.filter((w) => w.action === 'created').map((w) => w.path),
    appended: initWrites.filter((w) => w.action === 'appended').map((w) => w.path),
    skipped: initWrites.filter((w) => w.action === 'skipped').map((w) => w.path),
    writes: initWrites,
  };
  log(`【Init】完成 — ✅新建 ${initReport.created.length} | ➕追加 ${initReport.appended.length} | ⚠️跳过 ${initReport.skipped.length}`);
}

// 不开发 feature:只做初始化就收口。
if (!featureDir) {
  phase('Collect');
  log('未提供 feature,只执行初始化。如需开发请传 args.feature。');
  return { mode: 'init-only', projectDir, analysis, init: initReport };
}

// ════════════════════════════════════════════════════════════
// 第二段:Plan → Execute → Collect(leon:ai 编排内核)
// ════════════════════════════════════════════════════════════
phase('Plan');
log(`【Plan】读取 ${featureDir} 的 tasks 并规划执行顺序…`);

const PLAN_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['featureName', 'tasks', 'groups'],
  properties: {
    featureName: { type: 'string' },
    tasks: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['id', 'desc', 'role', 'deps'],
        properties: {
          id: { type: 'string' },
          desc: { type: 'string' },
          role: { type: 'string', enum: ['frontend', 'backend', 'database', 'other'] },
          deps: { type: 'array', items: { type: 'string' } },
          done: { type: 'boolean', description: 'tasks.md 已标 [x] 的为 true(跳过)' },
        },
      },
    },
    groups: { type: 'array', description: '组间串行、组内并行;只放未完成的 task id', items: { type: 'array', items: { type: 'string' } } },
  },
};

const plan = await agent(
  `你在为 leon:ai 规划单个 feature 的执行顺序。feature 目录:${featureDir}

请 Read 这个 feature 的 tasks.md、requirements.md、design.md,产出执行计划:
1. 解析每个任务:id、描述、工种(frontend/backend/database;无法归类填 other)、依赖。已标 [x] 的 done=true。
2. 按依赖排成 groups(组间串行、组内并行):有依赖/改同文件/共享 schema → 串行;无依赖/不同项目/隔离 → 并行。groups 只放未完成 task id。
只读不写。`,
  { label: 'plan:feature', phase: 'Plan', schema: PLAN_SCHEMA, effort: 'low' },
);

const taskById = {};
for (const t of plan.tasks || []) taskById[t.id] = t;
const pending = (plan.tasks || []).filter((t) => !t.done);
const completedCount = (plan.tasks || []).filter((t) => t.done).length;
log(`【Plan】Feature「${plan.featureName}」:共 ${(plan.tasks || []).length} 任务,已完成跳过 ${completedCount}(断点续跑),待执行 ${pending.length},分 ${(plan.groups || []).length} 组`);

phase('Execute');
const ROLE_AGENT = { frontend: 'leon-frontend-engineer', backend: 'leon-backend-engineer', database: 'leon-database-engineer' };
const TASK_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['taskId', 'files', 'verification', 'blockers'],
  properties: {
    taskId: { type: 'string' },
    files: { type: 'array', items: { type: 'string' } },
    verification: { type: 'string' },
    blockers: { type: 'array', items: { type: 'string' }, description: '需人工确认的阻塞点;没有则空数组' },
  },
};

const REVIEW_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['taskId', 'verdict', 'issues', 'p0Issues'],
  properties: {
    taskId: { type: 'string' },
    verdict: { type: 'string', enum: ['pass', 'fail'], description: 'codex review 是否通过' },
    issues: { type: 'array', items: { type: 'string' }, description: 'review 指出的问题(含 P0);pass 时为空数组' },
    p0Issues: {
      type: 'array',
      items: { type: 'string' },
      description: 'codex review 里标为 P0/Critical 的「不修就不能交」的问题,原样抠出;没有则空数组。这些会被当场派 agent 修复',
    },
    summary: { type: 'string' },
  },
};

function runTask(t) {
  const agentType = ROLE_AGENT[t.role];
  const prompt = `你负责开发 leon:ai 的单个 task,只做这一个 task,不要擅自扩展范围。

项目根(在此开发): ${projectDir}
featureDir: ${featureDir}
TASK ${t.id}: ${t.desc}
工种: ${t.role}

开工前加载上下文:本 feature 的 requirements.md/design.md/tasks.md、${projectDir}/.claude/CLAUDE.md + .claude/rules/(项目规范与记忆)、${projectDir}/AGENTS.md(项目踩坑/教训,务必读并遵守)。
技术选型自行选最优解不要停。遇到破坏性变更/业务歧义/PII 无法脱敏/缺设计稿等需人工确认的情况,不要擅自执行——写进 blockers 返回。
完成后返回 {taskId, files, verification, blockers}。`;
  const opts = { label: `task:${t.id}:${t.role}`, phase: 'Execute', schema: TASK_SCHEMA };
  if (agentType) opts.agentType = agentType;
  return agent(prompt, opts);
}

// task 开发成功后把 tasks.md 对应行 [ ] 改成 [x](支持断点续跑:重跑时 Plan 读到 [x] 即跳过)。
const MARK_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['taskId', 'marked'],
  properties: {
    taskId: { type: 'string' },
    marked: { type: 'boolean', description: '是否成功把该 task 标成 [x]' },
    note: { type: 'string' },
  },
};

function markDone(t) {
  return agent(
    `把 ${featureDir}/tasks.md 里 task ${t.id}(${t.desc})对应的复选框从 [ ] 改成 [x]。
用 Read 找到该行,只 Edit 这一行的复选框,不要动其它任何内容、不要重排。找不到对应行则 marked=false 并在 note 说明。
返回 {taskId, marked, note}。`,
    { label: `mark:${t.id}`, phase: 'Review', schema: MARK_SCHEMA },
  );
}

// P0 当场修复:reviewer 只读、只判;一旦 codex review 报了 P0(不修就不能交),
// 另派一个带 Write/Edit 的修复 agent 当场改(职责与只读 reviewer 分开,不让评审者改自己评的东西)。
const FIX_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['taskId', 'fixed', 'fixedFiles'],
  properties: {
    taskId: { type: 'string' },
    fixed: { type: 'boolean', description: '是否已修复全部 P0' },
    fixedFiles: { type: 'array', items: { type: 'string' }, description: '本次修改的文件' },
    remaining: { type: 'array', items: { type: 'string' }, description: '无法当场修复、仍需人工的 P0;全修完则空数组' },
    note: { type: 'string' },
  },
};

function fixP0(taskResult, reviewResult, t) {
  const p0 = (reviewResult && reviewResult.p0Issues) || [];
  if (!p0.length) return null; // 没有 P0 → 不派修复 agent
  const files = (taskResult.files || []).join(' ');
  return agent(
    `task ${t.id}(${t.desc})的 codex review 报出了 P0(不修就不能交)。立刻修复这些 P0,只改 P0,不要顺手重构。

项目根: ${projectDir}
featureDir: ${featureDir}
task 改动文件: ${files || '(未报告)'}
要修的 P0:
${p0.map((x, i) => `${i + 1}. ${x}`).join('\n')}

开工前读 ${projectDir}/.claude/rules/ 与 ${projectDir}/AGENTS.md,修复要符合项目规范、别重蹈已知坑。
逐条修复并自检(能跑的话编译/测试过一遍)。确实无法当场修(需人工决策/缺设计)的留进 remaining 别硬改。
返回 {taskId, fixed, fixedFiles, remaining, note}。`,
    { label: `fix-p0:${t.id}`, phase: 'Review', schema: FIX_SCHEMA },
  );
}

// 自学习闭环:task 完成后把本 task 踩的坑/重要约定追加到项目根 AGENTS.md,后续 task 开工前会读它。
const LEARN_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['taskId', 'appended'],
  properties: {
    taskId: { type: 'string' },
    appended: { type: 'boolean', description: '是否往 AGENTS.md 追加了教训(本 task 无新教训则 false)' },
    lessons: { type: 'array', items: { type: 'string' }, description: '写进去的教训条目;无则空数组' },
  },
};

function learnTask(taskResult, reviewResult, fixResult, t) {
  if (!taskResult) return null;
  const issues = ((reviewResult && reviewResult.issues) || []).join('; ');
  const p0 = ((reviewResult && reviewResult.p0Issues) || []).join('; ');
  const blockers = (taskResult.blockers || []).join('; ');
  const fixedNote = fixResult && fixResult.fixed ? `已当场修复(改了 ${(fixResult.fixedFiles || []).join(' ') || '若干文件'})` : (fixResult ? '尝试修复但有遗留' : '');
  return agent(
    `把开发 task ${t.id}(${t.desc})过程中的「项目级教训」沉淀到 ${projectDir}/AGENTS.md(自学习闭环,供后续 task 与人类开发者读)。

本 task 改动文件: ${(taskResult.files || []).join(' ') || '(未报告)'}
本 task 暴露的 blocker: ${blockers || '(无)'}
review 指出的问题: ${issues || '(无)'}
其中 codex 报的 P0: ${p0 || '(无)'}${fixedNote ? `(${fixedNote})` : ''}
若有 P0 已被当场修复,优先把「为什么会犯这个 P0、以后怎么避免」沉淀成一条教训(这是最值钱的复用知识)。

只记「对后续开发有复用价值」的东西:这个库/接口的坑、易踩错的约定、必须先做的前置步骤、环境/配置陷阱、被 review 反复指出的反模式。
不要记:一次性的业务细节、纯属本 task 的实现描述、已经在 .claude/rules 里的通用规范。若本 task 没有值得沉淀的教训,appended=false 不要硬写。

操作:用 Read 看 AGENTS.md 现状(没有就新建,顶部加 "# 项目踩坑与教训(AGENTS.md)" 标题)。追加时去重——已有同类条目就不要重复写。每条一行,带 task 来源,如 "- [${t.id}] xxx 坑:……"。
返回 {taskId, appended, lessons}。`,
    { label: `learn:${t.id}`, phase: 'Review', schema: LEARN_SCHEMA },
  );
}

// pipeline 第二阶段:task 成功后做「review」(同时标 [x])→ 若 review 报 P0 当场修 → 沉淀教训。
async function runAndReview(taskResult, t) {
  if (!taskResult) return { task: null, review: null, fix: null, marked: false, learned: false };
  // review 先跑(后面 fix/learn 都要用它的结论),mark 与之并行。
  const [rv, mark] = await parallel([
    () => reviewTask(taskResult, t),
    () => markDone(t),
  ]);
  // codex review 报了 P0 → 当场派修复 agent 改(只修 P0)。
  const fix = await fixP0(taskResult, rv, t);
  // learn 在 review+fix 之后:沉淀的教训能带上「P0 是怎么修的」。
  const learn = await learnTask(taskResult, rv, fix, t);
  return {
    task: taskResult,
    review: rv,
    fix,
    marked: !!(mark && mark.marked),
    learned: !!(learn && learn.appended),
  };
}

// 每个 task 完成后派 leon-code-reviewer subagent 做只读检查并跑 codex review。
// 脚本只传上下文,review 逻辑沉在 agent/skill 里 —— 和工种 engineer 一个套路。
function reviewTask(taskResult, t) {
  if (!taskResult) return null;
  const files = (taskResult.files || []).join(' ');
  return agent(
    `审查刚完成的 task ${t.id}(${t.desc})。
改动文件: ${files || '(task 未报告文件)'}
项目根: ${projectDir}
featureDir: ${featureDir}

先读 ${projectDir}/AGENTS.md(项目已知坑/教训),评审时核对改动有没有重蹈这些坑。
按你的 skill 流程评审,并对改动跑 codex review。无人值守:发现问题不要等审批,当 fail 写进 issues 冒泡。
重要:把 codex review 里明确标为 P0 / Critical / 「不修就不能交」的问题,原样单独抠进 p0Issues(同时也保留在 issues 里);
这些 P0 会被 workflow 当场派 agent 修复,所以描述要具体到文件:行 + 问题本身,别只写一句泛泛结论。没有 P0 则 p0Issues 为空数组。
返回 {taskId, verdict, issues, p0Issues, summary}。`,
    { label: `review:${t.id}`, phase: 'Review', schema: REVIEW_SCHEMA, agentType: 'leon-code-reviewer' },
  );
}

// 逐组串行保依赖顺序,组内 pipeline:task 一完成就触发它自己的 review。
phase('Review');
const reviewed = [];
for (let g = 0; g < (plan.groups || []).length; g++) {
  const group = (plan.groups[g] || []).map((id) => taskById[id]).filter(Boolean);
  if (!group.length) continue;
  log(`【Execute】第 ${g + 1}/${plan.groups.length} 组:${group.map((t) => t.id).join(' + ')}（组内并行 + 各自 review）`);
  const groupReviewed = (await pipeline(group, runTask, runAndReview)).filter((x) => x && x.task);
  for (const x of groupReviewed) reviewed.push(x);
}

const results = reviewed.map((x) => x.task);
const reviews = reviewed.map((x) => x.review).filter(Boolean);

phase('Collect');
// 冒泡规则:task 自身 blocker 全冒泡;review fail 的 issues 冒泡,但「已被当场修复的 P0」剔除——
// 一个 task 的 P0 若 fix.fixed=true,说明那些 P0 已就地改掉,不必再让外层人工处理(仅 fix.remaining 仍需冒泡)。
const fixById = {};
for (const x of reviewed) if (x.fix) fixById[x.task.taskId] = x.fix;
const allBlockers = [
  ...results.flatMap((r) => (r.blockers || []).map((b) => ({ taskId: r.taskId, kind: 'task', blocker: b }))),
  ...reviews.filter((rv) => rv.verdict === 'fail').flatMap((rv) => {
    const fix = fixById[rv.taskId];
    const p0Set = new Set(rv.p0Issues || []);
    // 已当场修复成功 → 该 task 的 P0 不冒泡;改 remaining(修不掉的)单独冒泡。
    const resolvedP0 = fix && fix.fixed ? p0Set : new Set();
    const stillOpen = (rv.issues || []).filter((i) => !resolvedP0.has(i));
    return stillOpen.map((i) => ({ taskId: rv.taskId, kind: 'review', blocker: i }));
  }),
  // 修复 agent 自己报「修不掉、仍需人工」的 P0。
  ...reviewed.flatMap((x) => ((x.fix && x.fix.remaining) || []).map((i) => ({ taskId: x.task.taskId, kind: 'p0-unfixed', blocker: i }))),
];
const failedReviews = reviews.filter((rv) => rv.verdict === 'fail').map((rv) => rv.taskId);
const markedCount = reviewed.filter((x) => x.marked).length;
const learnedCount = reviewed.filter((x) => x.learned).length;
const p0FixedCount = reviewed.filter((x) => x.fix && x.fix.fixed).length;
const p0SeenCount = reviews.filter((rv) => (rv.p0Issues || []).length).length;
log(`【Collect】完成 ${results.length} 个 task;已标 [x] ${markedCount} 个;沉淀教训 ${learnedCount} 个 → AGENTS.md;codex P0 命中 ${p0SeenCount} 个 task、当场修复 ${p0FixedCount} 个;review 未过 ${failedReviews.length} 个;冒泡 ${allBlockers.length} 个待人工确认的 blocker`);

return {
  mode: 'init+dev',
  projectDir,
  featureDir,
  featureName: plan.featureName,
  init: initReport,
  plannedTasks: (plan.tasks || []).length,
  executedTasks: results.length,
  results,
  reviews,
  p0Fixed: p0FixedCount,
  blockers: allBlockers,
  note: 'P0(codex review)当场派 agent 修复;非 P0 review 问题 / 标记完成 / QA / 审批 由外层 command 与 Stop hook 门禁处理',
};
}
