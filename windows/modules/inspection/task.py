"""
点检采集任务
"""
from module.tasks.base import BaseTask, TaskResult, TaskStatus
from module.config.config import Config, DATA_DIR
from pathlib import Path
from datetime import datetime
import json
import sys

# 添加当前目录到路径，以便导入本地 scraper
sys.path.insert(0, str(Path(__file__).parent))
from scraper import SmartSalesScraper


class InspectionTask(BaseTask):
    """门店点检采集任务"""

    task_id = "inspection"
    task_name = "门店点检"

    def run(self) -> TaskResult:
        self.status = TaskStatus.RUNNING
        start_time = datetime.now()
        self.log("INFO", f"开始执行点检任务, 时间: {start_time.strftime('%H:%M:%S')}")

        try:
            # 数据文件
            data_file = DATA_DIR / "inspection_data.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)
            self.log("INFO", f"数据文件路径: {data_file}")

            # 获取之前的记录
            prev_latest = self._get_latest_records(data_file)
            prev_count = 0
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    prev_data = json.load(f)
                    prev_count = len(prev_data.get('stores', []))
                self.log("INFO", f"已有历史记录: {prev_count} 条")
            else:
                self.log("INFO", "无历史记录文件")

            self.update_progress(10, "连接模拟器...")

            # 从模块配置读取门店列表，从全局配置读取 ADB 端口
            stores = self.config.get('stores', [])
            dry_run = self.dry_run
            adb_port = Config.get_adb_port()
            self.log("INFO", f"ADB端口: {adb_port}")
            self.log("INFO", f"门店数量: {len(stores) if stores else 0}")
            if dry_run:
                self.log("INFO", "测试模式: 不会写入数据文件")

            if not stores:
                self.log("ERROR", "门店列表为空，请检查配置")
                return TaskResult(
                    success=False,
                    message="门店列表为空，请检查配置",
                    start_time=start_time,
                    end_time=datetime.now()
                )

            # 执行采集
            self.log("INFO", "创建 SmartSalesScraper 实例...")
            scraper = SmartSalesScraper(adb_port=adb_port, log_callback=self.log)
            try:
                self.update_progress(30, "正在采集点检数据...")
                self.log("INFO", "开始调用 fetch_inspection_data...")
                results = scraper.fetch_inspection_data(
                    stores=[{'name': s} for s in stores] if stores and isinstance(stores[0], str) else stores,
                    output_file=str(data_file),
                    dry_run=dry_run
                )
                self.log("INFO", f"fetch_inspection_data 返回，结果数量: {len(results) if results else 0}")

                if results is None:
                    results = []

                new_count = len(results) - prev_count
                self.log("INFO", f"采集完成，总数: {len(results)}，新增: {new_count}")
                self.update_progress(70, f"采集完成，新增 {new_count} 条")

                # 找出有变化的门店
                if dry_run:
                    # 测试模式: data_file 未写入，从内存结果直接计算变化
                    changed_stores = self._find_changed_stores_from_results(prev_latest, results)
                else:
                    changed_stores = self._find_changed_stores(prev_latest, data_file)
                self.log("INFO", f"有变化的门店: {len(changed_stores)} 个")

                self.status = TaskStatus.COMPLETED
                self.update_progress(100, f"完成，共 {len(results)} 条记录")
                self.log("SUCCESS", f"任务完成，共 {len(results)} 条记录，新增 {new_count} 条")

                # 生成通知内容
                notify_title = f"📊 门店点检报告"
                notify_content = self._format_notify_content(changed_stores, new_count, len(results), prev_latest)

                return TaskResult(
                    success=True,
                    message=f"采集完成，共 {len(results)} 条记录，新增 {new_count} 条",
                    data={"total": len(results), "new": new_count, "changed": len(changed_stores)},
                    start_time=start_time,
                    end_time=datetime.now(),
                    notify_title=notify_title,
                    notify_content=notify_content
                )

            except Exception as e:
                self.log("ERROR", f"采集过程异常: {str(e)}")
                import traceback
                self.log("ERROR", traceback.format_exc())
                raise
            finally:
                self.log("INFO", "关闭 scraper...")
                scraper.close()

        except Exception as e:
            self.status = TaskStatus.ERROR
            self.log("ERROR", f"任务执行异常: {str(e)}")
            import traceback
            self.log("ERROR", traceback.format_exc())
            return TaskResult(
                success=False,
                message=f"执行失败: {str(e)}",
                error=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )

    def _get_latest_records(self, data_file: Path) -> dict:
        """获取每个门店的最新记录"""
        if not data_file.exists():
            return {}

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        latest = {}
        for record in data.get('stores', []):
            name = record.get('name', '')
            if name:
                if name not in latest or record.get('crawl_time', '') > latest[name].get('crawl_time', ''):
                    latest[name] = record

        return latest

    def _find_changed_stores(self, prev_latest: dict, data_file: Path) -> list:
        """找出有变化的门店（用年度数据判断）"""
        new_latest = self._get_latest_records(data_file)
        return self._diff_latest(prev_latest, new_latest)

    def _find_changed_stores_from_results(self, prev_latest: dict, results: list) -> list:
        """从内存结果中找出有变化的门店（用于测试模式）"""
        new_latest = {}
        for record in results:
            name = record.get('name', '')
            if name:
                if name not in new_latest or record.get('crawl_time', '') > new_latest[name].get('crawl_time', ''):
                    new_latest[name] = record
        return self._diff_latest(prev_latest, new_latest)

    def _diff_latest(self, prev_latest: dict, new_latest: dict) -> list:
        changed = []

        for name, record in new_latest.items():
            if name not in prev_latest:
                changed.append(record)
            else:
                prev = prev_latest[name]
                # 用年度数据判断变化
                prev_yearly_count = prev.get('yearly_count', 0)
                prev_yearly_score = prev.get('yearly_score', 0)
                curr_yearly_count = record.get('yearly_count', 0)
                curr_yearly_score = record.get('yearly_score', 0)

                if (curr_yearly_count != prev_yearly_count or
                    curr_yearly_score != prev_yearly_score):
                    changed.append(record)

        return changed

    def _format_notify_content(self, changed_stores: list, new_count: int, total: int, prev_latest: dict = None) -> str:
        """格式化通知内容"""
        lines = [f"共 {total} 条记录，新增 {new_count} 条"]

        if changed_stores:
            lines.append("")
            for store in changed_stores[:15]:  # 最多显示15个
                name = store.get('short_name', store.get('name', '未知'))
                mc = store['monthly_count']
                ms = store['monthly_score']

                store_name = store.get('name', '')
                tag = "(新) " if prev_latest and store_name not in prev_latest else ""
                lines.append(f"**{name}** {tag}月度{mc}次/{ms}分")

            if len(changed_stores) > 15:
                lines.append(f"... 还有 {len(changed_stores) - 15} 个门店")

        lines.append(f"\n⏰ {datetime.now().strftime('%m-%d %H:%M')}")
        return "\n".join(lines)
