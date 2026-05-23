"""
大众点评数据采集任务
"""
from module.tasks.base import BaseTask, TaskResult, TaskStatus
from module.config.config import Config, DATA_DIR
from pathlib import Path
from datetime import datetime
import sys

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from scraper import DianpingScraper


class DianpingTask(BaseTask):
    """大众点评数据采集任务"""

    task_id = "dianping"
    task_name = "大众点评采集"

    def run(self) -> TaskResult:
        self.status = TaskStatus.RUNNING
        start_time = datetime.now()

        try:
            # 数据目录
            dianping_data_dir = DATA_DIR / "dianping"
            dianping_data_dir.mkdir(parents=True, exist_ok=True)
            data_file = dianping_data_dir / "reviews.json"

            # 获取配置
            stores = self.config.get("stores", [])
            max_reviews = self.config.get("max_reviews", 50)
            request_delay = self.config.get("request_delay", 5)
            use_proxy = self.config.get("use_proxy", False)
            proxy_url = self.config.get("proxy_url", "") if use_proxy else None

            if not stores:
                return TaskResult(
                    success=False,
                    message="未配置店铺列表，请先添加要采集的店铺",
                    start_time=start_time,
                    end_time=datetime.now()
                )

            mode_text = "[测试模式] " if self.dry_run else ""
            self.log("INFO", f"{mode_text}开始采集 {len(stores)} 个店铺")
            self.update_progress(5, f"{mode_text}准备采集 {len(stores)} 个店铺...")

            # 创建采集器
            scraper = DianpingScraper(proxy=proxy_url, headless=True)

            # 进度回调
            def progress_callback(current, total, message):
                progress = 5 + int((current / total) * 90)
                self.update_progress(progress, message)
                self.log("INFO", message)

            # 执行采集
            all_data = scraper.fetch_stores(
                stores=stores,
                max_reviews=max_reviews,
                delay=request_delay,
                output_file=str(data_file) if not self.dry_run else None,
                progress_callback=progress_callback
            )

            # 统计结果
            total_reviews = sum(len(d.get('reviews', [])) for d in all_data)
            success_count = sum(1 for d in all_data if d.get('store_info') and not d.get('store_info', {}).get('error'))

            self.status = TaskStatus.COMPLETED
            self.update_progress(100, f"采集完成: {success_count}/{len(stores)} 个店铺, 共 {total_reviews} 条评论")

            # 生成通知内容
            notify_lines = [f"共采集 **{success_count}** 个店铺，**{total_reviews}** 条评论\n"]

            for data in all_data[:5]:  # 最多显示5个店铺
                store_info = data.get('store_info', {})
                if store_info and not store_info.get('error'):
                    name = store_info.get('name', '未知')
                    rating = store_info.get('rating', '-')
                    review_count = len(data.get('reviews', []))
                    notify_lines.append(f"- **{name}** 评分: {rating} | 评论: {review_count}条")

            if len(all_data) > 5:
                notify_lines.append(f"\n... 还有 {len(all_data) - 5} 个店铺")

            notify_lines.append(f"\n⏰ {datetime.now().strftime('%m-%d %H:%M')}")

            return TaskResult(
                success=True,
                message=f"采集完成: {success_count}/{len(stores)} 个店铺, 共 {total_reviews} 条评论",
                data={
                    "total_stores": len(stores),
                    "success_stores": success_count,
                    "total_reviews": total_reviews
                },
                start_time=start_time,
                end_time=datetime.now(),
                notify_title="📊 大众点评采集报告",
                notify_content="\n".join(notify_lines)
            )

        except ImportError as e:
            self.status = TaskStatus.ERROR
            self.log("ERROR", str(e))
            return TaskResult(
                success=False,
                message=f"依赖未安装: {str(e)}",
                error=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )

        except Exception as e:
            self.status = TaskStatus.ERROR
            self.log("ERROR", f"执行失败: {str(e)}")
            return TaskResult(
                success=False,
                message=f"执行失败: {str(e)}",
                error=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
