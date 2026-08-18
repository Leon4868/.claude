# 费用配置独立成弹窗（ai-admin-ui）

## Context

TAPD 需求「企业费用配置调整：增加"大模型计费"相关配置项及账单展示相关调整」要求把费用配置从企业配置中独立出来：在「运营平台管理」列表的操作项增加「费用配置」入口，点击打开独立弹窗，弹窗顶部是分组的快速跳转锚点。后端已经把费用配置拆成独立的查询/保存接口（`/company-aggre/admin/sd/platform/priceConfig`），前端目前仍把费用字段塞在 create/edit 大接口的 `config.priceConfig` 里。

上一轮已在旧的 5-Tab 抽屉 Tab2 内实现了「启用大模型计费」开关和「AI外呼单价（大模型）」配置块（工作区未提交）。本次改造把**整个费用配置（含刚加的大模型部分）**迁到新弹窗，抽屉不再持有任何 priceConfig 代码，create/edit 入参的 `config.priceConfig` 固定传 `{}`。

改造后预期：抽屉只剩 4 个 Tab（基础/个性化/高级/拦截）；费用配置有独立入口、独立接口、独立校验，与抽屉互不影响。

---

## 0. 开工前置：核对蓝湖设计稿

本计划的 UI 分组与字段来自 **TAPD 需求正文内嵌的弹窗原型图**（与蓝湖应为同一份设计）。蓝湖 MCP 当前未接入 Claude Code（配置在 VSCode 的 `chat.mcp.serverSampling` 下，Claude Code 读不到），开工前需接入并核对。

**已完成接入**（2026-08-06，`claude mcp get lanhu-context-mcp` → `✔ Connected`）。最终写入用户级配置的定义：

```bash
claude mcp add-json lanhu-context-mcp --scope user '{
  "type": "stdio",
  "command": "/Users/zhizhidemac/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node",
  "args": ["/Users/zhizhidemac/codexWorkSpace/scripts/lanhu-context-mcp-wrapper.mjs"],
  "cwd": "/Users/zhizhidemac/codexWorkSpace",
  "env": {
    "ENV_FILE": "/Users/zhizhidemac/codexWorkSpace/.env.local",
    "CODEX_PLAYWRIGHT_MODULE_DIR": "/Users/zhizhidemac/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules",
    "LANHU_MCP_COMMAND": "/Users/zhizhidemac/.local/bin/npx",
    "LANHU_MCP_ARGS": "-y lanhu-context-mcp",
    "LANHU_WRAPPER_HTTP_TIMEOUT": "30000",
    "PATH": "/Users/zhizhidemac/.local/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  }
}'
```

直接照搬 VSCode 那份配置会连不上（`-32000: Connection closed`），有两处必须改：
1. `LANHU_MCP_COMMAND: "npx"` → 绝对路径。`npx` 装在 `~/.local/bin`，不在 Claude Code 拉起子进程时的 PATH 里，会 `spawn npx ENOENT`。同时显式注入 `PATH`。
2. 追加 `ENV_FILE` 绝对路径。wrapper 第 477 行按 `path.resolve(process.cwd(), ENV_FILE || '.env.local')` 找凭证，只靠 `cwd` 字段不可靠；cwd 不对时会判定 token-missing 并尝试拉起 Chrome 重新登录，撞上"Chrome 正在运行、profile 被锁"直接失败。

排障时可手工握手验证：向 wrapper 的 stdin 发一条 `initialize` JSON-RPC，正常应在约 2.5 秒内返回 `serverInfo: lanhu-context-mcp`。wrapper 的日志走 stderr，不污染 stdout。

**下一步**：本会话启动时 MCP 尚未注册，工具要重启会话才加载。重启后 → 我读蓝湖设计稿 → 把差异写回本文件 → 你确认后才动业务代码。

设计稿：`https://lanhuapp.com/web/#/item/project/detailDetach?pid=d5f4ce5a-95c6-460e-b4d3-d2b047248664&project_id=d5f4ce5a-95c6-460e-b4d3-d2b047248664&image_id=fbe6f4fd-5146-4844-a6c7-1902081fb7c2`

### 蓝湖核对结果（2026-08-06 已读稿）

设计稿输出超 25k token 被截断，末尾「短链每日生成上限」「短信测试额度」未取到，这两项按 TAPD 原型图与现有代码实现即可（分组归属已确认）。已确认的事实：

**① 是右侧抽屉，不是居中弹窗** —— 画布 1920×2384，遮罩 `rgba(0,0,0,.5)` 全屏；面板 `width:1000px; height:全高; margin-left:920px`（920+1000=1920，右边缘贴齐）。所以用 `el-drawer size="1000px"`，与本模块现有配置抽屉（750px）同一形态，**不是 `el-dialog`**。抽屉底色 `rgba(240,242,245,1)` 浅灰。

**② 标题栏与锚点 chip 同一行**（高 52px，带 inset 下边框）：左侧标题「费用配置」16px/PingFang SC-Medium/`rgba(0,0,0,.85)`，右侧紧跟 4 个 chip，最右是 10×10 关闭图标。chip 规格：高 32px、`border-radius:17px`、内左边距 24px、字号 13px；**选中态** 背景 `rgba(17,119,255,.1)` + 文字 `#1177FF` + Medium；**未选中** 背景透明 + 文字 `rgba(0,0,0,.85)` + Regular。宽度随文字（100 / 126px），不等宽。

**③ 每个分区是白色圆角卡片**：`background:#fff; border-radius:16px; width:936px`，左右各留 32px；卡片头高 44px，带 inset 下边框，左侧 icon + 标题 14px/Medium。

**④ 邮件通知确认是 4 个 checkbox**（欠费停用/余额预警/每月账单/每月对账详单）——与现有代码一致，TAPD 原型图那版画少了一个。下方「企业邮箱地址」是独立必填项，含「添加邮箱」按钮与收件/抄送下拉，也与现有代码一致。

**⑤「修改记录」链接确实在结算币种右侧**（`#1177FF` 13px）→ 按已定方案**去掉不做**。

**⑦ 单选文案差异（已定）**：AI外呼单价、AI外呼单价（大模型）、语音通知单价、人工外呼单价四处，设计稿写「按时长/按接通」，旧页面与 TAPD 表格写「按接通时长/按接通数」。**保持现状以 TAPD 为准**，不改线上已有控件文案。提测时如被质疑按本条解释。（外呼/短信测试额度那两处本就是「按时长/按接通」，与设计稿一致。）

**⑧ 必填星号（已改）**：设计稿 13 个必填项 label 后有红色星号（`#F56C6C`、13px、间距 6px、位于 label **之后**）。旧 Tab 用了 `hide-required-asterisk` 全隐藏，新抽屉已去掉该属性，并用 `::after` 覆盖 Element 默认的 `::before`，把星号移到 label 后。

**⑥ 文案差异（已定）**：设计稿写「启用大模型收费」、大模型单价标题截断后显示为「AI 外呼单价」（与上方非大模型项同名）。均**以 TAPD 需求表格为准**——开关用「启用大模型计费」，单价用「AI 外呼单价（大模型）」，与上一轮已实现的代码及账单报表列名保持一致。此处与设计稿的文字出入是有意为之，提测时如被质疑按本条解释。

---

## 1. 新组件结构

在模块下新建子目录，沿用本模块 `.vue` 模板 + `.es6` 逻辑 + mixin 分层的既有风格：

```
src/views/operationPlatformReConfiguration/priceConfigDialog/
├── index.js                  # export { default } from './priceConfigDialog.vue'
├── priceConfigDialog.vue     # 模板 + scoped style（迁来的费用类 + 抽屉/chip/卡片新样式）
├── priceConfigDialog.es6     # 组件主体：props/data/watch/生命周期/打开-提交流程/锚点逻辑
├── config.js                 # 映射 mixin：init/回显/提交三件套
├── rule.js                   # 校验 mixin：12 个 validator + rules
└── methods.js                # 交互 mixin：阶梯增删、单位切换、币种切换、邮箱增删
```

**锚点交互：自己写，不复用 `smsChannel/components/NavTabs`。** 理由：① 设计稿是标题栏内的横向 chip，NavTabs 是可折叠的左侧竖排列表，模板本来就用不上；② `NavTabs/hooks.js` 的 `useNavTabsScroll` 是 Ref-based 组合式写法（项目 Vue 2.7 支持，但本模块是 options + `.es6`），混入要包一层反而更绕。实现照抄 `hooks.js` 的算法即可（约 30 行放在 `.es6`）：
- `partRefs`：4 个分区容器 `ref`（`ref="part0..3"`）
- `handleChangeTab(i)`：先摘 scroll 监听 → `partRefs[i].scrollIntoView({behavior:'smooth'})` → 设 `navIndex` → 500ms 后重新挂监听（防抖动回跳）
- `handleScroll`：`lodash.throttle`，取各分区 `offsetTop` 与容器 `scrollTop` 差值最小者作为 `navIndex`
- `open` 时 `scrollTop = 0`、`navIndex = 0`；`beforeDestroy`/关闭时移除监听

**容器：`el-drawer`**（`size="1000px"`、`direction="rtl"`、`:wrapper-closable="false"`），与本模块现有配置抽屉同形态。结构 = 标题+chip 同行的头部（52px）+ 可滚动内容区（`ref="scrollRef"`，4 张 `.part-card` 白色圆角卡片）+ 底部取消/确定。父组件用法照抄 [taskReclaimDialog.vue](fontend-code/ai-admin-ui/src/views/operationPlatformReConfiguration/taskReclaimDialog.vue)：`:visible.sync` + props，`computed dialogVisible { get/set → $emit('update:visible') }`。

---

## 2. 分组与显隐

四个分区严格按原型分组（内部字段顺序沿用旧 Tab2，减少视觉 diff）：

| 分区 | 内容 | 显隐条件 |
|---|---|---|
| 基础配置 | 结算币种、收费方式、开始收费日期、免费话术个数、预警余额、邮件通知 + 邮箱列表 | 预警余额 `paymentType == 1`；邮箱列表 = 三个邮件开关任一为 1 |
| 外呼费用配置 | 线路收费单价、AI外呼单价、启用大模型计费、AI外呼单价（大模型）、AI坐席收费单价、语音通知单价、外呼测试额度 | 大模型单价 `enableLlm == 1`；AI坐席 `voiceType == 3 \|\| voiceType == 1`；语音通知 `voiceType != 2` |
| 人工坐席费用配置 | 人工坐席单价、人工外呼单价 | 均 `voiceType == 3` |
| 消息费用配置 | 短信收费、短链每日生成上限、短信测试额度 | — |

`voiceType` 来自 props（列表行 `row.voiceType`），新增 `data.voiceType`，模板里把原来的 `addWin.form.voiceType` 换成 `voiceType`。

---

## 3. 数据流

**props**：`visible`（`.sync`）、`row`（整行传，用到 `orgId / id / voiceType / countryId / startPaymentDate / orderId`）。
**emits**：`update:visible`、`success`（父组件收到后 `this.list()` 刷列表）。
**state**：`form`（`getInitPriceConfig()` 的结果，**不再叫 `addWin.form`**）、`voiceTag`、`serverUnit`、`llmServerUnit`、`voiceMinute`、`labourUnit`、`formCurrencyName`、`formCurrencyCode`、`settlementCurrencyFlag`、`exchangeRateList`、`originStartPaymentDate`、`max`/`commonMax`、`emailRecipientTypeOptions`、`navIndex`、`loading`、`submitting`。

打开流程（`@open` 或 `watch visible`）：
1. `form = this.getInitPriceConfig()`；`navIndex = 0`；清校验
2. `exchangeRageAllList()` 拉币种（迁自 [methods/listSeries.js:128](fontend-code/ai-admin-ui/src/views/operationPlatformReConfiguration/methods/listSeries.js#L128)）
3. `GET priceConfig({orgId})` → `res`
4. 回显（顺序照搬旧 [changeConfiguration](fontend-code/ai-admin-ui/src/views/operationPlatformReConfiguration/operationPlatformReConfiguration.es6#L205-L258) 的费用段）：
   - 短信收费类型默认：`res.smsPaymentType` 为空时按 `row.countryId == 1 ? 1 : 2`
   - `originStartPaymentDate = res.startPaymentDate`
   - `serverUnit / llmServerUnit / voiceMinute` 按各自 `*PaymentType` 置「通/分钟」
   - 6 处 `initSpecialPriceConfig`（`max === 9999999 → 999999999` 兼容）
   - `syncPriceConfig(res)`（内含厘转元、`*UnitTime` 拆成「数值 + 分钟/秒」、`voiceTag`、testTime 组数组、`settlementCurrency == -1 → 1`）
   - `settlementCurrencyFlag = !!originStartPaymentDate`；`changeSettlementCurrency(form.settlementCurrency)` 初始化币种名/码

**首次配置（GET 返回空对象 / 无记录）**：`syncValue` 本来就只覆盖 `!= undefined` 的 key，空响应天然落到 `getInitPriceConfig()` 的默认值；额外确保 `originStartPaymentDate = ''`、`settlementCurrencyFlag = false`、币种回落 1。入口按钮已限制「配置已创建」才可点，这条是兜底。

**收费日期锁定的状态收敛**：旧代码有三份状态（`company.startPaymentDate` 控禁用、`addWin.form.startPaymentDate` 是编辑值、`originStartPaymentDate` 控提交校验）。新弹窗统一为两份：`originStartPaymentDate`（GET 原值，控禁用 + 提交校验）和 `form.startPaymentDate`（编辑值）。模板中所有 `!!company.startPaymentDate` 改成 `!!originStartPaymentDate`。

提交流程（确定按钮）：
1. 合同校验（迁自 [clickSub:306-323](fontend-code/ai-admin-ui/src/views/operationPlatformReConfiguration/operationPlatformReConfiguration.es6#L306-L323)）：`isDomesticEnv` 时 `aiCompany.listReconfig({id: orgId})` → `testEnable` 豁免；否则按「已有/未有 `originStartPaymentDate` × 新填 `form.startPaymentDate` × 无 `orderId`」两分支 warning 并中断。`orderId` 取 `data[0]?.orderId ?? row.orderId`（**实现时需确认 listReconfig 是否返回 orderId**，不返回就退回 `row.orderId`）
2. `this.$refs.priceForm.validate()`，失败时把 `navIndex` 跳到出错字段所在分区并滚过去（错误 prop → 分区序号用一张静态映射表）
3. `freeTemplateCount` 兜底为 0
4. `POST priceConfig({ orgId, priceConfig: this.getPriceConfigFrontEndToBackend() })`
5. 成功：`$openMessage.success('配置成功')` → 关弹窗 → `$emit('success')`；失败按现有 request 层弹后端 message（含"操作太频繁，稍后再编辑"）

---

## 4. 旧代码摘除清单

### `operationPlatformReConfiguration.vue`
- 删 777-1446 整段 `<el-form ref="againAddWin">`（Tab2 全部内容，含上一轮新加的大模型块）
- 删 Tab 页签第 2 项（363-372 内的 `companyConf_CostAllocation` 那个 `el-radio-button`）
- 挂载新组件：`<price-config-dialog :visible.sync="priceConfigVisible" :row="priceConfigRow" @success="list" />`
- **保留**：列表列 slot（`aiOutboundCallUnitPrice` / `smsPaymentPrice` / `channelFeePricesSlot` / `manualOutboundCallFeeSlot` / `settlementCurrency` / `balanceWarning` / `paymentType`）及其 `formatServerPrice`、`formatSmsPrice`、`gatewayPriceFn`、`formatBalanceWarning`、`formatPay`；log 弹窗（328-350）与 `callPriceLogFn` 等全部不动

### `config.js`
- 移出 `getInitPriceConfig`(224-284) / `syncPriceConfig`(285-288) / `syncPriceConfigBackendToFrontEnd`(289-394) / `getPriceConfigFrontEndToBackend`(395-468) / `syncPriceConBackendToFrontEnd`(1203-1219) → 新 `priceConfigDialog/config.js`
- 删 `getInitConfigForm()`(68) 里的 `...this.getInitPriceConfig()`
- 删 `syncConfig()` 里的 `syncPriceConfig(config.priceConfig)` 调用
- 删 `addWin` 上的 4 个 `*UnitEdited`(31-34)（模板未使用的遗留）和 `emailRecipientTypeOptions`(15-18)（随迁）
- 若 `priceUtils` 在 config.js 内不再被引用，删 import（`const.js` 的那份保留）

### `rule.js`
- 移出 12 个费用 validator（`serverPriceListValid` / `llmServerPriceListValid` / `smsPriceListValid` / `channelFeePriceListValid` / `labourGatewayPriceValidFn` / `informPriceListValid` / `aiSeatsPriceValid` / `seatsPriceValid` / `shortUrlCountValid` / `autoSendBillEmailValid`）与对应 rules key，以及 message-only 的 `paymentType` / `balanceWarning` / `settlementCurrency`
- **保留**：`mailAddressValid`（`everyDayDataSendMail`，属个性化）、`phoneLimitValid`（`phoneLimitCount`）
- 迁移时把 validator 内的 `this.addWin.form.*` 改成 `this.form.*`

### `methods/changeSeries.js`
- 移出 `changeVoiceInform` / `changeUnitFn` / `changeLlmUnitFn` / `changeLabourPriceTypeFn` / `changeFn` / `changeSettlementCurrency`
- `changePayment`(120-131)：**整个方法删除**（收费方式→`arrearsStop` 联动改由后端处理），同时删模板中已随 Tab2 移除的 `@change="changePayment"`
- **注意**：`changeSettlementCurrency` 若列表页/其他 Tab 还有调用点，实现时先 grep 确认；当前已知调用点只在费用相关处

### `methods/dynamicOperationSeries.js`
- 移出 `addSmsFn/removeSmsFn`、`addLabourFn/removeLabourFn`、`addServerFn/removeServerFn`、`addGatewayServerFn/removeGatewayServerFn`、`addLlmServerFn/removeLlmServerFn`、`addVoiceMinute/removeVoiceMinute`、`addEmail/deleteMessage`
- **保留**：`plusData/minusData`、`addMailAddress/deleteMailAddress`、`addOrigin/delOrigin`、`addFsServerFn/removeFsServerFn`

### `methods/formatSeries.js` / `listSeries.js`
- `getCurrencyName` / `getCurrencyCode`：**两处都要用**（列表 `formatServerPrice` 也在用）→ 新组件里复制一份，原文件保留
- `exchangeRageAllList`(listSeries.js:128) 同理，两处各留一份（或新组件自行请求币种列表）

### `operationPlatformReConfigurationMixin.js`
- 删费用相关 data：`voiceTag`(307)、`serverUnit`(308)、`llmServerUnit`(309)、`voiceMinute`(310)、`labourUnit`(311)、`settlementCurrencyFlag`(306)、`originStartPaymentDate`(331)
- `formCurrencyName`/`formCurrencyCode`(304-305)、`exchangeRateList`(292)、`max`/`commonMax`(277-278)：确认列表列格式化是否还用（`formatServerPrice` 用 `getCurrencyName` 不直接用这些）——用则保留，不用则删
- `operationList`(217-245) 增加「费用配置」项（见 §5）

### `operationPlatformReConfiguration.es6`
- `changeConfiguration`：删 205-232 的费用回显段（`originStartPaymentDate`、三个 unit、6 处 `initSpecialPriceConfig`）与 255-258（`settlementCurrencyFlag` / `changeSettlementCurrency`）
- 删 `initSpecialPriceConfig`(296) 定义（随迁）
- `clickSub`：删 306-323 合同校验段（随迁）、删 337-345 的 `againAddWin` 分支（改为直接 `this.collectSubmitData()`）、删 `nextTick` 里的 `$refs.againAddWin?.clearValidate()`
- `collectSubmitData`：删 377 的 `freeTemplateCount` 兜底；432 改成 `priceConfig: {}`；删 414-421 注释掉的旧校验和 `somePriceMoreThanZero`(439)
- 删 `changeChannelBillPrice`(507) / `changeChannelFeePrice`(515) 两个空函数
- 新增 `openPriceConfigDialog(row)`：`this.priceConfigRow = row; this.priceConfigVisible = true`

### `operationPlatformReConfiguration.scss`
- 把费用相关的约 20 个类迁到新组件 scoped style：`.price-rule-wrap`/`.list-item`、`.unit_append`、`.each_append`、`.input-box`、`.line-height_28`、`.settlement-tip`、`.fee-config-tip`、`.w_fill`、`.mark-bg`、`.mail-box` 及 `.mail-*` 系列
- 原 scss 中确认无其他 Tab 使用后再删（`.line-height_28`、`.input-box` 大概率被其他 Tab 复用，**只复制不删**）

---

## 5. 操作列新入口

在 [mixin.js:217](fontend-code/ai-admin-ui/src/views/operationPlatformReConfiguration/operationPlatformReConfigurationMixin.js#L217) 的 `operationList` 中，紧跟「更改配置」之后插入：

```js
{
  name: this.$t('companyConf_CostAllocation'),   // 复用现有「费用配置」i18n key
  destroy: () => !hasButtonPermission('companyManager-operationPlatformReConfiguration-priceConfig'),
  disabled: row => !row.id,                      // 配置未创建则置灰
  onClick: this.openPriceConfigDialog
}
```

`disabled` 走 nf-table 已支持但本仓库尚无先例的函数式写法（`nf-table.vue:156-170` 有 `:disabled="resolveValue(item.disabled, scope.row, scope)"`）——实现后需**实测**置灰效果。若 nf-table 版本不支持，退路是用 `destroy` 直接隐藏按钮，但那与需求「置灰」不符，需回来确认。

权限 key `...-priceConfig` 需要同步找后端/运维在权限系统里配置，否则所有人看不到按钮。**这一步不能漏，实现时先确认 key 命名与配置流程。**

---

## 6. API / URI 新增

`src/api/uri.js`（加在 634 行 create/edit 之后，与同族放一起）：
```js
export const AI_OPERATIONPLATFORM_PRICE_CONFIG = getewayApi + '/company-aggre/admin/sd/platform/priceConfig'
```
（查询与保存同路径不同 method，一个常量即可。注意前缀变量拼写就是 `getewayApi`。）

`src/api/aiCompany.js`（照抄同文件既有写法，运营平台系列统一用 `naCostGet` / `naCosPost`）：
```js
export function getPriceConfig(param) { return request.naCostGet(uri.AI_OPERATIONPLATFORM_PRICE_CONFIG, param) }
export function savePriceConfig(param) { return request.naCosPost(uri.AI_OPERATIONPLATFORM_PRICE_CONFIG, param) }
```

---

## 6.1 已知遗留缺陷（本次不修，已与需求方确认保持原样）

`getPriceConfigFrontEndToBackend()` 中，`labourPrice`（人工坐席单价）与 `gatewayPaymentPrice`（人工外呼单价）的**元→厘转换被 `if (voiceType == 3)` 包住**，而 `syncPriceConfigBackendToFrontEnd()` 的厘→元转换是**无条件**的。两侧不对称：

- 非呼叫中心企业（`voiceType != 3`）若历史上存过非零的这两个值，每保存一次费用配置就会被除以 10000。
- 同一个 `if` 块内的 `gatewayPaymentUnitTime` 也只在 `voiceType == 3` 时下发，导致非呼叫中心企业会发出 `gatewayPaymentPrice` 却不带计费周期。

这是从旧 5-Tab 抽屉原样继承的行为（旧流程保存时同样携带 priceConfig），**不是本次改造引入**。费用配置独立成入口后被单独保存的频率上升，触发概率随之变高。需求方确认保持与旧代码一致，风险由后端兼容（后端对非呼叫中心企业应忽略这两个字段）。若后续要修，把 `config.js` 提交侧那两行移出 `if (voiceType == 3)` 即可，与回显侧对称。

---

## 7. 风险与回归点

1. **抽屉保存会不会清空费用配置** —— 最高优先级。`priceConfig: {}` 传给 edit 接口，需后端确认空对象是「不更新」而非「清空」。实现前先和后端对齐；若后端按整体覆盖处理，改为不传 `priceConfig` 字段（`delete`），仍不行就得由后端提供部分更新。
2. **`this.addWin.form` → `this.form` 的机械改名**：模板段（~670 行）+ 12 个 validator + 14 个方法都要改，漏一个就是运行时 `undefined`。建议迁移后全局 grep 新目录确认零 `addWin` 残留，再逐分区点测。
3. **`voiceTag` 不在 form 里**：语音通知单价的「分钟/秒」下拉 `v-model="voiceTag"`，提交时被 `getPriceConfigFrontEndToBackend` 读取。迁移时极易漏，需专门验证「按时长 + 秒」保存后回显正确。
4. **`orderId` 来源未验证**：合同校验依赖它，需确认在 `row` 或 `listReconfig` 响应里存在，否则校验形同虚设（`!undefined` 恒为 true 会误报"请先绑定合同"）。
5. **权限 key 未配置**：按钮不显示。
6. **列表页格式化函数的连带依赖**：删 mixin data / methods 时若删多了，列表的单价列会白屏或显示异常。删除前对每个待删项 grep 全模块确认无其他引用。
7. **旧 Tab 的表单校验联动**：`clickSub` 删掉 `againAddWin` 分支后，抽屉的 `$refs.addWin.validate` 仍要能正常走到 `collectSubmitData`；`interceptAutoJump(errOption)` 里若有跳 `titleTab = 2` 的映射，需一并调整（Tab 序号发生了位移：原 3/4/5 变成 2/3/4）。**这是最容易被忽略的一处——Tab 重新编号会影响所有 `titleTab = N` 的跳转代码**，需全模块 grep `titleTab`。
8. **表格列缓存**：本次不涉及列变更，无需 bump storage-key。
9. `changePayment` 删除后，预付/月结切换不再自动改欠费停用——需求已确认由后端处理，但要在提测说明里写清，避免测试按旧行为提 bug。

---

## 8. 验证

**静态**：
- `npx eslint` 跑新目录 + 所有被改文件（本模块无单测）
- 全模块 grep：`addWin.form.` 在新目录零命中；`againAddWin` 全仓零命中；`titleTab` 的所有赋值点已按新编号修正

**手工回归（需要能登录管理后台）**：
1. 列表 →「费用配置」按钮：未创建配置的企业置灰、已创建可点、无权限不显示
2. 弹窗打开 → 4 个 chip 点击滚动定位正确、滚动时高亮跟随
3. 回显核对（挑一个已配置的企业，逐项与改造前的 Tab2 截图比对）：币种/收费方式/各阶梯价格（厘转元）/计费周期数值与单位/测试额度有效期/跨月剩余额度/邮箱列表
4. 大模型：开关关→开，单价块出现；配「按接通时长 + 秒」保存后重开回显一致；关闭开关保存后再开，历史值处理符合预期
5. voiceType 三种业务类型（智能语音1 / 语音通知2 / 呼叫中心3）各开一次，确认 4 个条件项显隐正确
6. 已设「开始收费日期」的企业：阶梯区间与计费周期禁用、币种禁用；未设的可编辑
7. 校验：阶梯不连续 / 价格小数超 4 位 / 邮件开关开但无收件人 → 报错并跳到对应分区
8. 合同校验：无合同 + 设收费日期 → warning 拦截
9. 保存成功后列表对应行的单价列刷新为新值
10. **抽屉回归（重点）**：打开 5→4 Tab 抽屉，确认只剩 4 个 Tab；改个性化/高级配置保存后，**重新打开费用配置弹窗确认费用数据没被清空**（对应风险 1）
11. 列表各单价列的「修改记录」弹窗仍可打开
