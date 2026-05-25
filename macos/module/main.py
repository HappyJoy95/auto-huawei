"""
Auto Controller - Python 后端入口（模块化架构）
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# 优先使用 shared/ 中的共享模块代码
SHARED_DIR = ROOT_DIR.parent / "shared"
if SHARED_DIR.is_dir():
    sys.path.insert(0, str(SHARED_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from module.api.routes import task, config, data, modules, scheduler
from module.tasks.scheduler import TaskQueueScheduler, set_scheduler, get_logs
from module.config.config import Config


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
    allow_origins=[
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(task.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(modules.router, prefix="/api/modules", tags=["modules"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/logs")
async def get_logs_endpoint(limit: int = 100):
    """获取运行日志"""
    return {"logs": get_logs(limit)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"[API] Starting on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
