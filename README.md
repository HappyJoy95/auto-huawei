# Auto Controller

自动化任务控制器 - 基于 Electron + Python 的模块化任务调度系统。

## 项目结构

```
auto-huawei/
├── shared/                  # 跨平台共享代码
│   ├── module/              # Python 后端（FastAPI + APScheduler）
│   ├── modules/             # 共享业务模块（douyin, jddj_orders, monthly_report）
│   ├── packages/            # 共享 Electron 前端（Vue 3 + Arco Design）
│   ├── scripts/             # 共享构建脚本
│   └── tsconfig.json        # 共享 TypeScript 配置
├── macos/                   # macOS 平台（仅保留差异部分）
│   ├── module/main.py       # Python 入口委托
│   ├── modules/             # 平台特有配置
│   ├── packages/            # 平台特有 Vue 组件
│   ├── config/              # 配置文件
│   └── *.sh                 # Shell 脚本
└── windows/                 # Windows 平台（仅保留差异部分）
    ├── module/main.py       # Python 入口委托
    ├── modules/             # 平台特有模块（inspection, xiaohongshu）+ 配置
    ├── packages/            # 平台特有 Vue 组件
    ├── config/              # 配置文件
    └── *.bat                # Batch 脚本
```

## 架构说明

项目采用 **shared + platform** 架构：

- `shared/` 存放所有跨平台共享代码，是唯一的共享代码源
- `macos/` 和 `windows/` 仅保留平台差异部分（脚本、特有模块、特有 UI 组件）
- Python 入口通过环境变量 `AUTO_CONTROLLER_ROOT` / `AUTO_CONTROLLER_SHARED_ROOT` 定位路径，委托给 `shared/module/main.py`
- 业务模块从 `shared/modules/` 和平台 `modules/` 双目录加载，共享模块提供代码，平台目录提供配置

## 功能特性

- **模块化架构**：每个功能模块独立管理，包含配置、任务代码
- **可视化调度**：任务等待中 → 排队中 → 运行中
- **灵活定时**：支持每天、每周、间隔、自定义 cron
- **通知推送**：支持企业微信 Webhook 和邮件通知
- **实时日志**：前端实时显示任务执行日志
- **自定义设置**：模块可定义自己的设置表单和样式

## 业务模块

| 模块 | 位置 | 说明 |
|------|------|------|
| douyin | shared | 抖音数据采集 |
| jddj_orders | shared | 京东到家订单同步 |
| monthly_report | shared | 月报生成 |
| inspection | windows | 门店点检（ADB） |
| xiaohongshu | windows | 小红书数据采集（ADB） |

## 快速开始

### macOS

```bash
cd macos
chmod +x install.sh start.sh stop.sh
./install.sh
./start.sh
```

### Windows

```bat
cd windows
npm install
pip install -r requirements.txt
npm run build
start.bat
```

## 技术栈

- **前端**：Vue 3 + Pinia + Vue Router + Arco Design
- **后端**：Python + FastAPI + APScheduler
- **桌面**：Electron
- **自动化**：Playwright + ADB

## 开发文档

- [模块开发指南](./shared/MODULE_DEVELOPMENT.md)
- [macOS 部署指南](./macos/DEPLOY.md)
- [macOS 安装指南](./macos/SETUP_GUIDE.md)
- [更新日志](./CHANGELOG.md)

## License

MIT
