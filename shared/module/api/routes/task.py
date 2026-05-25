"""
任务管理 API
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter()


@router.get("/")
async def list_tasks():
    """获取所有任务状态"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        return {"running": False, "waiting": [], "queue": [], "running_now": []}
    return scheduler.get_status()


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """获取单个任务状态"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    return scheduler.get_task_status(task_id)


@router.post("/{task_id}/run")
async def run_task(task_id: str, mode: Optional[str] = "normal"):
    """立即执行任务"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    success = scheduler.run_now(task_id, mode=mode or "normal")
    if not success:
        raise HTTPException(status_code=409, detail=f"Task {task_id} is already running")
    return {"success": True, "message": f"Task {task_id} started"}


@router.post("/{task_id}/stop")
async def stop_task(task_id: str):
    """停止任务"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    task = scheduler.task_instances.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task.stop()
    return {"success": True, "message": f"Task {task_id} stopped"}


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str, limit: int = 100):
    """获取任务日志（按模块过滤）"""
    from module.tasks.scheduler import get_logs
    all_logs = get_logs(limit=limit * 5)
    filtered = [log for log in all_logs if log.get("module") == task_id]
    return filtered[-limit:]
