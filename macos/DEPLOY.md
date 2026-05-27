# Auto Controller 部署指南 (macOS)

## 项目信息

- **项目名称**: Auto Controller
- **版本**: 0.3.0
- **类型**: Electron + Python 桌面应用
- **架构**: shared + platform（共享代码 + 平台差异）

## 环境要求

```bash
node -v    # 需要 18+
python3 -v # 需要 3.9+
npm -v
```

如缺少环境：
- Node.js: `brew install node` 或使用 nvm
- Python: `brew install python@3.9`

## 部署步骤

### 1. 进入项目目录

```bash
cd /path/to/auto-huawei/macos
```

### 2. 安装 Node.js 依赖

```bash
npm install
```

### 3. 创建 Python 虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 构建前端

```bash
npm run build
```

构建使用 `shared/packages/` 中的 vite 配置，产物输出到本平台 `packages/*/dist/`。

### 5. 启动应用

```bash
chmod +x start.sh stop.sh
./start.sh
```

### 6. 验证启动成功

```bash
curl http://localhost:5001/api/modules
# 应返回模块列表 JSON
```

## 目录结构

```
macos/
├── module/main.py        # Python 入口（委托给 shared/module/main.py）
├── modules/              # 平台特有模块配置
├── packages/             # 平台特有前端代码
│   ├── main/src/main.ts  # Electron 主进程
│   └── renderer/src/     # 平台特有 Vue 组件
├── config/               # 配置文件
├── data/                 # 运行时数据
├── venv/                 # Python 虚拟环境
├── start.sh / stop.sh   # 启停脚本
└── requirements.txt      # Python 依赖
```

Python 后端代码和共享业务模块在 `../shared/` 中，通过环境变量 `AUTO_CONTROLLER_ROOT` 和 `AUTO_CONTROLLER_SHARED_ROOT` 定位。

## 打包为 macOS 应用

```bash
npm run build
npx electron-builder --mac
```

`electron-builder.yml` 已配置将 `../shared/module` 和 `../shared/modules` 映射到打包目录。

## 配置说明

### 环境变量（优先级最高）

复制项目根目录 `.env.example` 为 `.env` 填入敏感凭据：

```bash
cp ../.env.example .env
```

### 全局配置

编辑 `config/general.yaml`（不会被 Git 追踪）：

```yaml
notify_level: "all"
smtp_server: "smtp.qq.com"
smtp_port: 587
```

配置读取优先级：`环境变量 > general.yaml > 代码默认值`

## 常见问题

### Electron 窗口不显示

```bash
unset ELECTRON_RUN_AS_NODE
```

### 端口 5001 被占用

```bash
lsof -i :5001
kill -9 <PID>
```

### Python 模块找不到

```bash
source venv/bin/activate
which python  # 应指向 macos/venv/bin/python
```

### preload 加载失败

```bash
npm run build  # 重新构建
```
