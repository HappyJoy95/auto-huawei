"""
配置管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import yaml
from pathlib import Path

router = APIRouter()

CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config"


class ConfigUpdateRequest(BaseModel):
    value: Any


class StoreItem(BaseModel):
    name: str
    short_name: Optional[str] = ""
    code: Optional[str] = ""
    douyin_url: Optional[str] = ""


@router.get("")
async def get_all_config():
    """获取所有配置"""
    from module.config.config import Config
    return Config.load()


@router.get("/general")
async def get_general_config():
    """获取通用配置"""
    config_file = CONFIG_DIR / "general.yaml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return {"success": True, "config": yaml.safe_load(f) or {}}
    return {"success": True, "config": {}}


@router.put("/general")
async def save_general_config(config: Dict[str, Any]):
    """保存通用配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_file = CONFIG_DIR / "general.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    return {"success": True}


@router.get("/{key:path}")
async def get_config(key: str):
    """获取配置项"""
    from module.config.config import Config
    value = Config.get(key)
    if value is None:
        return {"key": key, "value": None}
    return {"key": key, "value": value}


@router.put("/{key:path}")
async def set_config(key: str, request: ConfigUpdateRequest):
    """设置配置项"""
    from module.config.config import Config
    Config.save_by_key(key, request.value)
    return {"success": True, "key": key}


# 门店管理 API
@router.get("/stores/list")
async def get_stores():
    """获取门店列表"""
    from module.config.config import Config
    stores = Config.get_stores()
    return {"stores": stores, "total": len(stores)}


@router.post("/stores/add")
async def add_store(store: StoreItem):
    """添加门店"""
    from module.config.config import Config
    stores = Config.get_stores()
    stores.append(store.dict())
    Config.set_stores(stores)
    return {"success": True, "message": "添加成功"}


@router.put("/stores/{index}")
async def update_store(index: int, store: StoreItem):
    """更新门店"""
    from module.config.config import Config
    stores = Config.get_stores()
    if index < 0 or index >= len(stores):
        raise HTTPException(status_code=400, detail="无效的索引")
    stores[index] = store.dict()
    Config.set_stores(stores)
    return {"success": True, "message": "更新成功"}


@router.delete("/stores/{index}")
async def delete_store(index: int):
    """删除门店"""
    from module.config.config import Config
    stores = Config.get_stores()
    if index < 0 or index >= len(stores):
        raise HTTPException(status_code=400, detail="无效的索引")
    stores.pop(index)
    Config.set_stores(stores)
    return {"success": True, "message": "删除成功"}
