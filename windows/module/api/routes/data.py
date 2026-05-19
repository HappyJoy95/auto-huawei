"""
数据访问 API - 动态根据模块加载数据
"""
from fastapi import APIRouter
import json
from pathlib import Path
from module.config.config import DATA_DIR
from module.core.module_manager import module_manager

router = APIRouter()


@router.get("/{module_name}")
async def get_module_data(module_name: str):
    """获取模块数据"""
    # 检查模块是否存在
    if module_name not in module_manager.modules:
        return {"error": f"Module {module_name} not found", "data": None}

    # 数据文件路径: data/{module_name}/*.json
    module_data_dir = DATA_DIR / module_name

    if not module_data_dir.exists():
        return {"data": None, "message": "No data directory"}

    # 查找所有 json 文件
    data_files = list(module_data_dir.glob("*.json"))

    if not data_files:
        return {"data": None, "message": "No data files"}

    # 返回所有数据
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
    # 检查模块是否存在
    if module_name not in module_manager.modules:
        return {"error": f"Module {module_name} not found"}

    data_file = DATA_DIR / module_name / f"{file_name}.json"

    if not data_file.exists():
        return {"error": f"File {file_name} not found"}

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}
