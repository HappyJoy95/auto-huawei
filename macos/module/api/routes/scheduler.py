"""
调度器 API
"""
from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/status")
async def get_scheduler_status():
    """获取调度器状态"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        return scheduler.get_status()
    return {"running": False, "waiting": [], "queue": [], "running_now": []}


@router.get("/task/{module_name}")
async def get_task_scheduler_status(module_name: str):
    """获取单个任务的调度状态"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        return scheduler.get_task_status(module_name)
    return {"status": "idle", "next_run": None}


@router.post("/task/{module_name}/run-now")
async def run_task_now(module_name: str, mode: str = "normal"):
    """立即执行任务，mode=test 表示测试模式（不写数据文件）"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        success = scheduler.run_now(module_name, mode=mode)
        return {"success": success}
    return {"success": False}


@router.post("/task/{module_name}/manual-time")
async def set_manual_time(module_name: str, time: str):
    """设置手动执行时间"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        scheduler.set_manual_time(module_name, time)
        return {"success": True}
    return {"success": False}
