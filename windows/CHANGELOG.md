# 更新日志 (Windows)

## v0.3.0 (2026-05-26)

### 架构重构：跨平台代码共享化

- Python 后端代码移至 `shared/module/`，本目录仅保留 `module/main.py` 入口委托
- 共享业务模块（douyin, jddj_orders, monthly_report）移至 `shared/modules/`
- 共享 Electron 前端代码移至 `shared/packages/`
- 前端将裸 `fetch()` 调用迁移至统一 `api.ts` 服务层
- 构建脚本引用 shared 的 vite 配置和 watch 脚本
- 版本号统一为 0.3.0

## v0.2.1 (2026-05-25)

### 安全加固

- 敏感凭据迁移至环境变量
- API 返回配置脱敏
- 从 Git 移除已追踪的凭据文件

### 配置体系整合

- 消除 `config.yaml` 与 `general.yaml` 的重复
- 统一 `general.yaml` 命名风格为 snake_case
- 删除 Config.vue 中无效的"通知设置"Tab

## v0.2.0 (2026-05-25)

- 修复 `check_paused` 逻辑反转
- 重写 `task.py` 路由
- CORS 限制、路径遍历防护
- 前端统一 API 服务层
- 路由拆分

## v0.1.1 (2026-05-19)

- 模块设置页面支持自定义样式
- 推送内容显示变化的数据详情
- 点检模块推送内容简化
- ADB 端口改为全局配置
- 修复定时配置加载问题

## v0.1.0 (2026-05-14)

- 初始版本
