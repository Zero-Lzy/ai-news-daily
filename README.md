# 🤖 AI 简讯自动抓取系统

每天自动获取 AI 行业最新资讯，生成结构化 Markdown 文件，支持 **GitHub 云端自动运行**、**本地定时运行** 和 **Web 页面浏览** 三种使用方式。

---

## ✨ 功能概览

| 功能 | 说明 |
|------|------|
| ⏰ **定时抓取** | 默认每天早 8:00 + 晚 20:00 自动执行，时间可自定义 |
| 📡 **多源聚合** | 内置 8+ 个 RSS 源 + 网页抓取，覆盖中英文 AI 媒体 |
| 🔍 **智能过滤** | 关键词匹配、时效性检查、标题去重，只保留高相关资讯 |
| 🧠 **AI 深度分析** | 接入大模型对资讯进行智能评分、排序，精选 Top 20 优质内容 |
| 📝 **Markdown 输出** | 结构化排版、AI 评分标注、按重要性排序 |
| 🌐 **Web 展示页面** | 深色主题响应式页面，支持搜索、筛选、分页浏览 |
| 🚀 **GitHub Actions** | 推送到 GitHub 即自动运行，零服务器成本 |
| 🔧 **灵活配置** | JSON 配置文件 + 环境变量覆盖，无需改代码 |

---

## 📂 项目结构

```
ai-news-daily/
├── main.py                          # 🚀 主入口
├── requirements.txt                 # 📦 Python 依赖
├── .gitignore                       # Git 忽略规则
│
├── config/
│   └── settings.json                # ⚙️ 全局配置文件
│
├── src/
│   ├── __init__.py
│   ├── config.py                    # 配置管理器
│   ├── fetcher.py                   # 数据抓取引擎
│   ├── filter.py                    # 内容过滤器
│   ├── ai_analyzer.py               # 🧠 AI 智能分析（LLM 评分排序）
│   ├── writer.py                    # Markdown 生成器
│   ├── json_writer.py               # JSON 数据输出器（Web 用）
│   ├── static_builder.py            # 静态页面生成器（GitHub Pages 用）
│   ├── web_server.py                # FastAPI Web 服务器（本地用）
│   └── scheduler.py                 # 定时调度器
│
├── web/
│   └── index.html                   # 🌐 Web 前端（本地 FastAPI 版）
│
├── docs/
│   └── index.html                   # 🌐 静态页面（GitHub Pages 自动部署）
│
├── data/                            # 📊 JSON 数据文件（自动生成）
│   ├── articles.json                #    全量文章列表
│   ├── dates.json                   #    可用日期索引
│   └── 2026-03-29.json              #    按日期拆分的文件
│
├── output/                          # 📄 生成的 Markdown 文件
│   └── AI简讯_2026-03-29.md         #    （示例）
│
├── .github/
│   └── workflows/
│       ├── fetch-news.yml           # 🤖 定时抓取工作流
│       └── deploy-pages.yml         # 🌐 GitHub Pages 部署工作流
│
└── README.md                        # 📖 本文档
```

---

## 🧩 模块功能说明

### 1. `src/config.py` — 配置管理器

| 功能 | 说明 |
|------|------|
| 加载配置 | 从 `config/settings.json` 读取 JSON 配置 |
| 环境变量覆盖 | `NEWS_` 前缀的环境变量可覆盖任何配置项 |
| 默认值回退 | 配置文件缺失时使用内置默认值，不会崩溃 |
| 路径访问 | 支持 `config.get("schedule.morning_hour")` 点号路径 |

**环境变量覆盖示例：**
```bash
# 将早报时间改为 9:00
export NEWS_SCHEDULE__MORNING_HOUR=9

# 将超时时间改为 60 秒
export NEWS_SOURCES__REQUEST_TIMEOUT=60
```

### 2. `src/fetcher.py` — 数据抓取引擎

| 功能 | 说明 |
|------|------|
| RSS 抓取 | 通过 feedparser 解析标准 RSS/Atom 订阅源 |
| 网页抓取 | 通过 BeautifulSoup 解析目标网页 |
| 并发执行 | 所有数据源并发请求，提高效率 |
| 自动去重 | 基于 URL + 标题的 MD5 去重 |
| 错误隔离 | 单个源失败不影响其他源 |

**内置数据源（8 个）：**
| 来源 | 语言 | 类型 |
|------|------|------|
| 机器之心 | 中文 | RSS |
| 量子位 | 中文 | RSS |
| 36氪 AI 频道 | 中文 | RSS |
| 少数派 AI | 中文 | RSS |
| Hacker News AI | 英文 | RSS |
| TechCrunch AI | 英文 | RSS |
| The Verge AI | 英文 | RSS |
| ArsTechnica | 英文 | RSS |

### 3. `src/filter.py` — 内容过滤器

依次执行 4 道过滤：

| 步骤 | 规则 | 说明 |
|------|------|------|
| ① | 关键词包含 | 标题/摘要中须含至少一个 AI 关键词 |
| ② | 关键词排除 | 标题/摘要不得含排除词（如 "广告"） |
| ③ | 时效性检查 | 超过 48 小时的旧闻自动丢弃 |
| ④ | 标题去重 | Jaccard 相似度 > 80% 视为重复 |

最后按发布时间倒序排列。

### 3.5 `src/ai_analyzer.py` — 🧠 AI 智能分析模块（🆕）

利用大模型（LLM）对过滤后的资讯进行深度分析，实现智能评分、排序和精选。

| 功能 | 说明 |
|------|------|
| LLM 评分 | 调用 OpenAI 兼容 API 对每篇资讯进行 **相关性**（0-10）+ **重要性**（0-10）评分 |
| 中文摘要 | LLM 为每篇资讯生成一句话中文摘要 |
| 智能分类 | 自动将资讯归类为"产品发布"、"技术突破"、"融资投资"等类别 |
| 复合排序 | `综合分 = 相关性 × 0.4 + 重要性 × 0.4 + 时效性 × 0.2`（权重可配置） |
| Top N 精选 | 默认输出评分最高的 **前 20 条**资讯 |
| 批量处理 | 文章分批发送给 LLM（默认每批 10 条），避免超出 Token 限制 |
| 优雅降级 | 未配置 API Key 时自动切换为**规则打分**（关键词匹配 + 来源权威度 + 时效性） |
| 容错重试 | API 调用失败自动重试，429 限流指数退避，单批失败不影响全局 |

**AI 分析流水线：**

```
过滤后文章列表
    ↓ 分批（每批 10 条）
    ↓ 构造结构化 Prompt → 调用 LLM API
    ↓ 解析 JSON 响应 → 提取评分 + 摘要 + 分类
    ↓ 计算复合分数 → 按分数降序排列
    ↓ 取 Top N（默认 20 条）
    ↓ 输出精选资讯
```

**支持的 LLM 服务商（OpenAI 兼容 API）：**

| 服务商 | base_url | 推荐模型 |
|--------|----------|----------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat`（默认） |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Kimi | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 零一万物 | `https://api.lingyiwanwu.com/v1` | `yi-large` |

### 4. `src/writer.py` — Markdown 生成器

| 功能 | 说明 |
|------|------|
| 结构化排版 | 标题、来源分组、元信息、摘要逐层展示 |
| 追加模式 | 同一天多次运行，自动追加到同一文件（早报 + 晚报） |
| 文件命名 | `AI简讯_2026-03-29.md` 格式，可在配置中修改 |

### 5. `src/json_writer.py` — JSON 数据输出器

| 功能 | 说明 |
|------|------|
| JSON 数据输出 | 每次抓取同时保存 JSON 格式，供 Web 页面读取 |
| 按日期拆分 | 每日生成独立 JSON 文件（`data/2026-03-29.json`） |
| 全量聚合 | `data/articles.json` 汇总全部文章，支持搜索筛选 |
| 日期索引 | `data/dates.json` 维护可用日期列表 |
| 自动去重 | 基于 URL 去重，防止重复写入 |

### 6. `src/web_server.py` — Web 展示服务器

基于 FastAPI 构建的 Web 服务，提供 API + 前端页面：

| API 端点 | 方法 | 说明 |
|----------|------|------|
| `/` | GET | 前端展示页面 |
| `/api/articles` | GET | 资讯列表（支持 `q` 搜索、`date` `source` `tag` 筛选、分页） |
| `/api/dates` | GET | 可用日期列表 |
| `/api/sources` | GET | 所有来源列表 |
| `/api/tags` | GET | 所有标签列表 |
| `/api/stats` | GET | 统计概览（总数、来源数、最新日期） |

### 7. `src/scheduler.py` — 定时调度器

| 模式 | 触发方式 | 适用场景 |
|------|----------|----------|
| 立即执行 | `python main.py` | 测试 / 手动运行 |
| 本地定时 | `python main.py --schedule` | 本地 7×24 运行 |
| Web 展示 | `python main.py --web` | 启动浏览器查看页面 |
| CI/CD 定时 | GitHub Actions cron | 推荐，零成本 |

### 8. `.github/workflows/fetch-news.yml` — GitHub Actions 工作流

| 触发条件 | 时间（北京时间） |
|----------|------------------|
| 自动 | 每天 08:00 + 20:00 |
| 手动 | Actions 页面点击 "Run workflow" |

执行流程：拉取代码 → 安装依赖 → 运行抓取 → AI 分析排序 → 提交结果到仓库

---

## 🚀 快速开始

### 方式一：GitHub 云端自动运行（推荐 ⭐）

> **零服务器、零费用**，推送代码到 GitHub 即可自动运行。

#### 第 1 步：创建 GitHub 仓库

1. 打开 [github.com/new](https://github.com/new)
2. 输入仓库名称，例如 `ai-news-daily`
3. 选择 **Public**（公开仓库 Actions 免费无限制）
4. 点击 **Create repository**

#### 第 2 步：推送代码到仓库

```bash
# 进入项目目录
cd ai-news-daily

# 初始化 Git 仓库
git init
git add .
git commit -m "🎉 初始化 AI 简讯抓取系统"

# 关联远程仓库（替换为你的用户名）
git remote add origin https://github.com/你的用户名/ai-news-daily.git
git branch -M main
git push -u origin main
```

#### 第 3 步：启用 GitHub Actions 权限

1. 进入仓库页面 → **Settings** → **Actions** → **General**
2. 在 "Workflow permissions" 中选择 **Read and write permissions**
3. 勾选 "Allow GitHub Actions to create and approve pull requests"
4. 点击 **Save**

#### 第 4 步：验证自动运行

1. 进入仓库 → **Actions** 标签页
2. 点击左侧 **"🤖 AI Daily News Fetch"**
3. 点击右上角 **"Run workflow"** → **"Run workflow"** 手动触发一次
4. 等待 1-2 分钟，检查是否成功
5. 回到 **Code** 页面，查看 `output/` 目录下是否生成了 `.md` 文件

> ✅ 之后每天 8:00 和 20:00（北京时间）会自动执行。

#### 第 5 步（可选）：修改执行时间

编辑 `.github/workflows/fetch-news.yml` 中的 cron 表达式：

```yaml
on:
  schedule:
    # 格式: 分 时 日 月 周  （UTC 时间！北京时间 - 8 小时）
    - cron: "0 0 * * *"     # UTC 00:00 = 北京 08:00
    - cron: "0 12 * * *"    # UTC 12:00 = 北京 20:00
```

**常用 cron 配置：**

| 北京时间 | UTC cron | 说明 |
|----------|----------|------|
| 每天 7:00 | `0 23 * * *` | UTC 前一天 23:00 |
| 每天 9:00 | `0 1 * * *` | UTC 01:00 |
| 每天 12:00 | `0 4 * * *` | UTC 04:00 |
| 每天 18:00 | `0 10 * * *` | UTC 10:00 |
| 每天 21:00 | `0 13 * * *` | UTC 13:00 |
| 工作日 9:00 | `0 1 * * 1-5` | 周一到周五 |

---

### 方式二：本地运行

#### 第 1 步：安装 Python

确保已安装 **Python 3.9+**。验证：

```bash
python --version
# 输出应为 Python 3.9.x 或更高
```

#### 第 2 步：安装依赖

```bash
cd ai-news-daily
pip install -r requirements.txt
```

#### 第 3 步：立即运行一次测试

```bash
python main.py
```

成功后会看到：
```
05:30:00 |   INFO   | 🤖 AI 简讯自动抓取系统 v1.0.0
05:30:00 |   INFO   | 🚀 开始执行资讯抓取任务 [2026-03-29 05:30:00]
05:30:05 |   INFO   | [Step 1/4] 抓取完成: 87 条原始资讯
05:30:05 |   INFO   | [Step 2/4] 过滤完成: 42 条有效资讯
05:30:05 |   INFO   | [Step 3/4] Markdown 保存完成: ./output/AI简讯_2026-03-29.md
05:30:05 |   INFO   | [Step 4/4] JSON 数据保存完成: ./data/2026-03-29.json
05:30:05 |   INFO   | ✅ 任务完成，耗时 5.3 秒，共保存 42 条资讯

📄 文件已保存: /path/to/output/AI简讯_2026-03-29.md
```

#### 第 4 步：启动定时任务（可选）

```bash
# 按配置时间（默认 8:00 + 20:00）定时运行
python main.py --schedule
```

程序会常驻运行，到时间自动执行。

---

### 方式三：Web 页面浏览（🆕）

> 通过浏览器查看资讯，支持搜索、筛选、分页，适合日常浏览。

#### 前置条件

需要先运行至少一次抓取，生成数据文件：

```bash
python main.py
```

#### 启动 Web 服务

```bash
# 默认端口 8080
python main.py --web

# 自定义端口
python main.py --web --port 3000
```

打开浏览器访问 **http://localhost:8080** 即可浏览：

| 功能 | 说明 |
|------|------|
| 🔍 搜索 | 按标题、摘要、来源关键词搜索 |
| 📅 日期筛选 | 选择特定日期查看当天资讯 |
| 📡 来源筛选 | 按数据源过滤（如只看"机器之心"） |
| 🏷️ 标签筛选 | 按标签分类查看 |
| 📄 分页浏览 | 每页 20 条，支持翻页 |
| 📱 响应式 | 桌面端和移动端均可流畅使用 |

**Web 页面截图特性：**
- 深色主题设计，长时间阅读护眼
- 统计卡片展示总文章数、来源数、覆盖天数
- 点击资讯卡片直接跳转原文

---

#### API 接口说明（供开发者）

Web 服务同时提供 JSON API：

```bash
# 获取资讯列表（支持搜索、筛选、分页）
GET /api/articles?q=GPT&date=2026-03-29&source=机器之心&page=1&page_size=20

# 获取可用日期
GET /api/dates

# 获取所有来源
GET /api/sources

# 获取所有标签
GET /api/tags

# 获取统计信息
GET /api/stats
```

---

### 方式四：GitHub Pages 在线访问（🆕 推荐）

> 无需服务器，每次抓取后自动部署更新，通过 URL 直接在线访问资讯页面。

#### 工作原理

```
抓取工作流运行 → 生成 JSON 数据 → 构建静态 HTML（数据内嵌）
    → 提交到 docs/ 目录 → 自动触发 Pages 部署 → 在线页面自动更新
```

#### 第 1 步：启用 GitHub Pages

1. 进入仓库 → **Settings**（顶部导航栏）
2. 左侧菜单找到 **Pages**（在 "Code and automation" 分类下）
3. **Source** 选择 **GitHub Actions**
4. 点击 **Save**

#### 第 2 步：运行一次抓取

手动触发抓取工作流（或等待定时触发）：

1. 进入 **Actions** 标签页
2. 左侧选择 **🤖 AI Daily News Fetch**
3. 点击 **Run workflow** → 选择 `main` → **Run workflow**
4. 等待运行完成（约 1-2 分钟）

#### 第 3 步：查看在线页面

抓取完成后，**🌐 Deploy to GitHub Pages** 工作流会自动触发部署。

部署完成后访问：

```
https://zero-lzy.github.io/ai-news-daily/
```

> 📌 每次抓取运行后页面都会自动更新，无需手动操作。

#### 查看部署状态

1. 进入 **Actions** 标签页
2. 左侧选择 **🌐 Deploy to GitHub Pages**
3. 查看最近的运行记录，绿色 ✅ 表示部署成功

---

## ⚙️ 配置说明

所有配置在 `config/settings.json` 中，以下是关键配置项：

### 执行时间

```json
{
  "schedule": {
    "morning_hour": 8,        // 早报：小时（0-23）
    "morning_minute": 0,      // 早报：分钟（0-59）
    "evening_hour": 20,       // 晚报：小时（0-23）
    "evening_minute": 0,      // 晚报：分钟（0-59）
    "timezone": "Asia/Shanghai"
  }
}
```

### 添加/删除数据源

```json
{
  "sources": {
    "rss_feeds": [
      {
        "name": "我的自定义源",
        "url": "https://example.com/rss.xml",
        "enabled": true
      }
    ]
  }
}
```

将 `enabled` 设为 `false` 即可禁用某个源，无需删除。

### 过滤关键词

```json
{
  "filter": {
    "keywords_include": ["AI", "大模型", "GPT"],
    "keywords_exclude": ["广告"],
    "max_age_hours": 48,
    "deduplicate": true
  }
}
```

### AI 智能分析（🆕）

```json
{
  "ai": {
    "api_key": "",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "top_n": 20,
    "batch_size": 10,
    "timeout": 60,
    "max_retries": 2,
    "weights": {
      "relevance": 0.4,
      "importance": 0.4,
      "recency": 0.2
    }
  }
}
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `api_key` | LLM API 密钥（留空则自动降级为规则打分） | `""` |
| `base_url` | OpenAI 兼容 API 端点 | `https://api.deepseek.com/v1` |
| `model` | 模型名称 | `deepseek-chat` |
| `top_n` | 最终输出的精选条数 | `20` |
| `batch_size` | 每批发送给 LLM 的文章数 | `10` |
| `timeout` | API 请求超时（秒） | `60` |
| `max_retries` | 失败重试次数 | `2` |
| `weights` | 复合评分权重（相关性 / 重要性 / 时效性） | `0.4 / 0.4 / 0.2` |

**配置 API Key 的两种方式：**

```bash
# 方式 1：环境变量（推荐，不会泄露到代码仓库）
export NEWS_AI_API_KEY="sk-xxxxxxxxxxxxxxxx"

# 方式 2：在 config/settings.json 中直接填写（仅本地使用）
```

**GitHub Actions 中配置 API Key：**

1. 进入仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. Name 填 `NEWS_AI_API_KEY`，Value 填你的 API Key
4. 点击 **Add secret**

> ⚠️ 未配置 API Key 时系统依然可以正常运行，会自动使用规则打分模式（基于关键词匹配 + 来源权威度 + 时效性）。

### 输出格式

```json
{
  "output": {
    "dir": "./output",
    "filename_format": "AI简讯_{date}.md",
    "append_if_exists": true
  }
}
```

- `{date}` 会被替换为当天日期（如 `2026-03-29`）
- `append_if_exists: true` — 同一天多次运行追加到同一文件

---

## 📦 依赖库说明

| 库 | 版本 | 用途 |
|----|------|------|
| `httpx` | ≥0.27.0 | 异步 HTTP 客户端，用于网络请求 + LLM API 调用 |
| `feedparser` | ≥6.0.11 | RSS/Atom 订阅源解析 |
| `beautifulsoup4` | ≥4.12.0 | HTML 页面解析（网页抓取） |
| `lxml` | ≥5.1.0 | 高性能 XML/HTML 解析后端 |
| `python-dateutil` | ≥2.8.0 | 灵活的日期时间解析 |
| `loguru` | ≥0.7.0 | 简洁的日志库 |
| `schedule` | ≥1.2.0 | 本地定时任务调度 |
| `pytz` | ≥2024.1 | 时区处理 |
| `jieba` | ≥0.42.1 | 中文分词（可选，优化中文过滤效果） |

---

## ✅ 部署后测试验证

### 测试清单

| # | 测试项 | 操作 | 预期结果 |
|---|--------|------|----------|
| 1 | 依赖安装 | `pip install -r requirements.txt` | 无报错 |
| 2 | 立即执行 | `python main.py` | 生成 `output/AI简讯_当天日期.md` + `data/` JSON |
| 3 | 文件内容 | 打开生成的 `.md` 文件 | 包含标题、来源分组、链接 |
| 4 | 追加模式 | 再运行一次 `python main.py` | 同一文件末尾追加了新内容 |
| 5 | 自定义标签 | `python main.py --label 测试` | 文件中显示 "测试" 标签 |
| 6 | Web 展示 | `python main.py --web` → 浏览器打开 localhost:8080 | 看到资讯列表页面 |
| 7 | Web 搜索 | 在 Web 页面输入关键词搜索 | 正确过滤显示匹配结果 |
| 8 | Actions | GitHub 手动触发 Run workflow | 运行成功，output/ + data/ 有新提交 |

### 常见问题排查

**Q: `pip install` 报错？**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Q: 抓取到 0 条资讯？**
- 检查网络是否正常（部分 RSS 源需要科学上网）
- 在 `config/settings.json` 中将无法访问的源 `enabled` 设为 `false`
- 查看 `logs/ai-news-daily.log` 中的错误信息

**Q: GitHub Actions 没有自动运行？**
- 确认 Settings → Actions → General → Workflow permissions 已设为 Read and write
- 新仓库的 Actions 可能需要手动触发一次才能激活 cron
- cron 执行可能有 5-15 分钟延迟，这是 GitHub 的正常行为

**Q: 如何只保留中文资讯？**
- 在 `keywords_include` 中只保留中文关键词
- 或者在 `rss_feeds` 中将英文源的 `enabled` 设为 `false`

**Q: 如何修改输出目录？**
```json
{
  "output": {
    "dir": "../my-custom-folder"
  }
}
```

---

## 📄 输出示例

`output/AI简讯_2026-03-29.md` 的内容示例：

```markdown
# 🤖 AI 行业简讯 — 2026-03-29

## 📡 早报（2026-03-29 08:00 | 🧠 AI 智能排序）

> 共收录 **20** 条资讯

### 1. [OpenAI 发布 GPT-5 技术预览版](https://example.com/1) `⭐9.2`

- 📡 机器之心 | ⏰ 2026-03-29 07:30 | 📂 产品发布
- OpenAI 今日正式宣布 GPT-5 预览版向部分开发者开放，在推理能力和多模态理解上实现显著突破。

### 2. [Google DeepMind 推出新一代蛋白质预测模型](https://example.com/2) `⭐8.8`

- 📡 TechCrunch AI | ⏰ 2026-03-29 06:15 | 📂 技术突破
- DeepMind 新模型在蛋白质结构预测准确率上提升 40%，有望加速药物研发进程。

### 3. [NVIDIA 发布 B300 GPU 加速卡](https://example.com/3) `⭐8.5`

- 📡 36氪 AI 频道 | ⏰ 2026-03-29 05:00 | 📂 硬件算力
- NVIDIA 新一代 AI 训练加速卡性能提升 3 倍，功耗降低 20%。

...

---

*由 AI News Daily 自动生成 | 2026-03-29 08:00*
```

---

## 📜 许可证

MIT License — 自由使用、修改和分发。
