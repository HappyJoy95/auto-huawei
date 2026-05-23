"""
大众点评店铺评论采集器 - 基于 Scrapling
支持：
1. 绕过反爬机制（使用 StealthyFetcher）
2. 采集店铺评分、星级
3. 采集用户评论内容
"""
import json
import time
import re
import random
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from pathlib import Path


@dataclass
class Review:
    """评论数据结构"""
    store_name: str
    user_name: Optional[str]
    rating: Optional[float]
    content: Optional[str]
    review_time: Optional[str]
    likes: Optional[int]
    reply_count: Optional[int]
    crawl_time: datetime

    def to_dict(self) -> dict:
        d = asdict(self)
        d['crawl_time'] = self.crawl_time.isoformat()
        return d


@dataclass
class StoreInfo:
    """店铺信息"""
    name: str
    rating: Optional[float]
    review_count: Optional[int]
    avg_price: Optional[str]
    address: Optional[str]
    category: Optional[str]
    crawl_time: datetime

    def to_dict(self) -> dict:
        d = asdict(self)
        d['crawl_time'] = self.crawl_time.isoformat()
        return d


class DianpingScraper:
    """大众点评采集器"""

    # 延迟范围
    DELAY_MIN = 3.0
    DELAY_MAX = 8.0

    def __init__(self, proxy: str = None, headless: bool = True, log_callback=None):
        """
        初始化采集器

        Args:
            proxy: 代理地址，如 "http://127.0.0.1:7890"
            headless: 是否无头模式
            log_callback: 日志回调函数
        """
        self.proxy = proxy
        self.headless = headless
        self.log_callback = log_callback
        self.fetcher = None

    def _log(self, level: str, msg: str):
        """输出日志"""
        if self.log_callback:
            self.log_callback(level, msg)
        print(f"[{level}] {msg}")

    def _get_fetcher(self):
        """获取 Scrapling fetcher"""
        if self.fetcher is None:
            try:
                from scrapling.fetchers import StealthyFetcher
                self.fetcher = StealthyFetcher
            except ImportError:
                raise ImportError(
                    "请先安装 scrapling: pip install 'scrapling[fetchers]' && scrapling install"
                )
        return self.fetcher

    def _delay(self, min_sec: float = None, max_sec: float = None):
        """随机延迟"""
        min_sec = min_sec or self.DELAY_MIN
        max_sec = max_sec or self.DELAY_MAX
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _parse_rating(self, rating_str: str) -> Optional[float]:
        """解析评分字符串"""
        if not rating_str:
            return None
        # 匹配 "4.8分" 或 "4.8" 格式
        match = re.search(r'(\d+\.?\d*)', str(rating_str))
        if match:
            return float(match.group(1))
        return None

    def _parse_count(self, count_str: str) -> Optional[int]:
        """解析数量字符串"""
        if not count_str:
            return None
        count_str = str(count_str).strip()
        try:
            if '万' in count_str:
                num = float(count_str.replace('万', ''))
                return int(num * 10000)
            elif '条' in count_str:
                num = re.search(r'(\d+)', count_str)
                return int(num.group(1)) if num else None
            else:
                return int(count_str)
        except:
            return None

    def fetch_store_info(self, store_url: str, store_name: str) -> Optional[StoreInfo]:
        """
        获取店铺基本信息

        Args:
            store_url: 店铺详情页 URL
            store_name: 店铺名称

        Returns:
            店铺信息
        """
        self._log("INFO", f"获取店铺信息: {store_name}")
        self._log("INFO", f"URL: {store_url}")

        try:
            fetcher = self._get_fetcher()

            # 使用 StealthyFetcher 获取页面
            kwargs = {
                'headless': self.headless,
                'network_idle': True,
            }
            if self.proxy:
                kwargs['proxy'] = self.proxy

            page = fetcher.fetch(store_url, **kwargs)

            # 提取店铺名称
            name_elem = page.css('h1.shop-name, .shop-name, h1[class*="shopName"]')
            name = name_elem[0].text_content().strip() if name_elem else store_name

            # 提取评分
            rating = None
            rating_elem = page.css('.shop-score, .score, [class*="rating"], [class*="score"]')
            if rating_elem:
                rating = self._parse_rating(rating_elem[0].text_content())

            # 提取评论数
            review_count = None
            review_elem = page.css('.review-count, [class*="reviewCount"], [class*="comment"]')
            if review_elem:
                review_count = self._parse_count(review_elem[0].text_content())

            # 提取人均价格
            avg_price = None
            price_elem = page.css('.avg-price, [class*="avgPrice"], [class*="price"]')
            if price_elem:
                avg_price = price_elem[0].text_content().strip()

            # 提取地址
            address = None
            addr_elem = page.css('.shop-addr, .address, [class*="address"]')
            if addr_elem:
                address = addr_elem[0].text_content().strip()

            # 提取分类
            category = None
            cat_elem = page.css('.shop-category, .category, [class*="category"]')
            if cat_elem:
                category = cat_elem[0].text_content().strip()

            store_info = StoreInfo(
                name=name,
                rating=rating,
                review_count=review_count,
                avg_price=avg_price,
                address=address,
                category=category,
                crawl_time=datetime.now()
            )

            self._log("INFO", f"店铺: {name}, 评分: {rating}, 评论数: {review_count}")

            return store_info

        except Exception as e:
            self._log("ERROR", f"获取店铺信息失败: {e}")
            import traceback
            self._log("ERROR", traceback.format_exc())
            return None

    def fetch_reviews(self, store_url: str, store_name: str,
                      max_reviews: int = 50) -> List[Review]:
        """
        获取店铺评论

        Args:
            store_url: 店铺详情页 URL
            store_name: 店铺名称
            max_reviews: 最大评论数

        Returns:
            评论列表
        """
        self._log("INFO", f"采集评论: {store_name}")

        reviews = []
        seen_content = set()

        try:
            fetcher = self._get_fetcher()

            # 使用 StealthyFetcher 获取页面
            kwargs = {
                'headless': self.headless,
                'network_idle': True,
            }
            if self.proxy:
                kwargs['proxy'] = self.proxy

            page = fetcher.fetch(store_url, **kwargs)

            # 等待页面加载
            self._delay(2, 4)

            # 尝试多种选择器获取评论列表
            review_selectors = [
                '.review-list .review-item',
                '.comment-list .comment-item',
                '[class*="reviewItem"]',
                '[class*="commentItem"]',
                '.review-item',
                '.comment-item',
            ]

            review_elements = []
            for selector in review_selectors:
                review_elements = page.css(selector)
                if review_elements:
                    self._log("INFO", f"使用选择器: {selector}, 找到 {len(review_elements)} 条评论")
                    break

            if not review_elements:
                self._log("WARNING", "未找到评论元素，尝试其他方式...")
                # 尝试查找所有可能的评论容器
                all_divs = page.css('div')
                for div in all_divs[:100]:  # 只检查前100个
                    class_name = div.attrib.get('class', '')
                    if 'review' in class_name.lower() or 'comment' in class_name.lower():
                        review_elements.append(div)

            for elem in review_elements[:max_reviews]:
                try:
                    # 提取用户名
                    user_name = None
                    user_elem = elem.css('.user-name, .userName, [class*="userName"], a[href*="user"]')
                    if user_elem:
                        user_name = user_elem[0].text_content().strip()

                    # 提取评分
                    rating = None
                    rating_elem = elem.css('.rating, .score, [class*="rating"], [class*="star"]')
                    if rating_elem:
                        # 检查是否有 star 类
                        star_elem = rating_elem[0].css('[class*="star"]')
                        if star_elem:
                            # 通常星级通过 CSS class 表示，如 star-50 表示 5 星
                            star_class = star_elem[0].attrib.get('class', '')
                            star_match = re.search(r'star-(\d+)', star_class)
                            if star_match:
                                rating = int(star_match.group(1)) / 10
                        else:
                            rating = self._parse_rating(rating_elem[0].text_content())

                    # 提取评论内容
                    content = None
                    content_elem = elem.css('.review-content, .content, [class*="content"], p')
                    if content_elem:
                        content = content_elem[0].text_content().strip()

                    # 过滤空内容和重复内容
                    if not content or len(content) < 5:
                        continue
                    if content in seen_content:
                        continue
                    seen_content.add(content)

                    # 提取评论时间
                    review_time = None
                    time_elem = elem.css('.time, .date, [class*="time"]')
                    if time_elem:
                        review_time = time_elem[0].text_content().strip()

                    # 提取点赞数
                    likes = None
                    likes_elem = elem.css('.like-count, .likes, [class*="like"]')
                    if likes_elem:
                        likes = self._parse_count(likes_elem[0].text_content())

                    # 提取回复数
                    reply_count = None
                    reply_elem = elem.css('.reply-count, [class*="reply"]')
                    if reply_elem:
                        reply_count = self._parse_count(reply_elem[0].text_content())

                    review = Review(
                        store_name=store_name,
                        user_name=user_name,
                        rating=rating,
                        content=content,
                        review_time=review_time,
                        likes=likes,
                        reply_count=reply_count,
                        crawl_time=datetime.now()
                    )
                    reviews.append(review)

                    self._log("INFO", f"[{len(reviews)}] {user_name or '匿名'}: {content[:30]}...")

                    if len(reviews) >= max_reviews:
                        break

                except Exception as e:
                    continue

        except Exception as e:
            self._log("ERROR", f"采集评论失败: {e}")
            import traceback
            self._log("ERROR", traceback.format_exc())

        self._log("INFO", f"共采集 {len(reviews)} 条评论")
        return reviews

    def fetch_store(self, store_url: str, store_name: str,
                    max_reviews: int = 50) -> Dict:
        """
        获取店铺完整数据（店铺信息 + 评论）

        Args:
            store_url: 店铺详情页 URL
            store_name: 店铺名称
            max_reviews: 最大评论数

        Returns:
            包含店铺信息和评论的字典
        """
        store_info = self.fetch_store_info(store_url, store_name)
        reviews = self.fetch_reviews(store_url, store_name, max_reviews)

        return {
            'store_info': store_info.to_dict() if store_info else None,
            'reviews': [r.to_dict() for r in reviews],
            'crawl_time': datetime.now().isoformat()
        }

    def fetch_stores(self, stores: List[Dict], max_reviews: int = 50,
                     delay: int = 5, output_file: str = None,
                     progress_callback=None) -> List[Dict]:
        """
        批量采集多个店铺

        Args:
            stores: 店铺列表，每个元素包含 name, url
            max_reviews: 每个店铺最大评论数
            delay: 请求间隔（秒）
            output_file: 输出文件路径
            progress_callback: 进度回调函数 callback(current, total, message)

        Returns:
            所有店铺数据列表
        """
        all_data = []
        total = len(stores)

        for i, store in enumerate(stores):
            store_name = store.get('name', '未知店铺')
            store_url = store.get('url')

            if not store_url:
                self._log("WARNING", f"[{i+1}/{total}] {store_name} 缺少URL，跳过")
                continue

            if progress_callback:
                progress_callback(i + 1, total, f"正在采集: {store_name}")

            self._log("INFO", f"[{i+1}/{total}] 采集: {store_name}")

            try:
                data = self.fetch_store(store_url, store_name, max_reviews)
                all_data.append(data)

                # 保存数据
                if output_file:
                    self._save_data(all_data, output_file)

            except Exception as e:
                self._log("ERROR", f"采集失败: {e}")
                import traceback
                self._log("ERROR", traceback.format_exc())
                all_data.append({
                    'store_info': {'name': store_name, 'error': str(e)},
                    'reviews': [],
                    'crawl_time': datetime.now().isoformat()
                })

            # 延迟
            if i < total - 1:
                actual_delay = delay + random.uniform(0, 2)
                self._log("INFO", f"等待 {actual_delay:.1f} 秒...")
                time.sleep(actual_delay)

        return all_data

    def _save_data(self, data: List[Dict], output_file: str):
        """保存数据到文件"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'data': data,
                'crawl_time': datetime.now().isoformat(),
                'total_stores': len(data)
            }, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试代码
    scraper = DianpingScraper(headless=False)

    test_url = "https://www.dianping.com/shop/xxxxx"  # 替换为实际URL
    data = scraper.fetch_store(test_url, "测试店铺", max_reviews=10)
    print(json.dumps(data, ensure_ascii=False, indent=2))
