"""
任务模块加载器 - 动态从指定目录加载任务模块
"""
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Type, Optional
import inspect

from module.tasks.base import BaseTask


class TaskLoader:
    """任务模块加载器"""
    
    def __init__(self, task_dirs: List[str] = None):
        """
        初始化加载器
        :param task_dirs: 任务目录列表，支持相对路径和绝对路径
        """
        self.task_dirs = task_dirs or []
        self.loaded_tasks: Dict[str, Type[BaseTask]] = {}
    
    def add_task_dir(self, dir_path: str):
        """添加任务目录"""
        path = Path(dir_path).resolve()
        if path.exists() and path.is_dir():
            self.task_dirs.append(str(path))
        else:
            print(f"[TaskLoader] Warning: Directory not found: {dir_path}")
    
    def load_tasks(self) -> Dict[str, Type[BaseTask]]:
        """
        从所有目录加载任务
        :return: 任务类字典 {task_id: TaskClass}
        """
        self.loaded_tasks.clear()
        
        for task_dir in self.task_dirs:
            self._load_from_directory(task_dir)
        
        print(f"[TaskLoader] Loaded {len(self.loaded_tasks)} tasks: {list(self.loaded_tasks.keys())}")
        return self.loaded_tasks
    
    def _load_from_directory(self, dir_path: str):
        """从单个目录加载任务"""
        path = Path(dir_path).resolve()

        if not path.exists():
            print(f"[TaskLoader] Directory not found: {path}")
            return

        # 扫描每个子目录中的 task.py 文件
        for subdir in path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("_"):
                task_file = subdir / "task.py"
                if task_file.exists():
                    self._load_task_file(task_file, subdir)
    
    def _load_task_file(self, py_file: Path, module_dir: Path):
        """加载单个 Python 文件中的任务类"""
        try:
            # 清除可能冲突的模块缓存
            for key in list(sys.modules.keys()):
                if key == 'scraper' or key.endswith('.scraper'):
                    del sys.modules[key]

            # 将模块目录加入 sys.path（放在最前面）
            module_dir_str = str(module_dir)
            if module_dir_str in sys.path:
                sys.path.remove(module_dir_str)
            sys.path.insert(0, module_dir_str)

            # 计算模块名
            module_name = f"modules.{module_dir.name}.task"

            # 动态导入模块
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找模块中继承 BaseTask 的类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseTask) and
                    obj is not BaseTask and
                    hasattr(obj, "task_id") and
                    obj.task_id != "base"):

                    task_id = obj.task_id
                    if task_id in self.loaded_tasks:
                        print(f"[TaskLoader] Warning: Duplicate task_id '{task_id}', overwriting")

                    self.loaded_tasks[task_id] = obj
                    print(f"[TaskLoader] Found task: {obj.task_name} ({task_id}) from {module_dir.name}/task.py")

        except Exception as e:
            import traceback
            print(f"[TaskLoader] Error loading {module_dir.name}/task.py: {e}")
            traceback.print_exc()
    
    def get_task_class(self, task_id: str) -> Optional[Type[BaseTask]]:
        """获取指定 ID 的任务类"""
        return self.loaded_tasks.get(task_id)
    
    def get_all_task_classes(self) -> Dict[str, Type[BaseTask]]:
        """获取所有加载的任务类"""
        return self.loaded_tasks.copy()
