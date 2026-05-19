"""
配置管理模块
"""
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from copy import deepcopy

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
TASKS_FILE = CONFIG_DIR / "tasks.yaml"

# 数据目录
DATA_DIR = Path(__file__).parent.parent.parent / "data"


class Config:
    """配置管理类"""

    _instance: Optional['Config'] = None
    _data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """加载所有配置"""
        config = {}

        # 主配置
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config.update(yaml.safe_load(f) or {})

        # 任务配置
        if TASKS_FILE.exists():
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                config['tasks'] = yaml.safe_load(f) or {}

        cls._data = config
        return deepcopy(config)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """获取配置项"""
        if not cls._data:
            cls.load()

        keys = key.split('.')
        value = cls._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return deepcopy(value) if value is not None else default

    @classmethod
    def set(cls, key: str, value: Any):
        """设置配置项"""
        if not cls._data:
            cls.load()

        keys = key.split('.')
        data = cls._data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = deepcopy(value)

    @classmethod
    def save(cls):
        """保存配置到文件"""
        cls._save_main_config()
        cls._save_tasks_config()

    @classmethod
    def _save_main_config(cls):
        """保存主配置"""
        main_config = {k: v for k, v in cls._data.items() if k not in ['tasks']}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(main_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    @classmethod
    def _save_tasks_config(cls):
        """保存任务配置"""
        if 'tasks' in cls._data:
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(cls._data['tasks'], f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    @classmethod
    def save_by_key(cls, key: str, value: Any):
        """根据 key 保存到对应文件"""
        cls.set(key, value)

        if key.startswith('tasks'):
            cls._save_tasks_config()
        else:
            cls._save_main_config()

    @classmethod
    def get_browser_config(cls) -> dict:
        """获取浏览器配置"""
        return cls.get('browser', {
            'headless': True,
            'timeout': 60000,
            'download_path': './data/downloads'
        })
