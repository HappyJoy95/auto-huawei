"""
模块管理 API
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from module.core.module_manager import module_manager

router = APIRouter()


@router.get("")
async def get_modules_list():
    """获取所有模块列表"""
    return {"modules": module_manager.get_modules_list()}


@router.get("/{module_name}/configs")
async def get_module_configs(module_name: str):
    """获取模块的所有配置"""
    try:
        return module_manager.get_module_configs(module_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{module_name}/scheduler-config")
async def get_scheduler_config(module_name: str):
    """获取调度器配置"""
    try:
        return module_manager.get_scheduler_config(module_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{module_name}/scheduler-config")
async def save_scheduler_config(module_name: str, config: dict):
    """保存调度器配置"""
    try:
        module_manager.save_scheduler_config(module_name, config)
        from module.tasks.scheduler import get_scheduler
        scheduler = get_scheduler()
        if scheduler:
            scheduler.reload_task(module_name)
        return {"success": True, "message": "调度器配置已保存"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{module_name}/module-config")
async def get_module_config(module_name: str):
    """获取模块配置"""
    try:
        return module_manager.get_module_config(module_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{module_name}/module-config")
async def save_module_config(module_name: str, config: dict):
    """保存模块配置"""
    try:
        module_manager.save_module_config(module_name, config)
        from module.tasks.scheduler import get_scheduler
        scheduler = get_scheduler()
        if scheduler:
            scheduler.reload_task(module_name)
        return {"success": True, "message": "模块配置已保存"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{module_name}/style")
async def get_module_style(module_name: str):
    """获取模块自定义样式"""
    try:
        style = module_manager.get_module_style(module_name)
        return {"style": style, "has_style": style is not None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reload")
async def reload_modules():
    """重新加载所有模块"""
    module_manager.load_all_modules()
    return {"success": True, "message": "模块已重新加载", "count": len(module_manager.modules)}
