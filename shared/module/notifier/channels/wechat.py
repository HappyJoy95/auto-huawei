"""
企业微信群机器人渠道
"""
import os
import requests
from typing import Dict, Any, Optional
from .base import BaseChannel


class WechatChannel(BaseChannel):
    """企业微信群机器人"""

    name = "wechat"
    target_key = "notify_wechat_target"

    @classmethod
    def get_target(
        cls, module_config: Dict, global_config: Dict, result: Dict = None
    ) -> str:
        """解析目标地址"""
        # 1. 模块配置的专属目标
        target = module_config.get(cls.target_key)
        if target:
            return target

        # 2. 通用的 notify_target
        if module_config.get("notify_target"):
            return module_config["notify_target"]

        # 3. 回退到全局配置
        return os.environ.get("WECHAT_WEBHOOK") or global_config.get(
            "wechat_webhook", ""
        )

    @classmethod
    def _is_configured(cls) -> bool:
        """检查是否已配置真实 Webhook"""
        webhook = os.environ.get("WECHAT_WEBHOOK")
        return bool(webhook)

    @classmethod
    def send(
        cls,
        target: str,
        title: str,
        content: str,
        attachment_path: str = None,
        mock: bool = False,
        **kwargs,
    ) -> bool:
        """
        发送企业微信消息
        :param target: webhook 地址
        :param title: 标题
        :param content: 内容
        :param mock: 是否 Mock 模式
        :return: 成功返回 True，Mock 模式返回 dict
        """
        # Mock 模式或未配置
        if mock or not cls._is_configured():
            return {
                "mock": True,
                "channel": cls.name,
                "target": target,
                "title": title,
                "content": content,
                "message": "Mock 模式：消息已构造但未发送（未配置企业微信）",
            }

        if not target:
            print("[WechatChannel] Webhook URL is empty")
            return False

        try:
            data = {"msgtype": "markdown", "markdown": {"content": f"**{title}**\n\n{content}"}}

            response = requests.post(target, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    print(f"[WechatChannel] WeChat notification sent: {title}")
                    return True
                else:
                    print(f"[WechatChannel] WeChat error: {result.get('errmsg')}")
            else:
                print(f"[WechatChannel] HTTP error: {response.status_code}")

        except Exception as e:
            print(f"[WechatChannel] Send error: {e}")

        return False
