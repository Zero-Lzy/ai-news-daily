"""
JSON 数据写入器
================
将过滤后的资讯保存为 JSON 格式，供 Web 前端读取展示。

输出文件结构：
  data/
  ├── articles.json          # 全量文章列表（追加模式）
  ├── dates.json             # 可用日期索引
  └── 2026-03-29.json        # 按日期拆分的单日文件
"""
import os
import json
from datetime import datetime
from typing import Dict, List
from loguru import logger

from .config import config


class JsonWriter:
    """JSON 数据输出器（配合 Web 前端使用）"""

    def __init__(self):
        self._data_dir = os.path.join(config.project_root, "data")
        os.makedirs(self._data_dir, exist_ok=True)

    def save(self, articles: List[Dict], run_label: str = "") -> str:
        """
        将资讯保存为 JSON 文件

        Args:
            articles: 过滤后的资讯列表
            run_label: 运行标签

        Returns:
            JSON 文件路径
        """
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not run_label:
            try:
                import pytz
                tz = pytz.timezone("Asia/Shanghai")
                hour = datetime.now(tz).hour
            except Exception:
                hour = datetime.now().hour
            run_label = "早报" if hour < 14 else "晚报"

        # --- 1. 保存当日文件 ---
        daily_path = os.path.join(self._data_dir, f"{today}.json")
        daily_data = self._load_json(daily_path, {"date": today, "runs": []})

        # 添加本次运行记录
        run_record = {
            "label": run_label,
            "time": now,
            "count": len(articles),
            "articles": articles,
        }
        daily_data["runs"].append(run_record)
        self._save_json(daily_path, daily_data)

        # --- 2. 更新全量 articles.json ---
        all_path = os.path.join(self._data_dir, "articles.json")
        all_data = self._load_json(all_path, [])

        # 合并并去重（基于 url）
        existing_urls = {a["url"] for a in all_data if a.get("url")}
        for art in articles:
            if art.get("url") and art["url"] not in existing_urls:
                art_copy = dict(art)
                art_copy["fetch_date"] = today
                art_copy["fetch_label"] = run_label
                all_data.append(art_copy)
                existing_urls.add(art["url"])

        # 按时间倒序排列
        all_data.sort(key=lambda a: a.get("published_at", ""), reverse=True)

        # 只保留最近 30 天的数据（防止文件过大）
        max_articles = 3000
        if len(all_data) > max_articles:
            all_data = all_data[:max_articles]

        self._save_json(all_path, all_data)

        # --- 3. 更新日期索引 ---
        dates_path = os.path.join(self._data_dir, "dates.json")
        dates_data = self._load_json(dates_path, [])

        if today not in dates_data:
            dates_data.append(today)
            dates_data.sort(reverse=True)
        self._save_json(dates_path, dates_data)

        logger.info(f"📦 JSON 数据已保存: {daily_path}")
        return daily_path

    @staticmethod
    def _load_json(path: str, default):
        """安全加载 JSON"""
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    @staticmethod
    def _save_json(path: str, data):
        """安全保存 JSON"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
