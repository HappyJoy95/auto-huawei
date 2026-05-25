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
SENSITIVE_KEYS = {"smtp_password", "wechat_webhook"}


class EmailTestRequest(BaseModel):
    to_email: str

CONFIG_DIR = get_project_root() / "config"


class ConfigUpdateRequest(BaseModel):
    value: Any


# 通用配置白名单字段
GENERAL_CONFIG_ALLOWED_KEYS = {
    "check_interval", "retry_count", "task_timeout", "concurrency",
    "adb_address", "emulator_type", "headless",
    "notify_level", "notify_type", "wechat_webhook",
    "smtp_server", "smtp_port", "smtp_user", "smtp_password",
    "receiver_email", "log_level", "log_retention", "browser"
}


class GeneralConfigModel(BaseModel):
    """通用配置 Schema - 仅允许已知字段"""
    model_config = {"extra": "allow"}

    check_interval: Optional[int] = None
    retry_count: Optional[int] = None
    task_timeout: Optional[int] = None
    concurrency: Optional[int] = None
    adb_address: Optional[str] = None
    emulator_type: Optional[str] = None
    headless: Optional[bool] = None
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


@router.get("")
async def get_all_config():
    """获取所有配置"""
    from module.config.config import Config
    return Config.load()


@router.get("/general")
async def get_general_config():
    """获取通用配置（敏感字段脱敏）"""
    config_file = CONFIG_DIR / "general.yaml"
    config = {}
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
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
    # 合并：环境变量优先
    merged = {**config, **env_overrides}
    # 脱敏：配置文件中的敏感字段用占位符替代
    for key in SENSITIVE_KEYS:
        if key in merged and key not in env_overrides:
            merged[key] = "********" if merged[key] else ""
    return {"success": True, "config": merged}


@router.put("/general")
async def save_general_config(config: GeneralConfigModel):
    """保存通用配置（脱敏占位符不会被写入）"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_file = CONFIG_DIR / "general.yaml"
    # 过滤掉 None 值和脱敏占位符，只写入有效配置
    config_data = {}
    for k, v in config.model_dump().items():
        if v is None:
            continue
        if k in SENSITIVE_KEYS and v == "********":
            continue
        config_data[k] = v
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
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
async def test_email(request: EmailTestRequest | None = None):
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
