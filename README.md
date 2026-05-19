# Auto Controller

自动化任务控制器 - 基于 Electron + Python 的模块化任务调度系统。

## 项目结构

```
auto-huawei/
├── macos/            # macOS 版本
│   ├── module/       # Python 后端
│   ├── modules/      # 功能模块
│   ├── packages/     # Electron 前端
│   └── ...
├── windows/          # Windows 版本
└── README.md
```

## 平台说明

### macOS 版本

参见 [macos/README.md](./macos/README.md)

```bash
cd macos
./install.sh
./start.sh
```

### Windows 版本

参见 [windows/README.md](./windows/README.md)

## 功能特性

- **模块化架构**：每个功能模块独立管理
- **可视化调度**：任务等待中 → 排队中 → 运行中
- **灵活定时**：支持每天、每周、间隔、自定义 cron
- **通知推送**：支持企业微信 Webhook 和邮件通知
- **实时日志**：前端实时显示任务执行日志

## 开发文档

- [模块开发指南](./macos/MODULE_DEVELOPMENT.md)
- [部署指南](./macos/DEPLOY.md)
- [更新日志](./macos/CHANGELOG.md)

## License

MIT
