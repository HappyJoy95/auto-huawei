"""
任务队列调度器 - 管理任务的等待、排队、执行状态
"""
import threading
import time
from typing import Dict, List, Optional, Type
from datetime import datetime, timedelta
from collections import deque
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from croniter import croniter

from module.tasks.base import BaseTask, TaskStatus, TaskInfo
from module.tasks.loader import TaskLoader
from module.core.module_manager import module_manager
from module.notifier.sender import Notifier

# 全局日志队列
_log_queue: deque = deque(maxlen=500)
_log_lock = threading.Lock()


def add_log(level: str, msg: str, module: str = "system"):
    """添加日志"""
    now = datetime.now()
    entry = {
        "time": now.strftime("%H:%M:%S"),
        "level": level,
        "msg": msg,
        "module": module,
        "timestamp": now.isoformat()
    }
    with _log_lock:
        _log_queue.append(entry)


def get_logs(limit: int = 100) -> List[Dict]:
    """获取日志"""
    with _log_lock:
        return list(_log_queue)[-limit:]


class TaskQueueScheduler:
    """任务队列调度器"""

    def __init__(self, task_dirs: List[str] = None, max_concurrent: int = 1):
        """
        初始化调度器
        :param task_dirs: 任务目录列表
        :param max_concurrent: 最大并发任务数
        """
        self.scheduler = BackgroundScheduler()
        self.task_classes: Dict[str, Type[BaseTask]] = {}
        self.task_instances: Dict[str, BaseTask] = {}

        # 任务状态
        self.task_configs: Dict[str, Dict] = {}  # 模块配置
        self.waiting_tasks: Dict[str, datetime] = {}  # 等待中: {module_name: next_run_time}
        self.queue_tasks: List[str] = []  # 队列中: [module_name, ...]
        self.running_tasks: Dict[str, threading.Thread] = {}  # 运行中: {module_name: thread}

        self.max_concurrent = max_concurrent
        self._lock = threading.Lock()
        self._running = False

        self.task_loader = TaskLoader(task_dirs)

    def add_task_dir(self, dir_path: str):
        """添加任务目录"""
        self.task_loader.add_task_dir(dir_path)

    def load_tasks(self):
        """加载任务类"""
        self.task_classes = self.task_loader.load_tasks()

    def start(self):
        """启动调度器"""
        if not self.task_classes:
            self.load_tasks()

        module_manager.load_all_modules()
        add_log("INFO", "调度器启动", "scheduler")

        # 初始化所有模块
        for module_name, module_info in module_manager.modules.items():
            if not module_info.get("has_task"):
                continue

            scheduler_config = module_info.get("scheduler_config", {})
            if not scheduler_config.get("enabled", True):
                continue

            # 保存配置
            self.task_configs[module_name] = {
                "scheduler": scheduler_config,
                "module": module_info.get("module_config", {})
            }

            # 创建任务实例
            task_class = self.task_classes.get(module_name)
            if task_class:
                task_instance = task_class(config=self.task_configs[module_name]["module"])
                task_instance.set_log_callback(add_log)  # 设置日志回调
                self.task_instances[module_name] = task_instance

            # 计算下次执行时间并加入等待队列
            next_run = self._calculate_next_run(scheduler_config)
            if next_run:
                self.waiting_tasks[module_name] = next_run
                add_log("INFO", f"{module_name} 计划执行: {next_run.strftime('%m-%d %H:%M:%S')}", module_name)

        # 启动检查循环
        self._running = True
        self.scheduler.add_job(self._check_loop, 'interval', seconds=1, id='_check_loop')
        self.scheduler.start()

        add_log("INFO", f"已加载 {len(self.waiting_tasks)} 个任务", "scheduler")

    def stop(self):
        """停止调度器"""
        self._running = False
        self.scheduler.shutdown(wait=False)

        for module_name, thread in self.running_tasks.items():
            if thread.is_alive():
                task = self.task_instances.get(module_name)
                if task:
                    task.stop()

        add_log("WARNING", "调度器已停止", "scheduler")

    def reload_task(self, module_name: str):
        """重新加载某个模块的调度"""
        with self._lock:
            module_manager.load_module(module_name)
            module_info = module_manager.modules.get(module_name)

            if not module_info or not module_info.get("has_task"):
                # 从所有队列移除
                self.waiting_tasks.pop(module_name, None)
                if module_name in self.queue_tasks:
                    self.queue_tasks.remove(module_name)
                return

            scheduler_config = module_info.get("scheduler_config", {})
            self.task_configs[module_name] = {
                "scheduler": scheduler_config,
                "module": module_info.get("module_config", {})
            }

            # 计算新的下次执行时间
            if scheduler_config.get("enabled", True):
                next_run = self._calculate_next_run(scheduler_config)
                if next_run:
                    self.waiting_tasks[module_name] = next_run
                    add_log("INFO", f"重新调度: {next_run.strftime('%m-%d %H:%M:%S')}", module_name)
            else:
                self.waiting_tasks.pop(module_name, None)

            # 从排队中移除（如果有）
            if module_name in self.queue_tasks:
                self.queue_tasks.remove(module_name)

    def _check_loop(self):
        """主检查循环 - 每秒执行"""
        if not self._running:
            return

        now = datetime.now()

        with self._lock:
            # 1. 检查等待中的任务是否到时间
            to_queue = []
            for module_name, next_run in list(self.waiting_tasks.items()):
                if next_run <= now:
                    to_queue.append(module_name)

            for module_name in to_queue:
                del self.waiting_tasks[module_name]
                self.queue_tasks.append(module_name)
                add_log("INFO", "进入队列等待执行", module_name)

            # 2. 从队列中取出任务执行
            while self.queue_tasks and len(self.running_tasks) < self.max_concurrent:
                module_name = self.queue_tasks.pop(0)
                self._start_task(module_name)

    def _start_task(self, module_name: str):
        """启动任务执行"""
        task = self.task_instances.get(module_name)
        if not task:
            return

        thread = threading.Thread(target=self._run_task, args=(module_name,))
        self.running_tasks[module_name] = thread
        thread.start()
        add_log("INFO", "开始执行", module_name)

    def _run_task(self, module_name: str):
        """执行任务"""
        task = self.task_instances.get(module_name)
        if not task:
            return

        module_config = self.task_configs.get(module_name, {}).get("module", {})
        module_display_name = module_manager.modules.get(module_name, {}).get("meta", {}).get("display_name", module_name)

        try:
            task.status = TaskStatus.RUNNING
            task._stop_event.clear()
            result = task.run()

            if result.success:
                task.status = TaskStatus.COMPLETED
                add_log("SUCCESS", f"执行完成: {result.message}", module_name)
            else:
                task.status = TaskStatus.ERROR
                add_log("ERROR", f"执行失败: {result.message}", module_name)

            task.last_run = datetime.now()

            # 发送通知
            Notifier.notify_task_result(
                module_name=module_name,
                module_display_name=module_display_name,
                module_config=module_config,
                result={"success": result.success, "message": result.message}
            )

        except Exception as e:
            task.status = TaskStatus.ERROR
            add_log("ERROR", f"执行异常: {str(e)}", module_name)

            # 发送失败通知
            Notifier.notify_task_result(
                module_name=module_name,
                module_display_name=module_display_name,
                module_config=module_config,
                result={"success": False, "message": str(e)}
            )

        finally:
            with self._lock:
                self.running_tasks.pop(module_name, None)

                # 计算下次执行时间并放回等待队列
                config = self.task_configs.get(module_name, {})
                scheduler_config = config.get("scheduler", {})

                if scheduler_config.get("enabled", True):
                    next_run = self._calculate_next_run(scheduler_config)
                    if next_run:
                        self.waiting_tasks[module_name] = next_run
                        add_log("INFO", f"下次执行: {next_run.strftime('%m-%d %H:%M:%S')}", module_name)

    def _calculate_next_run(self, config: Dict) -> Optional[datetime]:
        """计算下次运行时间"""
        now = datetime.now()

        # 检查是否有定时配置（interval 或 schedule）
        has_schedule = config.get("interval") or config.get("schedule")

        # 手动设置的时间（没有其他定时配置时使用）
        if not has_schedule:
            manual_time = config.get("manual_time") or "01-01 00:00:00"
            try:
                # 格式: mm-dd HH:MM:SS
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
        interval = config.get("interval")
        if interval:
            start_time = config.get("interval_start", "00:00")
            end_time = config.get("interval_end", "23:59")
            days = config.get("interval_days", [1, 2, 3, 4, 5])

            # 检查今天是否在生效日期内
            today_dow = now.weekday()
            py_to_frontend = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}

            if py_to_frontend[today_dow] in days:
                h, m = map(int, start_time.split(":"))
                start_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
                h, m = map(int, end_time.split(":"))
                end_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)

                if now < start_dt:
                    return start_dt
                elif now <= end_dt:
                    minutes_since_start = (now - start_dt).total_seconds() / 60
                    intervals_passed = int(minutes_since_start / interval)
                    next_run = start_dt + timedelta(minutes=(intervals_passed + 1) * interval)
                    if next_run <= end_dt:
                        return next_run

            # 找下一个生效日期
            for i in range(1, 8):
                next_day = (today_dow + i) % 7
                if py_to_frontend[next_day] in days:
                    h, m = map(int, start_time.split(":"))
                    next_run = now.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=i)
                    return next_run

            return None

        # Cron 表达式
        schedule = config.get("schedule")
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

    def get_status(self) -> Dict:
        """获取调度器状态"""
        with self._lock:
            waiting = []
            for name, next_run in sorted(self.waiting_tasks.items(), key=lambda x: x[1]):
                waiting.append({
                    "name": name,
                    "next_run": next_run.isoformat()
                })

            return {
                "running": self._running,
                "waiting": waiting,
                "queue": self.queue_tasks.copy(),
                "running_now": list(self.running_tasks.keys())
            }

    def get_task_status(self, module_name: str) -> Dict:
        """获取单个任务状态"""
        status = "idle"
        next_run = None

        if module_name in self.running_tasks:
            status = "running"
        elif module_name in self.queue_tasks:
            status = "queued"
        elif module_name in self.waiting_tasks:
            status = "waiting"
            next_run = self.waiting_tasks[module_name].isoformat()

        task = self.task_instances.get(module_name)
        task_info = None
        if task:
            info = task.get_info()
            task_info = {
                "status": info.status.value,
                "progress": info.progress,
                "message": info.message
            }

        return {
            "status": status,
            "next_run": next_run,
            "task": task_info
        }

    def run_now(self, module_name: str) -> bool:
        """立即执行任务"""
        with self._lock:
            if module_name in self.running_tasks:
                return False

            # 从等待中移除
            self.waiting_tasks.pop(module_name, None)

            # 加入队列首位
            if module_name not in self.queue_tasks:
                self.queue_tasks.insert(0, module_name)

            return True

    def set_manual_time(self, module_name: str, time_str: str):
        """设置手动执行时间"""
        with self._lock:
            if module_name not in self.task_configs:
                return

            self.task_configs[module_name]["scheduler"]["manual_time"] = time_str

            # 解析时间
            try:
                now = datetime.now()
                parts = time_str.split()
                date_parts = parts[0].split("-")
                time_parts = parts[1].split(":")

                month = int(date_parts[0])
                day = int(date_parts[1])
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2]) if len(time_parts) > 2 else 0

                next_run = now.replace(month=month, day=day, hour=hour, minute=minute, second=second, microsecond=0)

                if next_run > now:
                    self.waiting_tasks[module_name] = next_run
                    # 保存到配置文件
                    module_manager.modules[module_name]["scheduler_config"]["manual_time"] = time_str
            except Exception:
                pass


# 全局实例
_scheduler: Optional[TaskQueueScheduler] = None


def get_scheduler() -> TaskQueueScheduler:
    global _scheduler
    return _scheduler


def set_scheduler(scheduler: TaskQueueScheduler):
    global _scheduler
    _scheduler = scheduler
