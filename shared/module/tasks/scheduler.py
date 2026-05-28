"""
任务队列调度器 - 管理任务的等待、排队、执行状态
"""
import threading
from typing import Dict, List, Optional, Type
from datetime import datetime
from collections import deque
from apscheduler.schedulers.background import BackgroundScheduler

from module.tasks.base import BaseTask, TaskStatus
from module.tasks.loader import TaskLoader
from module.core.module_manager import module_manager
from module.notifier.sender import Notifier
from module.utils.scheduler_utils import calculate_next_run, parse_manual_time

POOL_SIMULATOR = "simulator"
POOL_BROWSER = "browser"
POOL_REPORT = "report"
POOL_TYPES = (POOL_SIMULATOR, POOL_BROWSER, POOL_REPORT)

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


def empty_scheduler_status() -> Dict:
    return {
        "running": False,
        "waiting": [],
        "queue": [],
        "running_now": [],
        "pools": {
            pool_type: {
                "max_concurrent": 1,
                "waiting": [],
                "queue": [],
                "running_now": []
            }
            for pool_type in POOL_TYPES
        }
    }


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
        self.queue_tasks: Dict[str, List[str]] = {pool_type: [] for pool_type in POOL_TYPES}
        self.running_tasks: Dict[str, threading.Thread] = {}  # 运行中: {module_name: thread}
        self.task_pool_types: Dict[str, str] = {}
        self.running_task_pool_types: Dict[str, str] = {}
        self.stopping_tasks = set()

        self.max_concurrent = max_concurrent
        self.pool_max_concurrent = {pool_type: max_concurrent for pool_type in POOL_TYPES}
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

            pool_type = self._normalize_pool_type(module_info.get("meta", {}).get("pool_type"))
            self.task_pool_types[module_name] = pool_type

            # 保存配置
            self.task_configs[module_name] = {
                "scheduler": scheduler_config,
                "module": module_info.get("module_config", {}),
                "pool_type": pool_type
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
        # 先在锁外执行 I/O 操作（读取配置文件）
        module_manager.load_module(module_name)
        module_info = module_manager.modules.get(module_name)

        # 再在锁内更新调度器状态
        with self._lock:
            if not module_info or not module_info.get("has_task"):
                # 从所有队列移除
                self.waiting_tasks.pop(module_name, None)
                self._remove_from_queues(module_name)
                self.task_pool_types.pop(module_name, None)
                return

            scheduler_config = module_info.get("scheduler_config", {})
            module_config = module_info.get("module_config", {})
            pool_type = self._normalize_pool_type(module_info.get("meta", {}).get("pool_type"))
            self.task_pool_types[module_name] = pool_type
            self.task_configs[module_name] = {
                "scheduler": scheduler_config,
                "module": module_config,
                "pool_type": pool_type
            }

            task = self.task_instances.get(module_name)
            if task:
                task.config = module_config

            self._remove_from_queues(module_name)

            # 计算新的下次执行时间
            if scheduler_config.get("enabled", True):
                next_run = self._calculate_next_run(scheduler_config)
                if next_run:
                    self.waiting_tasks[module_name] = next_run
                    add_log("INFO", f"重新调度: {next_run.strftime('%m-%d %H:%M:%S')}", module_name)
            else:
                self.waiting_tasks.pop(module_name, None)

    def _normalize_pool_type(self, pool_type: str) -> str:
        return pool_type if pool_type in POOL_TYPES else POOL_SIMULATOR

    def _get_task_pool(self, module_name: str) -> str:
        return self._normalize_pool_type(self.task_pool_types.get(module_name))

    def _running_count(self, pool_type: str) -> int:
        return sum(1 for task_pool in self.running_task_pool_types.values() if task_pool == pool_type)

    def _is_queued(self, module_name: str) -> bool:
        return any(module_name in queue for queue in self.queue_tasks.values())

    def _remove_from_queues(self, module_name: str):
        for queue in self.queue_tasks.values():
            while module_name in queue:
                queue.remove(module_name)

    def _flatten_queue_tasks(self) -> List[str]:
        result = []
        for pool_type in POOL_TYPES:
            result.extend(self.queue_tasks[pool_type])
        return result

    def _build_waiting_items(self) -> List[Dict]:
        waiting = []
        for name, next_run in sorted(self.waiting_tasks.items(), key=lambda x: x[1]):
            waiting.append({
                "name": name,
                "next_run": next_run.isoformat(),
                "pool_type": self._get_task_pool(name)
            })
        return waiting

    def _build_pool_status(self, waiting: List[Dict]) -> Dict:
        pools = {}
        for pool_type in POOL_TYPES:
            pools[pool_type] = {
                "max_concurrent": self.pool_max_concurrent[pool_type],
                "waiting": [item for item in waiting if item["pool_type"] == pool_type],
                "queue": self.queue_tasks[pool_type].copy(),
                "running_now": [
                    name
                    for name, running_pool in self.running_task_pool_types.items()
                    if running_pool == pool_type
                ]
            }
        return pools

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
                pool_type = self._get_task_pool(module_name)
                if not self._is_queued(module_name):
                    self.queue_tasks[pool_type].append(module_name)
                    add_log("INFO", f"进入 {pool_type} 池队列", module_name)

            # 2. 从各池队列中取出任务执行
            for pool_type in POOL_TYPES:
                queue = self.queue_tasks[pool_type]
                while queue and self._running_count(pool_type) < self.pool_max_concurrent[pool_type]:
                    module_name = queue.pop(0)
                    self._start_task(module_name)

    def _start_task(self, module_name: str):
        """启动任务执行"""
        task = self.task_instances.get(module_name)
        if not task or module_name in self.running_tasks:
            return

        pool_type = self._get_task_pool(module_name)
        thread = threading.Thread(target=self._run_task, args=(module_name,))
        self.running_tasks[module_name] = thread
        self.running_task_pool_types[module_name] = pool_type
        thread.start()
        add_log("INFO", f"开始执行 {pool_type} 池任务", module_name)

    def _run_task(self, module_name: str):
        """执行任务"""
        task = self.task_instances.get(module_name)
        if not task:
            return

        is_test = getattr(task, '_run_mode', 'normal') == 'test'
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

            # 测试模式标记通知，不写入数据
            if is_test:
                result.message = f"[测试] {result.message}"
                if result.notify_title:
                    result.notify_title = f"[测试] {result.notify_title}"

            Notifier.notify_task_result(
                module_name=module_name,
                module_display_name=module_display_name,
                module_config=module_config,
                result={
                    "success": result.success,
                    "message": result.message,
                    "notify_title": result.notify_title,
                    "notify_content": result.notify_content,
                    "attachment_path": result.attachment_path
                },
                log_callback=add_log
            )

        except Exception as e:
            task.status = TaskStatus.ERROR
            add_log("ERROR", f"执行异常: {str(e)}", module_name)

            error_msg = f"[测试] 执行异常: {str(e)}" if is_test else f"执行异常: {str(e)}"
            Notifier.notify_task_result(
                module_name=module_name,
                module_display_name=module_display_name,
                module_config=module_config,
                result={"success": False, "message": error_msg},
                log_callback=add_log
            )

        finally:
            task._run_mode = "normal"
            with self._lock:
                self.running_tasks.pop(module_name, None)
                self.running_task_pool_types.pop(module_name, None)

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
        return calculate_next_run(config, log_warning=lambda msg, mod: add_log("WARNING", msg, mod))

    def get_status(self) -> Dict:
        """获取调度器状态"""
        with self._lock:
            waiting = self._build_waiting_items()
            return {
                "running": self._running,
                "waiting": waiting,
                "queue": self._flatten_queue_tasks(),
                "running_now": list(self.running_tasks.keys()),
                "pools": self._build_pool_status(waiting)
            }

    def get_task_status(self, module_name: str) -> Dict:
        """获取单个任务状态"""
        with self._lock:
            status = "idle"
            next_run = None
            pool_type = self._get_task_pool(module_name)

            if module_name in self.running_tasks:
                status = "running"
            elif self._is_queued(module_name):
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
            "pool_type": pool_type,
            "task": task_info
        }

    def run_now(self, module_name: str, mode: str = "normal") -> bool:
        """立即执行任务"""
        with self._lock:
            if module_name not in self.task_instances:
                return False

            if module_name in self.running_tasks:
                return False

            # 设置运行模式（测试/正常）
            task = self.task_instances.get(module_name)
            task._run_mode = mode

            if self._is_queued(module_name):
                return True

            # 从等待中移除
            self.waiting_tasks.pop(module_name, None)

            self.stopping_tasks.discard(module_name)

            # 加入对应池队列首位
            pool_type = self._get_task_pool(module_name)
            self.queue_tasks[pool_type].insert(0, module_name)
            add_log("INFO", f"进入 {pool_type} 池队列", module_name)

            return True

    def stop_task(self, module_name: str) -> bool:
        with self._lock:
            task = self.task_instances.get(module_name)
            if not task:
                return False

            if self._is_queued(module_name):
                self._remove_from_queues(module_name)
                add_log("WARNING", "已从队列移除", module_name)
                return True

            if module_name in self.running_tasks:
                self.stopping_tasks.add(module_name)
                task.stop()
                add_log("WARNING", "已发送停止请求，等待任务安全退出", module_name)
                return True

            task.stop()
            add_log("WARNING", "任务已标记停止", module_name)
            return True

    def set_manual_time(self, module_name: str, time_str: str):
        """设置手动执行时间"""
        with self._lock:
            if module_name not in self.task_configs:
                return

            self.task_configs[module_name]["scheduler"]["manual_time"] = time_str

            # 解析时间
            next_run = parse_manual_time(time_str)
            if next_run:
                self.waiting_tasks[module_name] = next_run
                # 保存到配置文件
                module_manager.modules[module_name]["scheduler_config"]["manual_time"] = time_str
            else:
                add_log("WARNING", f"手动时间设置失败: {time_str}", module_name)


# 全局实例
_scheduler: Optional[TaskQueueScheduler] = None


def get_scheduler() -> TaskQueueScheduler:
    global _scheduler
    return _scheduler


def set_scheduler(scheduler: TaskQueueScheduler):
    global _scheduler
    _scheduler = scheduler
