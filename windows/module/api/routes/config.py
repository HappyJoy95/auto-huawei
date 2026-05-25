"""
配置管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
import yaml
from pathlib import Path
from module.utils.paths import get_project_root

router = APIRouter()


class EmailTestRequest(BaseModel):
    to_email: str

CONFIG_DIR = get_project_root() / "config"


class ConfigUpdateRequest(BaseModel):
    value: Any


# 通用配置白名单字段
GENERAL_CONFIG_ALLOWED_KEYS = {
    "notify_level", "notify_type", "wechat_webhook", "headless",
    "smtp_server", "smtp_port", "smtp_user", "smtp_password",
    "receiver_email", "adb_port", "browser"
}


class GeneralConfigModel(BaseModel):
    """通用配置 Schema - 仅允许已知字段"""
    model_config = {"extra": "allow"}

    notify_level: Optional[str] = None
    notify_type: Optional[str] = None
    wechat_webhook: Optional[str] = None
    headless: Optional[bool] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    receiver_email: Optional[str] = None
    adb_port: Optional[str] = None
    browser: Optional[str] = None


@router.get("")
async def get_all_config():
    """获取所有配置"""
    from module.config.config import Config
    return Config.load()


@router.get("/general")
async def get_general_config():
    """获取通用配置"""
    config_file = CONFIG_DIR / "general.yaml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return {"success": True, "config": yaml.safe_load(f) or {}}
    return {"success": True, "config": {}}


@router.put("/general")
async def save_general_config(config: GeneralConfigModel):
    """保存通用配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_file = CONFIG_DIR / "general.yaml"
    # 过滤掉 None 值，只写入有效配置
    config_data = {k: v for k, v in config.model_dump().items() if v is not None}
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
    smtp_user = config.get("smtp_user") or config.get("smtpUser") or ""
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
