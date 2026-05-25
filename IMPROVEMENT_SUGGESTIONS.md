# Auto Controller 改进建议

> 基于当前代码状态复核后整理。本文档优先记录已确认的问题；推测性、过大范围的重构建议放到后续优化阶段，避免和阻断性 Bug 混在一起。

---

## 一、已确认的阻断性问题

这些问题会直接导致功能不可用或运行异常，建议优先处理，并且 macOS / Windows 两套代码需要同步确认。

| # | 问题 | 位置 | 说明 | 建议 |
|---|------|------|------|------|
| 1 | `task` 路由调用不存在的方法 | `macos/module/api/routes/task.py`、`windows/module/api/routes/task.py` | 路由中调用 `get_all_tasks()`、`run_task_async()`、`stop_task()`、`enable_task()`、`get_task_logs()`，但 `TaskQueueScheduler` 未实现这些方法。访问 `/api/tasks` 相关接口会失败。 | 要么补齐调度器方法，要么删除/改写这套路由，统一使用已有 `/api/scheduler/*` 接口。 |
| 2 | `check_paused()` 逻辑反转 | `module/tasks/base.py` | 当前实现 `self._pause_event.wait()` 会导致未暂停时阻塞、暂停时立即返回。 | 改成循环等待暂停状态清除，例如 `while self._pause_event.is_set(): time.sleep(...)`，并同时检查 stop 状态。 |
| 3 | `save_module_config` 直接引用全局 `scheduler` | `module/main.py` | 当前依赖 lifespan 中的 global 变量，正常启动后可能可用，但写法脆弱；测试、热重载或异常启动路径下可能出错。 | 改为和其他接口一致：通过 `get_scheduler()` 获取实例，判空后再 `reload_task()`。 |
| 4 | `Config.vue` 变量名拼写错误 | `packages/renderer/src/views/Config.vue` | `jddiConfig` 应为 `jddjConfig`，会导致运行时 `ReferenceError`。 | 统一替换为 `jddjConfig`。 |
| 5 | `Tasks.vue` 使用不存在的 `window.api` | `packages/renderer/src/views/Tasks.vue` | 当前项目其他地方主要使用 `fetch()` 或 `window.electronAPI`，`window.api` 未确认存在。 | 如果页面仍保留，改为统一 API 调用方式；如果是死页面，直接删除路由和组件。 |

---

## 二、安全问题

这些问题不一定马上影响本地单人使用，但如果应用暴露在局域网、浏览器或不可信渲染进程环境中，风险会放大。

| # | 问题 | 位置 | 风险 | 建议 |
|---|------|------|------|------|
| 1 | CORS 完全开放 | `module/main.py` | `allow_origins=["*"]` 允许任意网页向本地后端发请求，可能触发任务、读取数据或修改配置。 | 限制为 Electron 前端来源、本地开发地址，或增加本地 token 校验。 |
| 2 | 数据文件接口缺少文件名校验 | `module/api/routes/data.py` | `module_name`、`file_name` 未做白名单校验。虽然 FastAPI path 参数未必直接匹配带 `/` 的路径，但仍应防止路径穿越和非法文件名。 | 限制为已注册模块名；`file_name` 仅允许 `[a-zA-Z0-9_-]`；最终路径用 `resolve()` 确认仍在 `DATA_DIR/module_name` 下。 |
| 3 | 配置写入缺少 Schema 验证 | `module/api/routes/config.py`、`module/main.py` | 任意 dict 可写入配置文件，容易写入无效配置或覆盖敏感字段。 | 为全局配置、调度配置、模块配置分别定义 Pydantic model 或按 `settings.yaml` 字段做白名单过滤。 |
| 4 | IPC 参数缺少校验 | `packages/main/src/main.ts` | 渲染进程参数可直接拼接到请求或文件操作路径中，恶意渲染进程可扩大影响面。 | 所有 IPC handler 校验参数类型、枚举值和路径。 |
| 5 | 模块 CSS 直接注入 DOM | `ModuleSettings.vue` | 模块返回的 CSS 被直接插入页面，可伪造 UI、遮挡按钮、发起外链资源请求。 | 如果必须支持自定义样式，只允许受控 CSS 子集；或仅加载本地可信模块。 |
| 6 | 凭据明文存储 | `config/*.yaml`、模块配置文件 | SMTP 授权码、Webhook、账号密码可能以明文保存。 | 本地应用可先接受明文，但应避免提交到 git；后续可迁移到系统钥匙串或环境变量。 |

---

## 三、稳定性和线程安全问题

| # | 问题 | 位置 | 说明 | 建议 |
|---|------|------|------|------|
| 1 | `get_task_status()` 无锁读取共享状态 | `module/tasks/scheduler.py` | `running_tasks`、`queue_tasks`、`waiting_tasks` 会被后台线程修改，读取时没有锁。 | 用 `self._lock` 包住状态读取。 |
| 2 | 锁内执行文件 I/O | `module/tasks/scheduler.py::reload_task` | 持锁期间调用 `module_manager.load_module()` 读取 YAML/JSON，I/O 慢时会阻塞调度器。 | 先在锁外加载配置，再在锁内更新调度器状态。 |
| 3 | `queue_tasks` 使用普通 list | `module/tasks/scheduler.py` | 当前配合锁使用时还能工作，但多个位置读写不统一，容易产生竞态。 | 所有读写统一加锁；如果队列行为变复杂，再换 `deque` 或 `queue.Queue`。 |
| 4 | `except Exception: pass` 吞掉错误 | `module_manager.py`、`scheduler.py` | 配置解析、时间解析等错误会被静默忽略，排查困难。 | 记录 warning/error 日志；只捕获预期异常。 |
| 5 | 文件写入非原子 | `module_manager.py`、`config/config.py` | 保存配置时如果进程崩溃，可能留下半截 JSON/YAML。 | 写入临时文件后用 `replace()` 原子替换。 |

---

## 四、前端问题

| # | 问题 | 位置 | 说明 | 建议 |
|---|------|------|------|------|
| 1 | 缺少统一 API 服务层 | `packages/renderer/src` | 组件中散落 `fetch()`、`window.api`、`window.electronAPI`，错误处理不一致。 | 新增 `src/services/api.ts`，逐步迁移，不必一次性重写所有页面。 |
| 2 | HTTP 响应未统一检查 | 多个 Vue 组件 | 直接 `response.json()`，接口 4xx/5xx 时用户提示不稳定。 | API 服务层统一检查 `response.ok` 并抛出可读错误。 |
| 3 | 异常对象直接字符串拼接 | `ModuleDetail.vue`、`ModuleSettings.vue` | `'失败: ' + e` 可能显示 `[object Object]`。 | 使用 `e instanceof Error ? e.message : String(e)`。 |
| 4 | `ModuleSettings.vue` 体积过大 | `ModuleSettings.vue` | 同时负责调度、动态表单、测试执行、样式加载，后续维护成本高。 | 后续拆成 `SchedulerConfig.vue`、`ModuleConfigForm.vue`、`DynamicFieldRenderer.vue`。 |
| 5 | 1 秒轮询日志/状态 | `Dashboard.vue` 等 | 本地应用可用，但会增加后端压力和日志噪音。 | 短期可改为 3-5 秒；长期再考虑 WebSocket。 |
| 6 | `any` 类型较多 | 多个组件和 store | 类型保护不足，容易把后端字段名变更拖到运行时才暴露。 | 先为模块、调度状态、日志、配置响应定义核心接口。 |

---

## 五、代码重复和架构整理

这些不是第一优先级，建议在阻断 Bug 和安全底线修完后再做。

| # | 问题 | 位置 | 建议 |
|---|------|------|------|
| 1 | `_calculate_next_run` 重复 | `module_manager.py`、`scheduler.py` | 提取到 `module/utils/scheduler_utils.py`。 |
| 2 | 手动时间解析重复 | `module_manager.py`、`scheduler.py` | 提取 `parse_manual_time(time_str, now=None)`。 |
| 3 | `main.py` 承担过多路由 | `module/main.py` | 分批迁移到 `api/routes/modules.py`、`api/routes/scheduler.py`。 |
| 4 | macOS / Windows 核心代码重复 | `macos/module`、`windows/module` | 短期每次修改同步两边；长期抽成共享包或生成式同步。 |
| 5 | 全局状态较多 | `module_manager`、`_scheduler`、`_log_queue` | 当前可接受；后续用 FastAPI 依赖注入收敛。 |
| 6 | `sys.path` 运行时修改 | `main.py`、`loader.py` | 后续改成规范包结构，减少导入冲突。 |

---

## 六、低优先级优化

| # | 问题 | 建议 |
|---|------|------|
| 1 | `apscheduler>=3.10.0` 未限制上限 | 改为 `apscheduler>=3.10.0,<4.0.0`，避免未来安装 4.x 破坏 API。 |
| 2 | 混用 `print` 和自定义日志 | 统一到 Python `logging`，调度器日志只作为 UI 展示层。 |
| 3 | 日志 API 缺少过滤和分页 | 添加 `module`、`level`、`since`、`limit` 等参数。 |
| 4 | 邮件附件一次性读入内存 | 对附件大小设上限，或至少在发送前检查文件大小。 |
| 5 | Python 后端启动健康检查不足 | Electron 启动时轮询 `/api/health`，确认后端 ready 后再进入页面。 |
| 6 | 生产环境 DevTools | 确认打包版本不自动打开 DevTools。 |

---

## 七、推荐修复顺序

```text
阶段 1：修功能阻断
  1. 修复 check_paused 逻辑
  2. 修复/删除 task.py 中无效任务路由
  3. save_module_config 改用 get_scheduler()
  4. 修复 Config.vue 的 jddjConfig 拼写
  5. 修复或删除 Tasks.vue 的 window.api 调用

阶段 2：修安全底线
  1. 限制 CORS 或增加本地 token
  2. data.py 增加模块名和文件名校验
  3. 配置写入增加白名单 / Schema 验证
  4. IPC handler 增加参数校验
  5. 明确凭据文件不提交 git，后续考虑钥匙串

阶段 3：稳定性
  1. 调度器状态读写加锁
  2. reload_task 避免锁内 I/O
  3. 异常日志保留堆栈
  4. 配置文件原子写入

阶段 4：重构优化
  1. 提取调度时间工具函数
  2. 建立前端 API 服务层
  3. 拆分 ModuleSettings.vue
  4. main.py 路由迁移到 routes/
  5. macOS / Windows 核心代码共享化
```

---

## 八、备注

- 本文档中的路径多以 macOS 版本为例；实际修复时需要同步检查 Windows 版本。
- 部分旧页面如 `Config.vue`、`Tasks.vue` 可能已经不在主导航中使用。如果确认是死代码，删除比修复更好。
- 不建议一次性做大重构；先修能复现的问题，再逐步收敛架构。
