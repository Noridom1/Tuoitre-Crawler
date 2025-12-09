import argparse
from request_sender import RequestSender
from bs4 import BeautifulSoup
import requests
from article_crawler import ArticleCrawler
import json
import os
import time


# ---------------------------
# ✅ EXTRACT FINISHED ARTICLES
# ---------------------------
def extract_finished_article_urls(data_dir="data"):
    urls = set()

    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(data_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

                # ✅ Case 1: LIST of articles
                if isinstance(data, list):
                    for article in data:
                        if isinstance(article, dict) and "url" in article:
                            urls.add(article["url"])

                # ✅ Case 2: Single article DICT
                elif isinstance(data, dict):
                    if "url" in data:
                        urls.add(data["url"])

        except json.JSONDecodeError:
            print(f"[WARNING] Skipped invalid JSON: {filename}")

    print(f"[INFO] Found {len(urls)} finished articles")
    return list(urls)


# ---------------------------
# ✅ COUNT TOTAL TARGET URLS
# ---------------------------
def count_total_urls(categories):
    total = 0
    for cat in categories.values():
        total += len(cat.get("articles", []))
    return total


# ---------------------------
# ✅ CLI MAIN
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="Article crawling runner with auto-restart")

    parser.add_argument(
        "--data_dir",
        type=str,
        default="data",
        help="Directory where crawled articles are stored"
    )

    parser.add_argument(
        "--categories_path",
        type=str,
        default="data/categories.json",
        help="Path to categories.json"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )

    parser.add_argument(
        "--max_restart",
        type=int,
        default=5,
        help="Maximum number of automatic restart attempts"
    )

    args = parser.parse_args()

    data_dir = args.data_dir
    categories_path = args.categories_path
    headless = args.headless
    max_restart = args.max_restart

    # ---------------------------
    # ✅ LOAD CATEGORIES
    # ---------------------------
    if not os.path.exists(categories_path):
        print(f"[ERROR] Categories file not found: {categories_path}")
        return

    categories = json.load(open(categories_path, "r", encoding="utf-8"))
    print(f"[INFO] Loaded {len(categories)} categories")

    for name, cat in categories.items():
        print(f"    Category: {name} - {len(cat.get('articles', []))} articles")

    total_urls = count_total_urls(categories)
    print(f"[INFO] Total target articles: {total_urls}")

    # ---------------------------
    # ✅ START BROWSER ONCE
    # ---------------------------
    crawler = ArticleCrawler(
        data_dir=data_dir
    )
    crawler.start_browser(headless=headless)

    restart_count = 0

    while restart_count <= max_restart:
        if restart_count > 0:
            print(f"\n🔁 Restart attempt {restart_count + 1}/{max_restart + 1}")

        # ✅ Reload finished URLs every round
        finished_urls = extract_finished_article_urls(data_dir)

        remaining = total_urls - len(finished_urls)
        print(f"[INFO] Remaining URLs: {remaining}")

        if remaining <= 0:
            print("[✅ DONE] All articles successfully crawled!")
            break

        try:
            crawler.crawl_articles(categories, finished_urls)

        except Exception as e:
            print(f"[❌ ERROR] Crawl crashed: {e}")

        restart_count += 1
        time.sleep(3)

    # ---------------------------
    # ✅ SHUTDOWN AFTER ALL ATTEMPTS
    # ---------------------------
    print("[INFO] Stopping browser...")
    crawler.stop_browser()


def crawl_article_info(categories, save_dir, headless, max_restart):
    crawler = ArticleCrawler(
        data_dir=save_dir
    )
    crawler.start_browser(headless=headless)

    restart_count = 0

    while restart_count <= max_restart:
        if restart_count > 0:
            print(f"\n🔁 Restart attempt {restart_count + 1}/{max_restart + 1}")

        # ✅ Reload finished URLs every round
        finished_urls = extract_finished_article_urls(save_dir)

        total_urls = count_total_urls(categories)
        remaining = total_urls - len(finished_urls)
        print(f"[INFO] Remaining URLs: {remaining}")

        if remaining <= 0:
            print("[✅ DONE] All articles successfully crawled!")
            break

        try:
            crawler.crawl_articles(categories, finished_urls)

        except Exception as e:
            print(f"[❌ ERROR] Crawl crashed: {e}")

        restart_count += 1
        time.sleep(3)

    # ---------------------------
    # ✅ SHUTDOWN AFTER ALL ATTEMPTS
    # ---------------------------
    print("[INFO] Stopping browser...")
    crawler.stop_browser()
if __name__ == "__main__":
    main()
