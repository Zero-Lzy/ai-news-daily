"""
内容过滤器
==========
对抓取到的原始资讯进行过滤和排序。

过滤规则（依次执行）：
  1. 关键词包含过滤 — 标题/摘要中必须包含至少一个 AI 相关关键词
  2. 关键词排除过滤 — 标题/摘要中不得包含任何排除关键词
  3. 时效性过滤     — 超过 max_age_hours 的旧闻自动丢弃
  4. 去重过滤       — 标题相似度 > 80% 视为重复

排序规则：
  - 按发布时间倒序（最新排前）
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger

from .config import config


class Filter:
    """资讯过滤器"""

    def __init__(self):
        flt = config.get_section("filter")
        self._include = [kw.lower() for kw in flt.get("keywords_include", [])]
        self._exclude = [kw.lower() for kw in flt.get("keywords_exclude", [])]
        self._max_age_hours = flt.get("max_age_hours", 48)
        self._deduplicate = flt.get("deduplicate", True)

    def apply(self, articles: List[Dict]) -> List[Dict]:
        """
        执行全部过滤流程

        Args:
            articles: 原始资讯列表

        Returns:
            过滤并排序后的资讯列表
        """
        before = len(articles)

        # 1. 关键词包含
        articles = [a for a in articles if self._match_include(a)]

        # 2. 关键词排除
        articles = [a for a in articles if not self._match_exclude(a)]

        # 3. 时效性
        articles = [a for a in articles if self._is_recent(a)]

        # 4. 标题去重
        if self._deduplicate:
            articles = self._dedup_by_title(articles)

        # 5. 按时间倒序
        articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)

        after = len(articles)
        logger.info(f"过滤完成: {before} → {after} 条（过滤 {before - after} 条）")
        return articles

    def _match_include(self, article: Dict) -> bool:
        """检查是否包含至少一个目标关键词"""
        if not self._include:
            return True  # 未配置包含词则全部通过
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        return any(kw in text for kw in self._include)

    def _match_exclude(self, article: Dict) -> bool:
        """检查是否包含排除关键词"""
        if not self._exclude:
            return False
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        return any(kw in text for kw in self._exclude)

    def _is_recent(self, article: Dict) -> bool:
        """检查时效性"""
        pub = article.get("published_at", "")
        if not pub:
            return True  # 无时间信息的保留
        try:
            from dateutil import parser as dp
            pub_dt = dp.parse(pub)
            # 移除时区信息进行比较
            if pub_dt.tzinfo:
                pub_dt = pub_dt.replace(tzinfo=None)
            cutoff = datetime.now() - timedelta(hours=self._max_age_hours)
            return pub_dt >= cutoff
        except Exception:
            return True

    @staticmethod
    def _dedup_by_title(articles: List[Dict]) -> List[Dict]:
        """基于标题的模糊去重"""
        seen_titles = []
        unique = []

        for art in articles:
            title = art.get("title", "").strip()
            # 归一化：去除标点、空格
            normalized = re.sub(r"[\s\W]+", "", title).lower()

            is_dup = False
            for seen in seen_titles:
                # 简单的包含关系去重
                if len(normalized) > 5 and len(seen) > 5:
                    shorter = min(normalized, seen, key=len)
                    longer = max(normalized, seen, key=len)
                    if shorter in longer:
                        is_dup = True
                        break
                    # Jaccard 字符级相似度
                    set_a = set(normalized)
                    set_b = set(seen)
                    intersection = len(set_a & set_b)
                    union = len(set_a | set_b)
                    if union > 0 and intersection / union > 0.8:
                        is_dup = True
                        break

            if not is_dup:
                seen_titles.append(normalized)
                unique.append(art)

        return unique
