import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import base64
import io

matplotlib.rcParams["font.family"] = "STHeiti"
matplotlib.rcParams["axes.unicode_minus"] = False

# ── 读取数据 ──────────────────────────────────────────
df = pd.read_csv("top250.csv")
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["year"]   = pd.to_numeric(df["year"],   errors="coerce")
df["decade"] = (df["year"] // 10 * 10).astype("Int64").astype(str) + "s"

# ── 生成图表 base64 ───────────────────────────────────
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

fig = plt.figure(figsize=(18, 11))
fig.suptitle("豆瓣 Top250 多维度分析", fontsize=16, y=0.98)
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

decade_counts = df["decade"].value_counts().sort_index()
decade_counts = decade_counts[decade_counts.index != "<NA>s"]

ax1 = fig.add_subplot(gs[0, 0])
ax1.hist(df["rating"], bins=14, color="#f28b00", edgecolor="white")
ax1.axvline(df["rating"].mean(), color="red", linestyle="--",
            label="均值 %.2f" % df["rating"].mean())
ax1.set_title("评分分布"); ax1.set_xlabel("评分"); ax1.set_ylabel("电影数量")
ax1.legend(fontsize=9)

ax2 = fig.add_subplot(gs[0, 1])
bars = ax2.bar(decade_counts.index, decade_counts.values, color="#4a90d9", edgecolor="white")
for bar, val in zip(bars, decade_counts.values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.5, str(val), ha="center", fontsize=9)
ax2.set_title("年代分布"); ax2.set_xlabel("年代"); ax2.set_ylabel("电影数量")
ax2.tick_params(axis="x", rotation=45)

ax3 = fig.add_subplot(gs[0, 2])
country_counts = df["country"].value_counts().head(10).iloc[::-1]
ax3.barh(country_counts.index, country_counts.values, color="#5cb85c", edgecolor="white")
for i, val in enumerate(country_counts.values):
    ax3.text(val+0.2, i, str(val), va="center", fontsize=9)
ax3.set_title("国家/地区 Top10"); ax3.set_xlabel("电影数量")

ax4 = fig.add_subplot(gs[1, 0])
genre_counts = df["genre"].value_counts().head(10).iloc[::-1]
ax4.barh(genre_counts.index, genre_counts.values, color="#9b59b6", edgecolor="white")
for i, val in enumerate(genre_counts.values):
    ax4.text(val+0.2, i, str(val), va="center", fontsize=9)
ax4.set_title("类型 Top10"); ax4.set_xlabel("电影数量")

ax5 = fig.add_subplot(gs[1, 1])
director_counts = df["director"].value_counts().head(10).iloc[::-1]
ax5.barh(director_counts.index, director_counts.values, color="#e74c3c", edgecolor="white")
for i, val in enumerate(director_counts.values):
    ax5.text(val+0.05, i, str(val), va="center", fontsize=9)
ax5.set_title("导演作品数 Top10"); ax5.set_xlabel("作品数量")

ax6 = fig.add_subplot(gs[1, 2])
decade_rating = df[df["decade"] != "<NA>s"].groupby("decade")["rating"].agg(["mean","count"])
decade_rating = decade_rating[decade_rating["count"] >= 3]
ax6.plot(decade_rating.index, decade_rating["mean"], marker="o",
         color="#f39c12", linewidth=2, markersize=7)
for x, y in zip(decade_rating.index, decade_rating["mean"]):
    ax6.text(x, y+0.005, "%.2f" % y, ha="center", va="bottom", fontsize=8)
ax6.set_title("年代 vs 平均评分"); ax6.set_xlabel("年代"); ax6.set_ylabel("平均评分")
ax6.set_ylim(8.7, 9.4); ax6.tick_params(axis="x", rotation=45); ax6.grid(axis="y", alpha=0.3)

chart_b64 = fig_to_base64(fig)
plt.close(fig)

# ── 统计表格 HTML ─────────────────────────────────────
def df_to_table(dataframe):
    return dataframe.to_html(index=False, border=0, classes="data-table")

top10_df = df.nlargest(10, "rating")[["title","director","year","country","genre","rating"]].copy()
top10_df.columns = ["片名","导演","年份","国家/地区","类型","评分"]

director_df = df["director"].value_counts().head(10).reset_index()
director_df.columns = ["导演","作品数"]

country_df = df["country"].value_counts().head(10).reset_index()
country_df.columns = ["国家/地区","电影数"]

genre_df = df["genre"].value_counts().head(10).reset_index()
genre_df.columns = ["类型","电影数"]

decade_df = decade_counts.reset_index()
decade_df.columns = ["年代","电影数"]

# ── 搜索下拉选项 ──────────────────────────────────────
country_options = "\n".join(
    '<option value="%s">%s</option>' % (c, c)
    for c in sorted(df["country"].dropna().unique())
)
genre_options = "\n".join(
    '<option value="%s">%s</option>' % (g, g)
    for g in sorted(df["genre"].dropna().unique())
)

# ── 批量下载封面图转 base64 ───────────────────────────
import base64, time as _time

IMG_HEADERS = {
    "Referer":    "https://movie.douban.com/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

def fetch_cover_b64(url, max_retries=3):
    import re
    if not url or str(url) == "nan":
        return ""
    req = __import__("requests")
    # 提取原始 CDN 域名，生成全部备用域名（img1~img9）
    m = re.search(r"(img\d+\.doubanio\.com)", url)
    cdn_variants = []
    if m:
        orig = m.group(1)
        for n in ["1","2","3","4","5","6","7","8","9"]:
            alt = "img%s.doubanio.com" % n
            if alt != orig:
                cdn_variants.append(url.replace(orig, alt))
    try_urls = [url] + cdn_variants

    for attempt in range(max_retries):
        for try_url in try_urls:
            try:
                r = req.get(try_url, headers=IMG_HEADERS, timeout=10)
                ct = r.headers.get("Content-Type", "")
                if r.status_code == 200 and len(r.content) > 5000 and "image" in ct:
                    mime = ct.split(";")[0]
                    b64  = base64.b64encode(r.content).decode()
                    return "data:%s;base64,%s" % (mime, b64)
            except Exception:
                pass
        _time.sleep(1.0 * (attempt + 1))
    return ""

print("正在下载封面图（共 %d 张）..." % len(df))
cover_b64_map = {}
failed_urls = []

for i, (_, row) in enumerate(df.iterrows(), 1):
    url = str(row.get("cover", ""))
    result = fetch_cover_b64(url)
    cover_b64_map[url] = result
    if not result and url and url != "nan":
        failed_urls.append((i, url))
    if i % 10 == 0:
        ok = sum(1 for v in cover_b64_map.values() if v)
        print("  已完成 %d / %d（成功: %d）" % (i, len(df), ok))
    _time.sleep(0.4)   # 加大间隔，降低触发限速概率

# 对失败的 URL 做二轮补充下载
if failed_urls:
    print("二轮补充下载 %d 张失败封面..." % len(failed_urls))
    _time.sleep(5)
    for idx, (rank, url) in enumerate(failed_urls, 1):
        result = fetch_cover_b64(url, max_retries=5)
        if result:
            cover_b64_map[url] = result
            print("  [%d/%d] 补充成功：第 %d 名" % (idx, len(failed_urls), rank))
        else:
            print("  [%d/%d] 仍失败：第 %d 名" % (idx, len(failed_urls), rank))
        _time.sleep(1.0)

ok_count = sum(1 for v in cover_b64_map.values() if v)
print("封面图下载完成：成功 %d / %d，失败 %d" % (ok_count, len(df), len(df) - ok_count))

# ── 全量电影表格行 ────────────────────────────────────
def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace('"',"&quot;")

full_rows = []
for rank, (_, row) in enumerate(df.iterrows(), 1):
    title    = esc(row["title"])
    director = esc(row["director"])
    year     = str(int(row["year"])) if pd.notna(row["year"]) else ""
    country  = esc(row["country"])  if pd.notna(row["country"]) else ""
    genre    = esc(row["genre"])    if pd.notna(row["genre"])   else ""
    rating   = str(row["rating"])   if pd.notna(row["rating"])  else ""
    quote    = esc(row["quote"])    if pd.notna(row["quote"])   else ""
    cover    = str(row["cover"])    if pd.notna(row.get("cover","")) and str(row.get("cover","")) not in ("","nan") else ""
    cover_src = cover_b64_map.get(cover, "")
    cover_td = ('<td><img class="cover-thumb" src="%s" alt="" loading="lazy"></td>' % cover_src) if cover_src else '<td></td>'
    full_rows.append(
        '<tr data-rank="%d" data-title="%s" data-rating="%s" '
        'data-director="%s" data-year="%s" data-country="%s" '
        'data-genre="%s" data-quote="%s" data-cover="%s">'
        '<td data-val="%d">%d</td>'
        '%s'
        '<td data-val="%s">%s</td>'
        '<td data-val="%s">%s</td>'
        '<td data-val="%s">%s</td>'
        '<td data-val="%s">%s</td>'
        '<td data-val="%s">%s</td>'
        '<td data-val="%s">%s</td>'
        '</tr>' % (
            rank, title, rating, director, year, country, genre, quote, cover_src,
            rank, rank,
            cover_td,
            title, title,
            rating, rating,
            director, director,
            year, year,
            country, country,
            genre, genre,
        )
    )
full_table_rows = "\n".join(full_rows)

# ── 核心统计数字 ──────────────────────────────────────
avg_rating  = "%.2f" % df["rating"].mean()
max_rating  = str(df["rating"].max())
max_title   = df.loc[df["rating"].idxmax(), "title"]
earliest    = str(int(df["year"].min()))

# ── CSS ───────────────────────────────────────────────
CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         background: #f5f6fa; color: #2d3436; }
  header { background: linear-gradient(135deg, #00b09b, #96c93d);
           color: white; padding: 40px 60px; }
  header h1 { font-size: 2rem; margin-bottom: 8px; }
  header p { opacity: 0.85; font-size: 0.95rem; }
  .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
  .stats-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin-bottom: 40px; }
  .stat-card { background: white; border-radius: 12px; padding: 24px;
               text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,.07); }
  .stat-card .num { font-size: 2rem; font-weight: 700; color: #00b09b; }
  .stat-card .label { font-size: .85rem; color: #636e72; margin-top: 4px; }
  .section { background: white; border-radius: 12px; padding: 30px;
             box-shadow: 0 2px 12px rgba(0,0,0,.07); margin-bottom: 30px; }
  .section h2 { font-size: 1.2rem; margin-bottom: 20px; padding-bottom: 10px;
                border-bottom: 2px solid #00b09b; color: #2d3436; }
  .chart-img { width: 100%; border-radius: 8px; }
  .data-table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  .data-table th { background: #00b09b; color: white; padding: 10px 14px;
                   text-align: left; font-weight: 600; }
  .data-table td { padding: 9px 14px; border-bottom: 1px solid #f0f0f0; }
  .data-table tr:last-child td { border-bottom: none; }
  .data-table tr:hover td { background: #f8fffe; }
  .three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; }

  /* 封面缩略图 */
  .cover-thumb { width: 40px; height: 56px; object-fit: cover;
                 border-radius: 4px; display: block; }
  /* 弹窗封面 */
  .modal-cover { width: 100px; height: 140px; object-fit: cover;
                 border-radius: 8px; float: right; margin: 0 0 12px 20px;
                 box-shadow: 0 4px 12px rgba(0,0,0,.2); }
  .modal-cover-placeholder { width: 100px; height: 140px; background: #f0f0f0;
                              border-radius: 8px; float: right; margin: 0 0 12px 20px; }

  /* 搜索 */
  .search-bar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
  .search-bar input { flex: 1; min-width: 200px; padding: 10px 16px;
                      border: 1.5px solid #dfe6e9; border-radius: 8px;
                      font-size: .95rem; outline: none; transition: border-color .2s; }
  .search-bar input:focus { border-color: #00b09b; }
  .search-bar select { padding: 10px 12px; border: 1.5px solid #dfe6e9;
                       border-radius: 8px; font-size: .9rem; outline: none;
                       background: white; cursor: pointer; }
  .search-bar select:focus { border-color: #00b09b; }
  .result-count { font-size: .85rem; color: #636e72; margin-bottom: 10px; }
  .highlight { background: #fff3cd; border-radius: 2px; padding: 0 2px; }
  #full-table tbody tr { cursor: pointer; }
  #full-table tbody tr:hover td { background: #f0fffe; }
  #full-table tbody tr.hidden { display: none; }

  /* 弹窗 */
  .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45);
                   display: flex; align-items: center; justify-content: center;
                   z-index: 1000; opacity: 0; pointer-events: none; transition: opacity .2s; }
  .modal-overlay.active { opacity: 1; pointer-events: auto; }
  .modal { background: white; border-radius: 16px; padding: 36px 40px; max-width: 520px;
           width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,.2);
           transform: translateY(20px); transition: transform .2s; position: relative; }
  .modal-overlay.active .modal { transform: translateY(0); }
  .modal-close { position: absolute; top: 16px; right: 20px; font-size: 1.4rem;
                 cursor: pointer; color: #b2bec3; border: none; background: none; line-height: 1; }
  .modal-close:hover { color: #636e72; }
  .modal-rating { font-size: 3rem; font-weight: 700; color: #f28b00; line-height: 1; }
  .modal-title  { font-size: 1.5rem; font-weight: 700; margin: 8px 0 4px; }
  .modal-meta   { font-size: .9rem; color: #636e72; margin-bottom: 20px; }
  .modal-rows   { display: grid; grid-template-columns: 90px 1fr; gap: 10px 12px;
                  font-size: .92rem; margin-bottom: 20px; }
  .modal-rows .key { color: #636e72; }
  .modal-rows .val { color: #2d3436; font-weight: 500; }
  .modal-quote  { background: #f8fffe; border-left: 3px solid #00b09b;
                  padding: 12px 16px; border-radius: 0 8px 8px 0;
                  font-style: italic; color: #555; font-size: .92rem; }
  footer { text-align: center; padding: 30px; color: #b2bec3; font-size: .85rem; }
"""

# ── JS（纯字符串，无需转义花括号）────────────────────
JS = """
(function() {
  var input    = document.getElementById("search-input");
  var selCty   = document.getElementById("filter-country");
  var selGenre = document.getElementById("filter-genre");
  var selSort  = document.getElementById("sort-by");
  var countEl  = document.getElementById("result-count");
  var tbody    = document.querySelector("#full-table tbody");
  var allRows  = Array.from(tbody.querySelectorAll("tr"));

  var rowData = allRows.map(function(tr) {
    var d = tr.dataset;
    return {
      el:       tr,
      rank:     parseInt(d.rank),
      title:    d.title    || "",
      rating:   parseFloat(d.rating) || 0,
      director: d.director || "",
      year:     parseInt(d.year) || 0,
      country:  d.country  || "",
      genre:    d.genre    || "",
    };
  });

  function escRe(s) {
    return s.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");
  }

  function highlight(text, kw) {
    if (!kw) return text;
    return text.replace(new RegExp(escRe(kw), "gi"), function(m) {
      return '<span class="highlight">' + m + '</span>';
    });
  }

  function render() {
    var kw     = input.value.trim();
    var cty    = selCty.value;
    var genre  = selGenre.value;
    var sort   = selSort.value;
    var kwLow  = kw.toLowerCase();

    var matched = rowData.filter(function(d) {
      var textOk  = !kw || (
        d.title.toLowerCase().indexOf(kwLow)    >= 0 ||
        d.director.toLowerCase().indexOf(kwLow) >= 0 ||
        d.country.toLowerCase().indexOf(kwLow)  >= 0 ||
        d.genre.toLowerCase().indexOf(kwLow)    >= 0
      );
      var ctyOk   = !cty   || d.country.indexOf(cty)   >= 0;
      var genreOk = !genre || d.genre.indexOf(genre)   >= 0;
      return textOk && ctyOk && genreOk;
    });

    matched.sort(function(a, b) {
      if (sort === "rating_desc") return b.rating - a.rating;
      if (sort === "rating_asc")  return a.rating - b.rating;
      if (sort === "year_desc")   return b.year - a.year;
      if (sort === "year_asc")    return a.year - b.year;
      return a.rank - b.rank;
    });

    var matchedSet = new Set(matched.map(function(d){ return d.el; }));

    rowData.forEach(function(d) {
      if (matchedSet.has(d.el)) {
        d.el.classList.remove("hidden");
        var cells = d.el.querySelectorAll("td");
    var fields = [
      {key:"title",    idx:2},
      {key:"director", idx:4},
      {key:"country",  idx:6},
      {key:"genre",    idx:7}
    ];
        fields.forEach(function(f) {
          cells[f.idx].innerHTML = highlight(d[f.key], kw);
        });
      } else {
        d.el.classList.add("hidden");
      }
    });

    matched.forEach(function(d) { tbody.appendChild(d.el); });
    countEl.textContent = "共找到 " + matched.length + " 部电影";
  }

  input.addEventListener("input", render);
  selCty.addEventListener("change", render);
  selGenre.addEventListener("change", render);
  selSort.addEventListener("change", render);
  render();
})();

// 详情弹窗
(function() {
  var overlay  = document.getElementById("modal-overlay");
  var closeBtn = document.getElementById("modal-close");

  function openModal(tr) {
    var d = tr.dataset;
    var coverEl = document.getElementById("m-cover");
    if (d.cover && d.cover.trim()) {
      coverEl.src          = d.cover;
      coverEl.style.display = "block";
    } else {
      coverEl.style.display = "none";
    }
    document.getElementById("m-rating").textContent   = d.rating   || "-";
    document.getElementById("m-title").textContent    = d.title    || "-";
    document.getElementById("m-meta").textContent     = (d.year || "") + "  ·  " + (d.country || "");
    document.getElementById("m-director").textContent = d.director || "-";
    document.getElementById("m-year").textContent     = d.year     || "-";
    document.getElementById("m-country").textContent  = d.country  || "-";
    document.getElementById("m-genre").textContent    = d.genre    || "-";
    document.getElementById("m-rank").textContent     = "Top " + d.rank;
    var quoteEl = document.getElementById("m-quote");
    if (d.quote && d.quote.trim()) {
      quoteEl.textContent    = "\u201c" + d.quote.trim() + "\u201d";
      quoteEl.style.display  = "block";
    } else {
      quoteEl.style.display  = "none";
    }
    overlay.classList.add("active");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    overlay.classList.remove("active");
    document.body.style.overflow = "";
  }

  document.querySelector("#full-table tbody").addEventListener("click", function(e) {
    var tr = e.target.closest("tr");
    if (tr) openModal(tr);
  });

  closeBtn.addEventListener("click", closeModal);
  overlay.addEventListener("click", function(e) {
    if (e.target === overlay) closeModal();
  });
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") closeModal();
  });
})();
"""

# ── 组装 HTML（全部用 % 或 .replace 注入，不用 f-string）──
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>豆瓣 Top250 分析报告</title>
<style>__CSS__</style>
</head>
<body>
<header>
  <h1>豆瓣电影 Top250 分析报告</h1>
  <p>数据来源：豆瓣电影 &nbsp;|&nbsp; 共 250 部电影 &nbsp;|&nbsp; 生成于 2026-05-20</p>
</header>

<div class="container">

  <div class="stats-grid">
    <div class="stat-card"><div class="num">250</div><div class="label">总电影数</div></div>
    <div class="stat-card"><div class="num">__AVG__</div><div class="label">平均评分</div></div>
    <div class="stat-card"><div class="num">__MAX__</div><div class="label">最高评分（__MAXTITLE__）</div></div>
    <div class="stat-card"><div class="num">__EARLIEST__</div><div class="label">最早年份</div></div>
  </div>

  <div class="section">
    <h2>多维度图表分析</h2>
    <img class="chart-img" src="data:image/png;base64,__CHART__" alt="分析图表">
  </div>

  <div class="section">
    <h2>Top 10 高分电影</h2>
    __TOP10__
  </div>

  <div class="three-col">
    <div class="section"><h2>国家/地区 Top10</h2>__COUNTRY__</div>
    <div class="section"><h2>类型 Top10</h2>__GENRE__</div>
    <div class="section"><h2>年代分布</h2>__DECADE__</div>
  </div>

  <div class="section">
    <h2>导演作品数 Top10</h2>
    __DIRECTOR__
  </div>

  <div class="section">
    <h2>搜索全部电影</h2>
    <div class="search-bar">
      <input type="text" id="search-input" placeholder="输入片名、导演、国家、类型...">
      <select id="filter-country">
        <option value="">全部国家/地区</option>
        __COUNTRY_OPTIONS__
      </select>
      <select id="filter-genre">
        <option value="">全部类型</option>
        __GENRE_OPTIONS__
      </select>
      <select id="sort-by">
        <option value="rank">排名排序</option>
        <option value="rating_desc">评分从高到低</option>
        <option value="rating_asc">评分从低到高</option>
        <option value="year_desc">年份从新到旧</option>
        <option value="year_asc">年份从旧到新</option>
      </select>
    </div>
    <div class="result-count" id="result-count"></div>
    <div id="search-table-wrap">
      <table class="data-table" id="full-table">
        <thead><tr>
          <th>排名</th><th>封面</th><th>片名</th><th>评分</th><th>导演</th>
          <th>年份</th><th>国家/地区</th><th>类型</th>
        </tr></thead>
        <tbody>
          __FULL_ROWS__
        </tbody>
      </table>
    </div>
  </div>

</div>

<div class="modal-overlay" id="modal-overlay">
  <div class="modal" id="modal">
    <button class="modal-close" id="modal-close">&#x2715;</button>
    <img id="m-cover" class="modal-cover" src="" alt="" style="display:none"
         onerror="this.style.display='none'">
    <div class="modal-rating" id="m-rating"></div>
    <div class="modal-title"  id="m-title"></div>
    <div class="modal-meta"   id="m-meta"></div>
    <div class="modal-rows">
      <span class="key">导演</span>    <span class="val" id="m-director"></span>
      <span class="key">年份</span>    <span class="val" id="m-year"></span>
      <span class="key">国家/地区</span><span class="val" id="m-country"></span>
      <span class="key">类型</span>    <span class="val" id="m-genre"></span>
      <span class="key">排名</span>    <span class="val" id="m-rank"></span>
    </div>
    <div class="modal-quote" id="m-quote" style="display:none"></div>
  </div>
</div>

<footer>豆瓣 Top250 分析报告 · 由 Python pandas + matplotlib 生成</footer>
<script>__JS__</script>
</body>
</html>"""

final_html = (HTML_TEMPLATE
    .replace("__CSS__",             CSS)
    .replace("__JS__",              JS)
    .replace("__CHART__",           chart_b64)
    .replace("__AVG__",             avg_rating)
    .replace("__MAX__",             max_rating)
    .replace("__MAXTITLE__",        max_title)
    .replace("__EARLIEST__",        earliest)
    .replace("__TOP10__",           df_to_table(top10_df))
    .replace("__COUNTRY__",         df_to_table(country_df))
    .replace("__GENRE__",           df_to_table(genre_df))
    .replace("__DECADE__",          df_to_table(decade_df))
    .replace("__DIRECTOR__",        df_to_table(director_df))
    .replace("__COUNTRY_OPTIONS__", country_options)
    .replace("__GENRE_OPTIONS__",   genre_options)
    .replace("__FULL_ROWS__",       full_table_rows)
)

with open("top250_report.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("报告已生成：top250_report.html")
