from crawl_article_info import *
from crawl_categories import *


def parse_args():
    parser = argparse.ArgumentParser(description="TuoiTre Article Info Crawler")

    parser.add_argument(
        "--save_dir",
        type=str,
        default="data",
        help="Directory to save crawled article information"
    )

    parser.add_argument(
        "--categories_list",
        type=str,
        default=None,
        help='JSON list of categories, e.g. \'["Thời sự", "Thể thao"]\''
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of articles per category"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )

    parser.add_argument(
        "--max_restart",
        type=int,
        default=3,
        help="Maximum number of restarts on failure"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    save_dir = args.save_dir
    if args.categories_list:
        try:
            categories_list = json.loads(args.categories_list.replace("'", '"'))
        except json.JSONDecodeError:
            print(type(args.categories_list))
            print(args.categories_list)
            print("[ERROR] Invalid JSON for categories_list. Using all categories.")
            categories_list = None
            return
    limit = args.limit
    headless = args.headless
    max_restart = args.max_restart

    os.makedirs(save_dir, exist_ok=True)
    categories_path = os.path.join(save_dir, 'categories.json')

    print("[INFO] Crawling categories...")
    categories = crawl_categories(
        url=DEFAULT_BASE_URL,
        BASE_URL=DEFAULT_BASE_URL,
        categories_list=categories_list,
        save_path=categories_path
    )

    for category_name, category in categories.items():
        url = category.get('url')
        article_urls = collect_n_articles(
            url=url,
            BASE_URL=DEFAULT_BASE_URL,
            limit=limit
        )

        print(f"[INFO] Found {len(article_urls)} articles for {category_name}")
        category['articles'] = article_urls

    with open(categories_path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)

    print(f"[✅ DONE] Saved {len(categories)} categories to {categories_path}")

    # else:
    #     print(f"[INFO] Categories file found: {categories_path}")
    #     with open(categories_path, 'r', encoding='utf-8') as f:
    #         categories = json.load(f)

    # # Load categories
    # with open(categories_path, 'r', encoding='utf-8') as f:
    #     categories = json.load(f)

    total_urls = count_total_urls(categories)
    print(f"[INFO] Total target article URLs: {total_urls}")

    # Crawl article information
    crawl_article_info(
        categories=categories,
        save_dir=save_dir,
        headless=headless,
        max_restart=max_restart
    )

if __name__ == "__main__":
    main()