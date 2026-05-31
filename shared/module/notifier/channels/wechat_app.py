"""
企业微信应用消息渠道
支持推送给指定人员，根据门店动态映射
"""
import os
import time
import requests
from typing import Dict, Any, Optional, List
from .base import BaseChannel
from module.utils.paths import get_project_root
import yaml


class WechatAppChannel(BaseChannel):
    """企业微信应用消息"""

    name = "wechat_app"
    target_key = "notify_wechat_app_target"
    store_field_key = "wechat_app_store_field"

    _token_cache: Dict = {"token": None, "expires_at": 0}

    @classmethod
    def get_global_config(cls) -> Dict[str, Any]:
        """获取全局配置"""
        config_file = get_project_root() / "config" / "general.yaml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    @classmethod
    def get_stores_config(cls) -> List[Dict[str, Any]]:
        """获取门店配置"""
        stores_file = get_project_root() / "config" / "stores.yaml"
        if stores_file.exists():
            with open(stores_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("stores", [])
        return []

    @classmethod
    def _get_app_config(cls) -> tuple:
        """获取企业微信应用配置（环境变量优先，回退到 general.yaml）"""
        global_config = cls.get_global_config()
        corpid = os.environ.get("WECHAT_CORP_ID") or global_config.get("wechat_corpid", "")
        corpsecret = os.environ.get("WECHAT_AGENT_SECRET") or global_config.get("wechat_corpsecret", "")
        agentid = os.environ.get("WECHAT_AGENT_ID") or global_config.get("wechat_agentid", "")
        return corpid, corpsecret, agentid

    @classmethod
    def _build_alias_index_from_stores(cls) -> Dict[str, List[str]]:
        """
        从 stores.yaml 构建门店名→userid列表 的映射
        """
        stores = cls.get_stores_config()
        index: Dict[str, List[str]] = {}
        for store in stores:
            userids = store.get("wechat_userids", [])
            if not userids:
                continue

            # 门店名称
            name = store.get("name")
            if name:
                index[name] = userids

            # 简称
            short_name = store.get("short_name")
            if short_name:
                index[short_name] = userids

            # 别称
            for alias in store.get("aliases", []):
                if alias:
                    index[alias] = userids

        return index

    @classmethod
    def _build_alias_index(cls, targets_map: Dict) -> Dict[str, list]:
        """
        构建别名→userid列表 的倒排索引（一个门店可对应多个负责人）
        兼容旧格式 general.yaml 中的 wechat_app_targets
        """
        index: Dict[str, list] = {}
        for key, value in targets_map.items():
            if isinstance(value, dict):
                # 旧格式: userid → {name, aliases}
                userid = key
                aliases = value.get("aliases", [])
                for alias in aliases:
                    if alias:
                        index.setdefault(alias, [])
                        if userid not in index[alias]:
                            index[alias].append(userid)
            elif isinstance(value, str):
                # 旧格式: 门店名 → userid
                index.setdefault(key, [])
                if value not in index[key]:
                    index[key].append(value)
        return index

    @classmethod
    def get_target(
        cls, module_config: Dict, global_config: Dict, result: Dict = None
    ) -> str:
        """
        解析目标地址
        优先级：
        1. 静态：直接配置的 userid
        2. 动态：根据 result.data 中的门店名列表查映射表（支持别名）
        3. 默认：环境变量配置的默认接收人
        """
        # 1. 静态：直接配置的 userid
        target = module_config.get(cls.target_key)
        if target:
            return target

        # 2. 动态：从 result.data 中取门店名列表，查映射表
        store_target = cls.get_target_by_store(module_config, global_config, result)
        if store_target:
            return store_target

        # 3. 默认
        return os.environ.get("WECHAT_DEFAULT_USERID", "")

    @classmethod
    def get_target_by_store(
        cls, module_config: Dict, global_config: Dict, result: Dict = None
    ) -> str:
        """
        仅根据门店名列表查映射表，返回门店负责人 userid
        用于同步推送场景：模块接收人 + 门店负责人 分别推送
        优先从 stores.yaml 读取，回退到 general.yaml 的 wechat_app_targets
        """
        if not result:
            return ""

        data = result.get("data") or {}
        store_field = module_config.get(cls.store_field_key, "store_names")
        store_names = data.get(store_field, [])
        if not store_names:
            return ""

        # 优先从 stores.yaml 读取
        alias_index = cls._build_alias_index_from_stores()
        if not alias_index:
            # 回退到 general.yaml 的 wechat_app_targets
            targets_map = global_config.get("wechat_app_targets", {})
            if targets_map:
                alias_index = cls._build_alias_index(targets_map)

        if not alias_index:
            return ""

        userids = []
        seen = set()
        for name in store_names:
            matched = alias_index.get(name, [])
            for userid in matched:
                if userid not in seen:
                    userids.append(userid)
                    seen.add(userid)
        return "|".join(userids) if userids else ""

    @classmethod
    def _is_configured(cls) -> bool:
        """检查是否已配置企业微信应用"""
        corpid, corpsecret, agentid = cls._get_app_config()
        return bool(corpid and corpsecret and agentid)

    @classmethod
    def _get_access_token(cls) -> Optional[str]:
        """获取 access_token，带缓存"""
        # 检查缓存
        if (
            cls._token_cache["token"]
            and time.time() < cls._token_cache["expires_at"]
        ):
            return cls._token_cache["token"]

        corpid, corpsecret, _ = cls._get_app_config()

        if not corpid or not corpsecret:
            print("[WechatAppChannel] CorpID or Secret not configured")
            return None

        # 企业微信获取 token 接口
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": corpid,
            "corpsecret": corpsecret,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                token = result["access_token"]
                expires_in = result.get("expires_in", 7200)
                cls._token_cache = {
                    "token": token,
                    "expires_at": time.time() + expires_in - 300,  # 提前5分钟过期
                }
                return token
            else:
                print(f"[WechatAppChannel] Token error: {result.get('errmsg')}")
        except Exception as e:
            print(f"[WechatAppChannel] Token exception: {e}")

        return None

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
        发送企业微信应用消息
        :param target: 接收人 userid，多人用 | 分隔
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
                "message": "Mock 模式：消息已构造但未发送（未配置企业微信应用）",
            }

        if not target:
            print("[WechatAppChannel] Target is empty")
            return False

        # 获取 access_token
        token = cls._get_access_token()
        if not token:
            return False

        _, _, agentid = cls._get_app_config()

        # 企业微信发送应用消息接口（markdown 类型）
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        # 企微 markdown 消息：title 作为一级标题，content 作为正文
        md_content = f"## {title}\n{content}"
        data = {
            "touser": target,
            "msgtype": "markdown",
            "agentid": int(agentid),
            "markdown": {
                "content": md_content,
            },
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                print(f"[WechatAppChannel] Sent to {target}: {title}")
                return True
            else:
                print(f"[WechatAppChannel] Error: {result.get('errmsg')}")
        except Exception as e:
            print(f"[WechatAppChannel] Exception: {e}")

        return False
