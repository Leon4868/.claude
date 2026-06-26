---
name: leon-test-runner
description: 自动生成测试用例并运行单元测试、组件测试、E2E 测试，使用 Chrome MCP 做可视化回归
---

# leon-test-runner — 自动化测试运行器

根据变更自动生成/更新测试，运行完整测试套件。

## 输入

- Feature 名称和 specs 路径
- 变更的文件列表

## 执行步骤

### 1. 检查测试基础设施

检查项目是否已配置测试框架：

```bash
# 检查 package.json 中是否有测试依赖
grep -E "vitest|jest|playwright|@testing-library" package.json
```

如果未配置，先安装：

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

确保 `vite.config.ts` 中有 test 配置：

```typescript
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
```

### 2. 生成测试用例

对每个变更的源文件：

- **组件文件** (`*.tsx`): 生成 React Testing Library 测试
  - 渲染测试（组件是否正常渲染）
  - 交互测试（用户操作是否产生预期效果）
  - Props 测试（不同 props 下的行为）
  - 边界情况（空数据、错误状态）

- **工具函数** (`utils/*.ts`): 生成纯单元测试
  - 正常输入
  - 边界值
  - 异常输入

- **Hooks** (`hooks/*.ts`): 生成 renderHook 测试

测试文件放在源文件同目录，命名为 `{filename}.test.tsx`。

### 3. 运行单元/组件测试

```bash
npx vitest run --reporter=verbose
```

收集结果：
- 通过/失败/跳过的测试数
- 失败测试的详细信息
- 覆盖率报告（如已配置）

### 4. 运行 E2E 测试（如已配置 Playwright）

```bash
# 检查是否有 playwright
test -f playwright.config.ts && npx playwright test
```

### 5. 可视化回归（Chrome MCP）

如果变更涉及 UI 组件：

1. 确保开发服务器运行中（`npm run dev`）
2. 使用 Chrome MCP 工具：
   - `mcp__chrome-devtools__navigate_page` 打开关键页面
   - `mcp__chrome-devtools__take_screenshot` 截图
   - 与 `specs/{feature-name}/screenshots/` 中的基准截图对比
3. 首次运行时保存截图作为基准
4. 后续运行时对比差异

### 6. 处理失败

如果测试失败：
- 分析失败原因
- 区分是测试问题还是代码问题
- 如果是代码问题，返回具体的失败信息给调用者
- 如果是测试本身的问题，修复测试后重新运行

## 输出

```markdown
## 测试报告

### 单元测试 / 组件测试
- 框架: Vitest
- 总计: N | 通过: N | 失败: N | 跳过: N
- 覆盖率: N%
- {失败详情（如有）}

### E2E 测试
- 状态: {PASSED / FAILED / SKIPPED}
- {详情}

### 可视化回归
- 截图页面: N
- 差异: {无差异 / 发现 N 处差异}

### 总结
- 测试结果: {PASSED / FAILED}
- {需要修复的问题列表（如有）}
```
