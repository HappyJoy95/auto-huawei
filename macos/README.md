# Auto Controller v0.3.0 (macOS)

自动化任务控制器 - macOS 版本

## 环境要求

- macOS 10.15+
- Node.js 18+
- Python 3.9+

## 快速安装

```bash
cd macos
chmod +x install.sh start.sh stop.sh
./install.sh
```

## 手动安装

```bash
npm install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm run build
```

## 启动应用

```bash
./start.sh    # 启动
./stop.sh     # 停止
```

## 打包为 macOS 应用

```bash
npm run build
npx electron-builder --mac
```

打包后的应用在 `release/` 目录。

## 目录结构

```
macos/
├── module/
│   └── main.py           # Python 入口（委托给 shared/module/main.py）
├── modules/               # 平台特有模块配置
│   ├── jddj_orders/       #   config.json, config.yaml（敏感凭据）
│   └── monthly_report/    #   config.yaml
├── packages/
│   └── main/src/main.ts   # Electron 主进程（平台特有）
│   └── renderer/src/      # 平台特有 Vue 组件
│       ├── components/LogPanel.vue
│       └── views/          # Dashboard, General, ModuleDetail, Modules, ModuleSettings
├── config/                # 配置文件
├── data/                  # 运行时数据
├── *.sh                   # Shell 脚本
└── requirements.txt       # Python 依赖
```

> Python 后端代码、共享业务模块、Electron 前端共享代码均在 `../shared/` 中，本目录仅保留平台差异部分。

## 可用模块

| 模块 | 位置 | 功能 |
|------|------|------|
| douyin | shared | 抖音数据采集 |
| jddj_orders | shared | 京东到家订单同步 |
| monthly_report | shared | 月报生成 |

## 常见问题

### Electron 启动失败

确保 Node.js >= 18，并清除 `ELECTRON_RUN_AS_NODE` 环境变量：

```bash
unset ELECTRON_RUN_AS_NODE
```

### Python 模块找不到

确保激活了虚拟环境：`source venv/bin/activate`

### 端口被占用

后端默认使用 5001 端口：`lsof -i :5001`

## 开发文档

- [模块开发指南](../shared/MODULE_DEVELOPMENT.md)
- [部署指南](./DEPLOY.md)
- [安装指南](./SETUP_GUIDE.md)
- [更新日志](./CHANGELOG.md)

## License

MIT
