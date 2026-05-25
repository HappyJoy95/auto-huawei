"""
数据访问 API - 动态根据模块加载数据
"""
import re
from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from module.config.config import DATA_DIR
from module.core.module_manager import module_manager

router = APIRouter()

# 合法文件名：仅允许字母、数字、下划线、连字符
SAFE_FILENAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


@router.get("/{module_name}")
async def get_module_data(module_name: str):
    """获取模块数据"""
    if module_name not in module_manager.modules:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")

    module_data_dir = DATA_DIR / module_name

    # 确保路径仍在 DATA_DIR 下
    if not module_data_dir.resolve().is_relative_to(DATA_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid module name")

    if not module_data_dir.exists():
        return {"data": None, "message": "No data directory"}

    data_files = list(module_data_dir.glob("*.json"))

    if not data_files:
        return {"data": None, "message": "No data files"}

    result = {}
    for data_file in data_files:
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                result[data_file.stem] = json.load(f)
        except Exception as e:
            result[data_file.stem] = {"error": str(e)}

    return {"module": module_name, "data": result}


@router.get("/{module_name}/{file_name}")
async def get_module_data_file(module_name: str, file_name: str):
    """获取模块特定数据文件"""
    if module_name not in module_manager.modules:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")

    # 校验文件名：仅允许安全字符
    if not SAFE_FILENAME_RE.match(file_name):
        raise HTTPException(status_code=400, detail="Invalid file name")

    data_file = DATA_DIR / module_name / f"{file_name}.json"

    # 确保解析后的路径仍在模块数据目录下
    module_data_dir = (DATA_DIR / module_name).resolve()
    if not data_file.resolve().is_relative_to(module_data_dir):
        raise HTTPException(status_code=400, detail="Path traversal detected")

    if not data_file.exists():
        raise HTTPException(status_code=404, detail=f"File {file_name} not found")

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
