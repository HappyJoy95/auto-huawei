# 模块管理器 - 动态加载和管理所有模块
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from module.utils.scheduler_utils import calculate_next_run
from module.utils.paths import get_project_root

MODULES_DIR = get_project_root() / "modules"


class ModuleManager:
    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.load_all_modules()

    def load_all_modules(self):
        """加载所有模块"""
        self.modules = {}
        if not MODULES_DIR.exists():
            return

        for module_dir in MODULES_DIR.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith("_") and (module_dir / "meta.yaml").exists():
                self.load_module(module_dir.name)

    def load_module(self, module_name: str):
        """加载单个模块"""
        module_dir = MODULES_DIR / module_name
        meta_file = module_dir / "meta.yaml"
        config_yaml = module_dir / "config.yaml"   # 调度器配置
        config_json = module_dir / "config.json"   # 模块配置
        settings_file = module_dir / "settings.yaml"  # 设置定义
        settings_css = module_dir / "settings.css"  # 自定义样式
        task_file = module_dir / "task.py"

        # 读取元信息
        meta = {
            "name": module_name,
            "display_name": module_name.replace("_", " ").title(),
            "description": "",
            "icon": "apps",
            "enabled": True
        }
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta.update(yaml.safe_load(f) or {})

        # 读取调度器配置 (config.yaml)
        scheduler_config = {"enabled": True}
        if config_yaml.exists():
            with open(config_yaml, "r", encoding="utf-8") as f:
                scheduler_config.update(yaml.safe_load(f) or {})

        # 读取模块配置 (config.json)
        module_config = {}
        if config_json.exists():
            with open(config_json, "r", encoding="utf-8") as f:
                module_config = json.load(f) or {}

        # 读取设置定义 (settings.yaml)
        settings_def = {"fields": []}
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                settings_def = yaml.safe_load(f) or {"fields": []}

        has_task = task_file.exists()
        has_style = settings_css.exists()

        self.modules[module_name] = {
            "meta": meta,
            "scheduler_config": scheduler_config,
            "module_config": module_config,
            "settings_def": settings_def,
            "has_task": has_task,
            "has_style": has_style,
            "path": str(module_dir)
        }

    def _calculate_next_run(self, scheduler_config: Dict[str, Any]) -> Optional[datetime]:
        """计算下次运行时间"""
        return calculate_next_run(scheduler_config)

    def get_modules_list(self) -> List[Dict[str, Any]]:
        """获取所有模块列表"""
        result = []
        for m in self.modules.values():
            scheduler_config = m["scheduler_config"]
            enabled = scheduler_config.get("enabled", True)

            # 计算下次运行时间
            next_run = None
            if enabled and m["has_task"]:
                next_run = self._calculate_next_run(scheduler_config)

            result.append({
                "name": m["meta"]["name"],
                "display_name": m["meta"]["display_name"],
                "description": m["meta"]["description"],
                "icon": m["meta"]["icon"],
                "enabled": enabled,
                "has_task": m["has_task"],
                "next_run": next_run.isoformat() if next_run else None
            })
        return result

    def get_module_configs(self, module_name: str) -> Dict[str, Any]:
        """获取模块的所有配置"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")
        m = self.modules[module_name]
        return {
            "scheduler": m["scheduler_config"],
            "module": m["module_config"],
            "settings_def": m.get("settings_def", {"fields": []})
        }

    def get_settings_def(self, module_name: str) -> Dict[str, Any]:
        """获取模块设置定义"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")
        return self.modules[module_name].get("settings_def", {"fields": []})

    def get_scheduler_config(self, module_name: str) -> Dict[str, Any]:
        """获取调度器配置"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")
        return self.modules[module_name]["scheduler_config"]

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """获取模块配置"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")
        return self.modules[module_name]["module_config"]

    def save_scheduler_config(self, module_name: str, config: Dict[str, Any]):
        """保存调度器配置"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")

        module_dir = MODULES_DIR / module_name
        config_file = module_dir / "config.yaml"

        from module.utils.file_utils import atomic_write
        atomic_write(config_file, yaml.dump(config, allow_unicode=True, default_flow_style=False))

        self.modules[module_name]["scheduler_config"] = config
        return True

    def save_module_config(self, module_name: str, config: Dict[str, Any]):
        """保存模块配置"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")

        module_dir = MODULES_DIR / module_name
        config_file = module_dir / "config.json"

        from module.utils.file_utils import atomic_write
        atomic_write(config_file, json.dumps(config, ensure_ascii=False, indent=2))

        self.modules[module_name]["module_config"] = config
        return True

    def get_module_style(self, module_name: str) -> Optional[str]:
        """获取模块自定义样式"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")

        module_dir = MODULES_DIR / module_name
        style_file = module_dir / "settings.css"

        if style_file.exists():
            with open(style_file, "r", encoding="utf-8") as f:
                return f.read()
        return None


# 全局模块管理器实例
module_manager = ModuleManager()
