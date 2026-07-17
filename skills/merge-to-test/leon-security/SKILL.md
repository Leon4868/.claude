---
name: leon-security
description: 安全扫描 Skill，基于 METATRON 对部署目标执行自动化渗透测试和漏洞检测（nmap/nikto 等），仅用于授权范围内的自有目标
---

# leon-security — 安全扫描 Skill

基于 [METATRON](https://github.com/sooryathejas/METATRON) 的安全扫描 skill，对部署目标执行自动化渗透测试和漏洞检测。

## 调用方式

```text
调用 leon-security skill，扫描 192.168.1.100
调用 leon-security skill，扫描 example.com
调用 leon-security skill，扫描 example.com，使用 nmap+nikto
```

## 执行流程

### 1. 环境检查

依次检查以下依赖是否就绪，任一缺失则报错并给出安装指引：

| 依赖 | 检查命令 | 安装方式 |
|------|---------|---------|
| Python 3 | `python3 --version` | 系统自带或 brew install python |
| Ollama | `ollama --version` | `brew install ollama` |
| metatron-qwen 模型 | `ollama list \| grep metatron-qwen` | `ollama pull metatron-qwen` |
| MariaDB | `mariadb --version` | `brew install mariadb` |
| nmap | `nmap --version` | `brew install nmap` |
| nikto | `nikto -Version` | `brew install nikto` |
| METATRON 代码 | 检查 `~/.metatron/metatron.py` | `git clone https://github.com/sooryathejas/METATRON ~/.metatron` |

如果是首次运行，自动执行：

```bash
cd ~/.metatron && pip install -r requirements.txt
```

### 2. 启动依赖服务

```bash
# 确保 Ollama 运行中
ollama serve &>/dev/null &

# 确保 MariaDB 运行中
brew services start mariadb
```

### 3. 解析输入

从用户输入中提取：

- **目标**（必须）：IP 地址或域名
- **工具选择**（可选）：指定使用哪些扫描工具，默认全部

支持的扫描工具：

| 工具 | 用途 | 速度 |
|------|------|------|
| nmap | 端口扫描、服务识别 | 快 |
| whois | 域名信息查询 | 快 |
| whatweb | Web 技术识别 | 快 |
| curl | HTTP 头分析 | 快 |
| dig | DNS 查询 | 快 |
| nikto | Web 漏洞扫描 | 慢 |

### 4. 执行扫描

通过 Bash 调用 METATRON，传入目标和工具选择：

```bash
cd ~/.metatron && python3 metatron.py
```

METATRON 是交互式 CLI，需要通过 stdin 传入选项：

- 选择侦察模式
- 输入目标 IP/域名
- 选择扫描工具
- 等待扫描 + AI 分析完成

METATRON 内部的 Agentic Loop 会自行决定是否追加扫描，无需外部干预。

扫描可能耗时较长（尤其包含 nikto 时），使用后台执行并在完成后通知用户。

### 5. 收集结果

扫描完成后：

- 从 MariaDB 查询本次扫描结果
- 导出 PDF/HTML 报告（如 METATRON 支持）
- 将报告保存到 specs 目录或用户指定路径

### 6. 输出报告

```text
🔒 安全扫描完成 — {目标}

扫描工具: {使用的工具列表}
耗时: {时间}

发现摘要:
- 🔴 高危: {N} 个
- 🟡 中危: {N} 个
- 🟢 低危: {N} 个

关键发现:
1. {漏洞描述} — {修复建议}
2. {漏洞描述} — {修复建议}

完整报告: {报告文件路径}
```

如发现高危漏洞，醒目提示并建议修复优先级。

---

## 与 leon:ai 的分工

| 检查类型 | 负责方 | 时机 |
|----------|--------|------|
| 硬编码密钥/token、.env 误提交、敏感文件入库 | leon:ai（每个 task 的 Step 3） | 开发过程中 |
| 端口扫描、Web 漏洞检测、渗透测试 | leon-security（本 skill） | 项目部署后 |

## 设计决策

**为什么是 Skill 而不是 Agent：**

- METATRON 本身是 CLI 工具，给目标就跑，不需要多轮推理决策
- METATRON 内置 Agentic Loop（AI 自行决定是否追加扫描），不需要再套一层 Agent
- 扫描耗时长，Agent 长时间占上下文是浪费
- Skill 封装更轻量：环境检查 → 启动扫描 → 等待 → 返回报告
