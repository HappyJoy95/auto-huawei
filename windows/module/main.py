"""
Auto Controller - Windows Python backend entrypoint
"""
import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHARED_ROOT = PROJECT_ROOT.parent / "shared"

os.environ["AUTO_CONTROLLER_ROOT"] = str(PROJECT_ROOT)
os.environ["AUTO_CONTROLLER_SHARED_ROOT"] = str(SHARED_ROOT)
sys.path.insert(0, str(SHARED_ROOT))

runpy.run_path(str(SHARED_ROOT / "module" / "main.py"), run_name="__main__")
