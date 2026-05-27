"""
路径解析工具 - 动态查找项目根目录

当 shared/ 代码被 macos/ 或 windows/ 的 main.py 通过 sys.path 加载时，
基于 __file__ 的路径会指向 shared/ 下不存在的目录。
此模块通过 sys.path 动态查找包含 modules/ 目录的真实项目根目录。
"""
import os
import sys
from pathlib import Path
from typing import Optional

_cached_root: Optional[Path] = None


def get_project_root() -> Path:
    """
    获取项目根目录（包含 modules/ 和 config/ 的目录）。

    查找策略：
    1. 遍历 sys.path，找到包含 modules/ 子目录的路径
    2. 回退到基于 __file__ 的默认路径
    """
    global _cached_root
    if _cached_root is not None:
        return _cached_root

    env_root = os.environ.get("AUTO_CONTROLLER_ROOT")
    if env_root:
        _cached_root = Path(env_root)
        return _cached_root

    default_root = Path(__file__).parent.parent.parent

    # 遍历 sys.path 查找包含 modules/ 的项目根目录
    for p in sys.path:
        candidate = Path(p)
        if (candidate / "modules").is_dir() and (candidate / "module").is_dir():
            _cached_root = candidate
            return _cached_root

    # 回退：默认路径如果存在 modules/ 则使用
    if (default_root / "modules").is_dir():
        _cached_root = default_root
        return _cached_root

    # 最终回退
    _cached_root = default_root
    return _cached_root
