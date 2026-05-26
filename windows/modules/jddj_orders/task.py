"""
京东到家订单监控任务
"""
import os
from module.tasks.base import BaseTask, TaskResult, TaskStatus
from module.config.config import DATA_DIR
from pathlib import Path
from datetime import datetime
import json
import re
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

JDDJ_DATA_DIR = DATA_DIR / "jddj_orders"


class JddjOrdersTask(BaseTask):
    """京东到家订单监控任务"""

    task_id = "jddj_orders"
    task_name = "京东到家订单监控"

    def run(self) -> TaskResult:
        self.status = TaskStatus.RUNNING
        start_time = datetime.now()

        try:
            JDDJ_DATA_DIR.mkdir(parents=True, exist_ok=True)
            cookies_file = JDDJ_DATA_DIR / "cookies.json"
            output_file = JDDJ_DATA_DIR / "pending_orders.json"

            username = os.environ.get("JDDJ_USERNAME") or self.config.get("username", "")
            password = os.environ.get("JDDJ_PASSWORD") or self.config.get("password", "")
            target_status = self.config.get("target_status", ["待接单", "待打印"])
            headless = self.config.get("headless", True)

            self.log("INFO", f"京东到家配置: headless={headless}")
            self.update_progress(10, "启动浏览器...")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                try:
                    context = browser.new_context(accept_downloads=True)
                    page = context.new_page()

                    if cookies_file.exists():
                        with open(cookies_file, "r", encoding="utf-8") as f:
                            cookies = json.load(f)
                        if cookies:
                            context.add_cookies(cookies)
                            self.log("INFO", "已加载 cookies")

                    self.update_progress(20, "访问京东到家...")
                    page.goto("https://store.jddj.com/", wait_until="domcontentloaded", timeout=60000)

                    if self._needs_login(page):
                        self.update_progress(30, "等待登录完成...")
                        self._login(page, username, password, headless)
                    else:
                        self.log("INFO", "cookies 登录状态有效")

                    if self._needs_login(page):
                        raise RuntimeError("登录未完成，无法继续获取订单")

                    with open(cookies_file, "w", encoding="utf-8") as f:
                        json.dump(context.cookies(), f, ensure_ascii=False, indent=2)

                    self.update_progress(50, "正在打开订单页面...")
                    page.goto("https://store.jddj.com/frame/347/3065", wait_until="domcontentloaded", timeout=60000)
                    self._wait_for_order_page(page, target_status)

                    self.update_progress(70, "正在解析订单...")
                    orders = self._get_orders(page, target_status)
                finally:
                    browser.close()

            pending_orders = [o for o in orders if o["状态"] in target_status]
            result = {
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "待接单数量": len([o for o in pending_orders if "待接单" in o["状态"]]),
                "待打印数量": len([o for o in pending_orders if "待打印" in o["状态"]]),
                "订单列表": pending_orders
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            self.status = TaskStatus.COMPLETED
            self.update_progress(100, f"获取完成，{len(pending_orders)} 条待处理订单")

            notify_content = ""
            if pending_orders:
                notify_lines = [
                    f"**待接单：** {result['待接单数量']} 单",
                    f"**待打印：** {result['待打印数量']} 单",
                    ""
                ]
                for i, order in enumerate(pending_orders[:5], 1):
                    notify_lines.append(f"**{i}. {order['状态']}**")
                    notify_lines.append(f"> 订单号：`{order['订单号']}`")
                    if order["门店"]:
                        notify_lines.append(f"> 门店：{order['门店']}")
                if len(pending_orders) > 5:
                    notify_lines.append(f"\n_... 还有 {len(pending_orders) - 5} 条订单_")
                notify_content = "\n".join(notify_lines)

            return TaskResult(
                success=True,
                message=f"获取 {len(pending_orders)} 条待处理订单",
                data=result,
                start_time=start_time,
                end_time=datetime.now(),
                notify_title="京东到家订单通知" if pending_orders else None,
                notify_content=notify_content if pending_orders else None
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

    def _needs_login(self, page) -> bool:
        page.wait_for_timeout(1000)
        return self._page_has_login_marker(page)

    def _login(self, page, username: str, password: str, headless: bool):
        user_input = self._first_visible(page, 'input[type="text"], input:not([type="password"])')
        pwd_input = self._first_visible(page, 'input[type="password"]')

        if username and password and user_input and pwd_input:
            user_input.fill(username)
            page.wait_for_timeout(200)
            pwd_input.fill(password)
            page.wait_for_timeout(200)

            login_btn = self._first_visible(page, 'button:has-text("登录")')
            if login_btn:
                login_btn.click()
            else:
                pwd_input.press("Enter")
        elif headless:
            raise RuntimeError("无头模式下无法处理当前登录页，请关闭无头模式后手动完成验证")
        else:
            self.log("WARNING", "当前登录页需要手动处理，请在浏览器窗口中完成登录/验证码/反人机验证")

        self.log("INFO", "等待登录完成，最长 180 秒")
        self._wait_until_logged_in(page)

    def _first_visible(self, page, selector: str):
        for frame in page.frames:
            for element in frame.query_selector_all(selector):
                if element.is_visible():
                    return element
        return None

    def _page_has_login_marker(self, page) -> bool:
        if "login" in page.url.lower():
            return True
        return self._first_visible(page, 'input[type="password"]') is not None

    def _wait_until_logged_in(self, page):
        deadline = datetime.now().timestamp() + 180
        while datetime.now().timestamp() < deadline:
            if not self._page_has_login_marker(page):
                self.log("INFO", "登录状态已确认")
                return
            page.wait_for_timeout(1000)
        raise RuntimeError("登录等待超时，请确认验证码、反人机验证或手动登录是否完成")

    def _wait_for_order_page(self, page, target_status: list):
        if self._needs_login(page):
            raise RuntimeError("打开订单页后仍处于登录状态")

        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            self.log("WARNING", "订单页网络请求未完全静止，继续检查页面内容")

        page.wait_for_timeout(3000)
        text = self._collect_page_text(page)
        empty_markers = ["暂无", "无数据", "没有相关", "未查询到"]
        if not self._find_order_ids(text) and not self._find_status_keywords(text, target_status) and not any(marker in text for marker in empty_markers):
            snippet = re.sub(r"\s+", " ", text)[:500]
            self.log("WARNING", f"订单页文本片段: {snippet}")
            raise RuntimeError("订单列表未加载完成或页面结构已变化，未检测到目标订单状态、订单号或空列表提示")

    def _collect_page_text(self, page) -> str:
        texts = []
        for frame in page.frames:
            try:
                body = frame.locator("body")
                if body.count() > 0:
                    frame_text = body.inner_text(timeout=3000)
                    if frame_text:
                        texts.append(frame_text)
            except Exception:
                pass
        return "\n".join(texts)

    def _get_orders(self, page, target_status: list) -> list:
        text = self._collect_page_text(page)
        empty_markers = ["暂无", "无数据", "没有相关", "未查询到"]
        order_matches = self._find_order_ids(text)
        status_matches = self._find_status_keywords(text, target_status)
        if not order_matches and not status_matches:
            if any(marker in text for marker in empty_markers):
                self.log("INFO", "订单页显示为空列表")
                return []
            snippet = re.sub(r"\s+", " ", text)[:500]
            self.log("WARNING", f"订单页文本片段: {snippet}")
            raise RuntimeError("未检测到目标订单状态或订单号，停止解析订单")

        orders = []
        seen_ids = set()
        for status_match in status_matches:
            try:
                status = status_match.group(0)
                block = self._build_status_block(text, status_match, order_matches)
                order_id_match = self._find_nearest_order_id(text, status_match, order_matches)
                if not order_id_match:
                    snippet = re.sub(r"\s+", " ", block)[:500]
                    self.log("WARNING", f"检测到{status}，但附近未找到订单号: {snippet}")
                    continue

                order_id = order_id_match.group(1)
                if order_id in seen_ids:
                    continue
                seen_ids.add(order_id)

                orders.append({
                    "订单号": order_id,
                    "状态": status,
                    "门店": self._extract_store(block) or self._find_nearest_store(text, status_match, order_id_match)
                })
            except Exception as e:
                self.log("WARNING", f"跳过无法解析的订单块: {e}")

        self.log("INFO", f"解析到 {len(orders)} 条目标状态订单")
        return orders

    def _find_order_ids(self, text: str) -> list:
        patterns = [
            r"(?:订单编号|订单号)\s*[:：]?\s*(\d{12,25})",
            r"\b(\d{15,20})\b"
        ]
        matches = []
        seen = set()
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                order_id = match.group(1)
                if order_id not in seen:
                    matches.append(match)
                    seen.add(order_id)
            if matches:
                return sorted(matches, key=lambda m: m.start())
        return []

    def _find_status_keywords(self, text: str, target_status: list) -> list:
        statuses = [status for status in target_status if status]
        if not statuses:
            statuses = ["待接单", "待打印"]
        pattern = "|".join(re.escape(status) for status in statuses)
        return list(re.finditer(pattern, text))

    def _build_status_block(self, text: str, status_match, order_matches: list) -> str:
        previous_order = None
        next_order = None
        for order_match in order_matches:
            if order_match.start() <= status_match.start():
                previous_order = order_match
            elif order_match.start() > status_match.start():
                next_order = order_match
                break

        if previous_order:
            start = max(0, previous_order.start() - 500)
            end = next_order.start() if next_order else min(len(text), status_match.end() + 1500)
        else:
            start = max(0, status_match.start() - 1200)
            end = next_order.start() if next_order else min(len(text), status_match.end() + 1500)
        return text[start:end]

    def _find_nearest_order_id(self, text: str, status_match, order_matches: list):
        if not order_matches:
            block = text[max(0, status_match.start() - 2000):min(len(text), status_match.end() + 2000)]
            matches = self._find_order_ids(block)
            return matches[0] if matches else None

        nearest = min(order_matches, key=lambda match: abs(match.start() - status_match.start()))
        if abs(nearest.start() - status_match.start()) <= 3000:
            return nearest
        return None

    def _extract_store(self, block: str) -> str:
        patterns = [
            r"(?:门店名称|店铺名称|商家名称)\s*[:：]\s*([^\n\r]{1,80})",
            r"(?:店铺|商家)\s*[:：]\s*([^\n\r]{1,80})",
            r"门店\s*[:：]\s*([^\n\r]{1,80})"
        ]
        for pattern in patterns:
            match = re.search(pattern, block)
            if match:
                store = self._clean_store(match.group(1))
                if store:
                    return store
        return ""

    def _find_nearest_store(self, text: str, status_match, order_id_match) -> str:
        start = max(0, min(status_match.start(), order_id_match.start()) - 2500)
        end = min(len(text), max(status_match.end(), order_id_match.end()) + 2500)
        return self._extract_store(text[start:end])

    def _clean_store(self, value: str) -> str:
        store = re.split(r"\s{2,}|订单|状态|下单|配送|顾客|客户|商品|金额|电话", value.strip())[0].strip()
        store = re.sub(r"^[：:\s]+", "", store).strip()
        if not store or re.fullmatch(r"[（(]?\d+[）)]?", store):
            return ""
        return store
