---
name: find-service-by-url
description: 根据请求 URL 查找对应的微服务工程和代码位置的映射规则。包含 company-aggre、data-center、ai-admin、ai-decision-system 等服务的 URL 识别规则和 Controller 映射方法。适用于需要从请求 URL 快速定位到对应微服务工程的场景。
---

# URL 查找微服务

本 Skill 提供根据请求 URL 查找对应的微服务工程和代码位置的映射规则。

## 使用方式

当需要根据请求 URL 定位到对应的微服务工程时，参考以下映射规则。

## URL 映射规则

### company-aggre 服务
- **URL 模式**: 包含 `/company-aggre/`
- **示例**: `http://gateway.test.k8s.com:31962/company-aggre/subject/page`
- **对应服务**: `company-aggre`
- **代码位置**: `company-aggre` 项目根目录下查找代码

### data-center 服务
- **URL 模式**: 包含 `/data-center/`
- **示例**: `http://gateway.test.k8s.com:31962/data-center/data/page`
- **对应服务**: `data-center`
- **代码位置**: `data-center` 项目根目录下查找代码

### ai-admin 服务
- **URL 模式**: 包含 `admin.test.k8s.com/api/`
- **对应服务**: `ai-admin` (通常在 `ai` 大库下)
- **代码位置**: `ai-admin/src/main/java/pro/ai94/admin/controller` 目录
- **映射规则**: URL 路径 `/api/{controller}/{method}` 映射到 `{Controller}Controller#{method}`
  - 注意 Controller 名称可能带有 `Ai` 前缀
- **示例**:
  - `http://admin.test.k8s.com/api/aiCompany/consumeList` -> `pro.ai94.admin.controller.AiCompanyController#consumeList`
  - `http://admin.test.k8s.com/api/aiCompany/consumeCharts` -> `pro.ai94.admin.controller.AiCompanyController#consumeCharts`

### ai-decision-system 服务
- **URL 模式**: 包含 `decision.test.k8s.com/api/`
- **对应服务**: `ai-decision-system` (通常在 `ai` 大库下)
- **代码位置**: `ai-decision-system/src/main/java/com/tkylin/ycloud/admin/controller` 目录
- **映射规则**: URL 路径 `/api/{controller}/{method}` 映射到 `{Controller}Controller#{method}`
  - 注意 Controller 名称可能带有 `Ai` 前缀
- **示例**:
  - `http://decision.test.k8s.com/api/task/list` -> `com.tkylin.ycloud.admin.controller.AiTaskController#list`
