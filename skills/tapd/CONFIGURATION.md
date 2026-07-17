# TAPD Skill 配置指南

## 快速开始

### 0. 初始化配置（推荐）

**首次使用时，运行初始化脚本进行交互式配置：**

```bash
cd ~/.claude/skills/tapd/scripts
python init_config.py
```

初始化脚本会询问：
- 项目代码根目录（默认：当前目录的父目录）
- 项目类型（frontend/backend/fullstack）
- 需求文档存放目录（默认：~/tapd-requirements）

完成后会生成环境变量设置命令，复制到你的 shell 配置文件即可。

### 1. 设置 TAPD Token

```bash
# Linux/Mac
export TAPD_TOKEN="your_token_here"

# Windows PowerShell
$env:TAPD_TOKEN="your_token_here"
```

### 2. 配置需求文档目录

**选项 A：使用交互式向导（推荐）**

```bash
cd ~/.claude/skills/tapd/scripts
python setup_path.py
```

向导会：
- 让您选择默认路径或自定义路径
- 自动创建目录
- 提供环境变量设置命令

**选项 B：手动设置环境变量**

```bash
# Linux/Mac
export PROJECT_ROOT_DIR="/path/to/your/project"
export PROJECT_TYPE="backend"  # 或 frontend / fullstack
export TAPD_REQUIREMENTS_DIR="/your/custom/path"

# Windows PowerShell
$env:PROJECT_ROOT_DIR="D:\YourProject"
$env:PROJECT_TYPE="backend"  # 或 frontend / fullstack
$env:TAPD_REQUIREMENTS_DIR="D:\YourPath"
```

**选项 C：使用默认路径**

如果不设置环境变量，将使用默认值：
- `PROJECT_TYPE`: backend
- `TAPD_REQUIREMENTS_DIR`: ~/tapd-requirements
- `PROJECT_ROOT_DIR`: 需要手动设置

## 配置原理

### 环境变量列表

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `PROJECT_ROOT_DIR` | 项目代码根目录 | 无（必须设置） |
| `PROJECT_TYPE` | 项目类型（frontend/backend/fullstack） | backend |
| `TAPD_REQUIREMENTS_DIR` | 需求文档存放目录 | ~/tapd-requirements |

### 环境变量优先级

1. 环境变量（最高优先级）
2. 配置文件中的默认值

### 配置文件格式

`config/tapd_config.yaml`:

```yaml
project:
  # 项目代码根目录（可通过环境变量 PROJECT_ROOT_DIR 覆盖）
  root_dir: "${PROJECT_ROOT_DIR}"

  # 项目类型：frontend / backend / fullstack
  type: "${PROJECT_TYPE:backend}"

requirement_doc:
  # 支持环境变量替换：${ENV_VAR:default_value}
  root_dir: "${TAPD_REQUIREMENTS_DIR:~/tapd-requirements}"
  dir_format: "{story_id}_{story_name_short}_{date}"
  max_name_length: 20
```

### 路径展开规则

- `~` 会自动展开为用户主目录
- 环境变量会在配置加载时替换
- 如果目录不存在，会自动创建

## 常见场景

### 场景 1：团队共享配置

团队成员可以使用不同的本地路径：

```bash
# 开发者 A
export TAPD_REQUIREMENTS_DIR="/Users/alice/work/tapd-docs"

# 开发者 B
export TAPD_REQUIREMENTS_DIR="/Users/bob/projects/tapd"
```

### 场景 2：多项目隔离

为不同项目使用不同的需求文档目录：

```bash
# 项目 A
export TAPD_REQUIREMENTS_DIR="/path/to/project-a/requirements"

# 项目 B
export TAPD_REQUIREMENTS_DIR="/path/to/project-b/requirements"
```

### 场景 3：持久化配置

将环境变量添加到 shell 配置文件：

```bash
# Linux/Mac: 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export TAPD_REQUIREMENTS_DIR="/your/path"' >> ~/.bashrc

# Windows PowerShell: 添加到 $PROFILE
Add-Content $PROFILE '$env:TAPD_REQUIREMENTS_DIR="D:\YourPath"'
```

## 验证配置

运行以下命令验证配置是否正确：

```bash
cd ~/.claude/skills/tapd/scripts
python -c "
from core.config_manager import get_config_manager
config = get_config_manager().get_requirement_doc_config()
print('需求文档目录:', config['requirement_doc']['root_dir'])
"
```

## 故障排查

### 问题：路径不存在

**症状**：脚本报错找不到目录

**解决**：
1. 检查环境变量是否正确设置：`echo $TAPD_REQUIREMENTS_DIR`
2. 确保路径存在或让脚本自动创建
3. 运行 `python setup_path.py` 重新配置

### 问题：权限不足

**症状**：无法创建目录或文件

**解决**：
1. 检查目录权限：`ls -la /path/to/parent`
2. 使用有写权限的目录
3. 或修改目录权限：`chmod 755 /path/to/dir`

### 问题：中文乱码

**症状**：Windows 命令行显示乱码

**解决**：
- 已在脚本中设置 UTF-8 编码
- 如仍有问题，使用 PowerShell 而非 CMD
- 或设置 `chcp 65001` 切换到 UTF-8

## 最佳实践

1. **使用环境变量**：便于团队协作和多环境管理
2. **持久化配置**：将环境变量添加到 shell 配置文件
3. **定期备份**：需求文档目录应纳入版本控制或定期备份
4. **统一命名**：遵循配置的目录命名格式
5. **权限管理**：确保目录有适当的读写权限
