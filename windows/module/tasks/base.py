"""
任务基类 - 所有自动化任务的基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum
import threading


class TaskStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notify_title: Optional[str] = None
    notify_content: Optional[str] = None


@dataclass
class TaskInfo:
    """任务信息"""
    id: str
    name: str
    status: TaskStatus = TaskStatus.IDLE
    progress: int = 0
    message: str = ""
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class BaseTask(ABC):
    """任务基类"""

    task_id: str = "base"
    task_name: str = "基础任务"

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.status = TaskStatus.IDLE
        self.progress = 0
        self.message = ""
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._status_callback: Optional[Callable] = None
        self._log_callback: Optional[Callable] = None

    @abstractmethod
    def run(self) -> TaskResult:
        """执行任务"""
        pass

    def stop(self):
        """停止任务"""
        self._stop_event.set()
        self.status = TaskStatus.STOPPED

    def pause(self):
        """暂停任务"""
        self._pause_event.set()
        self.status = TaskStatus.PAUSED

    def resume(self):
        """恢复任务"""
        self._pause_event.clear()
        self.status = TaskStatus.RUNNING

    def check_stopped(self) -> bool:
        """检查是否被停止"""
        return self._stop_event.is_set()

    def check_paused(self):
        """检查暂停状态，如果暂停则阻塞"""
        self._pause_event.wait()

    def set_status_callback(self, callback: Callable):
        """设置状态更新回调"""
        self._status_callback = callback

    def set_log_callback(self, callback: Callable):
        """设置日志回调"""
        self._log_callback = callback

    def update_progress(self, progress: int, message: str = ""):
        """更新进度"""
        self.progress = min(100, max(0, progress))
        self.message = message
        if self._status_callback:
            self._status_callback({
                "task_id": self.task_id,
                "status": self.status.value,
                "progress": self.progress,
                "message": self.message
            })
        # 输出到调度器日志
        if self._log_callback and message:
            self._log_callback("INFO", message, self.task_id)

    def log(self, level: str, message: str):
        """输出日志到调度器"""
        if self._log_callback:
            self._log_callback(level, message, self.task_id)

    def get_info(self) -> TaskInfo:
        """获取任务信息"""
        return TaskInfo(
            id=self.task_id,
            name=self.task_name,
            status=self.status,
            progress=self.progress,
            message=self.message,
            enabled=self.config.get("enabled", True)
        )
