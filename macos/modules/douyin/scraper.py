"""
抖音 Web 端采集器 - 基于 Playwright + Chromium
支持：
1. 扫码登录并保存 cookies
2. 从关注列表获取门店账号
3. 采集门店视频数据
"""
import json
import time
import re
import os
import random
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext


@dataclass
class Post:
    store_name: str
    platform: str
    title: Optional[str]
    post_time: Optional[str]
    likes: Optional[int]
    post_link: Optional[str]
    crawl_time: datetime


class DouyinWebScraper:
    """抖音 Web 端采集器"""

    BASE_URL = "https://www.douyin.com"
    FOLLOWING_URL = "https://www.douyin.com/user/following"

    # 随机延迟范围
    DELAY_MIN = 2.0
    DELAY_MAX = 5.0

    def __init__(self, adb_port: str = None, headless: bool = False,
                 cookies_file: str = None, user_data_dir: str = None):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 设置 cookies 保存路径
        project_root = Path(__file__).parent.parent
        self.cookies_file = cookies_file or str(project_root / "data" / "douyin_cookies.json")
        self.user_data_dir = user_data_dir or str(project_root / "data" / "browser_data")

        # 确保目录存在
        Path(self.cookies_file).parent.mkdir(parents=True, exist_ok=True)
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

    def _init_browser(self):
        """初始化浏览器 - 使用Edge"""
        if self.playwright is None:
            self.playwright = sync_playwright().start()

        if self.browser is None:
            # 使用 Edge 浏览器
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                channel='msedge',  # 使用 Microsoft Edge
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized',
                ]
            )

        if self.context is None:
            # 尝试加载已保存的 cookies
            cookies = self._load_cookies()
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN'
            )
            # 添加 cookies
            if cookies:
                self.context.add_cookies(cookies)
            self.page = self.context.new_page()

    def _delay(self, min_sec: float = None, max_sec: float = None):
        """随机延迟，模拟人类操作"""
        min_sec = min_sec or self.DELAY_MIN
        max_sec = max_sec or self.DELAY_MAX
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _load_cookies(self) -> Optional[List[Dict]]:
        """加载保存的 cookies"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                print(f"已加载 {len(cookies)} 个 cookies")
                return cookies
            except Exception as e:
                print(f"加载 cookies 失败: {e}")
        return None

    def _save_cookies(self):
        """保存当前 cookies"""
        if self.context:
            cookies = self.context.cookies()
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"已保存 {len(cookies)} 个 cookies")

    def _check_login_status(self) -> bool:
        """检查当前页面登录状态（不刷新页面）"""
        try:
            # 检查是否存在登录按钮（未登录状态）
            login_elements = self.page.query_selector_all('text=登录')
            for elem in login_elements:
                try:
                    if elem.is_visible():
                        return False
                except:
                    pass

            # 检查是否有用户头像或"我"元素（已登录状态）
            avatar = self.page.query_selector('[class*="avatar"], img[class*="Avatar"]')
            me_text = self.page.query_selector('text=我')

            return avatar is not None or me_text is not None
        except Exception as e:
            return False

    def login(self) -> bool:
        """
        登录抖音
        如果有有效 cookies 则直接使用，否则打开浏览器等待扫码登录
        """
        self._init_browser()

        print("访问抖音首页...")
        self.page.goto(self.BASE_URL, wait_until='domcontentloaded', timeout=30000)
        time.sleep(3)

        print("检查登录状态...")
        if self._check_login_status():
            print("已登录")
            return True

        print("\n" + "=" * 60)
        print("[!] 请在打开的浏览器中扫码登录！")
        print("    点击右上角 [登录] -> 选择 [扫码登录]")
        print("    等待时间：最多 5 分钟")
        print("=" * 60 + "\n")

        # 等待用户扫码登录，最多等待 5 分钟
        start_time = time.time()
        max_wait = 300  # 5分钟
        last_print = 0

        while time.time() - start_time < max_wait:
            elapsed = int(time.time() - start_time)
            # 每10秒提示一次
            if elapsed - last_print >= 10:
                print(f"  等待登录... 已等待 {elapsed} 秒")
                last_print = elapsed

            if self._check_login_status():
                print("\n[OK] 登录成功！")
                self._save_cookies()
                return True
            time.sleep(2)

        print("登录超时")
        return False

    def _parse_count(self, count_str: str) -> int:
        """解析点赞/粉丝数量"""
        if not count_str:
            return 0
        count_str = str(count_str).strip()
        try:
            if '万' in count_str:
                num = float(count_str.replace('万', ''))
                return int(num * 10000)
            elif 'w' in count_str.lower():
                num = float(count_str.lower().replace('w', ''))
                return int(num * 10000)
            elif '亿' in count_str:
                num = float(count_str.replace('亿', ''))
                return int(num * 100000000)
            else:
                return int(count_str)
        except:
            return 0

    def get_following_list(self, max_users: int = 100) -> List[Dict]:
        """
        获取关注列表

        Args:
            max_users: 最大获取数量

        Returns:
            关注列表，每个元素包含 name, url, avatar 等信息
        """
        print("\n开始获取关注列表...")

        # 方法：点击右上角头像 -> 进入个人主页 -> 点击"关注"
        try:
            # 1. 点击右上角头像进入个人主页
            print("  步骤1: 点击头像进入个人主页...")
            time.sleep(2)

            # 查找头像元素 (多种可能的选择器)
            avatar_selectors = [
                'img[class*="avatar"]',
                'div[class*="avatar"] img',
                '[class*="Avatar"]',
                'img[class*="Avatar"]',
            ]

            avatar_clicked = False
            for selector in avatar_selectors:
                avatar = self.page.query_selector(selector)
                if avatar:
                    try:
                        avatar.click()
                        avatar_clicked = True
                        break
                    except:
                        continue

            if not avatar_clicked:
                print("  未找到头像，尝试点击'我'链接...")
                me_link = self.page.query_selector('a:has-text("我"), text=我')
                if me_link:
                    me_link.click()
                else:
                    print("  未找到个人主页入口，尝试直接访问...")
                    self.page.goto(self.BASE_URL, wait_until='networkidle', timeout=30000)

            time.sleep(3)
            print(f"  当前页面: {self.page.url}")

            # 2. 点击"关注"进入关注列表
            print("  步骤2: 点击'关注'进入关注列表...")
            time.sleep(1)

            follow_clicked = False
            follow_selectors = [
                'text=关注',
                'span:has-text("关注")',
                '[class*="follow"]:has-text("关注")',
            ]

            for selector in follow_selectors:
                follow_elem = self.page.query_selector(selector)
                if follow_elem:
                    try:
                        follow_elem.click()
                        follow_clicked = True
                        break
                    except:
                        continue

            if not follow_clicked:
                print("  未找到'关注'按钮")

            time.sleep(3)

        except Exception as e:
            print(f"  导航失败: {e}")
            # 备用方案：直接访问关注页面URL
            self.page.goto(self.FOLLOWING_URL, wait_until='networkidle', timeout=30000)

        print(f"  当前页面: {self.page.url}")

        following = []
        seen_names = set()
        scroll_attempts = 0
        max_scroll_attempts = 50  # 最多滚动 50 次

        while len(following) < max_users and scroll_attempts < max_scroll_attempts:
            # 获取当前页面的所有关注用户 - 尝试多种选择器
            user_elements = self.page.query_selector_all(
                '[class*="user-list-item"], [class*="FollowingUser"], '
                '[class*="avatar-wrapper"], div[class*="List"] a, '
                'a[href*="/user/"]'
            )

            print(f"  第 {scroll_attempts + 1} 次滚动，发现 {len(user_elements)} 个元素")

            for element in user_elements:
                try:
                    # 获取用户名 - 尝试多种方式
                    name = None

                    # 方式1: 查找name/nickname元素
                    name_elem = element.query_selector('[class*="name"], [class*="nickname"], [class*="Name"]')
                    if name_elem:
                        name = name_elem.text_content().strip()

                    # 方式2: 如果元素本身就是链接，获取其文本
                    if not name:
                        tag_name = element.evaluate('el => el.tagName')
                        if tag_name == 'A':
                            name = element.text_content().strip()
                            # 清理可能包含的额外信息
                            if name and len(name) > 50:
                                name = name[:50]

                    if not name or name in seen_names:
                        continue

                    seen_names.add(name)

                    # 获取用户主页链接
                    user_url = None
                    tag_name = element.evaluate('el => el.tagName') if element else 'DIV'

                    if tag_name == 'A':
                        href = element.get_attribute('href')
                    else:
                        link_elem = element.query_selector('a[href*="/user/"]')
                        href = link_elem.get_attribute('href') if link_elem else None

                    if href:
                        user_url = self.BASE_URL + href if href.startswith('/') else href

                    # 获取粉丝数
                    followers_text = ''
                    followers_elem = element.query_selector('[class*="count"], [class*="follower"], [class*="Count"]')
                    if followers_elem:
                        followers_text = followers_elem.text_content().strip()

                    following.append({
                        'name': name,
                        'url': user_url,
                        'followers': followers_text,
                        'followers_count': self._parse_count(followers_text)
                    })

                    print(f"  [{len(following)}] {name} - {followers_text}")

                    if len(following) >= max_users:
                        break

                except Exception as e:
                    continue

            if len(following) >= max_users:
                break

            # 滚动加载更多
            before_count = len(following)
            self.page.evaluate('window.scrollBy(0, 800)')
            time.sleep(1.5)

            if len(following) == before_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0

        print(f"共获取 {len(following)} 个关注用户")
        return following

    def fetch_user_videos(self, user_url: str, store_name: str,
                          max_posts: int = 50) -> List[Post]:
        """
        采集指定用户的视频数据

        Args:
            user_url: 用户主页 URL
            store_name: 门店名称
            max_posts: 最大采集数量

        Returns:
            帖子列表
        """
        print(f"\n采集用户: {store_name}")
        print(f"  URL: {user_url}")

        posts = []
        seen_titles = set()

        try:
            # 访问用户主页，带重试机制
            load_success = False
            max_retry = 10

            for retry in range(max_retry):
                self.page.goto(user_url, wait_until='domcontentloaded', timeout=60000)
                self._delay(3, 6)  # 页面加载后等待

                # 检查是否有视频卡片
                video_elements = self.page.query_selector_all('li:has(a[href*="/video/"])')
                title_elem = self.page.query_selector('p.PHhKt_o4.jvzvQhgp')

                if video_elements and title_elem:
                    load_success = True
                    print(f"  页面加载成功，找到 {len(video_elements)} 个视频卡片")
                    break
                else:
                    print(f"  第 {retry + 1} 次加载失败，5秒后刷新重试...")
                    time.sleep(5)

            if not load_success:
                print(f"  [警告] 10次刷新后仍未加载成功，跳过此门店")
                return posts  # 返回空列表

            scroll_attempts = 0
            max_scroll_attempts = 30

            while len(posts) < max_posts and scroll_attempts < max_scroll_attempts:
                # 查找包含视频链接的 li 元素
                video_elements = self.page.query_selector_all('li:has(a[href*="/video/"])')

                for video_elem in video_elements:
                    try:
                        # 获取标题 - p 元素有 PHhKt_o4 和 jvzvQhgp 两个class（注意大写）
                        title = None
                        title_elem = video_elem.query_selector('p.PHhKt_o4.jvzvQhgp')

                        if not title_elem:
                            continue

                        title = title_elem.text_content().strip()

                        # 过滤无效标题
                        if not title or title in seen_titles or len(title) < 2:
                            continue

                        seen_titles.add(title)

                        # 获取点赞数 - class包含 ziwD8xbw
                        likes = 0
                        likes_elem = video_elem.query_selector('[class*="ziwD8xbw"]')
                        if likes_elem:
                            likes_text = likes_elem.text_content().strip()
                            likes = self._parse_count(likes_text)

                        # 获取视频链接
                        video_url = None
                        link_elem = video_elem.query_selector('a[href*="/video/"]')
                        if link_elem:
                            href = link_elem.get_attribute('href')
                            if href:
                                video_url = self.BASE_URL + href if href.startswith('/') else href

                        post = Post(
                            store_name=store_name,
                            platform="抖音",
                            title=title,
                            post_time=None,
                            likes=likes,
                            post_link=video_url,
                            crawl_time=datetime.now()
                        )
                        posts.append(post)
                        print(f"    [{len(posts)}] {title[:40]}... 点赞:{likes}")

                        if len(posts) >= max_posts:
                            break

                    except Exception as e:
                        continue

                if len(posts) >= max_posts:
                    break

                # 滚动加载更多 - 模拟人类滚动行为
                before_count = len(posts)
                scroll_distance = random.randint(400, 800)
                self.page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                self._delay(2, 4)  # 滚动后等待

                if len(posts) == before_count:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0

        except Exception as e:
            print(f"  采集失败: {e}")

        print(f"  共采集 {len(posts)} 条视频")
        return posts

    def fetch_posts(self, store_name: str, max_posts: int = 50, store_url: str = None) -> List[Post]:
        """
        采集单个门店的帖子

        Args:
            store_name: 门店名称
            max_posts: 最大采集数量
            store_url: 门店抖音主页URL（可选，如果提供则直接使用）

        Returns:
            帖子列表
        """
        if store_url:
            # 直接使用提供的URL
            return self.fetch_user_videos(store_url, store_name, max_posts)

        # 如果没有提供URL，尝试从关注列表查找（旧逻辑）
        following = self.get_following_list(max_users=200)

        # 在关注列表中查找匹配的门店
        matched_users = []
        for user in following:
            if store_name in user['name'] or user['name'] in store_name:
                matched_users.append(user)

        if not matched_users:
            print(f"未在关注列表中找到: {store_name}")
            return []

        print(f"找到 {len(matched_users)} 个匹配账号")

        # 采集第一个匹配账号的视频
        user = matched_users[0]
        if user['url']:
            return self.fetch_user_videos(user['url'], store_name, max_posts)
        else:
            print(f"用户 {user['name']} 没有有效的主页链接")
            return []

    def fetch_stores(self, stores: List[Dict], max_posts_per_store: int = 50,
                     output_file: str = None) -> List[Post]:
        """
        采集多个门店的帖子

        Args:
            stores: 门店列表，每个元素包含 name, douyin_url 等字段
            max_posts_per_store: 每个门店最大采集数量
            output_file: 输出文件路径

        Returns:
            所有帖子列表
        """
        all_posts = []

        # 加载已有数据用于去重
        existing_titles = set()
        output_path = None
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists() and output_path.stat().st_size > 0:
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        for post in existing_data.get('posts', []):
                            existing_titles.add(post['title'])
                except json.JSONDecodeError:
                    pass

        # 记录加载失败的门店
        failed_stores = []

        # 采集每个门店
        for i, store in enumerate(stores):
            store_name = store['name']
            store_url = store.get('douyin_url', '')

            print(f"\n[{i+1}/{len(stores)}] 采集: {store_name}")

            if not store_url:
                print(f"  未配置抖音主页链接，跳过")
                continue

            # 采集视频
            posts = self.fetch_user_videos(
                store_url,
                store.get('short_name', store_name),
                max_posts_per_store
            )
            all_posts.extend(posts)

            # 记录加载失败的门店
            if len(posts) == 0:
                failed_stores.append(store_name)

            # 保存数据（增量，去重）
            if output_path and posts:
                existing_data = {'posts': []}
                if output_path.exists() and output_path.stat().st_size > 0:
                    try:
                        with open(output_path, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = {'posts': []}

                new_count = 0
                for post in posts:
                    # 去重：标题已存在则跳过
                    if post.title in existing_titles:
                        continue
                    existing_titles.add(post.title)

                    existing_data['posts'].append({
                        'store_name': post.store_name,
                        'title': post.title,
                        'likes': post.likes,
                        'post_link': post.post_link,
                        'crawl_time': post.crawl_time.isoformat()
                    })
                    new_count += 1

                existing_data['crawl_time'] = datetime.now().isoformat()
                existing_data['platform'] = '抖音'
                existing_data['total_posts'] = len(existing_data['posts'])

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)

                print(f"  新增 {new_count} 条，总计 {len(existing_data['posts'])} 条")

            # 门店之间随机延迟 30-60 秒，避免被反爬
            if i < len(stores) - 1:
                delay_time = random.randint(30, 60)
                print(f"  等待 {delay_time} 秒后继续...")
                time.sleep(delay_time)

        # 打印加载失败的门店
        if failed_stores:
            print(f"\n[注意] 以下 {len(failed_stores)} 个门店加载失败:")
            for name in failed_stores:
                print(f"  - {name}")

        print(f"\n总计采集 {len(all_posts)} 条帖子")
        return all_posts

    def close(self):
        """关闭浏览器"""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("浏览器已关闭")
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")


if __name__ == "__main__":
    # 测试代码
    scraper = DouyinWebScraper(headless=False)
    try:
        if scraper.login():
            following = scraper.get_following_list(max_users=50)
            print(f"\n关注列表: {len(following)} 个用户")
            for user in following[:5]:
                print(f"  - {user['name']}: {user['followers']}")
    finally:
        scraper.close()