"""
小红书采集器 - MuMu模拟器 + ADB + UIAutomator
"""
import subprocess
import time
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Post:
    store_name: str
    platform: str
    title: Optional[str]
    post_time: Optional[str]
    likes: Optional[int]
    post_link: Optional[str]
    crawl_time: datetime


class XiaohongshuScraper:
    ADB_PATH = "adb"

    def __init__(self, adb_port: str = "127.0.0.1:16448", headless: bool = True):
        self.adb_port = adb_port
        self.headless = headless
        self.connected = False

    def _run_adb(self, cmd: str) -> str:
        full_cmd = f"{self.ADB_PATH} -s {self.adb_port} {cmd}"
        result = subprocess.run(full_cmd, shell=True, capture_output=True, encoding='utf-8', errors='ignore')
        return result.stdout

    def _connect(self) -> bool:
        result = subprocess.run(
            f"{self.ADB_PATH} connect {self.adb_port}",
            shell=True, capture_output=True, encoding='utf-8', errors='ignore'
        )
        if "connected" in result.stdout.lower() or "already connected" in result.stdout.lower():
            self.connected = True
            print(f"已连接 MuMu 模拟器: {self.adb_port}")
            return True
        print(f"连接失败: {result.stderr}")
        return False

    def _tap(self, x: int, y: int, delay: float = 0.5):
        # 坐标边界检查，限制在屏幕范围内
        x = max(0, min(x, 1079))  # 屏幕宽度1080
        y = max(0, min(y, 1919))  # 屏幕高度1920
        self._run_adb(f"shell input tap {x} {y}")
        time.sleep(delay)

    def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        # 坐标边界检查
        x1 = max(0, min(x1, 1079))
        y1 = max(0, min(y1, 1919))
        x2 = max(0, min(x2, 1079))
        y2 = max(0, min(y2, 1919))
        self._run_adb(f"shell input swipe {x1} {y1} {x2} {y2} {duration}")
        time.sleep(0.5)

    def _press_back(self):
        self._run_adb("shell input keyevent KEYCODE_BACK")
        time.sleep(0.5)

    def _launch_app(self):
        self._run_adb("shell am start -n com.xingin.xhs/.index.v2.IndexActivityV2")
        time.sleep(10)  # 启动后等待10秒

    def _dump_ui(self) -> str:
        """获取UI层级XML"""
        self._run_adb("shell uiautomator dump /sdcard/ui.xml")
        return self._run_adb("shell cat /sdcard/ui.xml")

    def _wait_for_element(self, pattern: str, timeout: int = 30, interval: float = 2.0) -> bool:
        """等待UI元素出现

        Args:
            pattern: 正则表达式模式
            timeout: 超时时间（秒）
            interval: 检测间隔（秒）

        Returns:
            bool: 是否检测到元素
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            ui_xml = self._dump_ui()
            if re.search(pattern, ui_xml):
                return True
            time.sleep(interval)
        return False

    def _wait_and_tap(self, pattern: str, offset_y: int = 0, timeout: int = 30) -> bool:
        """等待元素出现后点击

        Args:
            pattern: 正则表达式模式
            offset_y: Y轴偏移量
            timeout: 超时时间

        Returns:
            bool: 是否成功点击
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            ui_xml = self._dump_ui()
            match = re.search(rf'{pattern}[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', ui_xml)
            if match:
                x1, y1, x2, y2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
                self._tap((x1 + x2) // 2, (y1 + y2) // 2 + offset_y, delay=1)
                return True
            time.sleep(2)
        return False

    def _parse_time_ago(self, time_str: str) -> Optional[str]:
        """解析时间格式，转换为 yy-mm-dd

        支持三种格式：
        - Xd ago（如 5d ago）
        - mm-dd（今年的日期）
        - yyyy-mm-dd（去年的日期）
        """
        if not time_str:
            return None

        now = datetime.now()

        try:
            # 格式1: 5d ago
            match = re.match(r"(\d+)d\s*ago", time_str.lower())
            if match:
                days = int(match.group(1))
                dt = now - timedelta(days=days)
                return dt.strftime("%y-%m-%d")

            # 格式2: mm-dd（今年的日期）
            match = re.match(r"(\d{1,2})-(\d{1,2})$", time_str)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                return f"{now.year % 100:02d}-{month:02d}-{day:02d}"

            # 格式3: yyyy-mm-dd
            match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", time_str)
            if match:
                year = int(match.group(1)) % 100
                month = int(match.group(2))
                day = int(match.group(3))
                return f"{year:02d}-{month:02d}-{day:02d}"
        except:
            pass

        return None

    def _get_following_accounts(self) -> List[str]:
        """获取关注列表中的账号名称"""
        all_accounts = []
        seen = set()

        # 已知的非账号文本
        skip_words = {
            'Friends', 'Following', 'Follower', 'Recommended',
            'Search following', 'Suggested', 'All', 'Merchants/Buyers',
            'update(s)', '还没有简介', 'Following（26）'
        }

        prev_ui = ""
        no_change_count = 0

        # 滑动到底部，收集所有账号
        for _ in range(20):
            ui_xml = self._dump_ui()

            # 检查UI是否变化
            if ui_xml == prev_ui:
                no_change_count += 1
                if no_change_count >= 3:
                    break
            else:
                no_change_count = 0
            prev_ui = ui_xml

            # 从 UI 中提取所有文本
            texts = re.findall(r'text="([^"]+)"', ui_xml)

            # 找账号名：账号名后面紧跟 "Following" 或者 "update(s)" 后面紧跟 "Following"
            i = 0
            while i < len(texts):
                text = texts[i]
                if text and text not in skip_words:
                    # 检查下一个是否是 "Following"（直接跟着）
                    if i + 1 < len(texts) and texts[i + 1] == 'Following':
                        if len(text) < 50 and '\n' not in text and 'update' not in text.lower():
                            if text not in seen:
                                seen.add(text)
                                all_accounts.append(text)
                        i += 2
                        continue
                    # 或者下一个是 "update(s)"，再下一个是 "Following"
                    elif i + 2 < len(texts) and 'update' in texts[i + 1].lower() and texts[i + 2] == 'Following':
                        if len(text) < 50 and '\n' not in text:
                            if text not in seen:
                                seen.add(text)
                                all_accounts.append(text)
                        i += 3
                        continue
                i += 1

            # 滑动获取更多
            self._swipe(540, 1500, 540, 500)
            time.sleep(1)

        print(f"共找到 {len(all_accounts)} 个关注账号")
        return all_accounts

    def _get_posts_from_page(self) -> List[dict]:
        """从当前页面获取帖子信息"""
        ui_xml = self._dump_ui()
        posts = []

        # 提取帖子的 content-desc
        # 格式: content-desc="视频,标题,来自xxx,N赞，" 或 content-desc="笔记,标题,来自xxx,N赞，"
        # 英文格式: content-desc="Video,标题,from xxx,N likes"
        post_patterns = [
            r'content-desc="视频,([^,]*),来自([^,]*),(\d+)',  # 中文视频
            r'content-desc="笔记,([^,]*),来自([^,]*),(\d+)',  # 中文笔记
            r'content-desc="[Vv]ideo,([^,]*),[Ff]rom\s*([^,]*),(\d+)',  # 英文视频
            r'content-desc="[Nn]otes,([^,]*),[Ff]rom\s*([^,]*),(\d+)',  # 英文笔记
        ]

        for pattern in post_patterns:
            for match in re.finditer(pattern, ui_xml):
                title = match.group(1)
                author = match.group(2)
                likes = int(match.group(3))

                # 处理 HTML 实体编码
                title = title.replace('&#129331;', '🤳').replace('&#127752;', '📍')

                # 避免重复添加
                if not any(p['title'] == title for p in posts):
                    posts.append({
                        'title': title,
                        'author': author,
                        'likes': likes,
                        'time': None
                    })

        # 提取时间信息，按顺序匹配
        # 格式: 5d ago, 04-10, 2025-03-15
        time_pattern = r'text="(\d+d\s*ago|\d{1,2}-\d{1,2}|\d{4}-\d{1,2}-\d{1,2})"'
        times = re.findall(time_pattern, ui_xml, re.IGNORECASE)

        for i, post in enumerate(posts):
            if i < len(times):
                post['time'] = self._parse_time_ago(times[i])

        return posts

    def login(self) -> bool:
        if not self._connect():
            return False
        print("已连接模拟器")
        return True

    def fetch_posts(self, store_name: str, max_posts: int = 100, output_file: str = None) -> List[Post]:
        """采集指定账号的帖子

        Args:
            store_name: 门店名称
            max_posts: 最大采集数量
            output_file: 输出文件路径，如果提供则实时写入
        """
        if not self.connected:
            if not self._connect():
                return []

        posts = []
        seen_titles = set()
        print(f"正在采集小红书: {store_name}")

        # 初始化输出文件
        if output_file:
            import json
            from pathlib import Path
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # 写入初始结构
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'crawl_time': datetime.now().isoformat(),
                    'store_name': store_name,
                    'platform': '小红书',
                    'total_posts': 0,
                    'posts': []
                }, f, ensure_ascii=False, indent=2)

        def save_post(post):
            """实时保存单条帖子"""
            if output_file:
                # 读取现有数据
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 添加新帖子
                data['posts'].append({
                    'title': post.title,
                    'post_time': post.post_time,
                    'likes': post.likes,
                    'crawl_time': post.crawl_time.isoformat()
                })
                data['total_posts'] = len(data['posts'])
                # 写回文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

        # 1. 启动小红书
        self._launch_app()

        # 等待首页加载
        print("等待首页加载...")
        if not self._wait_for_element('text="Home"', timeout=30):
            print("首页加载超时")
            return []

        # 2. 等待并点击Me
        print("点击Me...")
        if not self._wait_and_tap(r'text="Me"', timeout=10):
            print("未找到Me按钮")
            return []
        time.sleep(2)

        # 3. 等待并点击Following
        print("点击关注...")
        if not self._wait_and_tap(r'text="Following"', timeout=10):
            print("未找到关注按钮")
            self._press_back()
            return []
        time.sleep(2)

        # 4. 查找账号
        print(f"查找门店: {store_name}")
        found = False
        for _ in range(20):
            ui_xml = self._dump_ui()
            pattern = rf'text="{re.escape(store_name)}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
            match = re.search(pattern, ui_xml)

            if match:
                x1, y1, x2, y2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
                center_y = (y1 + y2) // 2 + 60

                # 检查是否在可点击范围内（200-1800）
                if y1 < 200:
                    print(f"  门店位置太靠上({y1})，向下滑动")
                    self._swipe(540, 1000, 540, 1400, duration=200)
                    time.sleep(1)
                    continue
                elif y2 > 1800:
                    print(f"  门店位置太靠下({y2})，向上滑动")
                    self._swipe(540, 1400, 540, 1000, duration=200)
                    time.sleep(1)
                    continue
                else:
                    self._tap((x1 + x2) // 2, center_y, delay=2)
                    found = True
                    break

            self._swipe(540, 1500, 540, 500)
            time.sleep(1)

        if not found:
            print(f"  未找到账号: {store_name}")
            self._press_back()
            self._press_back()
            return []

        # 5. 等待帖子列表加载
        print("等待帖子列表加载...")
        time.sleep(3)

        # 6. 采集帖子
        prev_ui = ""

        for scroll_count in range(50):  # 最多滑动50次
            # 等待帖子列表加载完成
            time.sleep(2)
            ui_xml = self._dump_ui()

            # 检测是否有帖子内容
            if 'content-desc=' not in ui_xml:
                time.sleep(1)
                ui_xml = self._dump_ui()

            # 提取帖子
            page_posts = self._get_posts_from_page()
            new_count = 0

            for post_info in page_posts:
                if post_info['title'] and post_info['title'] not in seen_titles:
                    # 时间为null的跳过，不记录seen_titles，下次有机会再采集
                    if not post_info['time']:
                        continue
                    seen_titles.add(post_info['title'])
                    post = Post(
                        store_name=store_name,
                        platform="小红书",
                        title=post_info['title'],
                        post_time=post_info['time'],
                        likes=post_info['likes'],
                        post_link=None,
                        crawl_time=datetime.now()
                    )
                    posts.append(post)
                    save_post(post)  # 实时保存
                    new_count += 1

            if new_count > 0:
                print(f"  第{scroll_count + 1}次滑动，新增 {new_count} 条，累计 {len(posts)} 条")

            if len(posts) >= max_posts:
                break

            # 滑动前保存当前UI
            ui_before_swipe = ui_xml

            # 滑动加载更多
            self._swipe(540, 1500, 540, 1100)

            # 等待UI加载完成
            time.sleep(2)

            # 等待帖子内容出现
            for _ in range(3):
                time.sleep(1)
                ui_after_swipe = self._dump_ui()
                if 'content-desc=' in ui_after_swipe:
                    break

            # 如果滑动后UI没变化，说明到底了
            if ui_after_swipe == ui_before_swipe:
                print(f"  UI无变化，已到底")
                break

        # 7. 返回
        self._press_back()
        self._press_back()
        self._press_back()

        print(f"  采集完成，共 {len(posts)} 条帖子")
        return posts

    def fetch_stores(self, store_names: list, max_posts_per_store: int = 100,
                      output_file: str = None, mode: str = 'full') -> List[Post]:
        """采集多个门店的帖子

        Args:
            store_names: 门店名称列表
            max_posts_per_store: 每个门店最大采集数量
            output_file: 输出文件路径
            mode: 'full' 全量获取, 'new' 只获取新增
        """
        if not self.connected:
            if not self._connect():
                return []

        import json
        from pathlib import Path

        all_posts = []
        existing_titles = set()

        # 初始化输出文件
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 如果文件存在，加载已有数据避免重复
            if output_path.exists():
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for post in existing_data.get('posts', []):
                        existing_titles.add(post['title'])
                print(f"已有 {len(existing_titles)} 条帖子记录")
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'crawl_time': datetime.now().isoformat(),
                        'platform': '小红书',
                        'total_posts': 0,
                        'posts': []
                    }, f, ensure_ascii=False, indent=2)

        def save_post(post):
            if output_file:
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['posts'].append({
                    'store_name': post.store_name,
                    'title': post.title,
                    'post_time': post.post_time,
                    'likes': post.likes,
                    'crawl_time': post.crawl_time.isoformat()
                })
                data['total_posts'] = len(data['posts'])
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

        # 启动小红书
        self._launch_app()

        # 等待首页加载完成
        print("Waiting for Home page...")
        if not self._wait_for_element('text="Home"', timeout=30):
            print("Home page load timeout")
            return []
        print("Home page loaded")

        for i, store_name in enumerate(store_names):
            print(f"\n[{i+1}/{len(store_names)}] 采集: {store_name}")

            # 第一个门店需要进入关注列表
            if i == 0:
                # 等待并点击Me按钮
                print("  点击Me...")
                if not self._wait_and_tap(r'text="Me"', timeout=10):
                    print("  未找到Me按钮")
                    return []
                time.sleep(2)

                # 等待并点击Following
                print("  点击关注...")
                if not self._wait_and_tap(r'text="Following"', timeout=10):
                    print("  未找到关注按钮")
                    self._press_back()
                    return []
                time.sleep(2)

            # 等待并查找门店名称
            print(f"  查找门店: {store_name}")
            found = False
            for _ in range(20):
                ui_xml = self._dump_ui()
                pattern = rf'text="{re.escape(store_name)}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
                match = re.search(pattern, ui_xml)
                if match:
                    x1, y1, x2, y2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
                    center_y = (y1 + y2) // 2 + 60

                    # 检查是否在可点击范围内（200-1800）
                    if y1 < 200:
                        # 太靠上，向下滑动
                        print(f"  门店位置太靠上({y1})，向下滑动")
                        self._swipe(540, 1000, 540, 1400, duration=200)
                        time.sleep(1)
                        continue
                    elif y2 > 1800:
                        # 太靠下，向上滑动
                        print(f"  门店位置太靠下({y2})，向上滑动")
                        self._swipe(540, 1400, 540, 1000, duration=200)
                        time.sleep(1)
                        continue
                    else:
                        # 位置合适，点击
                        self._tap((x1 + x2) // 2, center_y, delay=2)
                        found = True
                        break
                self._swipe(540, 1500, 540, 500)
                time.sleep(1)

            if not found:
                print(f"  未找到账号: {store_name}")
                # 未找到也滑动到顶端，准备找下一个
                for _ in range(5):
                    self._swipe(540, 500, 540, 1500, duration=200)
                time.sleep(0.5)
                continue

            # 等待门店页面加载
            print("  等待帖子列表加载...")
            time.sleep(3)  # 等待页面加载

            seen_titles = set()
            store_posts = []
            consecutive_no_new = 0  # 连续无新内容计数

            for scroll_count in range(50):
                # 等待帖子列表加载完成
                time.sleep(2)
                ui_xml = self._dump_ui()

                # 检测是否有帖子内容
                if 'content-desc=' not in ui_xml:
                    time.sleep(1)
                    ui_xml = self._dump_ui()

                page_posts = self._get_posts_from_page()
                new_count = 0

                for post_info in page_posts:
                    title = post_info['title']
                    if title and title not in seen_titles:
                        # 时间为null的跳过，不记录seen_titles，下次有机会再采集
                        if not post_info['time']:
                            continue
                        # 跳过已存在的帖子
                        if title in existing_titles:
                            seen_titles.add(title)
                            continue
                        seen_titles.add(title)
                        post = Post(
                            store_name=store_name,
                            platform="小红书",
                            title=title,
                            post_time=post_info['time'],
                            likes=post_info['likes'],
                            post_link=None,
                            crawl_time=datetime.now()
                        )
                        store_posts.append(post)
                        all_posts.append(post)
                        save_post(post)
                        new_count += 1

                if new_count > 0:
                    print(f"  第{scroll_count + 1}次滑动，新增 {new_count} 条")
                    consecutive_no_new = 0  # 有新内容，重置
                else:
                    consecutive_no_new += 1
                    if consecutive_no_new >= 3:
                        print(f"  连续{consecutive_no_new}次无新内容，停止")
                        break

                if len(store_posts) >= max_posts_per_store:
                    break

                ui_before = ui_xml
                self._swipe(540, 1500, 540, 1100)

                # 等待UI加载完成
                time.sleep(2)

                # 等待帖子内容出现
                for _ in range(3):
                    time.sleep(1)
                    ui_after = self._dump_ui()
                    if 'content-desc=' in ui_after:
                        break

                if ui_after == ui_before:
                    print(f"  已到底")
                    break

            print(f"  本店采集 {len(store_posts)} 条")

            # 返回关注列表
            self._press_back()
            time.sleep(1)

            # 等待关注列表加载
            if not self._wait_for_element(r'text="Following"', timeout=10):
                print("  关注列表加载超时，尝试再返回一次")
                self._press_back()
                time.sleep(1)

            # 滑动到关注列表顶端，方便找下一个门店
            for _ in range(5):
                self._swipe(540, 500, 540, 1500, duration=200)
            time.sleep(0.5)

        print(f"\n总计采集 {len(all_posts)} 条帖子")
        return all_posts

    def fetch_all_following(self, max_posts_per_account: int = 50, max_accounts: int = None) -> List[Post]:
        """采集所有关注账号的帖子（已废弃，请使用 fetch_stores）"""
        print("警告: fetch_all_following 已废弃，请使用 fetch_stores")
        return []

    def close(self):
        """退出小红书app"""
        print("正在退出小红书...")
        # 强制停止小红书应用
        self._run_adb("shell am force-stop com.xingin.xhs")
        print("已退出小红书")
