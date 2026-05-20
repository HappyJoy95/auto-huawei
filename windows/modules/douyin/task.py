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
            # 数据目录
            douyin_data_dir = DATA_DIR / "douyin"
            douyin_data_dir.mkdir(parents=True, exist_ok=True)
            data_file = douyin_data_dir / "posts.json"

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

            # 生成新增视频 CSV 附件
            attachment_path = None
            if posts:
                import csv
                csv_file = douyin_data_dir / f"douyin_new_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                csv_file.parent.mkdir(parents=True, exist_ok=True)
                with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['门店名称', '标题', '点赞数', '视频链接', '采集时间'])
                    for p in posts:
                        writer.writerow([
                            p.store_name,
                            p.title,
                            p.likes or 0,
                            p.post_link or '',
                            p.crawl_time.strftime('%Y-%m-%d %H:%M:%S')
                        ])
                attachment_path = str(csv_file)

            return TaskResult(
                success=True,
                message=f"采集完成，共 {len(posts)} 条视频",
                data={"total": len(posts)},
                start_time=start_time,
                end_time=datetime.now(),
                attachment_path=attachment_path
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
