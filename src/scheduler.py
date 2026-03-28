"""
定时任务调度器
==============
负责按配置时间自动触发抓取任务。

调度策略：
  - 默认每天早 8:00 + 晚 20:00 各执行一次
  - 支持通过配置文件修改执行时间
  - 支持通过环境变量覆盖（NEWS_SCHEDULE__MORNING_HOUR=9）
  - 支持手动立即执行（--now 参数）

实现方式：
  - 本地运行: 使用 schedule 库的轮询模式
  - CI/CD 运行: 由 GitHub Actions cron 触发，每次只执行一次后退出
"""
import asyncio
import time
from datetime import datetime
from loguru import logger

try:
    import schedule
except ImportError:
    schedule = None

from .config import config
from .fetcher import Fetcher
from .filter import Filter
from .writer import MarkdownWriter
from .json_writer import JsonWriter


async def run_once(label: str = "") -> str:
    """
    执行一次完整的 抓取 → 过滤 → 保存 流程

    Args:
        label: 运行标签（"早报" / "晚报" / 自定义），空值则自动判断

    Returns:
        保存的文件路径
    """
    start = time.time()
    logger.info("=" * 50)
    logger.info(f"🚀 开始执行资讯抓取任务 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    logger.info("=" * 50)

    # Step 1: 抓取
    fetcher = Fetcher()
    articles = await fetcher.fetch_all()
    logger.info(f"[Step 1/4] 抓取完成: {len(articles)} 条原始资讯")

    # Step 2: 过滤
    flt = Filter()
    filtered = flt.apply(articles)
    logger.info(f"[Step 2/4] 过滤完成: {len(filtered)} 条有效资讯")

    # Step 3: 保存 Markdown
    writer = MarkdownWriter()
    filepath = writer.save(filtered, run_label=label)
    logger.info(f"[Step 3/4] Markdown 保存完成: {filepath}")

    # Step 4: 保存 JSON（供 Web 页面读取）
    try:
        json_writer = JsonWriter()
        json_path = json_writer.save(filtered, run_label=label)
        logger.info(f"[Step 4/4] JSON 数据保存完成: {json_path}")
    except Exception as e:
        logger.warning(f"[Step 4/4] JSON 保存跳过（非致命）: {e}")

    elapsed = time.time() - start
    logger.info(f"✅ 任务完成，耗时 {elapsed:.1f} 秒，共保存 {len(filtered)} 条资讯")
    logger.info("=" * 50)

    return filepath


def _sync_run_once():
    """schedule 库需要的同步包装"""
    asyncio.run(run_once())


def start_scheduler():
    """
    启动定时调度器（本地常驻模式）

    按配置的时间点每天定时执行。程序会持续运行，直到手动终止。
    """
    if schedule is None:
        logger.error("schedule 库未安装，请运行: pip install schedule")
        return

    sch_cfg = config.get_section("schedule")
    morning_h = sch_cfg.get("morning_hour", 8)
    morning_m = sch_cfg.get("morning_minute", 0)
    evening_h = sch_cfg.get("evening_hour", 20)
    evening_m = sch_cfg.get("evening_minute", 0)

    morning_time = f"{morning_h:02d}:{morning_m:02d}"
    evening_time = f"{evening_h:02d}:{evening_m:02d}"

    schedule.every().day.at(morning_time).do(_sync_run_once)
    schedule.every().day.at(evening_time).do(_sync_run_once)

    logger.info(f"⏰ 定时调度已启动")
    logger.info(f"   早报时间: 每天 {morning_time}")
    logger.info(f"   晚报时间: 每天 {evening_time}")
    logger.info(f"   按 Ctrl+C 停止")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # 每 30 秒检查一次
    except KeyboardInterrupt:
        logger.info("调度器已停止")
