"""
Web 服务器
==========
基于 FastAPI 的 Web 服务，提供资讯展示页面和 JSON API 接口。

API 端点：
  GET /                   — 前端页面
  GET /api/articles       — 获取资讯列表（支持搜索、筛选、分页）
  GET /api/dates          — 获取可用日期列表
  GET /api/sources        — 获取所有来源列表
  GET /api/tags           — 获取所有标签列表
  GET /api/stats          — 获取统计信息
"""
import os
import json
from datetime import datetime
from typing import Optional
from loguru import logger

from .config import config

try:
    from fastapi import FastAPI, Query
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
except ImportError:
    FastAPI = None


def create_app() -> "FastAPI":
    """创建 FastAPI 应用"""
    if FastAPI is None:
        raise ImportError("请安装 FastAPI: pip install fastapi uvicorn")

    app = FastAPI(
        title="AI 简讯 Daily",
        description="每日 AI 行业资讯聚合展示",
        version="1.0.0",
    )

    data_dir = os.path.join(config.project_root, "data")

    # ------------------------------------------------------------------
    #  辅助函数
    # ------------------------------------------------------------------

    def _load_json(filename: str, default=None):
        """从 data/ 目录加载 JSON"""
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            return default if default is not None else []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default if default is not None else []

    def _get_all_articles():
        """获取全量文章列表"""
        return _load_json("articles.json", [])

    # ------------------------------------------------------------------
    #  API 端点
    # ------------------------------------------------------------------

    @app.get("/api/articles")
    async def get_articles(
        q: Optional[str] = Query(None, description="搜索关键词"),
        date: Optional[str] = Query(None, description="日期筛选 YYYY-MM-DD"),
        source: Optional[str] = Query(None, description="来源筛选"),
        tag: Optional[str] = Query(None, description="标签筛选"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ):
        """获取资讯列表（支持搜索、筛选、分页）"""
        articles = _get_all_articles()

        # 日期筛选
        if date:
            articles = [
                a for a in articles
                if a.get("published_at", "").startswith(date)
                or a.get("fetch_date", "") == date
            ]

        # 来源筛选
        if source:
            articles = [
                a for a in articles
                if a.get("source", "").lower() == source.lower()
            ]

        # 标签筛选
        if tag:
            tag_lower = tag.lower()
            articles = [
                a for a in articles
                if any(t.lower() == tag_lower for t in a.get("tags", []))
            ]

        # 搜索
        if q:
            q_lower = q.lower()
            articles = [
                a for a in articles
                if q_lower in a.get("title", "").lower()
                or q_lower in a.get("summary", "").lower()
                or q_lower in a.get("source", "").lower()
                or any(q_lower in t.lower() for t in a.get("tags", []))
            ]

        total = len(articles)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size else 1,
            "articles": articles[start:end],
        }

    @app.get("/api/dates")
    async def get_dates():
        """获取所有可用日期"""
        dates = _load_json("dates.json", [])
        return {"dates": dates}

    @app.get("/api/sources")
    async def get_sources():
        """获取所有来源列表"""
        articles = _get_all_articles()
        sources = sorted(set(a.get("source", "") for a in articles if a.get("source")))
        return {"sources": sources}

    @app.get("/api/tags")
    async def get_tags():
        """获取所有标签列表"""
        articles = _get_all_articles()
        tags = set()
        for a in articles:
            for t in a.get("tags", []):
                if t:
                    tags.add(t)
        return {"tags": sorted(tags)}

    @app.get("/api/stats")
    async def get_stats():
        """获取统计信息"""
        articles = _get_all_articles()
        dates = _load_json("dates.json", [])
        sources = set(a.get("source", "") for a in articles if a.get("source"))

        return {
            "total_articles": len(articles),
            "total_dates": len(dates),
            "total_sources": len(sources),
            "latest_date": dates[0] if dates else None,
            "sources": sorted(sources),
        }

    # ------------------------------------------------------------------
    #  前端页面
    # ------------------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """主页面"""
        html_path = os.path.join(config.project_root, "web", "index.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>AI 简讯 Daily</h1><p>前端页面未找到，请确认 web/index.html 存在。</p>"

    return app


def start_web(host: str = "0.0.0.0", port: int = 8080):
    """启动 Web 服务器"""
    import uvicorn

    config.load()
    app = create_app()
    logger.info(f"🌐 Web 服务启动: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
