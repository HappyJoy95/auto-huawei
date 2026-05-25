"""
文件工具 - 原子写入等
"""
import os
import tempfile
from pathlib import Path
from typing import Union


def atomic_write(file_path: Union[str, Path], content: str, encoding: str = "utf-8"):
    """
    原子写入文件：先写入临时文件，再原子重命名。
    防止写入过程中崩溃导致文件损坏。
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 在同一目录创建临时文件（确保同一文件系统，rename 才是原子的）
    fd, tmp_path = tempfile.mkstemp(
        dir=str(file_path.parent),
        prefix=f".{file_path.name}.tmp",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
        # 原子重命名（同一文件系统下是原子操作）
        os.replace(tmp_path, str(file_path))
    except Exception:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
