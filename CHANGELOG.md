# 更新日志

## v0.3.0 (2026-05-26)

### 架构重构：跨平台代码共享化

将 `macos/` 和 `windows/` 中重复的代码提取到 `shared/`，各平台仅保留差异部分。

**Python 后端共享：**
- `shared/module/` 成为唯一的 Python 后端代码源，macos/windows 的 `module/` 副本已删除
- 平台 `module/main.py` 精简为入口委托：设置 `AUTO_CONTROLLER_ROOT` / `AUTO_CONTROLLER_SHARED_ROOT` 环境变量，然后 `runpy.run_path()` 执行 `shared/module/main.py`
- `shared/module/main.py` 支持双 modules 目录扫描（`shared/modules/` + 平台 `modules/`）
- `module_manager.py` 支持多目录查找，`_get_module_dirs()` 分离 code_dir（shared）和 config_dir（平台）
- `utils/paths.py` 优先读取 `AUTO_CONTROLLER_ROOT` 环境变量定位项目根目录

**业务模块共享：**
- `douyin/`、`jddj_orders/`、`monthly_report/` 的共享文件移入 `shared/modules/`
- 平台仅保留敏感配置（`config.json`、`config.yaml`）和平台特有模块
- Windows 独有 `inspection/`（点检）和 `xiaohongshu/`（小红书）模块保留在 `windows/modules/`

**Electron 前端共享：**
- 共享前端代码移入 `shared/packages/`：`python.ts`、`index.ts`、`App.vue`、`main.ts`、`api.ts`、`module.ts`、`Data.vue`、`Logs.vue`、vite 配置等
- `shared/packages/renderer/vite.config.ts` 使用 `process.cwd()` 动态定位平台根目录
- `@` 别名指向 `shared/packages/renderer/src`，`@platform` 指向平台 `packages/renderer/src`
- `@shared-main` 别名指向 `shared/packages/main/src`
- Vue 组件 import 路径统一为 `@/services/api`、`@/stores/module`
- Windows 前端将裸 `fetch()` 调用迁移至统一 `api.ts` 服务层

**构建配置共享：**
- `tsconfig.json`、`scripts/watch.mjs` 移入 `shared/`
- macos/windows 的 `package.json` 构建脚本引用 shared 的 vite 配置
- `electron-builder.yml` 映射 `../shared/module` → `module`，`../shared/modules` → `modules`

**版本号统一：** macOS 和 Windows 统一为 `0.3.0`

### 项目结构（重构后）

```
auto-huawei/
├── shared/                  # 跨平台共享代码
│   ├── module/              # Python 后端（唯一源）
│   ├── modules/             # 共享业务模块（douyin, jddj_orders, monthly_report）
│   ├── packages/            # 共享 Electron 前端
│   ├── scripts/             # 共享构建脚本
│   └── tsconfig.json
├── macos/                   # macOS 平台（仅保留差异）
│   ├── module/main.py       # 入口委托
│   ├── modules/             # 平台特有配置
│   ├── packages/            # 平台特有 Vue 组件
│   └── ...
└── windows/                 # Windows 平台（仅保留差异）
    ├── module/main.py       # 入口委托
    ├── modules/             # 平台特有模块（inspection, xiaohongshu）+ 配置
    ├── packages/            # 平台特有 Vue 组件
    └── ...
```

## v0.2.1 (2026-05-25)

### 安全加固

- **敏感凭据迁移至环境变量**：SMTP 授权码、发件邮箱、企业微信 Webhook、京东账号密码优先从环境变量读取，回退到配置文件
- **API 返回配置脱敏**：`GET /api/config/general` 对 `smtp_password`、`wechat_webhook` 等敏感字段返回 `********`，`PUT` 保存时跳过占位符
- **从 Git 移除已追踪的凭据文件**：`macos/config/general.yaml`（含 SMTP 授权码）、`modules/*/config.yaml` 取消 Git 追踪
- **补充 `.gitignore` 规则**：新增 `.env`、`*.local`、`*.tmp`、`.cache/`、`logs/`、`modules/*/config.yaml`、`.claude/` 等

### 配置体系整合

- **消除 `config.yaml` 与 `general.yaml` 的重复**：移除 `config.yaml` 中无效的 `notification` 块
- **统一 `general.yaml` 命名风格为 snake_case**：`smtpServer` → `smtp_server`、`notifyLevel` → `notify_level` 等
- **移除 Python 代码中的 camelCase 兼容**：`sender.py` 不再尝试旧键名
- **修复 SMTP 端口默认值冲突**：统一为 587（STARTTLS）
- **删除 Windows Config.vue 中无效的"通知设置"Tab**

### 配置读取优先级

```
环境变量 > general.yaml > 代码默认值
```

## v0.2.0 (2026-05-25)

### 关键 Bug 修复

- **修复 `check_paused` 逻辑反转**：原实现 `wait()` 在未暂停时阻塞，暂停时反而放行
- **重写 `task.py` 路由**：原路由调用不存在的 scheduler 方法，改为使用实际方法
- **修复 `save_module_config` 未定义变量**

### 安全加固

- **CORS 限制**：`allow_origins` 从 `["*"]` 改为仅允许本地
- **路径遍历防护**：`data.py` 增加文件名正则校验
- **配置写入 Schema 验证**：使用 Pydantic `GeneralConfigModel`
- **IPC 参数校验**：Electron IPC handler 增加 `validateSafeName()`

### 架构重构

- **提取共享工具函数**：`scheduler_utils.py`、`file_utils.py`
- **前端统一 API 服务层**：新建 `services/api.ts`
- **路由拆分**：`main.py` 从 238 行精简至 ~70 行
- **macOS/Windows 代码共享**：创建 `shared/module/` 公共代码目录
- **动态路径解析**：新建 `utils/paths.py`

## v0.1.3 (2026-05-20)

### 新增功能

- **测试执行模式（Dry Run）**：点击"测试执行"按钮时自动以测试模式运行
- **通知标题/内容自定义**：`TaskResult` 的 `notify_title` 和 `notify_content` 字段
- **邮件附件支持**：Notifier 支持在邮件中添加 CSV 文件附件

## v0.1.0 (2026-05-14)

### 初始版本

- 模块化架构：每个功能模块独立管理
- 可视化调度：任务等待中 → 排队中 → 运行中
- 灵活定时：支持每天、每周、间隔、自定义 cron
- 通知推送：支持企业微信 Webhook 和邮件通知
- 实时日志：前端实时显示任务执行日志
