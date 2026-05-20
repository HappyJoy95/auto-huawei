"""
Smart Sales 点检数据采集器 - MuMu模拟器 + ADB + UIAutomator
"""
import subprocess
import time
import re
import json
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path


class SmartSalesScraper:
    ADB_PATH = "adb"

    def __init__(self, adb_port: str = "127.0.0.1:16448", log_callback=None):
        self.adb_port = adb_port
        self.connected = False
        self.log_callback = log_callback

    def _log(self, level: str, msg: str):
        """输出日志"""
        print(msg)
        if self.log_callback:
            self.log_callback(level, msg)

    def _run_adb(self, cmd: str) -> str:
        full_cmd = f"{self.ADB_PATH} -s {self.adb_port} {cmd}"
        result = subprocess.run(full_cmd, shell=True, capture_output=True, encoding='utf-8', errors='ignore')
        return result.stdout

    def _connect(self) -> bool:
        self._log("INFO", f"正在连接模拟器: {self.adb_port}...")
        result = subprocess.run(
            f"{self.ADB_PATH} connect {self.adb_port}",
            shell=True, capture_output=True, encoding='utf-8', errors='ignore'
        )
        stdout = result.stdout.lower()
        stderr = result.stderr
        self._log("INFO", f"ADB连接响应: {stdout}")
        if stderr:
            self._log("WARNING", f"ADB连接stderr: {stderr}")

        if "connected" in stdout or "already connected" in stdout:
            self.connected = True
            self._log("INFO", f"已连接模拟器: {self.adb_port}")
            return True
        self._log("ERROR", f"连接失败: {stderr or stdout}")
        return False

    def _tap(self, x: int, y: int, delay: float = 0.5):
        x = max(0, min(x, 1079))
        y = max(0, min(y, 1919))
        self._run_adb(f"shell input tap {x} {y}")
        time.sleep(delay)

    def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        self._run_adb(f"shell input swipe {x1} {y1} {x2} {y2} {duration}")
        time.sleep(0.5)

    def _press_back(self):
        self._run_adb("shell input keyevent KEYCODE_BACK")
        time.sleep(0.5)

    def _dump_ui(self) -> str:
        self._run_adb("shell uiautomator dump /sdcard/ui.xml")
        return self._run_adb("shell cat /sdcard/ui.xml")

    def _wait_for_element(self, pattern: str, timeout: int = 30, interval: float = 2.0) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            ui_xml = self._dump_ui()
            if re.search(pattern, ui_xml):
                return True
            time.sleep(interval)
        return False

    def _launch_app(self):
        self._log("INFO", "启动 Smart Sales 应用...")
        self._run_adb("shell am start -n com.huawei.iretail.salesassistant/.splash.SplashActivity")
        self._log("INFO", "等待应用启动 (8秒)...")
        time.sleep(8)
        self._log("INFO", "应用启动完成")

    def _go_to_inspection_page(self) -> bool:
        """从Home页面进入点检页面"""
        self._log("INFO", "检查当前页面状态...")
        ui_xml = self._dump_ui()

        # 检查是否已经在点检页面
        if '智慧门店' in ui_xml:
            self._log("INFO", "已在点检页面")
            return True

        # 点击Me标签进入个人页面
        self._log("INFO", "点击 Me 标签 (810, 1838)")
        self._tap(810, 1838, delay=2)
        time.sleep(2)
        ui_xml = self._dump_ui()

        # 点击点检入口 (Inspection of Security Measures)
        match = re.search(r'Inspection of Security Measures[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', ui_xml)
        if match:
            x1, y1, x2, y2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            self._log("INFO", f"点击点检入口 ({cx}, {cy})")
            self._tap(cx, cy, delay=3)
        else:
            self._log("ERROR", "未找到点检入口元素")
            return False

        # 等待智慧门店页面加载
        self._log("INFO", "等待点检页面加载...")
        if not self._wait_for_element(r'智慧门店', timeout=15):
            self._log("ERROR", "点检页面加载超时")
            return False

        self._log("INFO", "已进入点检页面")
        time.sleep(2)
        return True

    def _get_current_store_info(self) -> Optional[Dict]:
        """获取当前门店信息和巡检数据"""
        self._log("INFO", "开始解析当前页面数据...")
        ui_xml = self._dump_ui()

        info = {
            'name': None,
            'code': None,
            'monthly_count': 0,
            'monthly_score': 0,
            'yearly_count': 0,
            'yearly_score': 0
        }

        # 获取所有text元素
        texts = re.findall(r'text="([^"]*)"', ui_xml)
        self._log("INFO", f"页面共有 {len(texts)} 个文本元素")

        # 获取门店名称 (包含华为/合作店的)
        for t in texts:
            if '华为' in t or '合作店' in t or '机场' in t:
                if len(t) > 10:  # 门店名称比较长
                    info['name'] = t
                    self._log("INFO", f"找到门店名称: {t}")
                    break

        if not info['name']:
            self._log("WARNING", "未找到门店名称")

        # 获取门店编码
        code_match = re.search(r'text="(SCN\d+|CNSCN\d+)"', ui_xml)
        if code_match:
            info['code'] = code_match.group(1)
            self._log("INFO", f"找到门店编码: {info['code']}")
        else:
            self._log("WARNING", "未找到门店编码")

        # 找到所有带坐标的text元素 (text, x1, y1, x2, y2)
        all_texts = re.findall(r'text="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', ui_xml)

        # 找月度巡检区域（用y坐标限定范围）
        monthly_y = None
        for text, x1, y1, x2, y2 in all_texts:
            if text == "月度巡检":
                monthly_y = int(y1)
                self._log("INFO", f"月度巡检区域 y坐标: {y1}")
                break

        if monthly_y:
            # 月度在左半部分 x<540，y在月度巡检+0~200范围内
            for text, x1, y1, x2, y2 in all_texts:
                x1, y1 = int(x1), int(y1)
                if monthly_y < y1 < monthly_y + 200 and x1 < 540:
                    if '/单' in text:
                        info['monthly_count'] = int(text.split('/')[0].strip())
                        self._log("INFO", f"月度次数: {text}")
                    if text.replace('.','').isdigit() and float(text) <= 100:
                        info['monthly_score'] = float(text)
                        self._log("INFO", f"月度得分: {text}")
        else:
            self._log("WARNING", "未找到月度巡检区域")

        # 找年度巡检区域
        for text, x1, y1, x2, y2 in all_texts:
            if text == "年度巡检":
                yearly_y = int(y1)
                self._log("INFO", f"年度巡检区域 y坐标: {y1}")
                # 年度在右半部分 x>540
                for t2, tx1, ty1, tx2, ty2 in all_texts:
                    tx1, ty1 = int(tx1), int(ty1)
                    if yearly_y < ty1 < yearly_y + 200 and tx1 > 540:
                        if '/单' in t2:
                            info['yearly_count'] = int(t2.split('/')[0].strip())
                            self._log("INFO", f"年度次数: {t2}")
                        if t2.replace('.','').isdigit() and float(t2) <= 100:
                            info['yearly_score'] = float(t2)
                            self._log("INFO", f"年度得分: {t2}")
                break

        if info['name']:
            self._log("INFO", f"解析结果: {info['code']} - 月度{info['monthly_count']}次/得分{info['monthly_score']}, 年度{info['yearly_count']}次/得分{info['yearly_score']}")
        return info if info['name'] else None

    def _open_store_list(self) -> bool:
        """打开门店列表"""
        self._log("INFO", "点击门店名称区域 (540, 300)")
        self._tap(540, 300, delay=2)

        # 等待门店列表加载
        self._log("INFO", "等待门店列表加载...")
        for i in range(8):
            ui_xml = self._dump_ui()
            if '选择门店' in ui_xml and '华为' in ui_xml:
                # 检查是否有门店数据加载出来
                if re.search(r'text="[^"]+华为[^"]+店"', ui_xml):
                    self._log("INFO", "门店列表已加载")
                    return True
            self._log("INFO", f"等待中... ({i+1}/8)")
            time.sleep(1)

        # 加载失败，返回重试
        self._log("WARNING", "门店列表加载失败")
        self._press_back()
        time.sleep(1)
        return False

    def _select_store(self, store_code: str, store_name: str) -> bool:
        """用门店代码搜索选择门店"""
        self._log("INFO", "点击搜索框 (540, 140)")
        self._tap(540, 140, delay=1)
        time.sleep(1)

        # 输入门店代码
        self._log("INFO", f"输入门店代码: {store_code}")
        self._run_adb(f'shell input text "{store_code}"')
        time.sleep(2)

        # 点击搜索结果（y=440，固定位置）
        self._log("INFO", "点击搜索结果 (540, 440)")
        self._tap(540, 440, delay=2)
        self._log("INFO", "门店切换完成")
        return True

    def _select_store_old(self, store_name: str) -> bool:
        """在门店列表中选择指定门店"""
        # 先滑动到顶部
        for _ in range(3):
            self._swipe(540, 800, 540, 1500, duration=200)
        time.sleep(1)

        no_change_count = 0
        last_ui_hash = 0

        # 查找门店
        while True:
            # 滑动完成后等待1s再识别
            time.sleep(1)
            ui_xml = self._dump_ui()

            # 检查是否找到门店（只匹配列表区域y=300-1500内的元素）
            pattern = rf'text="{re.escape(store_name)}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
            matches = list(re.finditer(pattern, ui_xml))
            for match in reversed(matches):  # 从后往前找，最后一个是列表项
                x1, y1, x2, y2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
                cy = (y1 + y2) // 2
                if 300 < cy < 1500:  # 只匹配列表区域内的
                    print(f"  [找到] 门店位置 y={cy}")

                    # 如果门店太靠下，滑动到中间位置
                    if cy > 1200:
                        scroll_dist = cy - 800
                        print(f"  [滑动] 位置太靠下，向上滑动 {scroll_dist} 像素到中间")
                        self._swipe(540, 1500, 540, 1500 - scroll_dist, duration=300)
                        time.sleep(1)
                        cy = 800

                    # 点击选中门店（直接点击就切换，不需要确认）
                    print(f"  [点击] 选中门店 (540, {cy})")
                    self._tap(540, cy, delay=2)
                    print("  [完成] 门店切换成功")
                    return True

            # 检查是否到底（连续3次滑动UI无变化）
            current_hash = hash(ui_xml)
            if current_hash == last_ui_hash:
                no_change_count += 1
                print(f"  [检测] UI无变化 ({no_change_count}/3)")
                if no_change_count >= 3:
                    # 拉到底了，最后再找一次，不受y坐标限制
                    print(f"  [重试] 已到底，最后查找一次（不受位置限制）")
                    matches = list(re.finditer(pattern, ui_xml))
                    if matches:
                        match = matches[-1]  # 取最后一个
                        x1, y1, x2, y2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
                        cy = (y1 + y2) // 2
                        print(f"  [找到] 底部门店位置 y={cy}")
                        print(f"  [点击] 选中门店 (540, {cy})")
                        self._tap(540, cy, delay=2)
                        print("  [完成] 门店切换成功")
                        return True
                    print(f"  [错误] 未找到门店: {store_name}")
                    return False
            else:
                no_change_count = 0
            last_ui_hash = current_hash

            # 向下滑动
            print("  [滑动] 向下查找门店")
            self._swipe(540, 1500, 540, 800, duration=300)
            time.sleep(1)

    def fetch_inspection_data(self, stores: List[Dict], output_file: str = None, dry_run: bool = False) -> List[Dict]:
        """采集多个门店的巡检数据"""
        self._log("INFO", f"fetch_inspection_data 开始执行")
        self._log("INFO", f"门店列表数量: {len(stores) if stores else 0}")
        if dry_run:
            self._log("INFO", "测试模式: 不会写入文件")

        if not stores:
            self._log("ERROR", "门店列表为空!")
            return []

        if not self.connected:
            self._log("INFO", "未连接，尝试连接模拟器...")
            if not self._connect():
                self._log("ERROR", "连接模拟器失败，退出采集")
                return []
            self._log("INFO", "模拟器连接成功")

        # 读取已有历史数据
        history = []
        if output_file and Path(output_file).exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    history = history_data.get('stores', [])
                self._log("INFO", f"加载历史记录: {len(history)} 条")
            except json.JSONDecodeError:
                self._log("WARNING", "历史文件损坏，重新开始")
                history = []

        results = history.copy()  # 保留已有数据
        initial_count = len(results)  # 记录初始数量
        self._log("INFO", f"初始记录数: {initial_count}")

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # 启动应用并进入点检页面
        self._log("INFO", "启动应用...")
        self._launch_app()
        self._log("INFO", "应用已启动，尝试进入点检页面...")

        if not self._go_to_inspection_page():
            self._log("ERROR", "无法进入点检页面")
            return []

        self._log("INFO", f"开始逐个采集门店，共 {len(stores)} 个")

        for i, store in enumerate(stores):
            self._log("INFO", f"--- 开始采集第 {i+1}/{len(stores)} 个门店 ---")
            store_name = store['name']
            short_name = store.get('short_name', store_name)
            self._log("INFO", f"门店名称: {short_name}")

            # 打开门店列表
            self._log("INFO", "打开门店列表...")
            if not self._open_store_list():
                # 加载失败，重新进入点检页面
                self._log("WARNING", "门店列表加载失败，重试...")
                self._go_to_inspection_page()
                continue

            # 选择门店
            store_code = store.get('code', '')
            self._log("INFO", f"选择门店，代码: {store_code or '无'}")
            if not self._select_store(store_code, store_name):
                self._log("WARNING", f"门店选择失败: {short_name}")
                continue

            # 等待数据加载，校验门店编码
            self._log("INFO", "等待门店数据加载...")
            for retry in range(5):
                time.sleep(1)
                ui_xml = self._dump_ui()
                if store_code and store_code in ui_xml:
                    self._log("INFO", f"门店已切换，找到代码: {store_code}")
                    break
                self._log("INFO", f"等待门店切换... ({retry+1}/5)")
            else:
                self._log("WARNING", "门店切换等待超时，继续尝试获取数据")

            # 检查是否误入了详情页面，是则返回
            if '巡检详情' in ui_xml or '得分详情' in ui_xml:
                self._log("WARNING", "误入详情页面，按返回")
                self._press_back()
                time.sleep(1)
            # 获取巡检数据
            self._log("INFO", "提取巡检数据...")
            info = self._get_current_store_info()

            if info:
                self._log("INFO", f"数据解析成功: {info}")

                # 检查数据有效性（月度或年度至少有一个有数据）
                monthly_valid = info['monthly_count'] > 0 or info['monthly_score'] > 0
                yearly_valid = info.get('yearly_count', 0) > 0 or info.get('yearly_score', 0) > 0

                if not monthly_valid and not yearly_valid:
                    self._log("WARNING", "数据全为0，跳过保存")
                    continue

                result = {
                    'name': store_name,
                    'short_name': short_name,
                    'code': store.get('code', info.get('code')),
                    'monthly_count': info['monthly_count'],
                    'monthly_score': info['monthly_score'],
                    'yearly_count': info.get('yearly_count', 0),
                    'yearly_score': info.get('yearly_score', 0),
                    'crawl_time': datetime.now().isoformat()
                }

                # 查找该门店上一次的记录
                last_record = None
                for r in reversed(results):
                    if r['name'] == store_name:
                        last_record = r
                        break

                # 用年度数据判断是否有变化（月度数据每月会清空）
                changed = True
                if last_record:
                    last_yearly_count = last_record.get('yearly_count', 0)
                    last_yearly_score = last_record.get('yearly_score', 0)
                    curr_yearly_count = info.get('yearly_count', 0)
                    curr_yearly_score = info.get('yearly_score', 0)

                    # 年度次数增加或得分变化才算有变化
                    if curr_yearly_count == last_yearly_count and curr_yearly_score == last_yearly_score:
                        changed = False
                        self._log("INFO", f"年度数据无变化，跳过写入")
                        self._log("INFO", f"月度: {info['monthly_count']}次/{info['monthly_score']}分")
                        self._log("INFO", f"年度: {curr_yearly_count}次/{curr_yearly_score}分")

                if changed:
                    results.append(result)
                    if last_record:
                        self._log("INFO", f"年度数据有变化，追加新记录")
                    else:
                        self._log("INFO", f"首次记录该门店数据")
                    self._log("INFO", f"月度: {info['monthly_count']}次/{info['monthly_score']}分")
                    self._log("INFO", f"年度: {info.get('yearly_count', 0)}次/{info.get('yearly_score', 0)}分")

                    # 保存到文件
                    if output_file and not dry_run:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump({
                                'crawl_time': datetime.now().isoformat(),
                                'total_stores': len(results),
                                'stores': results
                            }, f, ensure_ascii=False, indent=2)
                        self._log("INFO", "已保存到文件")
                    elif dry_run:
                        self._log("INFO", f"测试模式: 跳过写入文件")
            else:
                self._log("WARNING", f"无法获取门店数据: {short_name}")

        # 统计本次新增
        new_count = len(results) - initial_count
        self._log("INFO", f"采集完成，总计 {len(results)} 条记录，本次新增 {new_count} 条")
        return results

    def close(self):
        self._log("INFO", "正在关闭应用...")
        self._run_adb("shell am force-stop com.huawei.iretail.salesassistant")
        self._log("INFO", "应用已退出")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # 加载门店列表
    with open('config/stores.json', 'r', encoding='utf-8') as f:
        store_config = json.load(f)

    stores = store_config['stores']

    scraper = SmartSalesScraper()
    try:
        results = scraper.fetch_inspection_data(
            stores=stores,
            output_file='data/inspection_data.json'
        )
    finally:
        scraper.close()
