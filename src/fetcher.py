"""
数据抓取引擎
============
从多个数据源并发获取AI行业资讯。

支持的数据源类型：
  1. RSS订阅源 — 通过 feedparser 解析标准 RSS/Atom
  2. 网页抓取   — 通过 BeautifulSoup 解析目标页面
  3. Hacker News API — 直接请求 Firebase API

每条资讯统一输出为字典格式：
  {
      "title":        标题 (str),
      "url":          原文链接 (str),
      "source":       来源名称 (str),
      "summary":      摘要/正文片段 (str),
      "published_at": 发布时间 (str, ISO格式),
      "tags":         标签列表 (list[str]),
  }
"""
import asyncio
import hashlib
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin

import httpx
from loguru import logger

from .config import config


class Fetcher:
    """
    资讯抓取引擎

    Methods:
        fetch_all()  -> List[Dict]: 从所有已启用数据源并发抓取
        fetch_rss()  -> List[Dict]: 抓取单个RSS源
        fetch_web()  -> List[Dict]: 抓取单个网页
    """

    def __init__(self):
        src_cfg = config.get_section("sources")
        self._timeout = src_cfg.get("request_timeout", 30)
        self._max_per_source = src_cfg.get("max_articles_per_source", 30)
        self._user_agent = src_cfg.get("user_agent", "Mozilla/5.0")
        self._seen_urls: set = set()  # URL 去重

    # ------------------------------------------------------------------
    #  公共接口
    # ------------------------------------------------------------------

    async def fetch_all(self) -> List[Dict]:
        """
        从所有已启用数据源并发抓取

        Returns:
            去重后的资讯列表
        """
        src_cfg = config.get_section("sources")
        tasks = []

        # RSS 源
        for feed in src_cfg.get("rss_feeds", []):
            if feed.get("enabled", True):
                tasks.append(self._safe_fetch_rss(feed))

        # 网页抓取
        for target in src_cfg.get("web_scrape", []):
            if target.get("enabled", True):
                tasks.append(self._safe_fetch_web(target))

        # 并发执行
        results = await asyncio.gather(*tasks)

        # 合并并去重
        all_articles = []
        for batch in results:
            all_articles.extend(batch)

        unique = self._deduplicate(all_articles)
        logger.info(f"抓取完成: 原始 {len(all_articles)} 条 → 去重后 {len(unique)} 条")
        return unique

    # ------------------------------------------------------------------
    #  RSS 抓取
    # ------------------------------------------------------------------

    async def _safe_fetch_rss(self, feed_cfg: Dict) -> List[Dict]:
        """带错误保护的 RSS 抓取"""
        name = feed_cfg.get("name", feed_cfg.get("url", ""))
        try:
            return await self._fetch_rss(feed_cfg)
        except Exception as e:
            logger.error(f"[RSS] {name} 抓取失败: {e}")
            return []

    async def _fetch_rss(self, feed_cfg: Dict) -> List[Dict]:
        """抓取单个 RSS 源"""
        import feedparser

        url = feed_cfg["url"]
        name = feed_cfg.get("name", url)

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": self._user_agent})
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        articles = []

        for entry in feed.entries[: self._max_per_source]:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue

            summary = self._clean_html(
                entry.get("summary") or entry.get("description") or ""
            )
            published = self._parse_date(entry.get("published") or entry.get("updated") or "")
            tags = [t.get("term", "") for t in entry.get("tags", []) if t.get("term")]

            articles.append({
                "title": title,
                "url": link,
                "source": name,
                "summary": summary[:500],
                "published_at": published,
                "tags": tags,
            })

        logger.info(f"[RSS] {name}: 获取 {len(articles)} 条")
        return articles

    # ------------------------------------------------------------------
    #  网页抓取
    # ------------------------------------------------------------------

    async def _safe_fetch_web(self, target: Dict) -> List[Dict]:
        """带错误保护的网页抓取"""
        name = target.get("name", target.get("url", ""))
        try:
            return await self._fetch_web(target)
        except Exception as e:
            logger.error(f"[Web] {name} 抓取失败: {e}")
            return []

    async def _fetch_web(self, target: Dict) -> List[Dict]:
        """抓取单个网页"""
        from bs4 import BeautifulSoup

        url = target["url"]
        name = target.get("name", url)
        selector = target.get("selector", "article")

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": self._user_agent})
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        articles = []

        for el in soup.select(selector)[: self._max_per_source]:
            title_tag = el.select_one("h1, h2, h3, a[href], .title, [class*=title]")
            link_tag = el.select_one("a[href]")
            desc_tag = el.select_one("p, .desc, .summary, [class*=desc], [class*=summary]")

            title = title_tag.get_text(strip=True) if title_tag else ""
            link = link_tag.get("href", "") if link_tag else ""
            desc = desc_tag.get_text(strip=True) if desc_tag else ""

            if not title:
                continue
            if link and not link.startswith("http"):
                link = urljoin(url, link)

            articles.append({
                "title": title,
                "url": link,
                "source": name,
                "summary": desc[:500],
                "published_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "tags": [],
            })

        logger.info(f"[Web] {name}: 获取 {len(articles)} 条")
        return articles

    # ------------------------------------------------------------------
    #  工具方法
    # ------------------------------------------------------------------

    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """基于 URL + 标题的去重"""
        unique = []
        for art in articles:
            key = hashlib.md5(f"{art['url']}|{art['title']}".encode()).hexdigest()
            if key not in self._seen_urls:
                self._seen_urls.add(key)
                unique.append(art)
        return unique

    @staticmethod
    def _clean_html(text: str) -> str:
        """去除 HTML 标签"""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @staticmethod
    def _parse_date(date_str: str) -> str:
        """解析日期字符串为统一格式"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            from dateutil import parser as dp
            dt = dp.parse(date_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return date_str
