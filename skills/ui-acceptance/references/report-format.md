# results.json 结构

放在证据目录里；截图路径用相对于 results.json 的路径，只支持 PNG/JPEG/WebP，并且必须在证据目录内。

```json
{
  "meta": {
    "title": "XX 页面 UI 验收",
    "design": "Figma: <文件名 / 画板范围>",
    "environment": "测试环境 https://example.test/xxx",
    "viewport": "1440×900 @2x",
    "tester": "验收人",
    "startedAt": "2026-10-14 10:00",
    "endedAt": "2026-10-14 10:40"
  },
  "boards": [
    {
      "id": "B-01",
      "name": "列表页",
      "state": "默认状态",
      "page": "https://example.test/list",
      "result": "有差异",
      "designShot": "design/B-01.png",
      "actualShot": "actual/B-01.jpeg",
      "note": "可选",
      "items": [
        {
          "id": "D-01",
          "severity": "明显",
          "element": "查询区右侧按钮",
          "property": "文案",
          "design": "配置通知",
          "actual": "通知配置",
          "note": "可选",
          "designShot": "design/D-01.png",
          "actualShot": "actual/D-01.jpeg"
        }
      ]
    }
  ],
  "notes": ["设计稿疑似笔误、字体回退、残留状态等说明"]
}
```

- `result`：`一致 / 有差异 / 未覆盖 / 受阻`。`未覆盖` 和 `受阻` 必须在 `note` 里写原因。
- `severity`：`阻断 / 明显 / 细微`。
- `result` 为 `有差异` 时至少要有一条 item；为 `一致` 时不能有 item。生成器会校验这两条。
- `id` 在所有画板和差异项之间都不能重复。
- 总结论由生成器计算：没有任何画板完成比对（`一致/有差异`）→ `BLOCKED`；否则只要有 `未覆盖/受阻` → `PARTIAL`；否则有差异 → `HAS_DIFF`；全部一致 → `PASSED`。
