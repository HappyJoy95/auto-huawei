from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import os


class BaseChannel(ABC):
    """消息渠道抽象基类"""

    name: str = ""  # 渠道标识
    target_key: str = ""  # 配置中的目标字段名

    @classmethod
    @abstractmethod
    def get_target(
        cls, module_config: Dict, global_config: Dict, result: Dict = None
    ) -> str:
        """解析目标地址，支持动态映射"""
        pass

    @classmethod
    @abstractmethod
    def send(
        cls,
        target: str,
        title: str,
        content: str,
        attachment_path: str = None,
        mock: bool = False,
        **kwargs,
    ) -> Union[bool, Dict]:
        """
        发送消息
        :param mock: Mock 模式下返回 dict 而不实际发送
        :return: 成功返回 True，失败返回 False，Mock 模式返回 dict
        """
        pass

    @classmethod
    def get_config(cls, key: str, default: Any = None) -> Any:
        """获取配置的通用方法"""
        return os.environ.get(key) or default
