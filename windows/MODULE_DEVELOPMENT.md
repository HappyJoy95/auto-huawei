# 模块开发指南

本文档面向 AI 开发工具，说明如何为 Auto Controller 开发新模块。

## 模块目录结构

每个模块位于 `modules/<module_name>/` 目录下：

```
modules/<module_name>/
├── meta.yaml        # 模块元信息（必需）
├── settings.yaml    # 设置表单定义（必需）
├── settings.css     # 自定义样式（可选）
├── config.yaml      # 调度器配置（运行时生成）
├── config.json      # 模块配置值（运行时生成）
├── task.py          # 任务主程序（必需）
└── *.py             # 功能模块（可选，按需组织）
```

**文件说明**：
- `task.py`：模块主程序入口，定义任务执行流程
- `settings.yaml`：定义模块在前端的配置表单
- `settings.css`：自定义设置页面样式（可选）
- 其他 `.py` 文件：功能模块，由 `task.py` 调用，按项目需要自由组织

## 文件说明

### meta.yaml - 模块元信息

```yaml
name: module_name              # 模块标识（英文，与目录名一致）
display_name: 模块显示名称      # 中文显示名
description: 模块功能描述       # 简要描述
icon: apps                     # 图标名称（Arco Design 图标）
```

### settings.yaml - 设置表单定义

定义模块在前端的配置表单：

```yaml
fields:
  # 文本输入
  - key: username
    label: 用户名
    type: text
    placeholder: "请输入用户名"
    default: ""
    hint: "提示文字"
    width: "200px"           # 可选，设置输入框宽度

  # 密码输入
  - key: password
    label: 密码
    type: password

  # 数字输入
  - key: max_count
    label: 最大数量
    type: number
    default: 100
    min: 1
    max: 1000

  # 开关
  - key: enabled
    label: 启用
    type: switch
    default: false

  # 下拉选择
  - key: mode
    label: 模式
    type: select
    default: "auto"
    options:
      - value: "auto"
        label: "自动"
      - value: "manual"
        label: "手动"

  # 复选框组
  - key: target_status
    label: 目标状态
    type: checkbox
    default: ["pending"]
    options:
      - value: "pending"
        label: "待处理"
      - value: "completed"
        label: "已完成"

  # 文本列表
  - key: stores
    label: 门店列表
    type: list
    default: []

  # 对象列表
  - key: accounts
    label: 账号列表
    type: object_list
    default: []
    fields:
      - key: name
        label: 名称
        type: text
        width: "200px"       # 可选，设置输入框宽度
      - key: url
        label: 链接
        type: text

  # 推送配置（标准字段，建议保留）
  - key: notify_enabled
    label: 启用推送
    type: switch
    default: false

  - key: notify_type
    label: 推送方式
    type: select
    default: "wechat"
    show_if: "notify_enabled"
    options:
      - value: "wechat"
        label: "企业微信"
      - value: "email"
        label: "邮箱"

  - key: notify_target
    label: 推送目标
    type: text
    show_if: "notify_enabled"
    placeholder: "Webhook URL 或邮箱地址"
```

### settings.css - 自定义样式（可选）

模块可以放置 CSS 文件自定义设置页面样式：

```css
/* 示例：调整对象列表输入框宽度 */
.module-settings .array-item input:nth-child(1) {
  width: 320px;
}

.module-settings .array-item input:nth-child(2) {
  width: 130px;
}
```

### task.py - 任务执行代码

必须继承 `BaseTask` 类：

```python
from module.tasks.base import BaseTask, TaskResult, TaskStatus
from datetime import datetime

class MyTask(BaseTask):
    """任务类"""

    task_id = "module_name"      # 必须与目录名一致
    task_name = "任务显示名称"

    def run(self) -> TaskResult:
        """执行任务"""
        start_time = datetime.now()

        try:
            # 更新进度
            self.update_progress(10, "开始执行...")
            self.log("INFO", "这是一条日志")

            # 获取配置
            config_value = self.config.get("config_key")

            # 检查是否被停止
            if self.check_stopped():
                return TaskResult(
                    success=False,
                    message="任务被停止",
                    start_time=start_time,
                    end_time=datetime.now()
                )

            # 执行业务逻辑
            self.update_progress(50, "处理中...")
            result = self.do_something()

            self.update_progress(100, "完成")

            return TaskResult(
                success=True,
                message=f"执行成功，处理了 {result} 条数据",
                data={"count": result},
                start_time=start_time,
                end_time=datetime.now(),
                # 可选：自定义通知内容
                notify_title="采集完成",
                notify_content=f"处理数据: {result} 条"
            )

        except Exception as e:
            return TaskResult(
                success=False,
                message=f"执行失败: {str(e)}",
                error=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )

    def do_something(self):
        """业务逻辑"""
        pass
```

## 调度器接口

### BaseTask 类方法

| 方法 | 说明 |
|------|------|
| `run()` | 主执行方法，必须实现，返回 TaskResult |
| `update_progress(progress, message)` | 更新进度 (0-100) |
| `log(level, message)` | 输出日志到调度器 |
| `check_stopped()` | 检查任务是否被停止 |
| `stop()` | 停止任务 |

### TaskResult 返回值

```python
TaskResult(
    success=True/False,           # 是否成功
    message="结果消息",            # 结果描述
    data={"key": "value"},        # 可选：返回数据
    error="错误信息",              # 可选：错误详情
    start_time=datetime.now(),
    end_time=datetime.now(),
    # 通知内容（可选，模块可自定义推送内容）
    notify_title="通知标题",       # 自定义通知标题
    notify_content="通知正文"      # 自定义通知内容（支持 Markdown）
)
```

### 自定义通知内容

模块可以自定义推送内容，只需在 TaskResult 中设置 `notify_title` 和 `notify_content`：

```python
return TaskResult(
    success=True,
    message="采集完成",
    notify_title="📊 采集报告",
    notify_content="""
共 25 条记录，新增 1 条

**青岛城阳万达店**  月度2次/100分
**青岛城阳万象汇店**  月度1次/100分

⏰ 05-18 19:30
"""
)
```

如果模块不提供 `notify_title` 和 `notify_content`，调度器会自动生成默认通知内容。

## 配置访问

```python
# 获取模块配置
value = self.config.get("config_key")

# 获取全局配置
from module.config.config import Config
adb_port = Config.get_adb_port()
```

## 数据存储

采集数据存储在 `data/` 目录，与模块配置分离：

```python
from module.config.config import DATA_DIR

data_file = DATA_DIR / "inspection_data.json"
```

## 通知系统

通知由调度器统一处理，模块无需关心。配置 `notify_enabled`、`notify_type`、`notify_target` 即可。

通知级别（全局设置）：
- `all`: 全部通知
- `error`: 仅错误时通知
- `none`: 不通知

## 全局配置文件

### config/general.yaml

```yaml
# 通知设置
notify_level: "all"

# 邮箱配置
smtp_server: "smtp.qq.com"
smtp_port: 465
smtp_user: "your@email.com"
smtp_password: "授权码"

# 调度器设置
check_interval: 10
retry_count: 3
task_timeout: 30
concurrency: 1

# 模拟器设置
adb_address: "127.0.0.1:16448"
emulator_type: "mumu"
headless: true
```

## API 接口

### 模块管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/modules` | GET | 获取模块列表 |
| `/api/modules/{name}/configs` | GET | 获取模块配置 |
| `/api/modules/{name}/scheduler-config` | PUT | 保存调度配置 |
| `/api/modules/{name}/module-config` | PUT | 保存模块配置 |
| `/api/modules/{name}/style` | GET | 获取模块自定义样式 |

### 调度器

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/scheduler/status` | GET | 获取调度器状态 |
| `/api/scheduler/task/{name}/run-now` | POST | 立即执行任务 |
| `/api/logs` | GET | 获取运行日志 |

### 配置

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/config/general` | GET | 获取通用配置 |
| `/api/config/general` | PUT | 保存通用配置 |

## 开发新模块步骤

1. 在 `modules/` 下创建模块目录
2. 编写 `meta.yaml` 定义模块信息
3. 编写 `settings.yaml` 定义配置表单
4. （可选）编写 `settings.css` 自定义样式
5. 编写 `task.py` 实现任务逻辑
6. （可选）编写其他 `.py` 实现采集逻辑
7. 重启应用，模块自动加载

## 注意事项

1. `task_id` 必须与模块目录名一致
2. 不要在模块中直接调用通知，由调度器统一处理
3. 使用 `self.log()` 输出日志会显示在前端
4. 长时间任务定期检查 `check_stopped()` 支持中断
5. ADB 端口使用全局配置，不在模块中单独配置
6. 采集数据存储在 `data/` 目录，与模块配置分离
