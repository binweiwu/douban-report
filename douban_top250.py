import requests
from bs4 import BeautifulSoup
import csv
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://movie.douban.com/",
}

# 填入你的豆瓣 Cookie（浏览器登录后从开发者工具复制）
# 步骤：Chrome → F12 → Network → 刷新页面 → 点任意请求 → Headers → Cookie
COOKIE = "bid=fz-hKSNnJfA; dbcl2=\"224805321:PIfop7fk0e8\"; ck=3n9v; _pk_id.100001.4cf6=7b348e551e5ea9fd.1779281650.; __utmc=30149280; __utmz=30149280.1779281651.1.1.utmcsr=accounts.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmc=223695111; __utmz=223695111.1779281651.1.1.utmcsr=accounts.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; push_noty_num=0; push_doumail_num=0; ll=\"108288\"; frodotk_db=\"a1d8394b7bc71669e588abe27355433b\"; __yadk_uid=pbezCErYFchS6OdopTKwLihRIhq561Bm; _vwo_uuid_v2=DA82DAAB63BE440EF90F749C467B8A6AD|98dc9bc7cdf0e6a0b51bae7338b196c7; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1779286572%2C%22https%3A%2F%2Faccounts.douban.com%2F%22%5D; _pk_ses.100001.4cf6=1; ap_v=0,6.0; __utma=30149280.899084690.1779281651.1779281651.1779286573.2; __utmb=30149280.0.10.1779286573; __utma=223695111.1028199318.1779281651.1779281651.1779286573.2; __utmb=223695111.0.10.1779286573"

def fetch_page(url):
    """请求单页 HTML"""
    cookies = {}
    if COOKIE:
        cookies = dict(item.split("=", 1) for item in COOKIE.split("; ") if "=" in item)
    response = requests.get(url, headers=HEADERS, cookies=cookies, timeout=10)
    response.raise_for_status()
    return response.text

def parse_movies(html):
    """从 HTML 中提取电影信息"""
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("ol.grid_view li")
    movies = []
    for item in items:
        title = item.select_one(".title").text.strip()
        rating = item.select_one(".rating_num").text.strip()
        quote_tag = item.select_one(".inq")
        quote = quote_tag.text.strip() if quote_tag else ""

        # bd 段落包含：导演 / 年份 / 国家 / 类型
        bd = item.select_one(".bd p")
        info_text = bd.text.strip() if bd else ""
        lines = [l.strip() for l in info_text.splitlines() if l.strip()]

        # 第一行：导演 主演
        director = ""
        if lines:
            first = lines[0]
            if "导演:" in first:
                director = first.split("导演:")[1].split("主演:")[0].strip()

        # 第二行：年份 / 国家 / 类型
        year, country, genre = "", "", ""
        if len(lines) >= 2:
            parts = [p.strip() for p in lines[1].split("/")]
            if len(parts) >= 1:
                year = parts[0].strip()
            if len(parts) >= 2:
                country = parts[1].strip()
            if len(parts) >= 3:
                genre = parts[2].strip()

        # 封面图 URL
        img_tag = item.select_one(".pic img")
        cover = img_tag["src"] if img_tag and img_tag.get("src") else ""

        movies.append({
            "title": title,
            "rating": rating,
            "director": director,
            "year": year,
            "country": country,
            "genre": genre,
            "quote": quote,
            "cover": cover,
        })
    return movies

def save_to_csv(movies, filename="top250.csv"):
    """保存结果到 CSV"""
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=["title", "rating", "director", "year", "country", "genre", "quote", "cover"]
        )
        writer.writeheader()
        writer.writerows(movies)
    print(f"已保存 {len(movies)} 条数据到 {filename}")

def main():
    all_movies = []
    base_url = "https://movie.douban.com/top250"

    for page in range(10):
        start = page * 25
        url = f"{base_url}?start={start}"
        print(f"正在爬取第 {page + 1} 页: {url}")

        html = fetch_page(url)
        movies = parse_movies(html)
        all_movies.extend(movies)

        time.sleep(1)  # 礼貌延迟，避免被封

    save_to_csv(all_movies)

if __name__ == "__main__":
    main()
