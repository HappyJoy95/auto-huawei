# 更新日志

## v0.2.0 (2026-05-25)

### 关键 Bug 修复

- **修复 `check_paused` 逻辑反转**：原实现 `wait()` 在未暂停时阻塞，暂停时反而放行，现已修正
- **重写 `task.py` 路由**：原路由调用不存在的 scheduler 方法（`get_all_tasks`、`run_task_async` 等），改为使用实际方法
- **修复 `save_module_config` 未定义变量**：原代码引用未定义的 `scheduler` 变量，改用 `get_scheduler()`
- **删除死代码**：移除未注册路由的 `Config.vue` 和使用不存在 `window.api` 的 `Tasks.vue`

### 安全加固

- **CORS 限制**：`allow_origins` 从 `["*"]` 改为仅允许本地 `localhost:5001` / `127.0.0.1:5001`
- **路径遍历防护**：`data.py` 增加文件名正则校验和 `resolve().is_relative_to()` 检查
- **配置写入 Schema 验证**：`save_general_config` 使用 Pydantic `GeneralConfigModel` 替代原始 `Dict[str, Any]`
- **IPC 参数校验**：Electron IPC handler 增加 `validateSafeName()` 防止注入
- **凭据文件排除**：`config/general.yaml`、`**/config.json` 加入 `.gitignore`

### 稳定性修复

- **调度器状态读取加锁**：`get_task_status()` 增加 `with self._lock:` 保证线程安全
- **避免锁内 I/O**：`reload_task()` 将 `load_module()` 移到锁外，仅状态更新在锁内
- **消除静默吞异常**：`except Exception: pass` 改为 `except (ValueError, IndexError) as e: add_log("WARNING", ...)`
- **配置文件原子写入**：使用 `tempfile` + `os.replace()` 防止写入中断导致文件损坏

### 架构重构

- **提取共享工具函数**：`scheduler_utils.py`（`calculate_next_run`、`parse_manual_time`）和 `file_utils.py`（`atomic_write`），消除 ~200 行重复代码
- **前端统一 API 服务层**：新建 `services/api.ts`，所有 `fetch()` 调用迁移至统一接口，Dashboard 轮询从 1s 改为 3s
- **路由拆分**：`main.py` 中模块/调度器路由迁移到 `routes/modules.py` + `routes/scheduler.py`，main.py 从 238 行精简至 ~70 行
- **macOS/Windows 代码共享**：创建 `shared/module/` 公共代码目录，`main.py` 通过 `sys.path` 优先导入
- **动态路径解析**：新建 `utils/paths.py`（`get_project_root()`），解决 shared/ 下 `__file__` 路径指向不存在目录的问题
- **进程精确停止**：`stop.sh` / `stop.bat` 移除 `pkill` / `taskkill /IM` 通配杀进程，改为 PID 文件 + 路径校验精确停止

### 文件变更

| 文件 | 变更 |
|---|---|
| `macos/module/tasks/base.py` | 修复 check_paused 逻辑 |
| `macos/module/api/routes/task.py` | 重写路由使用实际 scheduler 方法 |
| `macos/module/main.py` | CORS 限制 + 路由拆分 + shared sys.path |
| `macos/module/api/routes/data.py` | 文件名校验 + 路径遍历防护 |
| `macos/module/api/routes/config.py` | Pydantic Schema 验证 + 动态路径 |
| `macos/module/api/routes/modules.py` | 新增：模块管理路由 |
| `macos/module/api/routes/scheduler.py` | 新增：调度器路由 |
| `macos/module/core/module_manager.py` | 共享工具函数 + 原子写入 + 动态路径 |
| `macos/module/tasks/scheduler.py` | 加锁 + 锁外I/O + 日志记录 + 共享工具函数 |
| `macos/module/config/config.py` | 动态路径解析 |
| `macos/module/notifier/sender.py` | 动态路径解析 |
| `macos/module/utils/paths.py` | 新增：动态项目根目录查找 |
| `macos/module/utils/scheduler_utils.py` | 新增：共享调度时间计算 |
| `macos/module/utils/file_utils.py` | 新增：原子写入 |
| `macos/packages/main/src/main.ts` | IPC 参数校验 + 静态 import + before-quit |
| `macos/packages/renderer/src/services/api.ts` | 新增：统一 API 服务层 |
| `macos/packages/renderer/src/components/LogPanel.vue` | 新增：通用日志面板组件 |
| `macos/packages/renderer/src/views/Dashboard.vue` | 迁移至 api 服务层 |
| `macos/packages/renderer/src/views/General.vue` | 迁移至 api 服务层 |
| `macos/packages/renderer/src/views/ModuleDetail.vue` | 迁移至 api 服务层 |
| `macos/packages/renderer/src/views/ModuleSettings.vue` | 迁移至 api 服务层 |
| `macos/stop.sh` | 精确停止进程 |
| `windows/stop.bat` | 精确停止进程 |
| `shared/module/` | 新增：macOS/Windows 共享 Python 代码 |
| `.gitignore` | 排除凭据文件 |

> Windows 平台所有对应文件同步修改。

## v0.1.3 (2026-05-20)

### 新增功能

#### 测试执行模式（所有模块）
- **测试模式（Dry Run）**：点击模块详情页的"测试执行"按钮时，自动以测试模式运行，不会写入数据文件
- 调度器层自动传递 `mode=test` 参数，BaseTask 提供 `dry_run` 属性供模块判断
- 测试模式下通知标题标记 `[测试]`，方便区分测试与实际执行
- 已在 **门店点检（inspection）** 模块实现，其余模块可简单通过 `self.dry_run` 接入

#### 通知优化
- **通知标题/内容自定义**：`TaskResult` 的 `notify_title` 和 `notify_content` 字段现在能正确发送
- **邮件附件支持**：Notifier 支持在邮件中添加 CSV 文件附件
- **小红书/抖音新增内容附件**：执行完成后自动生成 CSV 附件，仅包含本次新增的帖子/视频，含点赞数
  - 小红书：`xiaohongshu_new_日期.csv`，字段：门店名称、标题、点赞数、发布时间、采集时间
  - 抖音：`douyin_new_日期.csv`，字段：门店名称、标题、点赞数、视频链接、采集时间

#### 门店点检模块改进
- **通知显示变化详情**：通知内容显示具体新增/变化门店及月度数据
- 新增门店标记 `(新)`，有年度变化的门店单独列出

### 技术改进
- **Config 类新增 `get_adb_port()`**：统一获取 ADB 端口配置
- **跨平台同步**：所有改动同步至 Windows 和 macOS 平台
- **调度器架构优化**：测试模式、通知传递等逻辑集中在调度器层，减少模块重复代码

### 修复
- 修复 `Config.get_adb_port()` 不存在导致的 AttributeError
- 修复 `TaskResult` 缺少 `notify_title`/`notify_content` 字段导致的 TypeError

### 文件变更

| 文件 | 变更 |
|---|---|
| `windows/module/config/config.py` | 新增 `get_adb_port()` |
| `macos/module/config/config.py` | 新增 `get_adb_port()` |
| `windows/module/tasks/base.py` | TaskResult 新增 `attachment_path`；BaseTask 新增 `dry_run` 属性 |
| `macos/module/tasks/base.py` | 同上 |
| `windows/module/tasks/scheduler.py` | `run_now` 支持 mode 参数；通知传递 title/content/attachment |
| `macos/module/tasks/scheduler.py` | 同上 |
| `windows/module/main.py` | API 接受 mode 查询参数 |
| `macos/module/main.py` | 同上 |
| `windows/module/notifier/sender.py` | 邮件附件支持；notify_task_result 使用自定义标题/内容 |
| `macos/module/notifier/sender.py` | 同上 |
| `windows/modules/inspection/task.py` | 测试模式 dry_run；通知格式优化 |
| `windows/modules/inspection/scraper.py` | 支持 dry_run 跳过文件写入 |
| `windows/modules/xiaohongshu/task.py` | 采集后生成新增帖子 CSV 附件 |
| `windows/modules/douyin/task.py` | 采集后生成新增视频 CSV 附件 |
| `windows/.../ModuleSettings.vue` | 测试执行按钮传 `mode=test` 参数 |