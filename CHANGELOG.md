# 更新日志

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