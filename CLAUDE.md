## 设计约束

1. **一次只戴一顶帽子**：加功能时不改结构，重构时不加功能。
   两者必须是不同的 commit。
2. **接口简单 > 实现简单**。宁可在模块内部多写 30 行，
   也不要让调用方多知道一件事。
3. **不要加配置参数**。如果能算出合理默认值就算出来。
   确实需要开关时，先问我。
4. **提炼的唯一理由是名字增加了信息**。如果新函数只被调用一次、
   且名字没比函数体说得更多，不要提炼。
5. **改动前先答**：把这个职责挪到隔壁会坏掉什么？
   答不上来说明边界是任意的，先跟我讨论再动手。
6. 写完立刻跑 `tsc --noEmit` 和测试。不要一次做完再验证。

# 全局规则

## Goal 任务：先过 CR 再 commit

固定工作流（适用于所有 /goal 任务）：

1. **写代码阶段绝不提前提交** —— 改动写完先停，**保持留在工作区（未提交）**，让 Stop hook 触发 codex review（`~/.claude/hooks/stop-codex-review-gate.mjs`，审 working-tree 的未提交改动，仅 goal 模式下运行）。
2. **每次某一轮停下时 CR 给 ALLOW，就在那一轮立刻提交这一版**（不攒到最后）：
   - 这一轮有改动、CR **通过 → 提交**。
   - 这一轮 CR **BLOCK → 改 → 再停 → 再 CR**，循环直到**过 → 提交**。
3. 提交完继续后续工作。

铁律：**先过 CR 再 commit，绝不在 CR 之前 commit。**

**Why:** review gate 只审「未提交的 working-tree 改动」。一旦提前 commit，工作区变干净，`hasChanges()` 返回 false，hook 静默放行 → 等于跳过审查。

**误提交补救:** 用 `git reset --soft HEAD~1` 把改动退回工作区再让 hook 审。

## 分支创建：必须基于最近的稳定分支

铁律：**新分支一律从「日期最新的 `release_*` 分支」切出；无法确定基线时，停下来问我，绝不擅自猜一个。**

适用范围：所有新建分支的场景 —— `git checkout -b` / `git switch -c` / `git worktree add -b`、worktree 隔离（`EnterWorktree`、subagent `isolation: "worktree"`）、以及各类 skill 里的建分支步骤。

稳定分支的形态：命名为 `release_YYYYMMDD`（如 `release_20260716`），一个仓库里同时存在很多个（20+），**日期最新的那个才是当前稳定线**。

- 基线**不是** `master`（它只是仓库的默认分支，不代表最新稳定态）。
- 基线**不是** `test`（堆着一堆未上线改动）。
- 基线**不是**当前恰好所在的某个 feature 分支。

执行要求：

1. 先取最新基线，不要凭印象：

   ```bash
   git fetch --prune
   git branch -r --list 'origin/release_*' | sed 's|.*origin/||' | grep -E '^release_[0-9]{8}$' | sort -r | head -5
   ```

   `grep` 那一段不能省：仓库里还有 `release_hotfix_YYYYMMDD`、`release_temp_YYYYMMDD` 这类分支，直接 `sort -r` 会把它们排到最前（字母序 `t` > `h` > 数字），取到错的基线。

2. 基于它建分支：`git switch -c <新分支名> origin/<最新 release_*>`（worktree 同理：`git worktree add -b <新分支名> <路径> origin/<最新 release_*>`）。

   **新需求的分支名必须带我的名字缩写前缀 `xxl/`**，格式：`xxl/feature/<需求名称>`。
   例：`xxl/feature/坐席组任务详情`、`xxl/fix/文案变量替换`。
   需求名称用中文或短横线英文都行，与该仓库历史做法保持一致即可。
   非新需求（如临时验证分支）可不带前缀，但拿不准就按带前缀处理。
3. **每次建完分支，必须立刻明确汇报两件事**（不许省略、不许混在一大段说明里让我自己找）：

   ```
   基线：origin/release_20260716
   新分支：feature/xxx-yyy
   ```

   一次建多个分支（多仓库并行、worktree 隔离）就逐条列全，每个仓库一行基线 + 一行分支名。subagent 在 worktree 里建的分支同样要回报上来。
4. 出现以下任一情况，**停下来找我确认，不要自己选**：
   - 排在最前的 `release_*` 日期**晚于今天**（提前建的下个版本分支，未必已稳定）；
   - 最新 `release_*` 的日期距今过久（如超过两周），可能这个仓库本轮没发版；
   - 仓库里根本没有 `release_*` 分支，或命名规则与上述不符；
   - 当前 HEAD 不在基线上，且不确定该不该带上现有改动。

**Why:** 从 `test` 或某个未合并的 feature 分支切出去，会把别人未上线的改动一并带进新分支，最终 PR 里混入无关提交，上线时污染 release，事后极难拆干净。

## Worktree：即用即弃，统一放 `.worktrees`

**worktree 本身不持久化**（用完就 `git worktree remove`），**持久化的是统一路径和下面这套流程**。

路径固定为：`~/Documents/Code/.worktrees/<repo名>/<分支名>`。不要建在各 repo 旁边，否则编辑器全局搜索、`rg`、备份都会扫到。

**什么时候才开 worktree**：只读探索阶段留在主目录，不要开。等到「要改哪些文件已明确、准备动第一行代码」那一刻再开。以下三种情况可以提前开：主目录已有未提交改动不想混在一起被 CR 审、探索本身会产生文件（跑 build/测试产物）、派 subagent 并行探索多个仓库。

**后端仓库（Maven，12 个）** —— 依赖在 `~/.m2` 全局共享，直接建，成本几乎为零：

```bash
git -C <repo> worktree add -b xxl/feature/<需求名> ~/Documents/Code/.worktrees/<repo>/<分支名> origin/<最新 release_*>
```

**前端仓库（yarn 1.22，4 个）** —— `node_modules` 不会跟过来（380M~1.8G，重装要几分钟）。用 APFS 写时复制克隆补上，实测 380M 只要 13 秒且**不占额外磁盘**：

```bash
git -C <repo> worktree add -b xxl/feature/<需求名> ~/Documents/Code/.worktrees/<repo>/<分支名> origin/<最新 release_*>
cp -Rc <repo>/node_modules ~/Documents/Code/.worktrees/<repo>/<分支名>/node_modules
cp <repo>/.env* ~/Documents/Code/.worktrees/<repo>/<分支名>/ 2>/dev/null   # 本地配置也不会跟过来
```

`-c` 不能省，那是 APFS clone；写成 `cp -R` 就变成真拷贝，慢且实打实占几百 MB。只有分支的 `package.json` 变了才需要再 `yarn install`（增量）。

**收尾**：分支合并后 `git -C <repo> worktree remove <路径>`，别留着。定期 `git worktree prune` 清理失效记录。

### 铁律：worktree 的改动绝不落到稳定分支

worktree 里的改动**只提交到它自己的 feature 分支**（`xxl/feature/<需求名>`）。稳定分支（`release_*`）是只读基线，只当切分支的起点，不当落脚点。

**禁止的四类动作**（未经我逐次明确指示，一律不做）：

1. **不在稳定分支上建 worktree** —— `git worktree add <路径> release_20260716` 这种「把 worktree 绑到 release 分支」的写法禁止。永远用 `-b <新分支名> origin/<最新 release_*>`，让 worktree 的 HEAD 始终是新建的 feature 分支。
2. **不把 commit 打到 `release_*` 上** —— 不在 worktree 里 `git switch release_*` 后提交，不 `git merge` 进本地 `release_*`，不 cherry-pick 过去。
3. **不推到稳定分支** —— `git push origin HEAD:release_*`、`git push origin release_*` 一律禁止。只推自己的 feature 分支。
4. **不把 feature 分支的 upstream 绑到稳定分支** —— `git push -u origin release_*`、`git branch -u origin/release_*` 禁止。upstream 只能是同名的 `origin/xxl/feature/<需求名>`。

**合并进 release 由我决定，走 MR / 发版流程。** `merge-to-release`、`merge-to-test` 这类 skill 只在我**明确点名要跑**的时候才执行，绝不作为「开发完成」的自动收尾动作。

**Why:** worktree 和主目录共用同一个 `.git`，在 worktree 里对 `release_*` 的任何提交、合并、推送都会立刻污染整个仓库的稳定线，而且当时主目录看不出异常，等发版才发现。基线必须保持和远端一致，否则下一个从它切出去的分支会继承脏改动。

## 密钥：不主动读、不外泄、不留痕

铁律：**代码和配置里的 apikey / token / 密码 / 证书私钥，一律不主动读取、不输出、不记录、不发到外网。**

涵盖对象：`apiKey` / `secret` / `token` / `password` / `accessKey` / `privateKey` 等字段值，以及 `.env`、`application-*.yml` 里的凭证段、`~/.archery-credentials.json`、`~/.archery_session.json` 这类本地凭证文件。

四条具体约束：

1. **不主动去找** —— 不为了"看看配置"而 grep 密钥字段、不整目录 dump `.env`。只在任务确实需要时读**最小范围**，且读了不等于可以复述。
2. **不输出** —— 任何情况下不把密钥明文打到回复里、不 `echo`/`cat` 到终端。必须指代时只说位置和字段名（「`application-prod.yml` 里的 `aliyun.accessKey`」），值一律写成 `<REDACTED>`。
3. **不留痕** —— 不写进 memory、不写进 CLAUDE.md / README / 需求文档 / 发版文档、不写进提交信息，也不新增把密钥硬编码进代码的改动。
4. **不出网** —— 不通过任何 MCP（github / tapd / stitch / figma / lanhu）、WebFetch、Artifact 发布、或外部 API 传出去。也不 `git push` 含密钥的改动。

**发现硬编码密钥时的动作**：停下来告诉我「哪个文件、哪一行、什么类型的凭证」，**不要贴出值**，等我决定怎么处理（换配置中心 / 轮换 / 加 `.gitignore`），不要擅自改动或提交。

**已知的两条外泄路径，要额外当心：**

- **codex review gate** 会把 working-tree diff 送进 codex CLI。改动里带凭证 → 随 diff 出去。所以密钥不该进工作区改动。
- **subagent / worktree** 里同样适用本条，隔离环境不豁免。

**Why:** 密钥一旦进了对话记录、提交历史或外部服务，就等于泄露，事后 rebase 或删文件都清不干净，只能走轮换。
