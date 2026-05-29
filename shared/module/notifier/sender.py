"""
通知模块 - 使用 Channel 策略模式
"""
import os
from datetime import datetime
from typing import Dict, Any
import yaml
from module.utils.paths import get_project_root
from .channels import get_channel


class Notifier:
    """通知发送器 - 注册中心模式"""

    @classmethod
    def get_global_config(cls) -> Dict[str, Any]:
        config_file = get_project_root() / "config" / "general.yaml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    @classmethod
    def send(cls, notify_type: str, target: str, title: str, content: str,
             attachment_path: str = None, mock: bool = False, **kwargs):
        channel = get_channel(notify_type)
        if not channel:
            print(f"[Notifier] Unknown notify type: {notify_type}")
            return False
        return channel.send(target, title, content,
                            attachment_path=attachment_path, mock=mock, **kwargs)

    @classmethod
    def notify_task_result(cls, module_name: str, module_display_name: str,
                           module_config: Dict[str, Any], result: Dict[str, Any],
                           log_callback=None):
        def log(level: str, message: str):
            if log_callback:
                log_callback(level, message, module_name)

        global_config = cls.get_global_config()
        notify_level = global_config.get("notify_level", "all")

        success = result.get("success", False)
        if notify_level == "none":
            log("INFO", "通知跳过: 全局通知级别为 none")
            return
        if notify_level == "error" and success:
            log("INFO", "通知跳过: 全局通知级别为 error，当前任务成功")
            return

        notify_enabled = module_config.get("notify_enabled", False)
        if not notify_enabled:
            log("INFO", "通知跳过: 模块未启用推送")
            return

        notify_types = module_config.get("notify_type", ["wechat"])
        if isinstance(notify_types, str):
            notify_types = [notify_types]

        # 同步推送：勾选后 wechat_app 渠道额外推送给门店负责人
        sync_enabled = module_config.get("notify_sync_enabled", False)

        log("INFO", f"通知配置: enabled={notify_enabled}, types={notify_types}, sync={sync_enabled}")

        message = result.get("message", "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        notify_title = result.get("notify_title")
        notify_content = result.get("notify_content")

        # 任务主动抑制推送：notify_title 为 None 表示不需要推送
        if notify_title is None:
            log("INFO", "通知跳过: 任务未提供推送标题（可能无新内容）")
            return

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

        for notify_type in notify_types:
            notify_type = notify_type.strip().lower()
            if not notify_type:
                continue

            channel = get_channel(notify_type)
            if not channel:
                log("WARNING", f"通知跳过: 未知渠道 {notify_type}")
                continue

            target = channel.get_target(module_config, global_config, result)
            log("INFO", f"通知目标检查: type={notify_type}, target={'已配置' if target else '未配置'}")

            if not target:
                log("WARNING", f"通知跳过: {notify_type} 未配置目标地址")
                continue

            sent = cls.send(notify_type, target, title, content,
                            attachment_path=attachment_path)
            # Mock 模式返回 dict，视为成功（仅构造未发送）
            if sent is True or (isinstance(sent, dict) and sent.get("mock")):
                log("SUCCESS", f"通知发送成功: {notify_type}")
            else:
                log("ERROR", f"通知发送失败: {notify_type}")

            # 同步推送：wechat_app 渠道额外推送给门店负责人
            if sync_enabled and notify_type == "wechat_app":
                from .channels.wechat_app import WechatAppChannel
                store_target = WechatAppChannel.get_target_by_store(
                    module_config, global_config, result
                )
                if store_target:
                    # 去重：排除已在主推送中包含的 userid
                    primary_userids = set(target.split("|"))
                    sync_userids = [uid for uid in store_target.split("|") if uid not in primary_userids]
                    if sync_userids:
                        sync_target = "|".join(sync_userids)
                        log("INFO", f"同步推送门店负责人: {sync_target}")
                        sent = cls.send(notify_type, sync_target, title, content,
                                        attachment_path=attachment_path)
                        if sent is True or (isinstance(sent, dict) and sent.get("mock")):
                            log("SUCCESS", f"同步推送成功: {notify_type} -> 门店负责人")
                        else:
                            log("ERROR", f"同步推送失败: {notify_type} -> 门店负责人")
                    else:
                        log("INFO", "同步推送跳过: 门店负责人与主推送接收人相同，无需重复推送")
                else:
                    log("INFO", "同步推送跳过: 未匹配到门店负责人")
