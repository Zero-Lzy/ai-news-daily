"""
静态页面生成器
==============
将 data/articles.json 内嵌到 HTML 模板中，生成不依赖后端的纯静态页面。
用于 GitHub Pages 部署，每次抓取后自动重新生成。

输出：docs/index.html （GitHub Pages 默认读取 docs/ 目录）
"""
import os
import json
from datetime import datetime
from loguru import logger

from .config import config


class StaticBuilder:
    """静态站点生成器"""

    def __init__(self):
        self._data_dir = os.path.join(config.project_root, "data")
        self._docs_dir = os.path.join(config.project_root, "docs")
        os.makedirs(self._docs_dir, exist_ok=True)

    def build(self) -> str:
        """
        读取 JSON 数据，生成纯静态 HTML 页面

        Returns:
            输出文件路径
        """
        articles = self._load_json("articles.json", [])
        dates = self._load_json("dates.json", [])

        # 提取来源和标签
        sources = sorted(set(a.get("source", "") for a in articles if a.get("source")))
        tags = set()
        for a in articles:
            for t in a.get("tags", []):
                if t:
                    tags.add(t)
        tags = sorted(tags)

        # 统计
        stats = {
            "total_articles": len(articles),
            "total_dates": len(dates),
            "total_sources": len(sources),
            "latest_date": dates[0] if dates else None,
        }

        # 生成 HTML
        html = self._render(articles, sources, tags[:50], stats)

        out_path = os.path.join(self._docs_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"🌐 静态页面已生成: {out_path} ({len(articles)} 条资讯)")
        return out_path

    def _load_json(self, filename, default):
        path = os.path.join(self._data_dir, filename)
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _render(self, articles, sources, tags, stats):
        """生成完整的自包含 HTML"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        articles_json = json.dumps(articles, ensure_ascii=False)
        sources_json = json.dumps(sources, ensure_ascii=False)
        tags_json = json.dumps(tags, ensure_ascii=False)
        stats_json = json.dumps(stats, ensure_ascii=False)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 简讯 Daily — 每日 AI 行业资讯</title>
<meta name="description" content="每日自动抓取 AI 行业最新资讯，覆盖中英文 AI 媒体">
<style>
:root {{
  --bg-primary: #0f1117;
  --bg-secondary: #1a1d2e;
  --bg-card: #222640;
  --bg-card-hover: #2a2f4a;
  --bg-input: #181b2a;
  --text-primary: #e8eaf0;
  --text-secondary: #9ca3b8;
  --text-muted: #6b7290;
  --accent: #6c8cff;
  --accent-light: #8aa4ff;
  --accent-dim: rgba(108, 140, 255, 0.15);
  --border: #2d3150;
  --border-light: #3a3f5c;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.2);
  --transition: 0.2s ease;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  min-height: 100vh;
}}
a {{ color: var(--accent); text-decoration: none; transition: color var(--transition); }}
a:hover {{ color: var(--accent-light); }}
.app-container {{ max-width: 1100px; margin: 0 auto; padding: 0 20px; }}
.app-header {{ padding: 32px 0 24px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }}
.app-header h1 {{
  font-size: 28px; font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #a78bfa);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  margin-bottom: 6px;
}}
.app-header p {{ color: var(--text-secondary); font-size: 14px; }}
.update-time {{ color: var(--text-muted); font-size: 12px; margin-top: 4px; }}
.stats-bar {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
.stat-chip {{
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; background: var(--bg-secondary);
  border: 1px solid var(--border); border-radius: 20px;
  font-size: 13px; color: var(--text-secondary);
}}
.stat-chip .num {{ font-weight: 600; color: var(--accent); }}
.search-section {{ margin-bottom: 24px; }}
.search-box {{ position: relative; margin-bottom: 16px; }}
.search-box input {{
  width: 100%; padding: 14px 20px 14px 48px;
  background: var(--bg-input); border: 1px solid var(--border);
  border-radius: var(--radius); color: var(--text-primary);
  font-size: 15px; outline: none;
  transition: border-color var(--transition), box-shadow var(--transition);
}}
.search-box input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-dim); }}
.search-box input::placeholder {{ color: var(--text-muted); }}
.search-box .search-icon {{
  position: absolute; left: 16px; top: 50%; transform: translateY(-50%);
  color: var(--text-muted); font-size: 18px;
}}
.filters-row {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
.filter-select {{
  padding: 8px 32px 8px 12px; background: var(--bg-input);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 13px; outline: none; cursor: pointer;
  appearance: none; min-width: 140px; transition: border-color var(--transition);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M3 4.5L6 7.5L9 4.5' stroke='%239ca3b8' stroke-width='1.5' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center;
}}
.filter-select:focus {{ border-color: var(--accent); }}
.filter-select option {{ background: var(--bg-secondary); }}
.date-input {{
  padding: 8px 12px; background: var(--bg-input);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 13px; outline: none; cursor: pointer;
  transition: border-color var(--transition);
}}
.date-input:focus {{ border-color: var(--accent); }}
.date-input::-webkit-calendar-picker-indicator {{ filter: invert(0.7); }}
.btn-clear {{
  padding: 8px 16px; background: transparent;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  color: var(--text-secondary); font-size: 13px; cursor: pointer;
  transition: all var(--transition);
}}
.btn-clear:hover {{ border-color: var(--accent); color: var(--accent); }}
.articles-header {{
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
}}
.articles-header h2 {{ font-size: 16px; font-weight: 600; color: var(--text-secondary); }}
.articles-count {{ font-size: 13px; color: var(--text-muted); }}
.articles-list {{ display: flex; flex-direction: column; gap: 12px; margin-bottom: 32px; }}
.article-card {{
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px;
  transition: all var(--transition); cursor: pointer;
}}
.article-card:hover {{
  background: var(--bg-card-hover); border-color: var(--border-light);
  box-shadow: var(--shadow-sm); transform: translateY(-1px);
}}
.article-card .card-title {{
  font-size: 16px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 8px; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5;
}}
.article-card .card-title a {{ color: inherit; }}
.article-card .card-title a:hover {{ color: var(--accent); }}
.article-card .card-meta {{
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
  margin-bottom: 10px; font-size: 12px; color: var(--text-muted);
}}
.card-meta .meta-item {{ display: flex; align-items: center; gap: 4px; }}
.card-meta .source-badge {{
  padding: 2px 8px; background: var(--accent-dim);
  color: var(--accent); border-radius: 4px; font-weight: 500;
}}
.article-card .card-summary {{
  font-size: 14px; color: var(--text-secondary); line-height: 1.7;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}}
.article-card .card-tags {{ margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px; }}
.card-tags .tag {{
  padding: 2px 8px; background: rgba(167, 139, 250, 0.1);
  color: #a78bfa; border-radius: 4px; font-size: 11px;
}}
.pagination {{
  display: flex; justify-content: center; align-items: center;
  gap: 8px; padding: 24px 0 48px;
}}
.page-btn {{
  padding: 8px 14px; background: var(--bg-secondary);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  color: var(--text-secondary); font-size: 13px; cursor: pointer;
  transition: all var(--transition);
}}
.page-btn:hover:not(:disabled) {{ border-color: var(--accent); color: var(--accent); }}
.page-btn.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
.page-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
.empty-state {{ text-align: center; padding: 60px 20px; color: var(--text-muted); }}
.empty-state .empty-icon {{ font-size: 48px; margin-bottom: 16px; opacity: 0.5; }}
.empty-state h3 {{ font-size: 18px; color: var(--text-secondary); margin-bottom: 8px; }}
.empty-state p {{ font-size: 14px; }}
.app-footer {{
  text-align: center; padding: 24px 0;
  border-top: 1px solid var(--border); color: var(--text-muted); font-size: 12px;
}}
@media (max-width: 768px) {{
  .app-header {{ padding: 20px 0 16px; }}
  .app-header h1 {{ font-size: 22px; }}
  .stats-bar {{ gap: 8px; }}
  .stat-chip {{ padding: 6px 12px; font-size: 12px; }}
  .filters-row {{ gap: 8px; }}
  .filter-select, .date-input {{ min-width: 0; flex: 1; font-size: 12px; }}
  .article-card {{ padding: 16px; }}
  .article-card .card-title {{ font-size: 15px; }}
  .article-card .card-summary {{ -webkit-line-clamp: 2; }}
}}
@media (max-width: 480px) {{
  .app-container {{ padding: 0 12px; }}
  .search-box input {{ padding: 12px 16px 12px 42px; font-size: 14px; }}
  .filters-row {{ flex-direction: column; }}
  .filter-select, .date-input {{ width: 100%; }}
  .stats-bar {{ overflow-x: auto; flex-wrap: nowrap; }}
  .stat-chip {{ white-space: nowrap; flex-shrink: 0; }}
}}
</style>
</head>
<body>
<div class="app-container">
  <header class="app-header">
    <h1>🤖 AI 简讯 Daily</h1>
    <p>每日 AI 行业资讯聚合 · 自动抓取 · 智能过滤</p>
    <div class="update-time">📅 数据更新于 {now}</div>
  </header>
  <div class="stats-bar">
    <div class="stat-chip">📰 资讯 <span class="num" id="statArticles">-</span> 条</div>
    <div class="stat-chip">📅 覆盖 <span class="num" id="statDates">-</span> 天</div>
    <div class="stat-chip">📡 来源 <span class="num" id="statSources">-</span> 个</div>
    <div class="stat-chip">🕐 最新 <span class="num" id="statLatest">-</span></div>
  </div>
  <section class="search-section">
    <div class="search-box">
      <span class="search-icon">🔍</span>
      <input type="text" id="searchInput" placeholder="搜索资讯标题、摘要、来源..." autocomplete="off">
    </div>
    <div class="filters-row">
      <input type="date" class="date-input" id="dateFilter" title="按日期筛选">
      <select class="filter-select" id="sourceFilter"><option value="">全部来源</option></select>
      <select class="filter-select" id="tagFilter"><option value="">全部标签</option></select>
      <button class="btn-clear" id="clearBtn">清除筛选</button>
    </div>
  </section>
  <div class="articles-header">
    <h2>📰 资讯列表</h2>
    <span class="articles-count" id="articlesCount"></span>
  </div>
  <div class="articles-list" id="articlesList"></div>
  <div class="pagination" id="pagination"></div>
  <footer class="app-footer">
    AI 简讯 Daily · 数据每日自动更新 · Powered by AI News Daily
  </footer>
</div>
<script>
// === 内嵌数据（由构建脚本自动生成，无需后端 API） ===
const ALL_ARTICLES = {articles_json};
const ALL_SOURCES = {sources_json};
const ALL_TAGS = {tags_json};
const STATS = {stats_json};

// === State ===
const state = {{ page: 1, pageSize: 20, query: '', date: '', source: '', tag: '' }};
const $ = s => document.querySelector(s);

// === Init ===
$('#statArticles').textContent = STATS.total_articles || 0;
$('#statDates').textContent = STATS.total_dates || 0;
$('#statSources').textContent = STATS.total_sources || 0;
$('#statLatest').textContent = STATS.latest_date || '-';
ALL_SOURCES.forEach(s => {{ const o = document.createElement('option'); o.value = s; o.textContent = s; $('#sourceFilter').appendChild(o); }});
ALL_TAGS.forEach(t => {{ const o = document.createElement('option'); o.value = t; o.textContent = t; $('#tagFilter').appendChild(o); }});

function getFiltered() {{
  let arts = ALL_ARTICLES;
  if (state.date) arts = arts.filter(a => (a.published_at||'').startsWith(state.date) || (a.fetch_date||'') === state.date);
  if (state.source) arts = arts.filter(a => (a.source||'').toLowerCase() === state.source.toLowerCase());
  if (state.tag) {{ const tl = state.tag.toLowerCase(); arts = arts.filter(a => (a.tags||[]).some(t => t.toLowerCase() === tl)); }}
  if (state.query) {{
    const q = state.query.toLowerCase();
    arts = arts.filter(a => (a.title||'').toLowerCase().includes(q) || (a.summary||'').toLowerCase().includes(q) || (a.source||'').toLowerCase().includes(q));
  }}
  return arts;
}}

function render() {{
  const filtered = getFiltered();
  const total = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;
  const start = (state.page - 1) * state.pageSize;
  const page = filtered.slice(start, start + state.pageSize);
  $('#articlesCount').textContent = '共 ' + total + ' 条';

  if (page.length === 0) {{
    $('#articlesList').innerHTML = '<div class="empty-state"><div class="empty-icon">📭</div><h3>暂无资讯</h3><p>' +
      (state.query || state.date || state.source || state.tag ? '未找到匹配的资讯，试试调整筛选条件' : '还没有抓取到资讯数据') + '</p></div>';
    $('#pagination').innerHTML = '';
    return;
  }}

  $('#articlesList').innerHTML = page.map(a => {{
    const t = esc(a.title||'无标题'), u = a.url||'#', s = esc(a.source||'未知'), sm = esc(trunc(a.summary||'',200)), p = a.published_at||'';
    const tgs = (a.tags||[]).slice(0,4);
    return '<div class="article-card" onclick="if(event.target.tagName!==\\'A\\')window.open(\\''+escA(u)+'\\',\\'_blank\\')">' +
      '<div class="card-title"><a href="'+escA(u)+'" target="_blank" rel="noopener">'+t+'</a></div>' +
      '<div class="card-meta"><span class="meta-item"><span class="source-badge">'+s+'</span></span>' +
      (p ? '<span class="meta-item">🕐 '+esc(p)+'</span>' : '') + '</div>' +
      (sm ? '<div class="card-summary">'+sm+'</div>' : '') +
      (tgs.length ? '<div class="card-tags">'+tgs.map(x=>'<span class="tag">'+esc(x)+'</span>').join('')+'</div>' : '') +
      '</div>';
  }}).join('');

  // Pagination
  if (totalPages <= 1) {{ $('#pagination').innerHTML = ''; return; }}
  let h = '<button class="page-btn" '+(state.page<=1?'disabled ':'')+' onclick="goPage('+(state.page-1)+')">‹ 上一页</button>';
  let s2 = Math.max(1, state.page-2), e2 = Math.min(totalPages, s2+4);
  s2 = Math.max(1, e2-4);
  if (s2 > 1) {{ h += '<button class="page-btn" onclick="goPage(1)">1</button>'; if (s2>2) h += '<span style="color:var(--text-muted)">…</span>'; }}
  for (let i=s2;i<=e2;i++) h += '<button class="page-btn '+(i===state.page?'active':'')+'" onclick="goPage('+i+')">'+i+'</button>';
  if (e2 < totalPages) {{ if (e2<totalPages-1) h += '<span style="color:var(--text-muted)">…</span>'; h += '<button class="page-btn" onclick="goPage('+totalPages+')">'+totalPages+'</button>'; }}
  h += '<button class="page-btn" '+(state.page>=totalPages?'disabled ':'')+' onclick="goPage('+(state.page+1)+')">下一页 ›</button>';
  $('#pagination').innerHTML = h;
}}

function goPage(p) {{ state.page = p; render(); window.scrollTo({{top:0,behavior:'smooth'}}); }}
function esc(s) {{ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }}
function escA(s) {{ return s.replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }}
function trunc(s,m) {{ return s.length>m ? s.slice(0,m)+'...' : s; }}

let timer;
$('#searchInput').addEventListener('input', () => {{ clearTimeout(timer); timer = setTimeout(() => {{ state.query=$('#searchInput').value.trim(); state.page=1; render(); }}, 300); }});
$('#dateFilter').addEventListener('change', () => {{ state.date=$('#dateFilter').value; state.page=1; render(); }});
$('#sourceFilter').addEventListener('change', () => {{ state.source=$('#sourceFilter').value; state.page=1; render(); }});
$('#tagFilter').addEventListener('change', () => {{ state.tag=$('#tagFilter').value; state.page=1; render(); }});
$('#clearBtn').addEventListener('click', () => {{
  $('#searchInput').value=''; $('#dateFilter').value=''; $('#sourceFilter').value=''; $('#tagFilter').value='';
  state.query=''; state.date=''; state.source=''; state.tag=''; state.page=1; render();
}});
render();
</script>
</body>
</html>'''
