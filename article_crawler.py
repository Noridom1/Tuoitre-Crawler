import os
import time
import json
import requests
from tqdm import tqdm
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl
from playwright.sync_api import sync_playwright
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
import logging
from datetime import datetime
from logger_config import get_logger


class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx
        )

session = requests.Session()
session.mount("https://", TLSAdapter())

class ArticleCrawler:
    def __init__(self, data_dir='data'):
        self.playwright = None
        self.browser = None
        self.page = None
        self.data_dir = Path(data_dir)
        self.image_dir = self.data_dir / "images"
        self.audio_dir = self.data_dir / "audio"
        self.logger = get_logger("ArticleCrawler")

    def start_browser(self, headless=True):
        """Start a single Playwright browser session."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def stop_browser(self):
        """Safely close Playwright browser."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def crawl_articles(self, posts: dict, finished_url: set):
        for category, data in posts.items():
            if category == "Video":
                continue
            urls = data.get("articles", [])
            print(f"[INFO] Started crawling category {category} with {len(urls)} articles")
            loop = tqdm(urls, leave=True)

            self.logger.info(f"Started crawling category: {category} | Articles: {len(urls)}")

            for url in loop:
                if url in finished_url:
                    self.logger.info(f"The url {url} has been crawled. Skipping.")
                    continue
                try:
                    soup = self.send_request(url)
                    post_data = self.extract_post_data(soup, url, category=category)
                    post_id = post_data["postId"]

                    post_data["images"] = self.download_images(post_id, post_data["images"])
                    post_data["audio_podcast"] = self.download_audio(post_id, post_data["audio_podcast"])
                    self.save_post_json(post_data)
                    self.logger.info(f"Saved article {post_id}")
                    loop.set_description(f"✅ Saved {post_id}")

                except Exception as e:
                    self.logger.error(f"Failed crawling article: {url}", exc_info=True)
                    self.log_failed_url(url, str(e))


    def send_request(self, url):
        self.logger.debug(f"Fetching URL: {url}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            r = session.get(url, headers=headers, timeout=15)
            r.raise_for_status()

        except Exception:
            self.logger.error(f"Request failed: {url}", exc_info=True)
            raise

        return BeautifulSoup(r.text, "html.parser")

    def extract_post_data(self, soup, url, category):
        post_id = self.extract_post_id(url)
        comments = self.extract_comments_api(post_id)
        title = self.extract_title(soup)
        date = self.extract_date(soup)
        author = self.extract_author(soup)
        content = self.extract_content(soup)
        audio_urls = self.extract_audio_urls(url)
        images = self.extract_images(soup)
        reactions = self.extract_reactions(url=url, wait_time=10)

        return {
            "postId": post_id,
            "category": category,
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "date": date,
            "audio_podcast": audio_urls,
            "images": images,
            "comments": comments,
            "reactions": reactions
        }

    def extract_post_id(self, url):
        return url.split("-")[-1].replace(".htm", "")

    def extract_title(self, soup):
        h1 = soup.select_one("h1")
        return h1.text.strip() if h1 else ""

    def extract_date(self, soup):
        meta = soup.select_one("meta[property='article:published_time']")
        return meta["content"] if meta else None

    def extract_author(self, soup):
        author = soup.select_one("div.author-info a")
        return author.text.strip() if author else "Tuoi Tre"

    def extract_content(self, soup):
        container = soup.select_one("div.detail-cmain")
        if not container:
            return ""

        allowed_selectors = [
            "div#main-detail-body p",
            "div.detail-cmain p",
            "div#article-body p",
            "div.article-content p",
            "div.content p"
        ]
        allowed_paragraphs = set()
        for sel in allowed_selectors:
            allowed_paragraphs.update(soup.select(sel))

        cleaned = []
        for p in container.select("p"):
            if p not in allowed_paragraphs:
                continue
            if p.has_attr("data-placeholder"):
                continue
            if "VCObjectBoxRelatedNewsItemSapo" in p.get("class", []):
                continue
            text = p.get_text(strip=True)
            if not text:
                continue
            bad_patterns = ["Ảnh:", "Nguồn:", "Video:", "Xem thêm:", "Đọc thêm:", "TTO -"]
            if any(text.startswith(bp) for bp in bad_patterns):
                continue
            cleaned.append(text)
        return "\n".join(cleaned)

    def extract_images(self, soup):
        """
        Extract images and captions from the article.

        Returns:
            List[dict]: Each dict has 'url' and 'caption'
        """
        images = []
        # Select all <figure> elements under the desired container
        figures = soup.select("#main-detail > div.detail-cmain.clearfix > div.detail-content.afcbc-body > figure")
        
        for fig in figures:
            img = fig.select_one("img")
            if img:
                # Prefer data-original if present (lazy-loaded images)
                url = img.get("data-original") or img.get("src")
                caption = img.get("alt", "").strip()  # get alt text
                if url:
                    images.append({"url": url, "caption": caption})
        
        return images


    def extract_comments_api(self, post_id):
        url = "https://id.tuoitre.vn/api/getlist-comment.api"
        params = {
            "pageindex": 1,
            "objId": str(post_id),
            "objType": 1,
            "objectpopupid": "",
            "sort": 2,
            "commentid": "",
            "command": "",
            "appKey": "lHLShlUMAshjvNkHmBzNqERFZammKUXB1DjEuXKfWAwkunzW6fFbfrhP/FIG0Xwp7aPwhwIuucLW1TVC9lzmUoA=="
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://tuoitre.vn/",
            "Origin": "https://tuoitre.vn"
        }

        all_comments = []

        def process_comment(item):
            """Recursively process a comment and its child_comments."""
            reactions = item.get("reactions", {})
            child_comments = item.get("child_comments") or []

            # Process child comments first
            replies = [process_comment(reply) for reply in child_comments]

            return {
                "commentId": item.get("id"),
                "author": item.get("sender_fullname"),
                "text": item.get("content"),
                "date": item.get("published_date"),
                "vote_reactions": {
                    "like": reactions.get("1", 0),
                    "love": reactions.get("3", 0),
                    "wow": reactions.get("5", 0),
                    "sad": reactions.get("7", 0),
                    "angry": reactions.get("9", 0)
                },
                "replies": replies  # nested child comments
            }

        page = 1
        while True:
            params["pageindex"] = page
            try:
                r = requests.get(url, params=params, headers=headers, timeout=15)
                if r.status_code != 200:
                    break
                data = r.json()
                page_data = json.loads(data.get("Data", "[]"))
                if not page_data:
                    break

                for item in page_data:
                    all_comments.append(process_comment(item))

                page += 1
                time.sleep(1)
            except Exception:
                self.logger.error("Comment API failed", exc_info=True)
                break
        return all_comments


    def extract_audio_urls(self, url, wait_time=5):
        audios = []
        try:
            self.page.goto(url, timeout=60000)
            time.sleep(wait_time)  # wait for JS to load
            audio_elements = self.page.query_selector_all("audio")
            for a in audio_elements:
                src = a.get_attribute("src")
                if src:
                    audios.append(
                        {
                            "url": src
                        }
                    )
        except Exception:
            self.logger.error(f"Failed extracting audio from {url}", exc_info=True)

        
        return audios

    def extract_reactions(self, url, wait_time=10):
        reactions = {"star": 0, "like": 0, "love": 0}
        try:
            # self.page.goto(url, timeout=60000)
            # wait for reactions container
            self.page.wait_for_selector(
                "#main-detail > div.sendstarauthor > div > div > div.reactinfo",
                timeout=wait_time*1000
            )
            selectors = {
                "star": "span:nth-child(2) > span",
                "like": "span:nth-child(3) > span",
                "love": "span:nth-child(4) > span"
            }
            for key, sel in selectors.items():
                el = self.page.query_selector(f"#main-detail > div.sendstarauthor > div > div > div.reactinfo > {sel}")
                if el:
                    text = el.inner_text().strip().replace(',', '')
                    reactions[key] = int(text) if text.isdigit() else 0
        except Exception:
            self.logger.error(f"Failed extracting reactions from {url}", exc_info=True)

        return reactions

    def download_images(self, post_id, images):
        if not images:
            return images
        
        folder = self.image_dir / post_id
        os.makedirs(folder, exist_ok=True)
        for image in images:
            url = image["url"]
            try:
                r = session.get(url, timeout=10)
                filename = os.path.basename(urlparse(url).path)
                path = os.path.join(folder, filename)
                with open(path, "wb") as f:
                    f.write(r.content)
                image["local_path"] = path
            except Exception:
                self.logger.error(f"Image download failed: {url}", exc_info=True)

        return images

    def download_audio(self, post_id, audios):
        if not audios:
            return audios
        folder = self.audio_dir / post_id
        os.makedirs(folder, exist_ok=True)
        for audio in audios:
            url = audio["url"]
            i = audios.index(audio) + 1
            try:
                r = session.get(url, timeout=15)
                ext = url.split(".")[-1]
                path = os.path.join(folder, f"{post_id}_{i}.{ext}")
                with open(path, "wb") as f:
                    f.write(r.content)
                audio["local_path"] = path
            except Exception:
                self.logger.error(f"Audio download failed: {url}", exc_info=True)

        return audios
    
    def save_post_json(self, post_data):
        os.makedirs(self.data_dir, exist_ok=True)
        path = os.path.join(self.data_dir, f"{post_data['postId']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(post_data, f, ensure_ascii=False, indent=2)

    def log_failed_url(self, url, reason=""):
        path = self.log_dir / "failed_urls.txt"
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{url} | {reason}\n")

