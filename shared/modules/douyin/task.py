"""
抖音数据采集任务
"""
from module.tasks.base import BaseTask, TaskResult, TaskStatus
from module.config.config import DATA_DIR
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import contextlib
import sys
import traceback

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from scraper import DouyinWebScraper


class TaskLogWriter:
    def __init__(self, task: BaseTask, level: str):
        self.task = task
        self.level = level
        self._buffer = ""

    def write(self, text: str):
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if line:
                self.task.log(self.level, line)

    def flush(self):
        line = self._buffer.strip()
        if line:
            self.task.log(self.level, line)
        self._buffer = ""


class DouyinTask(BaseTask):
    """抖音数据采集任务"""

    task_id = "douyin"
    task_name = "抖音采集"

    def run(self) -> TaskResult:
        self.status = TaskStatus.RUNNING
        start_time = datetime.now()
        scraper = None

        try:
            douyin_data_dir = DATA_DIR / "douyin"
            douyin_data_dir.mkdir(parents=True, exist_ok=True)
            data_file = douyin_data_dir / "posts.json"

            headless = self.config.get("headless", True)
            accounts = self.config.get("accounts", [])
            max_posts = self.config.get("max_posts_per_store", 50)

            self.log("INFO", f"抖音数据目录: {douyin_data_dir}")
            self.log("INFO", f"抖音数据文件: {data_file}")
            self.log("INFO", f"抖音配置: headless={headless}, accounts={len(accounts)}, max_posts_per_store={max_posts}")
            for index, account in enumerate(accounts, start=1):
                account_url = account.get('douyin_url') or account.get('url')
                self.log("INFO", f"账号[{index}]: name={account.get('name', '')}, short_name={account.get('short_name', '')}, url={'已配置' if account_url else '未配置'}")

            if not accounts:
                self.log("ERROR", "未配置抖音账号列表")
                return TaskResult(
                    success=False,
                    message="未配置抖音账号列表",
                    start_time=start_time,
                    end_time=datetime.now()
                )

            self.update_progress(10, "启动浏览器...")
            scraper = DouyinWebScraper(headless=headless)
            self.log("INFO", f"cookies 文件: {scraper.cookies_file}")
            self.log("INFO", f"浏览器数据目录: {scraper.user_data_dir}")

            with contextlib.redirect_stdout(TaskLogWriter(self, "INFO")), contextlib.redirect_stderr(TaskLogWriter(self, "ERROR")):
                self.update_progress(20, "检查抖音登录状态...")
                if not scraper.login():
                    self.status = TaskStatus.ERROR
                    self.log("ERROR", "抖音登录失败，可能是 cookies 失效、扫码超时或浏览器启动失败")
                    return TaskResult(
                        success=False,
                        message="抖音登录失败，请检查浏览器或手动扫码登录",
                        start_time=start_time,
                        end_time=datetime.now()
                    )

                self.update_progress(35, f"开始采集 {len(accounts)} 个账号...")
                posts = scraper.fetch_stores(
                    stores=accounts,
                    max_posts_per_store=max_posts,
                    output_file=str(data_file)
                )

            self.status = TaskStatus.COMPLETED

            # 只保留新增内容：对比 data_file 中的已有数据，找出新增的帖子
            new_posts = []
            try:
                if data_file.exists():
                    with open(data_file, 'r', encoding='utf-8') as f:
                        import json
                        existing_data = json.load(f)
                        existing_links = {post.get('post_link') for post in existing_data.get('posts', [])}

                        # 找出新增的帖子（以采集时间为准，采集时间在任务开始后的为新增）
                        for p in posts:
                            if p.crawl_time >= start_time:
                                new_posts.append(p)

                self.update_progress(100, f"采集完成，共 {len(posts)} 条视频，新增 {len(new_posts)} 条")
                self.log("INFO", f"抖音采集完成: total={len(posts)}, new={len(new_posts)}")
            except Exception as e:
                self.log("ERROR", f"筛选新增内容失败: {e}")
                new_posts = posts

            attachment_path = None
            if new_posts:
                import csv
                csv_file = douyin_data_dir / f"douyin_new_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                csv_file.parent.mkdir(parents=True, exist_ok=True)
                with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['门店名称', '标题', '点赞数', '视频链接', '采集时间'])
                    for p in new_posts:
                        writer.writerow([
                            p.store_name,
                            p.title,
                            p.likes or 0,
                            p.post_link or '',
                            p.crawl_time.strftime('%Y-%m-%d %H:%M:%S')
                        ])
                attachment_path = str(csv_file)
                self.log("INFO", f"抖音新增 CSV: {csv_file} (仅包含本次新增的 {len(new_posts)} 条内容)")

            notify_title = "📊 抖音采集报告"
            notify_content = self._format_notify_content(new_posts, len(posts), accounts)

            return TaskResult(
                success=True,
                message=f"采集完成，共 {len(posts)} 条视频，新增 {len(new_posts)} 条",
                data={
                    "total": len(posts),
                    "new": len(new_posts),
                    "store_names": list({p.store_name for p in new_posts if p.store_name}),
                },
                start_time=start_time,
                end_time=datetime.now(),
                notify_title=notify_title,
                notify_content=notify_content,
                attachment_path=attachment_path
            )

        except Exception as e:
            self.status = TaskStatus.ERROR
            error_detail = traceback.format_exc()
            self.log("ERROR", f"抖音任务异常: {e}")
            self.log("ERROR", error_detail)
            return TaskResult(
                success=False,
                message=f"执行失败: {str(e)}",
                error=error_detail,
                start_time=start_time,
                end_time=datetime.now()
            )
        finally:
            if scraper:
                try:
                    scraper.close()
                except Exception as e:
                    self.log("ERROR", f"关闭抖音浏览器失败: {e}")

    def _format_notify_content(self, new_posts: list, total_posts: int, accounts: list) -> str:
        stats = defaultdict(lambda: {"count": 0, "likes": 0})
        for post in new_posts:
            stats[post.store_name]["count"] += 1
            stats[post.store_name]["likes"] += post.likes or 0

        top = sorted(
            [
                {"name": name, "count": data["count"], "likes": data["likes"]}
                for name, data in stats.items()
            ],
            key=lambda item: (-item["count"], -item["likes"], item["name"])
        )[:5]

        account_names = [a.get("name") or a.get("short_name") for a in accounts if a.get("name") or a.get("short_name")]
        zero_stores = [name for name in account_names if name not in stats]
        total_likes = sum(item["likes"] for item in top) + sum(
            data["likes"] for name, data in stats.items() if name not in {item["name"] for item in top}
        )

        lines = [
            f"**本次新增：**{len(new_posts)}条 | **累计：**{total_posts}条 | **新增获赞：**{total_likes}",
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
