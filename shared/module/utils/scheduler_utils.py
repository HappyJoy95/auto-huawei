"""
调度工具函数 - 提取自 module_manager.py 和 scheduler.py 的重复逻辑
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from croniter import croniter


def parse_manual_time(time_str: str, now: datetime = None) -> Optional[datetime]:
    """
    解析手动时间字符串，格式: mm-dd HH:MM:SS
    返回对应 datetime（基于当前年份），如果时间已过则返回 None。
    """
    if not time_str:
        return None

    now = now or datetime.now()

    try:
        parts = time_str.split()
        if len(parts) != 2:
            return None

        date_parts = parts[0].split("-")
        time_parts = parts[1].split(":")

        month = int(date_parts[0])
        day = int(date_parts[1])
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0

        next_run = now.replace(month=month, day=day, hour=hour, minute=minute, second=second, microsecond=0)

        if next_run > now:
            return next_run
        return None
    except (ValueError, IndexError):
        return None


def calculate_next_run(config: Dict, now: datetime = None, log_warning: callable = None) -> Optional[datetime]:
    """
    计算下次运行时间（统一实现）。

    :param config: 调度器配置字典
    :param now: 当前时间（可注入，默认 datetime.now()）
    :param log_warning: 日志回调，签名 (msg, module) -> None
    :return: 下次运行时间，或 None
    """
    now = now or datetime.now()

    def _log(msg: str):
        if log_warning:
            log_warning(msg, "scheduler")

    # 检查是否有定时配置（interval 或 schedule）
    has_schedule = config.get("interval") or config.get("schedule")

    # 手动设置的时间（没有其他定时配置时使用）
    if not has_schedule:
        manual_time = config.get("manual_time") or "01-01 00:00:00"
        result = parse_manual_time(manual_time, now)
        if result is None and manual_time != "01-01 00:00:00":
            _log(f"手动时间解析失败: {manual_time}")
        if result is not None:
            return result

    # 间隔执行
    interval = config.get("interval")
    if interval:
        start_time = config.get("interval_start", "00:00")
        end_time = config.get("interval_end", "23:59")
        days = config.get("interval_days", [1, 2, 3, 4, 5])

        # 检查今天是否在生效日期内
        today_dow = now.weekday()
        py_to_frontend = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}

        if py_to_frontend[today_dow] in days:
            h, m = map(int, start_time.split(":"))
            start_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            h, m = map(int, end_time.split(":"))
            end_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)

            if now < start_dt:
                return start_dt
            elif now <= end_dt:
                minutes_since_start = (now - start_dt).total_seconds() / 60
                intervals_passed = int(minutes_since_start / interval)
                next_run = start_dt + timedelta(minutes=(intervals_passed + 1) * interval)
                if next_run <= end_dt:
                    return next_run

        # 找下一个生效日期
        for i in range(1, 8):
            next_day = (today_dow + i) % 7
            if py_to_frontend[next_day] in days:
                h, m = map(int, start_time.split(":"))
                next_run = now.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=i)
                return next_run

        return None

    # Cron 表达式
    schedule = config.get("schedule")
    if schedule:
        schedules = schedule if isinstance(schedule, list) else [schedule]
        next_runs = []

        for sch in schedules:
            if isinstance(sch, str):
                try:
                    cron = croniter(sch, now)
                    next_runs.append(cron.get_next(datetime))
                except (ValueError, KeyError) as e:
                    _log(f"Cron 表达式解析失败: {sch} - {e}")

        if next_runs:
            return min(next_runs)

    return None
