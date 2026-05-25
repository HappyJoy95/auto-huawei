# macOS 安装使用指南

## 前置条件

- macOS 10.15+
- [Homebrew](https://brew.sh)（Mac 包管理器）
- Node.js 18+（`brew install node`）
- Python 3.9+（`brew install python3`）

## 安装和启动

```bash
# 1. 克隆项目
git clone https://github.com/HappyJoy95/auto-huawei.git
cd auto-huawei/macos

# 2. 添加执行权限
chmod +x install.sh start.sh stop.sh

# 3. 一键安装（安装 npm 依赖 + Python venv + 构建前端）
./install.sh

# 4. 安装 Playwright 浏览器（京东到家模块需要）
source venv/bin/activate
playwright install chromium

# 5. 启动应用
./start.sh
```

启动后会打开 Electron 桌面窗口，左侧导航栏有"通用设置"、"模块"等页面。

## 配置通知（可选）

在"通用设置"页面填写：

- **SMTP 服务器/端口**：默认 `smtp.qq.com:587`
- **发件邮箱 + 授权码**：QQ 邮箱需先开启 SMTP 服务获取授权码
- **通知级别**：全部通知 / 仅错误 / 不通知

或者用环境变量（在启动前设置）：

```bash
export SMTP_USER=xxx@qq.com
export SMTP_PASSWORD=你的授权码
./start.sh
```

## 停止应用

```bash
./stop.sh
```

## 常见问题

### Electron 启动失败

确保 Node.js 版本 >= 18：

```bash
node -v
```

如果环境变量 `ELECTRON_RUN_AS_NODE=1` 被设置，需要先清除：

```bash
unset ELECTRON_RUN_AS_NODE
```

### Python 模块找不到

确保激活了虚拟环境：

```bash
source venv/bin/activate
```

### 端口被占用

后端默认使用 5001 端口，确保未被占用：

```bash
lsof -i :5001
```

### Playwright 浏览器未安装

如果京东到家模块报错，需要安装 Chromium：

```bash
source venv/bin/activate
playwright install chromium
```

## 安全说明

- `general.yaml` 和模块的 `config.json` 不会被 Git 追踪，本地填的凭据不会上传
- 敏感配置优先从环境变量读取，回退到配置文件，最后使用代码默认值
- 可复制项目根目录的 `.env.example` 为 `.env` 填入环境变量
