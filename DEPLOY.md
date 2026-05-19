# Auto Controller 部署指南

本文档供 AI 助手阅读，请按步骤完成部署。

## 项目信息

- **项目名称**: Auto Controller
- **版本**: 0.1.1-mac
- **类型**: Electron + Python 桌面应用
- **功能**: 模块化任务调度系统，支持定时执行、通知推送

## 环境要求

请先检查以下环境：

```bash
# 1. 检查 Node.js (需要 18+)
node -v

# 2. 检查 Python (需要 3.9+)
python3 -v

# 3. 检查 npm
npm -v
```

如果缺少环境：
- Node.js: `brew install node` 或使用 nvm 安装
- Python: `brew install python@3.9`

## 部署步骤

### 步骤 1: 进入项目目录

```bash
cd /path/to/macos
```

### 步骤 2: 安装 Node.js 依赖

```bash
npm install
```

### 步骤 3: 创建 Python 虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 步骤 4: 构建前端

```bash
npm run build
```

构建完成后应生成：
- `packages/main/dist/main.cjs`
- `packages/preload/dist/index.cjs`
- `packages/renderer/dist/index.html`

### 步骤 5: 启动应用

```bash
# 添加执行权限
chmod +x start.sh stop.sh

# 启动
./start.sh
```

### 步骤 6: 验证启动成功

检查以下内容：

```bash
# 1. 检查后端 API
curl http://localhost:5001/api/modules

# 应返回类似:
# {"modules":[{"name":"jddj_orders",...},{"name":"douyin",...}]}
```

应用窗口应正常显示，左侧导航栏应显示：
- 总览
- 通用设置
- 京东到家订单
- 抖音

## 常见问题

### 问题 1: Electron 窗口不显示

检查是否设置了 `ELECTRON_RUN_AS_NODE` 环境变量：

```bash
echo $ELECTRON_RUN_AS_NODE
# 如果输出 1，需要清除
unset ELECTRON_RUN_AS_NODE
```

### 问题 2: 端口 5001 被占用

```bash
# 查找占用进程
lsof -i :5001

# 终止进程
kill -9 <PID>
```

### 问题 3: Python 模块找不到

确保已激活虚拟环境：

```bash
source venv/bin/activate
which python
# 应输出: /path/to/macos/venv/bin/python
```

### 问题 4: preload 加载失败

检查文件是否存在：

```bash
ls -la packages/preload/dist/index.cjs
ls -la packages/main/dist/main.cjs
```

如果不存在，重新构建：

```bash
npm run build
```

## 目录结构

```
macos/
├── module/            # Python 后端
│   ├── main.py       # 后端入口
│   ├── api/          # API 路由
│   ├── tasks/        # 调度器
│   └── core/         # 模块管理
├── modules/           # 功能模块
│   ├── douyin/       # 抖音采集
│   └── jddj_orders/  # 京东订单
├── packages/          # Electron 前端
│   ├── main/         # 主进程
│   ├── preload/      # 预加载脚本
│   └── renderer/     # Vue 3 前端
├── config/            # 配置文件
├── data/              # 数据存储
├── venv/              # Python 虚拟环境（需创建）
├── node_modules/      # Node 依赖（需安装）
├── start.sh           # 启动脚本
├── stop.sh            # 停止脚本
└── requirements.txt   # Python 依赖
```

## 停止应用

```bash
./stop.sh
```

## 打包为 macOS 应用

如需打包为独立应用：

```bash
npm run build
npx electron-builder --mac
```

打包后的应用在 `release/` 目录。

## 配置说明

### 全局配置

编辑 `config/general.yaml`：

```yaml
# 通知级别: all / error / none
notify_level: "all"

# 企业微信 Webhook（全局默认）
wechat_webhook: ""

# 邮箱配置
smtp_server: "smtp.qq.com"
smtp_port: 465
smtp_user: ""
smtp_password: ""
```

### 模块配置

在应用界面中点击左侧模块名称进入设置页面。

## 技术栈

- 前端: Vue 3 + Pinia + Arco Design
- 后端: Python + FastAPI + APScheduler
- 桌面: Electron
- 自动化: Playwright

## AI 助手注意事项

1. 执行命令前先确认当前目录是否正确
2. 如果 `npm install` 失败，尝试删除 `node_modules` 和 `package-lock.json` 后重试
3. 如果 Python 依赖安装失败，确保 pip 版本是最新的：`pip install --upgrade pip`
4. 构建完成后，先停止可能残留的进程再启动
5. 验证时确保 API 返回正确的 JSON 格式

部署完成后报告：
- Node.js 版本
- Python 版本
- 构建是否成功
- 启动是否成功
- API 是否正常响应
