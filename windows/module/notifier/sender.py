"""
通知发送模块 - 支持企业微信和邮箱（可多选）
"""
import os
import requests
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from typing import Dict, Any
from datetime import datetime
import yaml
from pathlib import Path
from module.utils.paths import get_project_root


class Notifier:
    """通知发送器"""

    @classmethod
    def get_global_config(cls) -> Dict[str, Any]:
        """获取全局配置"""
        config_file = get_project_root() / "config" / "general.yaml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    @classmethod
    def send(cls, notify_type: str, target: str, title: str, content: str,
             attachment_path: str = None) -> bool:
        """
        发送通知
        :param notify_type: wechat 或 email
        :param target: webhook地址 或 邮箱地址
        :param title: 标题
        :param content: 内容
        :param attachment_path: 附件文件路径（仅邮件支持）
        :return: 是否成功
        """
        if notify_type == "wechat":
            return cls._send_wechat(target, title, content)
        elif notify_type == "email":
            return cls._send_email(target, title, content, attachment_path=attachment_path)
        else:
            print(f"[Notifier] Unknown notify type: {notify_type}")
            return False

    @classmethod
    def _send_wechat(cls, webhook: str, title: str, content: str) -> bool:
        """发送企业微信消息"""
        if not webhook:
            print("[Notifier] Webhook URL is empty")
            return False

        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"**{title}**\n\n{content}"
                }
            }

            response = requests.post(webhook, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    print(f"[Notifier] WeChat notification sent: {title}")
                    return True
                else:
                    print(f"[Notifier] WeChat error: {result.get('errmsg')}")
            else:
                print(f"[Notifier] WeChat HTTP error: {response.status_code}")

        except Exception as e:
            print(f"[Notifier] WeChat send error: {e}")

        return False

    @classmethod
    def _send_email(cls, to_email: str, title: str, content: str,
                    attachment_path: str = None) -> bool:
        """发送邮件"""
        global_config = cls.get_global_config()

        # 优先从环境变量读取敏感配置，回退到配置文件
        smtp_server = os.environ.get("SMTP_SERVER") or global_config.get("smtp_server", "smtp.qq.com")
        smtp_port = int(os.environ.get("SMTP_PORT") or global_config.get("smtp_port", 587))
        smtp_user = os.environ.get("SMTP_USER") or global_config.get("smtp_user", "")
        smtp_password = os.environ.get("SMTP_PASSWORD") or global_config.get("smtp_password", "")

        if not smtp_user or not smtp_password:
            print("[Notifier] Email not configured (smtp user/password)")
            return False

        if not to_email:
            print("[Notifier] Target email is empty")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to_email
            msg["Subject"] = f"[AutoController] {title}"

            msg.attach(MIMEText(content, "plain", "utf-8"))

            # 添加附件
            if attachment_path:
                attach_file = Path(attachment_path)
                if attach_file.exists():
                    with open(attach_file, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    from email import encoders
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={attach_file.name}"
                    )
                    msg.attach(part)
                    print(f"[Notifier] Attached file: {attach_file.name}")

            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_user, to_email, msg.as_string())
            else:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_user, to_email, msg.as_string())

            print(f"[Notifier] Email sent to {to_email}: {title}")
            return True

        except Exception as e:
            print(f"[Notifier] Email send error: {e}")
            return False

    @classmethod
    def notify_task_result(cls, module_name: str, module_display_name: str,
                           module_config: Dict[str, Any], result: Dict[str, Any],
                           log_callback=None):
        """
        发送任务结果通知（支持多个通知类型）
        :param module_name: 模块名
        :param module_display_name: 显示名
        :param module_config: 模块配置
        :param result: 执行结果，支持 success, message, notify_title, notify_content, attachment_path
        """
        def log(level: str, message: str):
            if log_callback:
                log_callback(level, message, module_name)

        # 获取全局配置
        global_config = cls.get_global_config()
        notify_level = global_config.get("notify_level", "all")

        # 检查通知级别
        success = result.get("success", False)
        if notify_level == "none":
            log("INFO", "通知跳过: 全局通知级别为 none")
            return
        if notify_level == "error" and success:
            log("INFO", "通知跳过: 全局通知级别为 error，当前任务成功")
            return

        # 获取模块推送配置
        notify_enabled = module_config.get("notify_enabled", False)
        if not notify_enabled:
            log("INFO", "通知跳过: 模块未启用推送")
            return

        # 支持单个字符串或数组格式（多选）
        notify_types = module_config.get("notify_type", ["wechat"])
        if isinstance(notify_types, str):
            notify_types = [notify_types]
        log("INFO", f"通知配置: enabled={notify_enabled}, types={notify_types}")

        # 构造通用的通知内容
        message = result.get("message", "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 优先使用模块自定义的通知标题和内容
        notify_title = result.get("notify_title")
        notify_content = result.get("notify_content")
        if notify_title and notify_content:
            title = notify_title
            content = notify_content
        else:
            if success:
                title = f"✅ {module_display_name} 执行成功"
                content = f"模块: {module_display_name}\n时间: {timestamp}\n结果: {message}"
            else:
                title = f"❌ {module_display_name} 执行失败"
                content = f"模块: {module_display_name}\n时间: {timestamp}\n错误: {message}"

        attachment_path = result.get("attachment_path")

        # 逐个发送每个配置的通知类型
        for notify_type in notify_types:
            notify_type = notify_type.strip().lower()
            if not notify_type:
                continue

            target = cls._get_notify_target(notify_type, module_config, global_config)
            log("INFO", f"通知目标检查: type={notify_type}, target={'已配置' if target else '未配置'}")

            if not target:
                log("WARNING", f"通知跳过: {notify_type} 未配置目标地址")
                continue

            sent = cls.send(notify_type, target, title, content, attachment_path=attachment_path)
            if sent:
                log("SUCCESS", f"通知发送成功: {notify_type}")
            else:
                log("ERROR", f"通知发送失败: {notify_type}")

    @classmethod
    def _get_notify_target(cls, notify_type: str, module_config: Dict[str, Any],
                           global_config: Dict[str, Any]) -> str:
        """
        根据通知类型获取对应的目标地址
        :param notify_type: 通知类型 (wechat, email)
        :param module_config: 模块配置
        :param global_config: 全局配置
        :return: 目标地址
        """
        # 先检查模块配置中是否有对应类型的专属目标
        type_target_key = f"notify_{notify_type}_target"
        if module_config.get(type_target_key):
            return module_config[type_target_key]

        # 检查通用的 notify_target
        if module_config.get("notify_target"):
            return module_config["notify_target"]

        # 回退到全局配置
        if notify_type == "wechat":
            webhook = os.environ.get("WECHAT_WEBHOOK") or global_config.get("wechat_webhook")
            if webhook:
                return webhook
        if notify_type == "email":
            return global_config.get("email", "")

        return ""
