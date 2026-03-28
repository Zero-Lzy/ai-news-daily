"""
AI 简讯自动抓取系统 — 主入口
==============================

使用方式：
  python main.py              # 立即执行一次抓取
  python main.py --schedule   # 启动定时调度（常驻进程）
  python main.py --label 早报  # 执行一次并指定标签
  python main.py --web         # 启动 Web 展示页面
  python main.py --web --port 3000  # 指定端口启动
"""
import os
import sys
import asyncio
import argparse

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from src.config import config
from src.scheduler import run_once, start_scheduler


def setup_logging():
    """配置日志"""
    log_cfg = config.get_section("logging")
    level = log_cfg.get("level", "INFO")
    log_file = log_cfg.get("file", "")

    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:^8}</level> | <cyan>{message}</cyan>",
        level=level,
    )

    if log_file:
        log_path = os.path.join(config.project_root, log_file)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        logger.add(log_path, rotation="5 MB", retention="30 days", level="DEBUG")


def main():
    parser = argparse.ArgumentParser(
        description="AI 简讯自动抓取系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                  # 立即执行一次
  python main.py --schedule       # 启动定时任务（每天 8:00 + 20:00）
  python main.py --label 早报     # 指定标签立即执行
  python main.py --config path    # 指定配置文件路径
  python main.py --web            # 启动 Web 展示页面（默认端口 8080）
  python main.py --web --port 3000  # 指定端口启动 Web
        """,
    )
    parser.add_argument(
        "--schedule", action="store_true",
        help="启动定时调度模式（常驻进程，按配置时间自动执行）",
    )
    parser.add_argument(
        "--web", action="store_true",
        help="启动 Web 展示页面（浏览器访问查看资讯）",
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0",
        help="Web 服务绑定地址（默认: 0.0.0.0）",
    )
    parser.add_argument(
        "--port", type=int, default=8080,
        help="Web 服务端口（默认: 8080）",
    )
    parser.add_argument(
        "--label", type=str, default="",
        help="运行标签，如 '早报' 或 '晚报'（为空则自动判断）",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="自定义配置文件路径（默认: config/settings.json）",
    )
    args = parser.parse_args()

    # 加载配置
    config.load(args.config)
    setup_logging()

    logger.info("🤖 AI 简讯自动抓取系统 v1.0.0")

    if args.web:
        # Web 展示模式
        from src.web_server import create_app
        import uvicorn

        app = create_app()
        logger.info(f"🌐 Web 服务启动: http://localhost:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)

    elif args.schedule:
        # 定时模式
        start_scheduler()
    else:
        # 立即执行一次
        filepath = asyncio.run(run_once(label=args.label))
        print(f"\n📄 文件已保存: {filepath}")


if __name__ == "__main__":
    main()
