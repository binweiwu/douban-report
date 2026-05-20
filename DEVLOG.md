# 豆瓣 Top250 爬虫 + 数据分析报告 开发记录

## 项目概述

从零开始用 Python 爬取豆瓣电影 Top250，完成数据分析、HTML 报告生成，并部署到 GitHub Pages。

- 仓库：https://github.com/binweiwu/douban-report
- 线上地址：https://binweiwu.github.io/douban-report/

---

## 阶段一：环境准备与爬虫开发

### 1. 安装依赖

```bash
pip3 install requests beautifulsoup4 pandas matplotlib
```

### 2. 编写爬虫 `douban_top250.py`

爬取豆瓣电影 Top250，共 10 页（每页 25 条），字段包括：

| 字段 | 说明 |
|------|------|
| title | 电影名 |
| rating | 评分 |
| director | 导演 |
| year | 上映年份 |
| country | 国家/地区 |
| genre | 类型 |
| quote | 经典台词 |
| cover | 封面图片 URL |

关键设计：
- 使用 `requests` + `BeautifulSoup` 解析 HTML
- 携带浏览器 `User-Agent` 和 `Referer` 头绕过基础反爬
- 携带登录 Cookie（`bid`、`dbcl2`、`ck` 等字段）绕过豆瓣登录验证
- 每页请求后 `time.sleep(1)` 礼貌间隔

翻页 URL 规律：`https://movie.douban.com/top250?start=0` 到 `?start=225`

输出：`top250.csv`（utf-8-sig 编码，250 行）

### 3. 遇到的问题与修复

**问题：运行报 `IndentationError: unexpected indent`（第2行）**

原因：复制代码时第 2 行起带了多余的前导空格。  
修复：用 Write 工具重写整个文件，去掉多余缩进。

**问题：豆瓣返回 403**

原因：未携带登录 Cookie，豆瓣拒绝未登录请求。  
修复：在 Chrome 开发者工具 Network 面板复制完整 Cookie，填入脚本 `COOKIE` 变量。

---

## 阶段二：数据分析

### 编写分析脚本 `analyze_top250.py`（后被 `export_report.py` 取代）

使用 `pandas` + `matplotlib` 生成以下图表：

1. **评分分布直方图**（含均值红线）
2. **年代分布柱状图**
3. **国家/地区 Top10 横向柱状图**
4. **类型 Top10 横向柱状图**
5. **导演作品数 Top10 横向柱状图**
6. **年代 vs 平均评分折线图**

中文字体配置：

```python
matplotlib.rcParams["font.family"] = "STHeiti"
matplotlib.rcParams["axes.unicode_minus"] = False
```

---

## 阶段三：导出 HTML 报告

### 编写 `export_report.py`

将所有图表和数据表格整合为单文件 HTML 报告，核心设计：

- 图表用 `matplotlib` 绘制后转 `base64` 内嵌（`fig_to_base64`）
- HTML 模板用普通字符串 + `__PLACEHOLDER__` 占位符，通过 `.replace()` 注入动态内容
- **避免 f-string**：HTML/JS 含大量花括号，f-string 会与 Python 格式化语法冲突，全部改用普通字符串

### 遇到的 Bug 与修复

**Bug 1：导演 Top10 表格空白**

原因：早期版本用 f-string 嵌套 HTML 模板，`{{df_to_html_table(director_df)}}` 经 f-string 处理变成 `{df_to_html_table(director_df)}`，后续 `.replace()` 找不到匹配字符串。  
修复：将整个 HTML 模板改为普通字符串，通过 `__DIRECTOR__` 占位符注入。

**Bug 2：搜索功能完全失效**

原因：JS 中 `escapeRe` 函数含 `\]` 反斜杠，嵌入 f-string 时触发 Python `SyntaxWarning` 并截断 JS，导致浏览器 JS 语法错误。  
修复：JS 代码独立为普通字符串常量 `JS = """..."""`，完全不经过 f-string。

---

## 阶段四：添加交互功能

### 搜索与筛选

在 HTML 报告中用纯前端 JavaScript 实现：

- **关键词搜索**：实时过滤片名、导演
- **国家/地区下拉筛选**
- **类型下拉筛选**
- **评分排序**（高→低 / 低→高）
- **高亮显示**匹配关键词

JS 字段索引（因表格有封面列，索引从1起算）：

| 字段 | `<td>` 索引 |
|------|------------|
| 排名 | 0 |
| 封面 | 1 |
| 片名 | 2 |
| 评分 | 3 |
| 导演 | 4 |
| 年份 | 5 |
| 国家/地区 | 6 |
| 类型 | 7 |

### 电影详情弹窗

点击表格行弹出包含封面大图、评分、导演、年份、国家、类型、经典台词的弹窗，使用 CSS `transition` 实现淡入动画。数据通过 `data-*` 属性存储在 `<tr>` 上：

```html
<tr data-title="肖申克的救赎" data-rating="9.7" data-director="弗兰克·德拉邦特"
    data-year="1994" data-country="美国" data-genre="剧情" 
    data-quote="..." data-cover="data:image/jpeg;base64,...">
```

---

## 阶段五：封面图集成

### 方案：base64 内嵌

直接将封面图下载后转为 `data:image/jpeg;base64,...` 内嵌到 HTML，彻底绕过豆瓣防盗链（浏览器无需发起跨域请求）。

下载时需携带 `Referer: https://movie.douban.com/` 头，否则豆瓣返回 403/418。

### 遇到的问题：80 张封面显示为空

**第一轮调查**：前三次重新生成，每次都是 170/250 张有图。

**根本原因定位**：

通过测试发现，失败的图片 URL（如泰坦尼克号 `img9.doubanio.com/.../p457760035.jpg`）返回 HTTP 200 但内容只有 ~988 bytes 的 `text/html`，而不是图片。

关键发现：**换一个 CDN 域名节点就能正常访问**：

```
img9.doubanio.com/.../p457760035.jpg  → 200, 988 bytes, text/html  ❌
img1.doubanio.com/.../p457760035.jpg  → 200, 27767 bytes, image/jpeg  ✓
img3.doubanio.com/.../p457760035.jpg  → 200, 27767 bytes, image/jpeg  ✓
```

豆瓣图片分布在 `img1~img9` 共 9 个 CDN 节点，部分节点上的图片已失效（URL 对应的图片 ID 在该节点不存在），但其他节点上仍然有效。

**修复方案**：自动遍历所有 CDN 节点

```python
def fetch_cover_b64(url, max_retries=3):
    import re
    m = re.search(r"(img\d+\.doubanio\.com)", url)
    cdn_variants = []
    if m:
        orig = m.group(1)
        for n in ["1","2","3","4","5","6","7","8","9"]:
            alt = "img%s.doubanio.com" % n
            if alt != orig:
                cdn_variants.append(url.replace(orig, alt))
    try_urls = [url] + cdn_variants
    for try_url in try_urls:
        r = requests.get(try_url, headers=IMG_HEADERS, timeout=10)
        ct = r.headers.get("Content-Type", "")
        if r.status_code == 200 and len(r.content) > 5000 and "image" in ct:
            # 成功，转 base64 返回
            ...
```

**结果：250/250 全部成功**，文件大小从 11.7 MB 增至 16.8 MB。

---

## 阶段六：部署到 GitHub Pages

### 创建仓库

```bash
# 本地初始化
cd ~/Desktop/douban-report
git init
git add index.html
git commit -m "init: 豆瓣Top250分析报告"

# 推送到 GitHub
git remote add origin https://github.com/binweiwu/douban-report.git
git push -u origin main
```

### 开启 GitHub Pages

通过 GitHub API 开启（Settings → Pages → Source: main branch / root）：

```bash
curl -X PUT \
  -H "Authorization: token <TOKEN>" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/binweiwu/douban-report/pages \
  -d '{"source":{"branch":"main","path":"/"}}'
```

### 后续更新推送

```bash
cp ~/Desktop/top250_report.html ~/Desktop/douban-report/index.html
cd ~/Desktop/douban-report
git add index.html
git commit -m "fix: 修复所有250张封面图（自动切换 CDN 节点）"
git push origin main
```

---

## 最终文件清单

| 文件 | 说明 |
|------|------|
| `~/Desktop/douban_top250.py` | 爬虫脚本，输出 `top250.csv` |
| `~/Desktop/top250.csv` | 爬取结果，250 行，含 cover 字段 |
| `~/Desktop/export_report.py` | 报告生成脚本，输出 `top250_report.html` |
| `~/Desktop/top250_report.html` | 本地报告文件（16.8 MB） |
| `~/Desktop/douban-report/index.html` | GitHub Pages 部署文件 |

---

## 技术要点总结

| 问题 | 解决方案 |
|------|----------|
| 豆瓣 403 反爬 | 携带登录 Cookie + 浏览器 User-Agent |
| HTML/JS 花括号与 f-string 冲突 | 全部改用普通字符串 + `__PLACEHOLDER__` 占位符 |
| 图片防盗链（GitHub Pages 跨域） | base64 内嵌，浏览器不发起图片请求 |
| 部分 CDN 节点图片失效 | 自动遍历 img1~img9 所有节点，取第一个成功的 |
