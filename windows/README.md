# Auto Controller v0.3.0 (Windows)

自动化任务控制器 - Windows 版本

## 环境要求

- Node.js 18+
- Python 3.9+
- MuMu 模拟器（用于 ADB 相关模块）

## 快速开始

```bat
cd windows
npm install
pip install -r requirements.txt
npm run build
start.bat
```

## 目录结构

```
windows/
├── module/
│   └── main.py           # Python 入口（委托给 shared/module/main.py）
├── modules/               # 平台特有模块
│   ├── inspection/        #   门店点检（ADB）
│   └── xiaohongshu/       #   小红书数据采集（ADB）
├── packages/
│   └── main/src/main.ts   # Electron 主进程（平台特有）
│   └── renderer/src/      # 平台特有 Vue 组件
│       └── views/          # Config, Dashboard, General, ModuleDetail, Modules, ModuleSettings, Tasks
├── config/                # 配置文件
├── *.bat                  # Batch 脚本
└── requirements.txt       # Python 依赖（含 pure-python-adb）
```

> Python 后端代码、共享业务模块、Electron 前端共享代码均在 `../shared/` 中，本目录仅保留平台差异部分。

## 可用模块

| 模块 | 位置 | 功能 |
|------|------|------|
| douyin | shared | 抖音数据采集 |
| jddj_orders | shared | 京东到家订单同步 |
| monthly_report | shared | 月报生成 |
| inspection | windows | 门店点检（ADB） |
| xiaohongshu | windows | 小红书数据采集（ADB） |

## 使用说明

### 模块设置

1. 点击左侧导航栏选择模块
2. 设置「启用模块」开关
3. 选择定时执行方式：不定时 / 每天 / 每周 / 间隔 / 自定义

### 通知配置

在"通用设置"页面配置：
- 通知级别：全部通知 / 仅错误 / 不通知
- SMTP 邮箱设置
- 企业微信 Webhook

## 技术栈

- **前端**：Vue 3 + Pinia + Vue Router + Arco Design
- **后端**：Python + FastAPI + APScheduler
- **桌面**：Electron
- **自动化**：Playwright + ADB

## 开发文档

- [模块开发指南](../shared/MODULE_DEVELOPMENT.md)
- [更新日志](./CHANGELOG.md)

## License

MIT
