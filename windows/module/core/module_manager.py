# 模块管理器 - 动态加载和管理所有模块
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from croniter import croniter

MODULES_DIR = Path(__file__).parent.parent.parent / "modules"


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
            if module_dir.is_dir() and not module_dir.name.startswith("_"):
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
        now = datetime.now()

        # 检查是否有定时配置
        has_schedule = scheduler_config.get("interval") or scheduler_config.get("schedule")

        # 手动设置的时间（没有其他定时配置时使用）
        if not has_schedule:
            manual_time = scheduler_config.get("manual_time") or "01-01 00:00:00"
            try:
                parts = manual_time.split()
                if len(parts) == 2:
                    date_parts = parts[0].split("-")
                    time_parts = parts[1].split(":")

                    month = int(date_parts[0])
                    day = int(date_parts[1])
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    second = int(time_parts[2]) if len(time_parts) > 2 else 0

                    next_run = now.replace(month=month, day=day, hour=hour, minute=minute, second=second, microsecond=0)

                    if next_run > now:
                        return next_run
            except Exception:
                pass

        # 间隔执行
        interval = scheduler_config.get("interval")
        if interval:
            start_time = scheduler_config.get("interval_start", "00:00")
            end_time = scheduler_config.get("interval_end", "23:59")
            days = scheduler_config.get("interval_days", [1, 2, 3, 4, 5])

            # 检查今天是否在生效日期内
            today_dow = now.weekday()  # 0=周一, 6=周日
            # 转换: 前端用 1=周一, 0=周日; Python weekday 用 0=周一, 6=周日
            py_to_frontend = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
            if py_to_frontend[today_dow] not in days:
                # 找下一个生效日期
                for i in range(1, 8):
                    next_day = (today_dow + i) % 7
                    if py_to_frontend[next_day] in days:
                        # 返回下一个生效日期的开始时间
                        h, m = map(int, start_time.split(":"))
                        next_run = now.replace(hour=h, minute=m, second=0, microsecond=0)
                        from datetime import timedelta
                        next_run += timedelta(days=i)
                        return next_run
                return None

            # 检查当前时间是否在生效时间段内
            h, m = map(int, start_time.split(":"))
            start_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            h, m = map(int, end_time.split(":"))
            end_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)

            if now < start_dt:
                return start_dt
            elif now > end_dt:
                # 今天已过，找下一个生效日期
                for i in range(1, 8):
                    next_day = (today_dow + i) % 7
                    if py_to_frontend[next_day] in days:
                        h, m = map(int, start_time.split(":"))
                        from datetime import timedelta
                        next_run = now.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=i)
                        return next_run
                return None
            else:
                # 在生效时间段内，计算下一个间隔时间
                from datetime import timedelta
                minutes_since_start = (now - start_dt).total_seconds() / 60
                intervals_passed = int(minutes_since_start / interval)
                next_run = start_dt + timedelta(minutes=(intervals_passed + 1) * interval)
                if next_run > end_dt:
                    # 超出今天的时间范围
                    for i in range(1, 8):
                        next_day = (today_dow + i) % 7
                        if py_to_frontend[next_day] in days:
                            h, m = map(int, start_time.split(":"))
                            next_run = now.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=i)
                            return next_run
                    return None
                return next_run

        # Cron 表达式
        schedule = scheduler_config.get("schedule")
        if schedule:
            schedules = schedule if isinstance(schedule, list) else [schedule]
            next_runs = []

            for sch in schedules:
                if isinstance(sch, str):
                    try:
                        cron = croniter(sch, now)
                        next_runs.append(cron.get_next(datetime))
                    except Exception:
                        pass

            if next_runs:
                return min(next_runs)

        return None

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

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

        self.modules[module_name]["scheduler_config"] = config
        return True

    def save_module_config(self, module_name: str, config: Dict[str, Any]):
        """保存模块配置"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")

        module_dir = MODULES_DIR / module_name
        config_file = module_dir / "config.json"

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

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
