"""
数据访问 API
"""
from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter()

# 数据目录
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "social-media-monitor" / "data"
JDDJ_DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "jddj_orders"


@router.get("/xiaohongshu")
async def get_xiaohongshu_data():
    """获取小红书数据"""
    data_file = DATA_DIR / "xiaohongshu_data.json"
    if not data_file.exists():
        return {"posts": []}
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@router.get("/douyin")
async def get_douyin_data():
    """获取抖音数据"""
    data_file = DATA_DIR / "douyin_data.json"
    if not data_file.exists():
        return {"posts": []}
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@router.get("/inspection")
async def get_inspection_data():
    """获取点检数据"""
    data_file = DATA_DIR / "inspection_data.json"
    if not data_file.exists():
        return {"stores": []}
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@router.get("/orders")
async def get_orders_data():
    """获取京东订单数据"""
    data_file = JDDJ_DATA_DIR / "pending_orders.json"
    if not data_file.exists():
        return {"时间": None, "待接单数量": 0, "待打印数量": 0, "订单列表": []}
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)
