from bs4 import BeautifulSoup
import requests

class RequestSender:
    def __init__(self):
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://tuoitre.vn/",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def send_request(self, url):
        r = requests.get(url, headers=self.headers, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")


