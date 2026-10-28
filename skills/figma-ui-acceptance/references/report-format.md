# 结果格式

results.json 与截图同处证据根目录。图片使用根目录内的 PNG/JPEG/WebP 相对路径；生成器嵌入图片，交付 HTML 后无需额外图片文件或网络。

```json
{
  "schemaVersion": 2,
  "meta": {
    "title": "用户列表 UI 验收",
    "design": "Figma 文件 / 本次画板范围",
    "environment": "线上页面地址（去除敏感参数）",
    "viewport": "按画板记录；单位 CSS px",
    "startedAt": "ISO 8601，含时区",
    "endedAt": "ISO 8601，含时区"
  },
  "boards": [
    {
      "id": "B-01",
      "name": "用户列表",
      "state": "默认状态",
      "page": "https://example.com/users",
      "designNode": "12:34",
      "viewport": "1440×900 CSS px，DPR 2，缩放 100%",
      "steps": "用户管理 → 用户列表",
      "result": "有差异",
      "designShot": "design/B-01.png",
      "actualShot": "actual/B-01.png",
      "inventoryNote": "依据默认态页面快照列出查询、状态筛选及表格滚动；弹窗内新入口继续追加",
      "targets": [
        {"id": "T-01", "name": "规则状态筛选", "kind": "筛选", "source": "页面观察"}
      ],
      "interactions": [
        {
          "id": "I-01", "targetId": "T-01", "action": "展开状态筛选，选择已停止并查询",
          "expected": "选中标签改变，结果列表仅呈现已停止记录",
          "actual": "选中标签为已停止，当前结果行状态均为已停止",
          "result": "已验证", "beforeShot": "actual/B-01.png", "afterShot": "actual/I-01.png",
          "cleanup": "恢复所有并查询，原列表重新出现"
        }
      ],
      "checks": [
        {"category": "布局与尺寸", "result": "一致", "note": "关键容器矩形与设计吻合"},
        {"category": "间距与对齐", "result": "有差异", "note": "D-01，按钮与表格间距"},
        {"category": "字体与文字", "result": "一致", "note": "标题和按钮文案、字体属性已核对"},
        {"category": "颜色与表面", "result": "一致", "note": "关键颜色、圆角和边框已核对"},
        {"category": "图标与图片", "result": "一致", "note": "图标形状、尺寸和颜色已核对"},
        {"category": "内容与溢出", "result": "一致", "note": "现有长名称样本显示正常"},
        {"category": "组件状态", "result": "不适用", "note": "本画板未定义额外状态"},
        {"category": "交互与滚动", "result": "一致", "note": "I-01已执行筛选并恢复；未发现其他范围内只读入口或溢出方向"}
      ],
      "items": [
        {
          "id": "D-01",
          "severity": "细微",
          "element": "查询按钮下方至表格顶部",
          "property": "垂直间距",
          "design": "24 CSS px",
          "actual": "32 CSS px",
          "method": "测量",
          "impact": "查询区和表格之间的留白偏大",
          "suggestion": "将该区域间距调整为设计的 24 CSS px",
          "note": "依据：measurements/B-01.json，相关元素矩形；整屏中表格上方"
        }
      ]
    }
  ],
  "notes": ["本次只读验收；验收边界和额外限制"]
}
```

这是字段示例，不代表真实验收。替换所有值，不复制示例的通过结论。

规则：

- 画板和问题 ID 全局唯一。result：一致/有差异/未覆盖/受阻。severity：阻断/明显/细微。
- checks 必须逐个列出八类；每项有依据或具体原因。结果为未覆盖/受阻时，画板 note 必须解释。完全受阻时八类可均为未覆盖，记录共同原因。
- 一致/有差异要求两张有效截图，且适用检查完成；有差异至少一个问题，一致不能有问题。
- 有未覆盖检查时，画板写未覆盖或受阻；仍可记录已确认的问题。有差异检查必须有对应问题。
- 每个问题必须有元素、属性、设计值、实际值、method（测量/目测）、impact、suggestion、note。note 说明 Figma 标注或节点及实际截图位置/测量文件；未知设计值不能填成数值。
- 无法精确测量但肉眼确认的形状或布局问题可用目测描述。每条问题可以增加 designShot/actualShot 局部截图；未增加时继承画板截图，两侧均须有证据。
- 额外画板字段 designNode、viewport、steps 会显示在 HTML 中。meta 使用字符串；截图和 JSON 里不含凭证或无关个人数据。
- 总结论：没有有效的已比较检查 → BLOCKED；存在未覆盖/受阻 → PARTIAL；全部完成且有问题 → HAS_DIFF；全部完成且一致 → PASSED。部分验收中的已确认问题仍计入严重度数量。

## 动态覆盖（v2 必填）

- 新运行写 `schemaVersion: 2`。每画板必填 `inventoryNote`（清单来源）、`targets` 和 `interactions`；每个目标至少有一条记录。目标及记录 ID 也必须全局唯一。
- target 字段：`id`、`name`、`kind`、`source`（设计/页面观察），可加 `designNode`。kind 使用具体交互名称，例如下拉、筛选、查询、页签、分页、滚动、弹窗、抽屉、悬停、焦点、状态；同一目标可有多条转换。
- interaction 必填：`id`、`targetId`、`action`、`expected`、`actual`、`result`。result 为 `已验证 / 有差异 / 未覆盖 / 受阻 / 不适用`。
- 已验证/有差异：必填不同路径的 `beforeShot`、`afterShot`（均为证据根目录内相对路径）及 `cleanup`。恢复失败如实写在 cleanup，并追加未覆盖的恢复记录；不能写已恢复。可加 `note` 引用快照/测量文件，`durationSeconds` 记实际耗时。
- 有差异：必填 `issueId`，引用该画板的已确认问题。未覆盖/受阻/不适用：必填具体 `reason`，不用空泛的“未测”。预建计划的 `actual` 可写“尚未执行”，不能沿用示例实际结果。
- 纯静态画板允许 targets/interactions 均为空，但需 `interactionNote` 解释没有可操作入口、动态设计状态或滚动内容，且八类中的“交互与滚动”为不适用；不能用空数组避开已有控件。
- 动态清单有未覆盖/受阻时画板只能为未覆盖/受阻；有已验证转换时不能把整画板写为受阻。有差异转换必须在八类检查和问题列表中体现。
- 生成器输出目标数、已执行转换数及缺口数，HTML 展示逐条操作和证据。它不能证明清单未漏控件，仍需对照设计结构及页面快照检查。
- 可选顶层 `timings`：`[{"phase":"页面交互","durationSeconds":42,"toolCalls":8}]`。只记实际可确认的耗时/调用数，不估算后冒充测量。
- 旧格式可读取并展示，但未提供动态清单时有效比较最多给 PARTIAL，并提示未记录动态覆盖；不自动把历史静态报告升级为完成验收。
