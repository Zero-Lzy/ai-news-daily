"""
配置管理器
=========
负责加载、校验和提供全局配置。

功能：
  - 从 config/settings.json 加载配置
  - 支持环境变量覆盖（如 NEWS_SCHEDULE_MORNING_HOUR=9）
  - 提供默认值回退
  - 配置路径点号访问（config.get("schedule.morning_hour")）
"""
import os
import json
from typing import Any
from loguru import logger

# 项目根目录（src/ 的上一级）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "settings.json")


class Config:
    """全局配置单例"""

    _instance = None
    _data: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, path: str = None):
        """
        加载配置文件

        Args:
            path: 配置文件路径，为空时使用默认路径
        """
        config_path = path or DEFAULT_CONFIG_PATH

        if not os.path.exists(config_path):
            logger.warning(f"配置文件不存在: {config_path}，使用内置默认值")
            self._data = self._defaults()
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"配置加载成功: {config_path}")
        except Exception as e:
            logger.error(f"配置加载失败: {e}，使用默认值")
            self._data = self._defaults()

        # 环境变量覆盖（NEWS_ 前缀，双下划线分隔层级）
        for key, value in os.environ.items():
            if key.startswith("NEWS_"):
                config_path_str = key[5:].lower().replace("__", ".")
                try:
                    # 尝试转换数字
                    if value.isdigit():
                        value = int(value)
                    self.set(config_path_str, value)
                    logger.debug(f"环境变量覆盖配置: {config_path_str} = {value}")
                except Exception:
                    pass

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号路径

        Args:
            key_path: 配置路径，如 "schedule.morning_hour"
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any):
        """设置配置值"""
        keys = key_path.split(".")
        d = self._data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

    def get_section(self, section: str) -> dict:
        """获取配置段"""
        return self._data.get(section, {})

    @staticmethod
    def _defaults() -> dict:
        """内置默认配置"""
        return {
            "schedule": {
                "morning_hour": 8,
                "morning_minute": 0,
                "evening_hour": 20,
                "evening_minute": 0,
                "timezone": "Asia/Shanghai",
            },
            "output": {
                "dir": "./output",
                "filename_format": "AI简讯_{date}.md",
                "append_if_exists": True,
            },
            "sources": {
                "rss_feeds": [],
                "web_scrape": [],
                "request_timeout": 30,
                "max_articles_per_source": 30,
                "user_agent": "Mozilla/5.0",
            },
            "filter": {
                "keywords_include": ["AI", "人工智能"],
                "keywords_exclude": [],
                "max_age_hours": 48,
                "deduplicate": True,
            },
            "logging": {
                "level": "INFO",
                "file": "./logs/ai-news-daily.log",
            },
        }

    @property
    def project_root(self) -> str:
        return PROJECT_ROOT


# 全局配置实例
config = Config()
