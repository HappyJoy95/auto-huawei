"""
抖音数据采集任务
"""
from module.tasks.base import BaseTask, TaskResult, TaskStatus
from module.config.config import Config, DATA_DIR
from pathlib import Path
from datetime import datetime
import sys

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from scraper import DouyinWebScraper


class DouyinTask(BaseTask):
    """抖音数据采集任务"""

    task_id = "douyin"
    task_name = "抖音采集"

    def run(self) -> TaskResult:
        self.status = TaskStatus.RUNNING
        start_time = datetime.now()

        try:
            # 数据文件
            data_file = DATA_DIR / "douyin_data.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)

            self.update_progress(10, "启动浏览器...")

            # 获取配置
            browser_config = Config.get_browser_config()
            headless = self.config.get("headless", browser_config.get("headless", True))
            accounts = self.config.get("accounts", [])
            max_posts = self.config.get("max_posts_per_store", 50)

            if not accounts:
                return TaskResult(
                    success=False,
                    message="未配置抖音账号列表",
                    start_time=start_time,
                    end_time=datetime.now()
                )

            # 创建采集器
            scraper = DouyinWebScraper(headless=headless)

            # 登录
            if not scraper.login():
                self.status = TaskStatus.ERROR
                return TaskResult(
                    success=False,
                    message="抖音登录失败，请检查浏览器或手动扫码登录",
                    start_time=start_time,
                    end_time=datetime.now()
                )

            self.update_progress(30, f"开始采集 {len(accounts)} 个账号...")

            # 执行采集
            posts = scraper.fetch_stores(
                stores=accounts,
                max_posts_per_store=max_posts,
                output_file=str(data_file)
            )

            scraper.close()

            self.status = TaskStatus.COMPLETED
            self.update_progress(100, f"采集完成，共 {len(posts)} 条视频")

            return TaskResult(
                success=True,
                message=f"采集完成，共 {len(posts)} 条视频",
                data={"total": len(posts)},
                start_time=start_time,
                end_time=datetime.now()
            )

        except Exception as e:
            self.status = TaskStatus.ERROR
            return TaskResult(
                success=False,
                message=f"执行失败: {str(e)}",
                error=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
