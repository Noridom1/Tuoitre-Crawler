import argparse
from bs4 import BeautifulSoup
from request_sender import RequestSender
import time
import json
import re
import feedparser
import os

DISALLOWED = [
    "/tim-kiem.htm",
    "/print/",
    "/ImageView.aspx",
    "/video.htm"
]

DEFAULT_BASE_URL = "https://tuoitre.vn"


# ---------------------------
# ✅ URL VALIDATION
# ---------------------------
def is_valid_article(href: str) -> bool:
    if not href:
        return False
    if not href.startswith("/"):
        return False
    if not href.endswith(".htm"):
        return False
    for bad in DISALLOWED:
        if bad in href:
            return False
    return True


# ---------------------------
# ✅ 1. FOCUS LIST
# ---------------------------
def get_focus_list_urls(soup: BeautifulSoup, BASE_URL):
    collected = set()

    focus_container = soup.select_one("div.list__focus")
    if not focus_container:
        print("❌ Focus list not found")
        return []

    selectors = [
        "div.item-first a[href]",
        "div.item-related a[href]",
        "div.box-sub a[href]"
    ]

    for selector in selectors:
        for a in focus_container.select(selector):
            href = a.get("href")
            if is_valid_article(href):
                collected.add(BASE_URL + href)

    # print(f"✅ FOCUS extracted: {len(collected)}")
    return list(collected)


# ---------------------------
# ✅ 2. SUB LIST
# ---------------------------
def extract_from_sub(soup, BASE_URL):
    urls = set()
    sub = soup.select_one("div.list__listing-sub")
    if not sub:
        return []

    for a in sub.select("div.box-category-item a[href]"):
        href = a.get("href")
        if is_valid_article(href):
            urls.add(BASE_URL + href)

    # print(f"✅ SUB extracted: {len(urls)}")
    return list(urls)


# ---------------------------
# ✅ 3. MAIN BLOCK
# ---------------------------
def extract_from_main(soup, BASE_URL):
    urls = set()

    for a in soup.select("a.box-category-link-title[href]"):
        href = a.get("href")
        if is_valid_article(href):
            urls.add(BASE_URL + href)

    # print(f"✅ MAIN extracted: {len(urls)}")
    return list(urls)


# ---------------------------
# ✅ 4. TIMELINE ID
# ---------------------------
def extract_timeline_id(soup):
    tag = soup.select_one("input#hdZoneId")
    if not tag:
        return None

    timeline_id = tag.get("value")
    # print(f"🧠 Timeline ID detected: {timeline_id}")
    return timeline_id


# ---------------------------
# ✅ 5. AJAX TIMELINE
# ---------------------------
def crawl_timeline(request_sender, timeline_id, collected, BASE_URL, limit=100):
    page = 2

    while len(collected) < limit:
        url = f"{BASE_URL}/timeline/{timeline_id}/trang-{page}.htm"
        print(f"🔄 Loading: {url}")

        soup = request_sender.send_request(url=url)
        new_urls = extract_from_main(soup, BASE_URL)

        before = len(collected)
        collected.update(new_urls)
        after = len(collected)

        # print(f"📌 Total: {after} (+{after - before})")

        if before == after:
            print("🛑 No new articles → stopping")
            break

        page += 1
        time.sleep(1.5)

    return list(collected)[:limit]


# ---------------------------
# ✅ 6. FULL COLLECTOR
# ---------------------------
def collect_n_articles(url, BASE_URL, limit=100):
    request_sender = RequestSender()
    collected = set()

    print(f"🔵 Starting crawl: {url}")
    soup = request_sender.send_request(url=url)

    collected.update(get_focus_list_urls(soup, BASE_URL))
    collected.update(extract_from_sub(soup, BASE_URL))
    collected.update(extract_from_main(soup, BASE_URL))

    # print(f"✅ After page 1: {len(collected)}")

    timeline_id = extract_timeline_id(soup)
    if not timeline_id:
        print("❌ Timeline ID not found — cannot load more")
        return list(collected)[:limit]

    collected = crawl_timeline(request_sender, timeline_id, collected, BASE_URL, limit)
    return list(collected)[:limit]


# ---------------------------
# ✅ 7. CATEGORY CRAWLER
# ---------------------------
def crawl_categories(url, BASE_URL, categories_list=None, save_path='data/categories.json'):
    request_sender = RequestSender()
    soup = request_sender.send_request(url)

    categories = {}
    links = soup.select("ul.menu-nav > li > a.nav-link")

    for a in links:
        name = a.text.strip()
        href = a.get("href")

        if name and href and href.endswith(".htm"):
            if categories_list is not None and name not in categories_list:
                continue
            full_url = BASE_URL + href
            slug = href.replace("/", "").replace(".htm", "")
            rss_url = f"{BASE_URL}/rss/{slug}.rss"

            categories[name] = {
                "url": full_url,
                "rss": rss_url
            }

    for category in categories_list:
        if category not in categories:
            print(f"[WARNING] Category '{category}' not found on the website.")
            
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)

    # print(f"\n✅ Saved categories to {save_path}")
    return categories


# ---------------------------
# ✅ 8. CLI ENTRYPOINT
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="TuoiTre Category & Article Crawler")

    parser.add_argument(
        "--save_dir",
        type=str,
        default="data_test",
        help="Directory to save output JSON"
    )

    parser.add_argument(
        "--num_categories",
        type=int,
        default=None,
        help="Number of categories to crawl (default: all)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of articles per category"
    )

    parser.add_argument(
        "--base_url",
        type=str,
        default=DEFAULT_BASE_URL,
        help="Base website URL"
    )

    args = parser.parse_args()

    save_dir = args.save_dir
    num_categories = args.num_categories
    limit = args.limit
    BASE_URL = args.base_url

    os.makedirs(save_dir, exist_ok=True)
    category_path = os.path.join(save_dir, 'categories.json')

    categories = crawl_categories(
        url=BASE_URL,
        BASE_URL=BASE_URL,
        num_categories=num_categories,
        save_path=category_path
    )

    for category_name, category in categories.items():
        url = category.get('url')
        article_urls = collect_n_articles(
            url=url,
            BASE_URL=BASE_URL,
            limit=limit
        )

        print(f"[INFO] Found {len(article_urls)} articles for {category_name}")
        category['articles'] = article_urls

    with open(category_path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)

    print(f"[✅ DONE] Saved output to {category_path}")


if __name__ == "__main__":
    main()
