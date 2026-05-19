# Auto Controller v0.1.1-mac

自动化任务控制器 - macOS 版本

## 环境要求

- macOS 10.15+
- Node.js 18+ （推荐使用 nvm 安装）
- Python 3.9+
- Homebrew （可选，用于安装依赖）

## 快速安装

```bash
# 1. 进入项目目录
cd macos

# 2. 添加执行权限
chmod +x install.sh start.sh stop.sh

# 3. 运行安装脚本
./install.sh
```

## 手动安装

如果自动安装失败，可以手动执行：

```bash
# 安装 Node.js 依赖
npm install

# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 构建前端（如果 dist 目录不存在）
npm run build
```

## 启动应用

```bash
# 启动
./start.sh

# 停止
./stop.sh
```

## 打包为 macOS 应用

```bash
# 安装依赖后执行
npm run build
npx electron-builder --mac
```

打包后的应用在 `release/` 目录。

## 目录结构

```
macos/
├── module/            # Python 后端
│   ├── api/          # FastAPI 路由
│   ├── config/       # 配置管理
│   ├── core/         # 模块管理器
│   ├── tasks/        # 调度器
│   └── notifier/     # 通知模块
├── modules/           # 功能模块
│   ├── douyin/       # 抖音数据采集
│   └── jddj_orders/  # 京东到家订单同步
├── packages/          # Electron 前端
│   ├── main/         # 主进程
│   ├── preload/      # 预加载脚本
│   └── renderer/     # 渲染进程（Vue 3）
├── config/            # 配置文件
├── data/              # 数据存储
├── install.sh         # 安装脚本
├── start.sh           # 启动脚本
├── stop.sh            # 停止脚本
└── requirements.txt   # Python 依赖
```

## 功能特性

- **模块化架构**：每个功能模块独立管理，包含配置、任务代码
- **可视化调度**：任务等待中 → 排队中 → 运行中的完整队列管理
- **灵活定时**：支持每天、每周、间隔、自定义 cron 表达式
- **通知推送**：支持企业微信 Webhook 和邮件通知
- **实时日志**：前端实时显示任务执行日志
- **自定义设置**：模块可定义自己的设置表单和样式

## 可用模块

| 模块 | 功能 |
|------|------|
| douyin | 抖音数据采集 |
| jddj_orders | 京东到家订单同步 |

## 开发新模块

参见 [MODULE_DEVELOPMENT.md](./MODULE_DEVELOPMENT.md)

## 常见问题

### 1. Electron 启动失败

确保 Node.js 版本 >= 18：
```bash
node -v
```

如果环境变量 `ELECTRON_RUN_AS_NODE=1` 被设置，需要先清除：
```bash
unset ELECTRON_RUN_AS_NODE
```

### 2. Python 模块找不到

确保激活了虚拟环境：
```bash
source venv/bin/activate
```

### 3. 端口被占用

后端默认使用 5001 端口，确保未被占用：
```bash
lsof -i :5001
```

## 更新日志

参见 [CHANGELOG.md](./CHANGELOG.md)

## License

MIT
