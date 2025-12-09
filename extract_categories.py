from bs4 import BeautifulSoup
import json
from request_sender import RequestSender
from urllib.parse import urlparse


BASE_URL = "https://tuoitre.vn"


def main(url='https://tuoitre.vn', save_path='data/categories.json'):
    request_sender = RequestSender()
    soup = request_sender.send_request(url)

    categories = {}

    links = soup.select("ul.menu-nav > li > a.nav-link")

    for a in links:
        name = a.text.strip()
        href = a.get("href")

        # ✅ Only real category links
        if name and href and href.endswith(".htm"):
            full_url = BASE_URL + href

            # ✅ Extract slug: /cong-nghe.htm → cong-nghe
            slug = href.replace("/", "").replace(".htm", "")

            rss_url = f"{BASE_URL}/rss/{slug}.rss"

            categories[name] = {
                "url": full_url,
                "rss": rss_url
            }

    # ✅ Print result
    for k, v in categories.items():
        print(f"{k}")
        print(f"   🌐 URL: {v['url']}")
        print(f"   📡 RSS: {v['rss']}")

    # ✅ Save to JSON
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved to {save_path}")


if __name__ == "__main__":
    main()
