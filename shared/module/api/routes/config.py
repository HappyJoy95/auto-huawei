"""
配置管理 API
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
import yaml
from pathlib import Path
from module.utils.paths import get_project_root

router = APIRouter()

# 敏感字段列表，API 返回时脱敏
SENSITIVE_KEYS = {
    "smtp_password",
    "wechat_webhook",
    "wechat_corpsecret",
}


class EmailTestRequest(BaseModel):
    to_email: str

CONFIG_DIR = get_project_root() / "config"


class ConfigUpdateRequest(BaseModel):
    value: Any


# 通用配置白名单字段
GENERAL_CONFIG_ALLOWED_KEYS = {
    "check_interval", "retry_count", "task_timeout", "concurrency",
    "adb_address", "emulator_type",
    "notify_level", "notify_type", "wechat_webhook",
    "smtp_server", "smtp_port", "smtp_user", "smtp_password",
    "receiver_email", "log_level", "log_retention", "browser",
    # 企业微信应用配置
    "wechat_corpid", "wechat_corpsecret", "wechat_agentid", "wechat_app_targets",
}


class GeneralConfigModel(BaseModel):
    """通用配置 Schema - 仅允许已知字段"""

    model_config = {"extra": "ignore"}

    check_interval: Optional[int] = None
    retry_count: Optional[int] = None
    task_timeout: Optional[int] = None
    concurrency: Optional[int] = None
    adb_address: Optional[str] = None
    emulator_type: Optional[str] = None
    notify_level: Optional[str] = None
    notify_type: Optional[str] = None
    wechat_webhook: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    receiver_email: Optional[str] = None
    log_level: Optional[str] = None
    log_retention: Optional[int] = None
    browser: Optional[str] = None
    # 企业微信应用配置
    wechat_corpid: Optional[str] = None
    wechat_corpsecret: Optional[str] = None
    wechat_agentid: Optional[str] = None
    wechat_app_targets: Optional[Dict[str, Any]] = None


@router.get("")
async def get_all_config():
    """获取所有配置"""
    from module.config.config import Config
    return Config.load()


# 敏感环境变量白名单（仅返回是否已配置，不返回值）
ENV_SECRET_KEYS = [
    "JDDJ_USERNAME", "JDDJ_PASSWORD",
    "SMTP_USER", "SMTP_PASSWORD",
    "WECHAT_WEBHOOK", "WECHAT_CORP_ID", "WECHAT_AGENT_SECRET",
    "WECHAT_DEFAULT_USERID",
]


@router.get("/env-status")
async def get_env_status():
    """获取环境变量配置状态（仅返回是否已配置，不返回值）"""
    status = {}
    for key in ENV_SECRET_KEYS:
        status[key] = bool(os.environ.get(key))
    return {"success": True, "status": status}


@router.get("/general")
async def get_general_config():
    """获取通用配置（敏感字段脱敏）"""
    config_file = CONFIG_DIR / "general.yaml"
    config = {}
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    config = {k: v for k, v in config.items() if k in GENERAL_CONFIG_ALLOWED_KEYS}
    # 环境变量覆盖：如果环境变量设置了敏感配置，标记为已配置
    env_overrides = {}
    if os.environ.get("SMTP_USER"):
        env_overrides["smtp_user"] = os.environ["SMTP_USER"]
    if os.environ.get("SMTP_PASSWORD"):
        env_overrides["smtp_password"] = "********"
    if os.environ.get("SMTP_SERVER"):
        env_overrides["smtp_server"] = os.environ["SMTP_SERVER"]
    if os.environ.get("SMTP_PORT"):
        env_overrides["smtp_port"] = int(os.environ["SMTP_PORT"])
    if os.environ.get("WECHAT_WEBHOOK"):
        env_overrides["wechat_webhook"] = "********"
    # 企业微信应用环境变量覆盖
    if os.environ.get("WECHAT_CORP_ID"):
        env_overrides["wechat_corpid"] = os.environ["WECHAT_CORP_ID"]
    if os.environ.get("WECHAT_AGENT_ID"):
        env_overrides["wechat_agentid"] = os.environ["WECHAT_AGENT_ID"]
    if os.environ.get("WECHAT_AGENT_SECRET"):
        env_overrides["wechat_corpsecret"] = "********"
    # 合并：环境变量优先
    merged = {**config, **env_overrides}
    # 脱敏：配置文件中的敏感字段用占位符替代
    for key in SENSITIVE_KEYS:
        if key in merged and key not in env_overrides:
            merged[key] = "********" if merged[key] else ""
    return {"success": True, "config": merged}


@router.put("/general")
async def save_general_config(config: GeneralConfigModel):
    """保存通用配置（合并写入，脱敏占位符不会被写入）"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_file = CONFIG_DIR / "general.yaml"
    # 先读取现有配置
    existing = {}
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            existing = yaml.safe_load(f) or {}
    # 合并：只更新前端传来的有效字段
    for k, v in config.model_dump().items():
        if v is None:
            continue
        if k in SENSITIVE_KEYS and v == "********":
            continue
        existing[k] = v
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(existing, f, allow_unicode=True, default_flow_style=False)
    return {"success": True}


@router.get("/{key:path}")
async def get_config(key: str):
    """获取配置项"""
    from module.config.config import Config
    value = Config.get(key)
    if value is None:
        return {"key": key, "value": None}
    return {"key": key, "value": value}


@router.put("/{key:path}")
async def set_config(key: str, request: ConfigUpdateRequest):
    """设置配置项"""
    from module.config.config import Config
    Config.save_by_key(key, request.value)
    return {"success": True, "key": key}


@router.post("/test-email")
async def test_email(request: Optional[EmailTestRequest] = None):
    """测试邮件发送"""
    from module.notifier.sender import Notifier
    from datetime import datetime

    config = Notifier.get_global_config()
    smtp_user = os.environ.get("SMTP_USER") or config.get("smtp_user", "")
    to_email = request.to_email if request else smtp_user

    if not to_email:
        raise HTTPException(status_code=400, detail="发件邮箱未配置")

    success = Notifier.send(
        "email",
        to_email,
        "Auto Controller 测试邮件",
        f"这是一封测试邮件\n\n发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n如果您收到此邮件，说明邮箱配置正确。"
    )

    if success:
        return {"success": True, "message": f"测试邮件已发送至 {to_email}"}
    raise HTTPException(status_code=500, detail="邮件发送失败，请检查SMTP配置")


class NotifyTestRequest(BaseModel):
    """通知测试请求"""

    channel: str  # wechat, wechat_app, email
    target: str  # 接收目标
    title: str = "测试消息"
    content: str = "这是一条测试消息"
    mock: bool = False  # 是否 Mock 模式


@router.post("/test-notify")
async def test_notify(request: NotifyTestRequest):
    """测试通知渠道（支持所有渠道和 Mock 模式）"""
    from module.notifier.channels import get_channel

    channel = get_channel(request.channel)
    if not channel:
        raise HTTPException(status_code=400, detail=f"未知渠道: {request.channel}")

    result = channel.send(
        request.target, request.title, request.content, mock=request.mock
    )

    if isinstance(result, dict) and result.get("mock"):
        return {"success": True, **result}

    if result:
        return {
            "success": True,
            "message": f"消息已通过 {request.channel} 发送",
            "channel": request.channel,
            "target": request.target,
        }

    raise HTTPException(status_code=500, detail="消息发送失败")
