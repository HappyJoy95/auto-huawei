"""
邮件渠道
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Dict, Any, Optional
from .base import BaseChannel
from module.utils.paths import get_project_root
import yaml


class EmailChannel(BaseChannel):
    """邮件渠道"""

    name = "email"
    target_key = "notify_email_target"

    @classmethod
    def get_global_config(cls) -> Dict[str, Any]:
        """获取全局配置"""
        config_file = get_project_root() / "config" / "general.yaml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

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
        return global_config.get("email", "")

    @classmethod
    def _is_configured(cls) -> bool:
        """检查是否已配置邮件"""
        global_config = cls.get_global_config()
        smtp_user = os.environ.get("SMTP_USER") or global_config.get("smtp_user", "")
        smtp_password = os.environ.get("SMTP_PASSWORD") or global_config.get(
            "smtp_password", ""
        )
        return bool(smtp_user and smtp_password)

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
        发送邮件
        :param target: 邮箱地址
        :param title: 标题
        :param content: 内容
        :param attachment_path: 附件路径
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
                "attachment": attachment_path,
                "message": "Mock 模式：消息已构造但未发送（未配置邮件）",
            }

        global_config = cls.get_global_config()

        # 优先从环境变量读取
        smtp_server = os.environ.get("SMTP_SERVER") or global_config.get(
            "smtp_server", "smtp.qq.com"
        )
        smtp_port = int(
            os.environ.get("SMTP_PORT") or global_config.get("smtp_port", 587)
        )
        smtp_user = os.environ.get("SMTP_USER") or global_config.get("smtp_user", "")
        smtp_password = os.environ.get("SMTP_PASSWORD") or global_config.get(
            "smtp_password", ""
        )

        if not smtp_user or not smtp_password:
            print("[EmailChannel] Email not configured")
            return False

        if not target:
            print("[EmailChannel] Target email is empty")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = target
            msg["Subject"] = f"[AutoController] {title}"

            msg.attach(MIMEText(content, "plain", "utf-8"))

            # 添加附件
            if attachment_path:
                attach_file = Path(attachment_path)
                if attach_file.exists():
                    with open(attach_file, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={attach_file.name}",
                    )
                    msg.attach(part)

            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_user, target, msg.as_string())
            else:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_user, target, msg.as_string())

            print(f"[EmailChannel] Email sent to {target}: {title}")
            return True

        except Exception as e:
            print(f"[EmailChannel] Send error: {e}")
            return False
