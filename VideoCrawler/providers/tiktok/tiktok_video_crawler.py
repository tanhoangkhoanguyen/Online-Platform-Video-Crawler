from VideoCrawler.base import ChromeDriver
from VideoCrawler.schema import TikTokVideoSchema, TIKTOK_HEADERS, TIKTOK_COOKIES

import json, requests, time, re, os, warnings
warnings.filterwarnings("ignore")
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from datetime import datetime

class TikTokVideoCrawler:
    def __init__(self):
        self.id = None
        self.link = None
        self.storage_path = None
        self.video_download_link = None
        self.session = requests.session()
        self.driver = ChromeDriver(window_size = "--window-size=300,1000").get_driver()
        self.video_schema = TikTokVideoSchema()

    def check_link(self):
        response_check = requests.get(self.link, allow_redirects = True)
        final_link = response_check.url
        if not final_link.startswith((
                "https://vt.tiktok.com", 
                "https://www.tiktok.com"
            )):
            print("""[ERROR] [VideoCrawler.providers.tiktok.tiktok_video_crawler.check_link] Wrong input link""")
            return False
        self.link = final_link
        return True

    def save_to_json(self):
        filename = f"tiktok_{self.id}.json"
        file_path = os.path.join(self.storage_path, filename)
        try:
            with open(file_path, 'w', encoding = 'utf-8') as f:
                json.dump(self.video_schema.model_dump(), f, ensure_ascii = False, indent = 4)
            print(f"""[INFO] [VideoCrawler.providers.tiktok.tiktok_video_crawler.save_to_json] Saved data for video {self.id}""")
        except Exception as e:
            print(f"""[ERROR] [VideoCrawler.providers.tiktok.tiktok_video_crawler.save_to_json] Unable to save data for video {self.id}:\n\t{str(e)}""")

    def download_video(self):
        if not self.video_download_link:
            print (f"""[ERROR] [VideoCrawler.providers.tiktok.tiktok_video_crawler.download_video] Unable to download video {self.id}""")
            return

        filename = f"tiktok_{self.id}.mp4"
        file_path = os.path.join(self.storage_path, filename)
        headers = TIKTOK_HEADERS
        headers["Range"] = "bytes=0-"
        
        try:
            response = self.session.get(self.video_download_link, headers = headers, cookies = TIKTOK_COOKIES)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"""[INFO] [VideoCrawler.providers.tiktok.tiktok_video_crawler.download_video] Saved video {self.id}""")
        except Exception as e:
            print(f"""[ERROR] [VideoCrawler.providers.tiktok.tiktok_video_crawler.download_video] Undefined error for video {self.id}:\n\t{str(e)}""")
    
    def get_video_comments(self, view_relies: int = 7):
        self.driver.get(self.link)
        time.sleep(2)

        comment_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-e2e='comment-icon']"))
        )
        comment_btn.click()

        last_count = 0
        no_change_count = 0

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            comments = self.driver.find_elements(By.CSS_SELECTOR, 'span[data-e2e="comment-level-1"]')
            current_count = len(comments)

            if current_count == last_count:
                no_change_count += 1
                if no_change_count >= 2:
                    break
            else:
                no_change_count = 0
            last_count = current_count
        
        for _ in range (view_relies):
            try:
                view_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'DivViewRepliesContainer')]"
                )
                for btn in view_buttons:
                    try:
                        text = btn.text.strip()
                        if "View" not in text:
                            continue
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        btn.click()
                        time.sleep(0.2)
                    except:
                        pass
            except:
                pass
        
        raw_html = self.driver.page_source
        soup = BeautifulSoup(raw_html, "html.parser")
        self.video_schema.comments = [comment.get_text(strip = True) for comment in soup.select('span[data-e2e="comment-level-1"], span[data-e2e="comment-level-2"]')]

    def get_video_metadata(self):
        self.video_schema.id = self.id
        self.video_schema.author = re.search(r'tiktok\.com/@([^/]+)/video', self.link).group(1)
        
        response = self.session.get(self.link, headers = TIKTOK_HEADERS, cookies = TIKTOK_COOKIES)
        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find("script", id = "__UNIVERSAL_DATA_FOR_REHYDRATION__")
        if script_tag:
            try:
                raw_json = script_tag.string
                data = json.loads(raw_json)
                ts = int(data['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']['createTime'])
                date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                self.video_schema.date = date_str
            except Exception as e:
                print(f"""[ERROR] [VideoCrawler.providers.tiktok.tiktok_video_crawler.extract_video_data_from_html] Unable to extract the video date {self.id}:\n\t{str(e)}""")
                
        if script_tag:
            try:
                raw_json = script_tag.string
                data = json.loads(raw_json)
                item_struct = data['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']
                stats = item_struct.get('stats', {})

                self.video_schema.likes = stats.get('diggCount', '')
                self.video_schema.views = stats.get('playCount', '')
                self.video_schema.description = re.sub(r'#\w+', '', item_struct.get('desc', '')).strip()

                text_tags = item_struct.get('textExtra', [])
                self.video_schema.hashtag = ['#'+tag.get('hashtagName', '') for tag in text_tags if tag.get('hashtagName')]
                
                video_data = item_struct.get('video', {})
                self.video_download_link = video_data.get('playAddr', '')
            except Exception as e:
                print(f"""[ERROR] [VideoCrawler.providers.tiktok.tiktok_video_crawler.extract_video_data_from_html] Unable to extract info from video {self.id}:\n\t{str(e)}""")
        self.download_video()

    def quit_driver(self):
        self.driver.quit()
        
    def execute(self, link: str):
        self.link = link
        if self.check_link() == False:
            return

        self.id = re.search(r'/video/(\d+)', self.link).group(1)
        self.storage_path = os.path.join("data/", self.id)
        os.makedirs(self.storage_path, exist_ok = True)

        with ThreadPoolExecutor(max_workers = 2) as executor:
            f0 = executor.submit(self.get_video_comments)
            f1 = executor.submit(self.get_video_metadata)

        self.save_to_json()