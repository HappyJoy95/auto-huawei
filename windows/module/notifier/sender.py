"""
通知发送模块 - 支持企业微信和邮箱
"""
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
import yaml
from pathlib import Path


class Notifier:
    """通知发送器"""

    @classmethod
    def get_global_config(cls) -> Dict[str, Any]:
        """获取全局配置"""
        config_file = Path(__file__).parent.parent.parent / "config" / "general.yaml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    @classmethod
    def send(cls, notify_type: str, target: str, title: str, content: str) -> bool:
        """
        发送通知
        :param notify_type: wechat 或 email
        :param target: webhook地址 或 邮箱地址
        :param title: 标题
        :param content: 内容
        :return: 是否成功
        """
        if notify_type == "wechat":
            return cls._send_wechat(target, title, content)
        elif notify_type == "email":
            return cls._send_email(target, title, content)
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
    def _send_email(cls, to_email: str, title: str, content: str) -> bool:
        """发送邮件"""
        global_config = cls.get_global_config()

        smtp_server = global_config.get("smtp_server", "smtp.qq.com")
        smtp_port = global_config.get("smtp_port", 465)
        smtp_user = global_config.get("smtp_user", "")
        smtp_password = global_config.get("smtp_password", "")

        if not smtp_user or not smtp_password:
            print("[Notifier] Email not configured (smtp_user/smtp_password)")
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

            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())

            print(f"[Notifier] Email sent to {to_email}: {title}")
            return True

        except Exception as e:
            print(f"[Notifier] Email send error: {e}")
            return False

    @classmethod
    def notify_task_result(cls, module_name: str, module_display_name: str,
                           module_config: Dict[str, Any], result: Dict[str, Any]):
        """
        发送任务结果通知
        :param module_name: 模块名
        :param module_display_name: 显示名
        :param module_config: 模块配置
        :param result: 执行结果
        """
        # 获取全局配置
        global_config = cls.get_global_config()
        notify_level = global_config.get("notify_level", "all")

        # 检查通知级别
        success = result.get("success", False)
        if notify_level == "none":
            return
        if notify_level == "error" and success:
            return

        # 获取模块推送配置
        notify_enabled = module_config.get("notify_enabled", False)
        notify_type = module_config.get("notify_type", "wechat")
        notify_target = module_config.get("notify_target", "")

        # 如果模块未配置推送目标，使用全局配置
        if not notify_enabled or not notify_target:
            global_webhook = global_config.get("wechat_webhook", "")
            if global_webhook:
                notify_type = "wechat"
                notify_target = global_webhook
            else:
                return

        message = result.get("message", "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if success:
            title = f"✅ {module_display_name} 执行成功"
            content = f"模块: {module_display_name}\n时间: {timestamp}\n结果: {message}"
        else:
            title = f"❌ {module_display_name} 执行失败"
            content = f"模块: {module_display_name}\n时间: {timestamp}\n错误: {message}"

        cls.send(notify_type, notify_target, title, content)
