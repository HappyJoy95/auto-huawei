# Auto Controller v0.1.1

自动化任务控制器 - 基于 Electron + Python 的模块化任务调度系统。

## 功能特性

- **模块化架构**：每个功能模块独立管理，包含配置、任务代码、采集器
- **可视化调度**：任务等待中 → 排队中 → 运行中的完整队列管理
- **灵活定时**：支持每天、每周、间隔、自定义 cron 表达式
- **通知推送**：支持企业微信 Webhook 和邮件通知，模块可自定义推送内容
- **实时日志**：前端实时显示任务执行日志
- **自定义设置**：模块可定义自己的设置表单和样式

## 项目结构

```
auto-controller/
├── packages/           # Electron 前端
│   ├── main/          # 主进程
│   ├── preload/       # 预加载脚本
│   └── renderer/      # Vue 3 渲染进程
├── module/            # Python 后端
│   ├── api/           # FastAPI 接口
│   ├── config/        # 配置管理
│   ├── core/          # 模块管理器
│   ├── notifier/      # 通知发送
│   └── tasks/         # 调度器
├── modules/           # 功能模块目录
│   ├── xiaohongshu/   # 小红书模块
│   ├── douyin/        # 抖音模块
│   ├── inspection/    # 巡检模块
│   └── jddj_orders/   # 京东到家订单模块
├── config/            # 全局配置
└── data/              # 数据存储
```

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+
- MuMu 模拟器（用于 ADB 相关模块）

### 安装依赖

```bash
# 安装 Node.js 依赖
npm install

# 安装 Python 依赖
pip install -r requirements.txt
```

### 启动应用

```bash
# 开发模式
./start.bat

# 或手动启动
# 1. 启动 Python 后端
python module/main.py

# 2. 启动 Electron 前端
npm run dev
```

### 构建生产版本

```bash
npm run build
```

## 使用说明

### 模块设置

1. 点击左侧导航栏选择模块
2. 设置「启用模块」开关
3. 选择定时执行方式：
   - **不定时**：手动设置执行时间
   - **每天**：指定时间执行
   - **每周**：指定星期和时间
   - **间隔**：指定间隔分钟数和生效时段
   - **自定义**：多个时间点组合

### 通知配置

**全局通知级别**（通用设置页面）：
- 全部通知：所有执行结果都通知
- 仅错误：只在失败时通知
- 不通知：关闭通知

**模块推送配置**（模块设置页面）：
- 启用推送：是否启用该模块的推送
- 推送方式：企业微信或邮箱
- 推送目标：Webhook 地址或邮箱地址

### 任务执行

- **等待中**：等待执行时间的任务
- **队列中**：时间到，排队等待执行
- **运行中**：正在执行的任务

## 模块开发

参见 [MODULE_DEVELOPMENT.md](./MODULE_DEVELOPMENT.md) 了解如何开发新模块。

## 技术栈

- **前端**：Vue 3 + Pinia + Vue Router + Arco Design
- **后端**：Python + FastAPI + APScheduler
- **桌面**：Electron
- **自动化**：Playwright + ADB

## License

MIT
