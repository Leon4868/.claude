# 设计稿取数

## Figma（Codex Figma 插件 / Figma MCP）

链接解析：
- `figma.com/design/<fileKey>/<name>?node-id=1-2` → `fileKey`，`nodeId = 1:2`（`-` 换成 `:`）。
- `figma.com/design/<fileKey>/branch/<branchKey>/...` → 用 `branchKey` 作为 fileKey。
- 链接没有 `node-id`：先调用 `get_metadata(fileKey)`（不传 nodeId）列出页面，再对页面调用 `get_metadata` 找画板（顶层 `frame`），然后请对方选画板。页面级的 metadata 可能很大，结果被落盘时用 jq/grep 只提取顶层 frame 的 `id / name / width / height`。

取数顺序：
1. `get_metadata(fileKey, nodeId)`：画板宽高（定视口用），子元素的 `x / y / width / height`（核对位置、尺寸、间距用）。
2. `get_screenshot(fileKey, nodeId, maxDimension=<画板长边>)`：返回短时有效的 URL，立即用 `curl -L -o design/<画板ID>.png "<url>"` 下载，再用 `file` 确认是 PNG（拿到的是 JSON 说明链接失效，重新调用）。
3. `get_variable_defs(fileKey, nodeId)`：颜色、字号、圆角等变量，用作设计值。
4. 单个元素的样式不确定时（比如某处文字的字号），对该元素的 nodeId 再调用一次 `get_metadata` 或 `get_screenshot`，放大核对。

不要调用 `get_design_context`：它面向生成代码，按插件要求还得先加载 design-to-code 指引，对验收没有额外收益。

## 蓝湖（lanhu-context-mcp）

- 链接需带 `tid`、`pid`、`image_id`，缺任何一个都请对方重新复制“设计图详情”链接。
- `get_design_context(url)` 一次返回：HTML+CSS 标注（含尺寸、颜色、字号、间距）、design tokens、切图映射和预览截图。
- 预览截图存为 `design/<画板ID>.png`；CSS 标注就是设计值。蓝湖标注一般是 @1x 的 px，二倍图的稿子要先除以 2 再比。

## 本地/其他

对方只给了图片时：放进 `design/`，只能做目测比对；数值类结论标为「目测」，不给精确设计值。

## 共同规则

- 设计稿之间互相矛盾（同一组件在不同画板里样式不同），或者设计稿明显笔误（如重复的选项名）：记为备注，请对方确认，不要直接判为页面差异。
- 设计稿没画到的状态（hover、空状态、报错态），不算验收范围，最多在备注里提一句。
