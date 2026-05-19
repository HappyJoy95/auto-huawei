"""
任务管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()


class TaskRunRequest(BaseModel):
    params: Optional[Dict[str, Any]] = None


@router.get("/")
async def list_tasks():
    """获取所有任务状态"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        return []
    return scheduler.get_all_tasks()


@router.post("/{task_id}/run")
async def run_task(task_id: str, request: TaskRunRequest = None):
    """立即执行任务"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    success = scheduler.run_task_async(task_id, request.params if request else None)
    return {"success": success, "message": f"Task {task_id} started" if success else "Task already running or not found"}


@router.post("/{task_id}/stop")
async def stop_task(task_id: str):
    """停止任务"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    scheduler.stop_task(task_id)
    return {"success": True, "message": f"Task {task_id} stopped"}


@router.post("/{task_id}/start")
async def start_task(task_id: str):
    """启用任务调度"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    scheduler.enable_task(task_id)
    return {"success": True, "message": f"Task {task_id} scheduled"}


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str, limit: int = 100):
    """获取任务日志"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        return []

    return scheduler.get_task_logs(task_id, limit)
