from typing import Dict, Optional
from .base import BaseChannel
from .wechat import WechatChannel
from .email import EmailChannel
from .wechat_app import WechatAppChannel

__all__ = [
    "BaseChannel",
    "WechatChannel",
    "EmailChannel",
    "WechatAppChannel",
    "get_channel",
]

# 渠道注册表
_channels = {}


def register_channels():
    """注册所有渠道"""
    global _channels
    _channels = {
        "wechat": WechatChannel(),
        "email": EmailChannel(),
        "wechat_app": WechatAppChannel(),
    }


def get_channel(name: str) -> Optional[BaseChannel]:
    """获取指定渠道"""
    if not _channels:
        register_channels()
    return _channels.get(name)


def get_all_channels() -> Dict[str, BaseChannel]:
    """获取所有渠道"""
    if not _channels:
        register_channels()
    return _channels.copy()
