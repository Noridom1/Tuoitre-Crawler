# Tuoitre-Crawler

A Python-based web crawler designed to extract articles, categories, and comments from Tuoi Tre News [tuoitre.vn](https://tuoitre.vn/), one of Vietnam's leading online newspapers.

## Objective

This crawler systematically collects news articles from Tuoi Tre, including article metadata, content, categories, and user comments. The project is designed to facilitate data collection for research, analysis, or archival purposes.

## Features

- Extract article categories and subcategories
- Crawl article metadata (title, author, publish date, etc.)
- Download article content and media links
- Collect user comments on articles
- Configurable logging system
- Robust request handling with retry mechanisms

## Requirements

- Python 3.7+
- Playwright (for browser automation)
- Required packages (install via `requirements.txt`):
  - playwright
  - requests
  - beautifulsoup4
  - lxml (or html.parser)
  - Additional dependencies as specified in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Noridom1/Tuoitre-Crawler.git
cd Tuoitre-Crawler
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

> **Note:** The first time you run Playwright, it will download the necessary browser binaries (Chromium, Firefox, WebKit). This is a one-time setup and may take a few minutes.

## Usage

### Main Crawler

The main script orchestrates the entire crawling process, from extracting categories to collecting article information.

**Basic usage:**
```bash
python main.py
```

**Advanced usage with options:**
```bash
python main.py --save_dir data --categories_list "['Thời sự','Pháp luật','Xe']" --limit 100 --headless
```

**Available arguments:**

- `--save_dir` (default: `"data"`): Directory to save crawled article information
  ```bash
  python main.py --save_dir output/articles
  ```

- `--categories_list` (optional): JSON list of specific categories to crawl. If not provided, all categories will be crawled.
  ```bash
  python main.py --categories_list "['Thời sự','Pháp luật','Xe']"
  ```

- `--limit` (default: `100`): Number of articles to crawl per category
  ```bash
  python main.py --limit 50
  ```

- `--headless` (flag): Run browser in headless mode (no UI)
  ```bash
  python main.py --headless
  ```

- `--max_restart` (default: `3`): Maximum number of restarts on failure
  ```bash
  python main.py --max_restart 5
  ```

**Example combinations:**
```bash
# Crawl 200 articles from specific categories in headless mode
python main.py --categories_list "['Thời sự','Pháp luật','Xe']" --limit 200 --headless

# Save to custom directory with higher restart tolerance
python main.py --save_dir custom_data --max_restart 10

# Full example with all options
python main.py --save_dir data/tuoitre --categories_list "['Thời sự','Pháp luật','Xe']" --limit 50 --headless --max_restart 5
```

### Individual Modules

You can also run individual components separately:

**Extract Categories:**
```bash
python extract_categories.py
```

**Crawl Specific Categories:**
```bash
python crawl_categories.py
```

**Crawl Article Information:**
```bash
python crawl_article_info.py
```

**Check Comments:**
```bash
python check_comments.py
```

## Project Structure

```
Tuoitre-Crawler/
├── main.py                  # Main entry point
├── article_crawler.py       # Article crawling logic
├── crawl_article_info.py    # Article information extraction
├── crawl_categories.py      # Category crawling
├── extract_categories.py    # Category extraction
├── check_comments.py        # Comment retrieval
├── request_sender.py        # HTTP request handler
├── logger_config.py         # Logging configuration
├── requirements.txt         # Python dependencies
└── media_links.txt          # Collected media links
```

## Output

The crawler generates:
- Extracted article data (JSON format)
- Logs for monitoring crawl progress

## Notes

- Please respect robots.txt and Tuoi Tre's terms of service
- Implement appropriate delays between requests to avoid overloading the server
- This tool is intended for educational and research purposes only

## License

This project is provided as-is for educational purposes.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the issues page.
