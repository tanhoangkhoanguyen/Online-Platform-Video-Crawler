from VideoCrawler.providers.tiktok.tiktok_links_crawler import TikTokLinksCrawler
from VideoCrawler.providers.tiktok.tiktok_video_crawler import TikTokVideoCrawler

import threading, os, logging, queue
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level = logging.INFO,
    format = "[%(levelname)s] [%(filename)s] %(message)s"
)
LOGGER = logging.getLogger()

class TikTokCrawlerService:
    def __init__(
            self, 
            keywords: list[str],
            channels: list[str],
            producer_workers: int,
            consumer_workers: int
        ):
        self.keywords = keywords
        self.channels = channels
        self.producer_workers = producer_workers
        self.consumer_workers = consumer_workers

        self.link_queue = queue.Queue()
        self.existing_links = set()

    def __producer(self):
        crawler = TikTokLinksCrawler()
        for keyword in self.keywords:
            for link in crawler.run(keyword = keyword):
                if link in self.existing_links:
                    continue
                self.existing_links.add(link)
                self.link_queue.put(link)

        for _ in range(self.consumer_workers):
            self.link_queue.put(None)
        crawler.quit_driver()

    def __consumer(self):
        crawler = TikTokVideoCrawler()
        while True:
            link = self.link_queue.get()
            if link is None:
                break
            try:
                crawler.run(link)
            except Exception as e:
                LOGGER.error(f"Failed processing {link}\n\t{e}")

    def run(self):
        producer_thread = threading.Thread(target = self.__producer)
        producer_thread.start()

        with ThreadPoolExecutor(max_workers = self.consumer_workers) as executor:
            for _ in range(self.consumer_workers):
                executor.submit(self.__consumer)
        producer_thread.join()

def validate_environment(workers: int):
    cpu_count = os.cpu_count()
    LOGGER.info(f"Available CPUs: {cpu_count}")

    if cpu_count < workers:
        LOGGER.error("Please modify the workers")
        raise SystemExit()

def run_demo(
        producer_workers: int = 1,
        consumer_workers: int = 4
    ):
    validate_environment(producer_workers + producer_workers)

    keywords = ["du lịch đà nẵng"]
    channels = ["whoisnikorain"]
    crawler = TikTokCrawlerService(
        keywords = keywords,
        channels = channels,
        producer_workers = producer_workers,
        consumer_workers = consumer_workers
    )
    crawler.run()

if __name__ == "__main__":
    run_demo()