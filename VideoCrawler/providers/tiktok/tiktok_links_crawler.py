from VideoCrawler.base import ChromeDriver
from VideoCrawler.schema import TikTokLinksSchema

import json, time, re, logging
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

logging.basicConfig(
    level = logging.INFO,
    format = "[%(levelname)s] [%(filename)s] %(message)s"
)
LOGGER = logging.getLogger()

class TikTokLinksCrawler:
    def __init__(self):
        self.driver = ChromeDriver().get_driver()
        self.driver.get("https://www.tiktok.com")
        self.__load_cookies()
        # self.link_schema = TikTokLinksSchema()

    def __load_cookies(self):
        try:
            with open("VideoCrawler/providers/tiktok/tiktok_cookies.json", "r", encoding = "utf-8") as f:
                cookie_data = json.load(f)
        except:
            LOGGER.error("No tiktok_cookies.json found")
            raise
        self.cookies = cookie_data["cookies"]
        time.sleep(2)
        for c in self.cookies:
            self.driver.add_cookie({
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", None),
                "path": c.get("path", "/"),
                "secure": c.get("secure", False),
                "httpOnly": c.get("httpOnly", False),
            })

    def extract_links_from_html(self, raw_html):
        pattern = re.compile(
            r"https://www\.tiktok\.com/@[A-Za-z0-9_.-]+/video/[0-9]+"
        )
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup.find_all("a", href = True):
            href = tag["href"]
            if pattern.match(href):
                yield href

    def get_html_source_by_keyword(self, keyword: str, scrolling: int = 5):
        encoded = keyword.replace(" ", "%20")
        url = f"https://www.tiktok.com/search?q={encoded}"
        self.driver.get(url)
        time.sleep(2)

        for _ in range(scrolling):
            # self.driver.execute_script("window.scrollBy(0, 1000);") # Cant scroll due to Tiktok uses a virtual/infinite scroll container
            self.driver.execute_script("""
                const items = document.querySelectorAll('a[href*="/video/"]');
                if (items.length) items[items.length - 1].scrollIntoView();
            """)
            time.sleep(2)

        raw_html = self.driver.page_source
        for link in self.extract_links_from_html(raw_html):
            yield link

        time.sleep(2)
        LOGGER.info(f"Crawled keyword '{keyword}'")

    def get_html_source_from_channel(self, channel: str):
        url = f"https://www.tiktok.com/@{channel}"
        self.driver.get(url)
        time.sleep(2)

        try:
            refresh_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Refresh')]"
            )
            refresh_btn.click()
        except:
            pass

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        no_change_count = 0
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                no_change_count += 1
                if no_change_count >= 3:
                    break
            else:
                no_change_count = 0
            last_height = new_height
        raw_html = self.driver.page_source
        for link in self.extract_links_from_html(raw_html):
            yield link

        time.sleep(2)
        LOGGER.info(f"Crawled channel '{channel}'")

    def quit_driver(self):
        self.driver.quit()

    def run(self, keyword: str = None, channel: str = None):
        if keyword:
            for link in self.get_html_source_by_keyword(keyword):
                yield link
        if channel:
            for link in self.get_html_source_from_channel(channel):
                yield link