"""
Markdown 格式化与文件保存
=========================
将过滤后的资讯列表渲染为结构化 Markdown 文件并保存到磁盘。

输出文件结构示例：
  # 🤖 AI 行业简讯 — 2026-03-29

  > 📅 生成时间：2026-03-29 08:00 | 共收录 42 条资讯

  ## 📰 资讯列表

  ### 1. OpenAI 发布 GPT-5 预览版
  - 🔗 来源：机器之心 | ⏰ 2026-03-29 07:30
  - 📝 OpenAI 今日宣布 GPT-5 预览版上线...

  ---
  ### 2. ...
"""
import os
from datetime import datetime
from typing import Dict, List
from loguru import logger

from .config import config


class MarkdownWriter:
    """
    Markdown 文件生成器

    Methods:
        save(articles) -> str: 保存资讯到 .md 文件，返回文件路径
    """

    def __init__(self):
        out_cfg = config.get_section("output")
        self._output_dir = out_cfg.get("dir", "./output")
        self._filename_fmt = out_cfg.get("filename_format", "AI简讯_{date}.md")
        self._append = out_cfg.get("append_if_exists", True)

    def save(self, articles: List[Dict], run_label: str = "") -> str:
        """
        将资讯列表保存为 Markdown 文件

        Args:
            articles: 过滤后的资讯列表
            run_label: 运行标签（如 "早报"/"晚报"），为空时自动判断

        Returns:
            保存的文件绝对路径
        """
        # 确保输出目录存在
        abs_dir = os.path.join(config.project_root, self._output_dir)
        os.makedirs(abs_dir, exist_ok=True)

        # 生成文件名
        today = datetime.now().strftime("%Y-%m-%d")
        filename = self._filename_fmt.replace("{date}", today)
        filepath = os.path.join(abs_dir, filename)

        # 自动判断标签（优先使用北京时间）
        if not run_label:
            try:
                import pytz
                tz = pytz.timezone("Asia/Shanghai")
                hour = datetime.now(tz).hour
            except Exception:
                hour = datetime.now().hour
            run_label = "早报" if hour < 14 else "晚报"

        # 生成 Markdown 内容
        md_content = self._render(articles, today, run_label)

        # 写入文件
        if os.path.exists(filepath) and self._append:
            # 追加模式：加分隔线后追加
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(f"\n\n---\n\n")
                f.write(md_content)
            logger.info(f"追加写入: {filepath}")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info(f"新建写入: {filepath}")

        logger.info(f"✅ 已保存 {len(articles)} 条资讯 → {filepath}")
        return filepath

    def _render(self, articles: List[Dict], date_str: str, label: str) -> str:
        """渲染 Markdown 内容"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 检测文章是否包含 AI 分析数据
        has_ai = any(art.get("ai_score") is not None for art in articles)

        lines = []

        # 标题（仅新建时）
        if not self._append or not os.path.exists(
            os.path.join(config.project_root, self._output_dir,
                         self._filename_fmt.replace("{date}", date_str))
        ):
            lines.append(f"# 🤖 AI 行业简讯 — {date_str}\n")

        # 小节标题
        ai_badge = " | 🧠 AI 智能排序" if has_ai else ""
        lines.append(f"## 📡 {label}（{now}{ai_badge}）\n")
        lines.append(f"> 共收录 **{len(articles)}** 条资讯\n")

        if not articles:
            lines.append("\n暂无符合条件的资讯。\n")
            return "\n".join(lines)

        # 渲染文章列表（AI 排序后已按分数排列，不再按来源分组）
        if has_ai:
            lines.append("")
            for idx, art in enumerate(articles, 1):
                title = art.get("title", "无标题")
                url = art.get("url", "")
                summary = art.get("ai_summary") or art.get("summary", "")
                pub_at = art.get("published_at", "")
                tags = art.get("tags", [])
                ai_score = art.get("ai_score")
                ai_category = art.get("ai_category", "")
                source = art.get("source", "")

                # 标题行（含排名序号和分数）
                score_badge = f" `⭐{ai_score:.1f}`" if ai_score is not None else ""
                if url:
                    lines.append(f"### {idx}. [{title}]({url}){score_badge}\n")
                else:
                    lines.append(f"### {idx}. {title}{score_badge}\n")

                # 元信息行
                meta_parts = []
                if source:
                    meta_parts.append(f"📡 {source}")
                if pub_at:
                    meta_parts.append(f"⏰ {pub_at}")
                if ai_category:
                    meta_parts.append(f"📂 {ai_category}")
                if tags:
                    meta_parts.append(f"🏷️ {', '.join(tags[:5])}")
                if meta_parts:
                    lines.append(f"- {' | '.join(meta_parts)}\n")

                # AI 摘要 / 原始摘要
                if summary:
                    if len(summary) > 300:
                        summary = summary[:300] + "..."
                    lines.append(f"- {summary}\n")

                lines.append("")  # 空行分隔
        else:
            # 无 AI 分析时保留原按来源分组的逻辑
            source_groups: Dict[str, List[Dict]] = {}
            for art in articles:
                src = art.get("source", "其他")
                if src not in source_groups:
                    source_groups[src] = []
                source_groups[src].append(art)

            idx = 1
            for source_name, group in source_groups.items():
                lines.append(f"\n### 📂 {source_name}（{len(group)} 条）\n")

                for art in group:
                    title = art.get("title", "无标题")
                    url = art.get("url", "")
                    summary = art.get("summary", "")
                    pub_at = art.get("published_at", "")
                    tags = art.get("tags", [])

                    if url:
                        lines.append(f"**{idx}. [{title}]({url})**\n")
                    else:
                        lines.append(f"**{idx}. {title}**\n")

                    meta_parts = []
                    if pub_at:
                        meta_parts.append(f"⏰ {pub_at}")
                    if tags:
                        meta_parts.append(f"🏷️ {', '.join(tags[:5])}")
                    if meta_parts:
                        lines.append(f"- {' | '.join(meta_parts)}\n")

                    if summary:
                        if len(summary) > 300:
                            summary = summary[:300] + "..."
                        lines.append(f"- {summary}\n")

                    lines.append("")
                    idx += 1

        # 页脚
        lines.append("---\n")
        lines.append(f"*由 AI News Daily 自动生成 | {now}*\n")

        return "\n".join(lines)
