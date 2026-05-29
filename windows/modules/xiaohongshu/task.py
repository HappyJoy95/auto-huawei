"""
小红书数据采集任务
"""
from module.tasks.base import BaseTask, TaskResult, TaskStatus
from module.config.config import Config, DATA_DIR
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import sys

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from scraper import XiaohongshuScraper


def is_previous_week_post(post_time: str, now: datetime) -> bool:
    try:
        post_date = datetime.strptime(post_time, "%y-%m-%d").date()
    except (TypeError, ValueError):
        return False

    this_monday = now.date() - timedelta(days=now.weekday())
    previous_monday = this_monday - timedelta(days=7)
    return previous_monday <= post_date < this_monday


class XiaohongshuTask(BaseTask):
    """小红书数据采集任务"""

    task_id = "xiaohongshu"
    task_name = "小红书采集"

    def run(self) -> TaskResult:
        self.status = TaskStatus.RUNNING
        start_time = datetime.now()

        try:
            # 数据文件
            data_file = DATA_DIR / "xiaohongshu_data.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)

            self.update_progress(10, "连接模拟器...")

            # 获取配置（ADB端口使用全局配置）
            adb_port = Config.get_adb_port()
            stores = self.config.get("stores", [])
            max_posts = self.config.get("max_posts_per_store", 100)

            if not stores:
                return TaskResult(
                    success=False,
                    message="未配置门店列表",
                    start_time=start_time,
                    end_time=datetime.now()
                )

            # 创建采集器
            scraper = XiaohongshuScraper(adb_port=adb_port)

            # 登录
            if not scraper.login():
                self.status = TaskStatus.ERROR
                return TaskResult(
                    success=False,
                    message="连接模拟器失败，请确保 MuMu 模拟器已启动",
                    start_time=start_time,
                    end_time=datetime.now()
                )

            self.update_progress(30, f"开始采集 {len(stores)} 个门店...")

            # 执行采集
            posts = scraper.fetch_stores(
                store_names=stores,
                max_posts_per_store=max_posts,
                output_file=str(data_file),
                mode='full'
            )

            scraper.close()

            self.status = TaskStatus.COMPLETED
            self.update_progress(100, f"采集完成，共 {len(posts)} 条帖子")

            attachment_path = None
            report_posts = [p for p in posts if is_previous_week_post(p.post_time, start_time)]
            if report_posts:
                import csv
                csv_file = DATA_DIR / f"xiaohongshu_new_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                csv_file.parent.mkdir(parents=True, exist_ok=True)
                with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['门店名称', '标题', '点赞数', '发布时间', '采集时间'])
                    for p in report_posts:
                        writer.writerow([
                            p.store_name,
                            p.title,
                            p.likes or 0,
                            p.post_time or '',
                            p.crawl_time.strftime('%Y-%m-%d %H:%M:%S')
                        ])
                attachment_path = str(csv_file)

            notify_title = "📊 小红书采集报告"
            notify_content = self._format_notify_content(report_posts, len(posts), stores)

            return TaskResult(
                success=True,
                message=f"采集完成，共 {len(posts)} 条新增帖子，推送上周新增 {len(report_posts)} 条",
                data={"total": len(posts), "weekly_total": len(report_posts)},
                start_time=start_time,
                end_time=datetime.now(),
                notify_title=notify_title,
                notify_content=notify_content,
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

    def _format_notify_content(self, report_posts: list, total_posts: int, stores: list) -> str:
        stats = defaultdict(lambda: {"count": 0, "likes": 0})
        for post in report_posts:
            stats[post.store_name]["count"] += 1
            stats[post.store_name]["likes"] += post.likes or 0

        top = sorted(
            [
                {"name": name, "count": data["count"], "likes": data["likes"]}
                for name, data in stats.items()
            ],
            key=lambda item: (-item["count"], -item["likes"], item["name"])
        )[:5]

        zero_stores = [name for name in stores if name and name not in stats]
        total_likes = sum(data["likes"] for data in stats.values())

        lines = [
            f"**上周新增：**{len(report_posts)}条 | **本次采集：**{total_posts}条 | **上周获赞：**{total_likes}",
        ]

        if top:
            lines.extend(["", "**TOP门店**"])
            for index, item in enumerate(top, 1):
                lines.append(f"> {index}. {item['name']} - {item['count']}条 / {item['likes']}赞")

        if zero_stores:
            shown = "、".join(zero_stores[:8])
            extra = f" 等{len(zero_stores)}家" if len(zero_stores) > 8 else ""
            lines.extend(["", f"**零新增：**{shown}{extra}"])

        lines.append(f"\n_{datetime.now().strftime('%m-%d %H:%M')}_")
        return "\n".join(lines)
