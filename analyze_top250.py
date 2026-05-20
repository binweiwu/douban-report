import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.gridspec as gridspec

matplotlib.rcParams["font.family"] = "STHeiti"
matplotlib.rcParams["axes.unicode_minus"] = False

# ── 读取数据 ──────────────────────────────────────────
df = pd.read_csv("top250.csv")
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["decade"] = (df["year"] // 10 * 10).astype("Int64").astype(str) + "s"

# ── 终端统计 ──────────────────────────────────────────
print("=" * 45)
print("基础统计")
print("=" * 45)
print(f"总电影数：{len(df)}")
print(f"平均评分：{df['rating'].mean():.2f}")
print(f"最高评分：{df['rating'].max()}  → {df.loc[df['rating'].idxmax(), 'title']}")
print(f"最低评分：{df['rating'].min()}  → {df.loc[df['rating'].idxmin(), 'title']}")
print(f"\nTop 5 导演（作品数）：")
print(df["director"].value_counts().head(5).to_string())
print(f"\nTop 5 国家/地区：")
print(df["country"].value_counts().head(5).to_string())

# ── 绘图：2×3 布局，6 张子图 ──────────────────────────
fig = plt.figure(figsize=(18, 11))
fig.suptitle("豆瓣 Top250 多维度分析", fontsize=16, y=0.98)
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

# 1. 评分分布直方图
ax1 = fig.add_subplot(gs[0, 0])
ax1.hist(df["rating"], bins=14, color="#f28b00", edgecolor="white")
ax1.axvline(df["rating"].mean(), color="red", linestyle="--",
            label=f"均值 {df['rating'].mean():.2f}")
ax1.set_title("评分分布")
ax1.set_xlabel("评分")
ax1.set_ylabel("电影数量")
ax1.legend(fontsize=9)

# 2. 年代分布柱状图
ax2 = fig.add_subplot(gs[0, 1])
decade_counts = df["decade"].value_counts().sort_index()
decade_counts = decade_counts[decade_counts.index != "<NA>s"]
bars = ax2.bar(decade_counts.index, decade_counts.values, color="#4a90d9", edgecolor="white")
for bar, val in zip(bars, decade_counts.values):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
             str(val), ha="center", va="bottom", fontsize=9)
ax2.set_title("年代分布")
ax2.set_xlabel("年代")
ax2.set_ylabel("电影数量")
ax2.tick_params(axis="x", rotation=45)

# 3. 国家/地区 Top10 水平条形图
ax3 = fig.add_subplot(gs[0, 2])
country_counts = df["country"].value_counts().head(10).iloc[::-1]
ax3.barh(country_counts.index, country_counts.values, color="#5cb85c", edgecolor="white")
for i, val in enumerate(country_counts.values):
    ax3.text(val + 0.2, i, str(val), va="center", fontsize=9)
ax3.set_title("国家/地区 Top10")
ax3.set_xlabel("电影数量")

# 4. 电影类型 Top10 水平条形图
ax4 = fig.add_subplot(gs[1, 0])
genre_counts = df["genre"].value_counts().head(10).iloc[::-1]
ax4.barh(genre_counts.index, genre_counts.values, color="#9b59b6", edgecolor="white")
for i, val in enumerate(genre_counts.values):
    ax4.text(val + 0.2, i, str(val), va="center", fontsize=9)
ax4.set_title("类型 Top10")
ax4.set_xlabel("电影数量")

# 5. 导演作品数 Top10
ax5 = fig.add_subplot(gs[1, 1])
director_counts = df["director"].value_counts().head(10).iloc[::-1]
ax5.barh(director_counts.index, director_counts.values, color="#e74c3c", edgecolor="white")
for i, val in enumerate(director_counts.values):
    ax5.text(val + 0.05, i, str(val), va="center", fontsize=9)
ax5.set_title("导演作品数 Top10")
ax5.set_xlabel("作品数量")

# 6. 年代 vs 平均评分折线图
ax6 = fig.add_subplot(gs[1, 2])
decade_rating = df[df["decade"] != "<NA>s"].groupby("decade")["rating"].agg(["mean", "count"])
decade_rating = decade_rating[decade_rating["count"] >= 3]  # 过滤样本太少的年代
ax6.plot(decade_rating.index, decade_rating["mean"], marker="o",
         color="#f39c12", linewidth=2, markersize=7)
for x, y in zip(decade_rating.index, decade_rating["mean"]):
    ax6.text(x, y + 0.005, f"{y:.2f}", ha="center", va="bottom", fontsize=8)
ax6.set_title("年代 vs 平均评分")
ax6.set_xlabel("年代")
ax6.set_ylabel("平均评分")
ax6.set_ylim(8.7, 9.4)
ax6.tick_params(axis="x", rotation=45)
ax6.grid(axis="y", alpha=0.3)

plt.savefig("top250_analysis.png", dpi=150, bbox_inches="tight")
print("\n图表已保存为 top250_analysis.png")
plt.show()
