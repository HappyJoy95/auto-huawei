"""
门店信息管理 API
"""
from fastapi import APIRouter
from pathlib import Path
import yaml
from typing import List, Dict, Any, Optional

router = APIRouter()

STORES_FILE = Path(__file__).parent.parent.parent.parent.parent / "config" / "stores.yaml"


def _load_stores() -> Dict[str, Any]:
    """加载门店配置"""
    if not STORES_FILE.exists():
        return {"stores": []}
    with open(STORES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"stores": []}


def _save_stores(data: Dict[str, Any]):
    """保存门店配置"""
    STORES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STORES_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


@router.get("")
async def get_stores():
    """获取门店列表"""
    return _load_stores()


@router.post("")
async def save_stores(data: Dict[str, Any]):
    """保存门店列表"""
    _save_stores(data)
    return {"success": True, "message": "门店信息已保存"}


def get_store_by_name(name: str) -> Optional[Dict[str, Any]]:
    """根据名称或别称查找门店"""
    data = _load_stores()
    for store in data.get("stores", []):
        if store.get("name") == name or store.get("short_name") == name:
            return store
        if name in store.get("aliases", []):
            return store
    return None


def get_store_userid_map() -> Dict[str, List[str]]:
    """
    构建门店名→userid列表 的映射
    用于企微推送时根据门店名查找接收人
    """
    data = _load_stores()
    mapping: Dict[str, List[str]] = {}
    for store in data.get("stores", []):
        userids = store.get("wechat_userids", [])
        if not userids:
            continue

        # 门店名称
        name = store.get("name")
        if name:
            mapping[name] = userids

        # 简称
        short_name = store.get("short_name")
        if short_name:
            mapping[short_name] = userids

        # 别称
        for alias in store.get("aliases", []):
            if alias:
                mapping[alias] = userids

    return mapping


def get_all_store_codes() -> Dict[str, str]:
    """获取门店名称→代码的映射"""
    data = _load_stores()
    return {
        store.get("name", ""): store.get("code", "")
        for store in data.get("stores", [])
        if store.get("name") and store.get("code")
    }
