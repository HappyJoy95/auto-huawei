"""
京东到家订单监控任务
"""
from module.tasks.base import BaseTask, TaskResult, TaskStatus
from module.config.config import Config, DATA_DIR
from module.notifier import Notifier
from pathlib import Path
from datetime import datetime
import json
import re
from playwright.sync_api import sync_playwright

# 数据目录
JDDJ_DATA_DIR = DATA_DIR / "jddj"


class JddjOrdersTask(BaseTask):
    """京东到家订单监控任务"""

    task_id = "jddj_orders"
    task_name = "京东到家订单监控"

    def run(self) -> TaskResult:
        self.status = TaskStatus.RUNNING
        start_time = datetime.now()

        try:
            cookies_file = JDDJ_DATA_DIR / "cookies.json"
            output_file = JDDJ_DATA_DIR / "pending_orders.json"

            username = self.config.get("username", "jd_sdslsmk73")
            password = self.config.get("password", "")
            target_status = self.config.get("target_status", ["待接单", "待打印"])
            headless = self.config.get("headless", True)

            self.update_progress(10, "启动浏览器...")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                context = browser.new_context(accept_downloads=True)
                page = context.new_page()

                # 加载 cookies
                if cookies_file.exists():
                    with open(cookies_file, 'r') as f:
                        cookies = json.load(f)
                    context.add_cookies(cookies)

                self.update_progress(20, "访问京东到家...")

                page.goto("https://store.jddj.com/", wait_until="domcontentloaded", timeout=60000)

                # 检查登录状态
                if "login" in page.url:
                    self.update_progress(30, "正在登录...")
                    self._login(page, username, password)
                    # 保存 cookies
                    with open(cookies_file, 'w') as f:
                        json.dump(context.cookies(), f)

                self.update_progress(50, "正在获取订单...")

                # 导航到订单查询
                orders = self._get_orders(page)

                browser.close()

            # 筛选目标状态订单
            pending_orders = [o for o in orders if o["状态"] in target_status]

            # 保存结果
            result = {
                "时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "待接单数量": len([o for o in pending_orders if "待接单" in o["状态"]]),
                "待打印数量": len([o for o in pending_orders if "待打印" in o["状态"]]),
                "订单列表": pending_orders
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # 发送通知
            if pending_orders:
                self._send_notification(pending_orders)

            self.status = TaskStatus.COMPLETED
            self.update_progress(100, f"获取完成，{len(pending_orders)} 条待处理订单")

            return TaskResult(
                success=True,
                message=f"获取 {len(pending_orders)} 条待处理订单",
                data=result,
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

    def _login(self, page, username: str, password: str):
        """登录"""
        user_input = page.query_selector('input[type="text"], input:not([type="password"])')
        pwd_input = page.query_selector('input[type="password"]')

        if user_input and pwd_input:
            user_input.fill(username)
            page.wait_for_timeout(200)
            pwd_input.fill(password)
            page.wait_for_timeout(200)

            login_btn = page.query_selector('button:has-text("登录")')
            if login_btn:
                login_btn.click()
                page.wait_for_timeout(3000)

    def _get_orders(self, page) -> list:
        """获取订单数据"""
        orders = []
        seen_ids = set()

        page_text = page.query_selector('body').inner_text()
        order_blocks = page_text.split("订单编号：")

        for block in order_blocks[1:]:
            try:
                order_id_match = re.search(r'(\d{15,20})', block)
                if not order_id_match:
                    continue

                order_id = order_id_match.group(1)
                if order_id in seen_ids:
                    continue
                seen_ids.add(order_id)

                status = ""
                status_keywords = ["待接单", "待打印", "已取消", "已完成"]
                lines = block.split('\n')
                for line in lines[:10]:
                    line = line.strip()
                    if line in status_keywords:
                        status = line
                        break

                store = ""
                if "门店：" in block:
                    start = block.find("门店：") + 3
                    end = block.find("\n", start)
                    if end == -1:
                        end = min(start + 50, len(block))
                    store = block[start:end].strip()

                orders.append({
                    "订单号": order_id,
                    "状态": status,
                    "门店": store
                })
            except:
                pass

        return orders

    def _send_notification(self, orders: list):
        """发送企业微信通知"""
        lines = [
            "## 京东到家新订单通知",
            f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**待接单：** {len([o for o in orders if '待接单' in o['状态']])} 单",
            f"**待打印：** {len([o for o in orders if '待打印' in o['状态']])} 单",
            "",
            "---",
            "**订单详情：**"
        ]

        for i, order in enumerate(orders, 1):
            lines.append(f"\n**{i}. {order['状态']}**")
            lines.append(f"> 订单号：`{order['订单号']}`")
            if order['门店']:
                lines.append(f"> 门店：{order['门店']}")

        Notifier.send("wechat", self.config.get("notify_target", ""), "京东到家新订单", "\n".join(lines))
