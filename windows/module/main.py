"""
Auto Controller - Python 后端入口（模块化架构）
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from module.api.routes import task, config, data
from module.tasks.scheduler import TaskQueueScheduler, set_scheduler
from module.config.config import Config
from module.core.module_manager import module_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    
    # 加载配置
    cfg = Config.load()
    
    # 任务目录配置 - 默认扫描 modules/ 目录
    modules_dir = ROOT_DIR / "modules"
    default_task_dirs = [str(modules_dir)]

    external_task_dirs = cfg.get("task_dirs", [])
    if isinstance(external_task_dirs, str):
        external_task_dirs = [external_task_dirs]

    env_task_dirs = os.environ.get("TASK_DIRS", "").split(";")
    env_task_dirs = [d.strip() for d in env_task_dirs if d.strip()]

    all_task_dirs = default_task_dirs + external_task_dirs + env_task_dirs
    
    # 初始化调度器
    scheduler = TaskQueueScheduler(task_dirs=all_task_dirs, max_concurrent=1)
    set_scheduler(scheduler)
    scheduler.start()
    
    yield
    
    scheduler.stop()
    print("[Scheduler] Stopped")


app = FastAPI(
    title="Auto Controller API",
    description="自动化任务控制器后端 API (模块化架构)",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(data.router, prefix="/api/data", tags=["data"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ===== 模块 API =====

@app.get("/api/modules")
async def get_modules_list():
    """获取所有模块列表"""
    return {"modules": module_manager.get_modules_list()}


@app.get("/api/modules/{module_name}/configs")
async def get_module_configs(module_name: str):
    """获取模块的所有配置"""
    try:
        return module_manager.get_module_configs(module_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/modules/{module_name}/style")
async def get_module_style(module_name: str):
    """获取模块的自定义样式"""
    from pathlib import Path
    module_dir = Path(__file__).parent.parent / "modules" / module_name
    style_file = module_dir / "settings.css"

    if style_file.exists():
        return {"css": style_file.read_text(encoding="utf-8")}
    return {"css": ""}


@app.get("/api/modules/{module_name}/scheduler-config")
async def get_scheduler_config(module_name: str):
    """获取调度器配置"""
    try:
        return module_manager.get_scheduler_config(module_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/api/modules/{module_name}/scheduler-config")
async def save_scheduler_config(module_name: str, config: dict):
    """保存调度器配置"""
    try:
        module_manager.save_scheduler_config(module_name, config)
        # 重新加载调度
        from module.tasks.scheduler import get_scheduler
        scheduler = get_scheduler()
        if scheduler:
            scheduler.reload_task(module_name)
        return {"success": True, "message": "调度器配置已保存"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/modules/{module_name}/module-config")
async def get_module_config(module_name: str):
    """获取模块配置"""
    try:
        return module_manager.get_module_config(module_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/api/modules/{module_name}/module-config")
async def save_module_config(module_name: str, config: dict):
    """保存模块配置"""
    try:
        module_manager.save_module_config(module_name, config)
        return {"success": True, "message": "模块配置已保存"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/modules/reload")
async def reload_modules():
    """重新加载所有模块"""
    module_manager.load_all_modules()
    return {"success": True, "message": "模块已重新加载", "count": len(module_manager.modules)}


# ===== 调度器 API =====

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """获取调度器状态"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        return scheduler.get_status()
    return {"running": False, "waiting": [], "queue": [], "running_now": []}


@app.get("/api/scheduler/task/{module_name}")
async def get_task_scheduler_status(module_name: str):
    """获取单个任务的调度状态"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        return scheduler.get_task_status(module_name)
    return {"status": "idle", "next_run": None}


@app.post("/api/scheduler/task/{module_name}/run-now")
async def run_task_now(module_name: str):
    """立即执行任务"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        success = scheduler.run_now(module_name)
        return {"success": success}
    return {"success": False}


@app.post("/api/scheduler/task/{module_name}/manual-time")
async def set_manual_time(module_name: str, time: str):
    """设置手动执行时间"""
    from module.tasks.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        scheduler.set_manual_time(module_name, time)
        return {"success": True}
    return {"success": False}


@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """获取运行日志"""
    from module.tasks.scheduler import get_logs
    return {"logs": get_logs(limit)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"[API] Starting on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
