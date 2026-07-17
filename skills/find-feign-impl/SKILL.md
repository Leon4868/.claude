---
name: find-feign-impl
description: 根据 FeignClient 接口定义查找对应的 Controller 实现的定位方法。包含识别 FeignClient、获取服务名、获取 URL 路径、定位目标服务代码的完整步骤。适用于需要从 Feign Client 接口快速定位到实际 Controller 实现的场景。
---

# Feign 实现查找

本 Skill 提供根据 FeignClient 接口定义查找对应的 Controller 实现的方法。

## 使用方式

当需要找到 FeignClient 接口对应的 Controller 实现时，参考以下步骤。

## 执行步骤

### 1. 识别 FeignClient
打开你关注的 Feign Client 接口文件（通常带有 `@FeignClient` 注解）。

### 2. 获取服务名
查看 `@FeignClient` 注解的 `value` 或 `name` 属性。

例如：
- `@FeignClient(value = "ai-flow-server")` -> 服务名为 `ai-flow-server`

### 3. 获取 URL 路径
查看接口方法的 `@PostMapping`, `@GetMapping` 等注解中的 URL 路径。

例如：
- `@PostMapping("/importCallTask")` -> 路径为 `/importCallTask`

### 4. 定位目标服务代码

1. 使用文件列表或文件树浏览，找到与服务名对应的模块目录（例如 `ai-flow/ai-flow-server`）
2. 在目标模块目录中，使用代码搜索工具搜索 URL 路径
3. 或者搜索实现了该 Feign Client 接口的 Controller 类（如果 Controller 实现了接口）
