# 模块管理器 - 动态加载和管理所有模块
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from module.utils.scheduler_utils import calculate_next_run
from module.utils.paths import get_project_root

PROJECT_ROOT = get_project_root()
SHARED_ROOT = Path(os.environ.get("AUTO_CONTROLLER_SHARED_ROOT", PROJECT_ROOT.parent / "shared"))
MODULE_DIRS = [path for path in (SHARED_ROOT / "modules", PROJECT_ROOT / "modules") if path.is_dir()]


class ModuleManager:
    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.load_all_modules()

    def _get_module_dirs(self, module_name: str) -> Tuple[Path, Path]:
        module_dirs = [root / module_name for root in MODULE_DIRS if (root / module_name).is_dir()]
        code_dir = next((path for path in module_dirs if (path / "meta.yaml").exists()), None)
        if code_dir is None:
            raise ValueError(f"Module {module_name} not found")
        config_dir = next((path for path in module_dirs if path.parent == PROJECT_ROOT / "modules"), code_dir)
        config_dir.mkdir(parents=True, exist_ok=True)
        return code_dir, config_dir

    def load_all_modules(self):
        self.modules = {}
        module_names = []
        for root in MODULE_DIRS:
            for module_dir in root.iterdir():
                if module_dir.is_dir() and not module_dir.name.startswith("_") and (module_dir / "meta.yaml").exists():
                    if module_dir.name not in module_names:
                        module_names.append(module_dir.name)

        for module_name in module_names:
            self.load_module(module_name)

    def load_module(self, module_name: str):
        code_dir, config_dir = self._get_module_dirs(module_name)
        meta_file = code_dir / "meta.yaml"
        config_yaml = config_dir / "config.yaml"
        config_json = config_dir / "config.json"
        settings_file = code_dir / "settings.yaml"
        settings_css = code_dir / "settings.css"
        task_file = code_dir / "task.py"

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

        scheduler_config = {"enabled": True}
        if config_yaml.exists():
            with open(config_yaml, "r", encoding="utf-8") as f:
                scheduler_config.update(yaml.safe_load(f) or {})

        module_config = {}
        if config_json.exists():
            with open(config_json, "r", encoding="utf-8") as f:
                module_config = json.load(f) or {}

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
            "path": str(code_dir),
            "config_path": str(config_dir)
        }

    def _calculate_next_run(self, scheduler_config: Dict[str, Any]) -> Optional[datetime]:
        return calculate_next_run(scheduler_config)

    def get_modules_list(self) -> List[Dict[str, Any]]:
        result = []
        for m in self.modules.values():
            scheduler_config = m["scheduler_config"]
            enabled = scheduler_config.get("enabled", True)

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
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")
        m = self.modules[module_name]
        return {
            "scheduler": m["scheduler_config"],
            "module": m["module_config"],
            "settings_def": m.get("settings_def", {"fields": []})
        }

    def get_settings_def(self, module_name: str) -> Dict[str, Any]:
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")
        return self.modules[module_name].get("settings_def", {"fields": []})

    def get_scheduler_config(self, module_name: str) -> Dict[str, Any]:
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")
        return self.modules[module_name]["scheduler_config"]

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")
        return self.modules[module_name]["module_config"]

    def save_scheduler_config(self, module_name: str, config: Dict[str, Any]):
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")

        config_file = Path(self.modules[module_name]["config_path"]) / "config.yaml"

        from module.utils.file_utils import atomic_write
        atomic_write(config_file, yaml.dump(config, allow_unicode=True, default_flow_style=False))

        self.modules[module_name]["scheduler_config"] = config
        return True

    def save_module_config(self, module_name: str, config: Dict[str, Any]):
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")

        config_file = Path(self.modules[module_name]["config_path"]) / "config.json"

        from module.utils.file_utils import atomic_write
        atomic_write(config_file, json.dumps(config, ensure_ascii=False, indent=2))

        self.modules[module_name]["module_config"] = config
        return True

    def get_module_style(self, module_name: str) -> Optional[str]:
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")

        style_file = Path(self.modules[module_name]["path"]) / "settings.css"

        if style_file.exists():
            with open(style_file, "r", encoding="utf-8") as f:
                return f.read()
        return None


module_manager = ModuleManager()
