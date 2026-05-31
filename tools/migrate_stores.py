"""
将巡检模块的门店配置迁移到全局 stores.yaml
"""
import json
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
INSPECTION_CONFIG = PROJECT_ROOT / "windows" / "modules" / "inspection" / "config.json"
STORES_FILE = PROJECT_ROOT / "config" / "stores.yaml"


def migrate():
    if not INSPECTION_CONFIG.exists():
        print(f"[SKIP] 巡检配置文件不存在: {INSPECTION_CONFIG}")
        return

    with open(INSPECTION_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)

    raw_stores = config.get("stores", [])
    if not raw_stores:
        print("[SKIP] 巡检配置中无门店数据")
        return

    stores = []
    for s in raw_stores:
        stores.append({
            "name": s.get("name", ""),
            "short_name": s.get("short_name", ""),
            "code": s.get("code", ""),
            "wechat_userids": [],
            "aliases": [],
        })

    STORES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STORES_FILE, "w", encoding="utf-8") as f:
        yaml.dump({"stores": stores}, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"[OK] 已迁移 {len(stores)} 个门店到 {STORES_FILE}")


if __name__ == "__main__":
    migrate()
