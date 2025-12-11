from VideoCrawler.providers.tiktok.tiktok_links_crawler import TikTokLinksCrawler
from VideoCrawler.providers.tiktok.tiktok_video_crawler import TikTokVideoCrawler

import threading, os, sys, queue
from concurrent.futures import ThreadPoolExecutor

link_queue = queue.Queue()
existing_links = set()

def producer_task(keywords):
    tiktok_links_crawler = TikTokLinksCrawler()
    for keyword in keywords:
        for link in tiktok_links_crawler.execute(keyword = keyword):
            if link in existing_links:
                continue
            existing_links.add(link)
            link_queue.put(link)

    for _ in range(4):
        link_queue.put(None)
    tiktok_links_crawler.quit_driver()

def consumer_task():
    tiktok_video_crawler = TikTokVideoCrawler()
    while True:
        link = link_queue.get()
        if link is None:
            break
        tiktok_video_crawler.execute(link)
    tiktok_video_crawler.quit_driver()

if __name__ == "__main__":
    keywords = ["du lịch đà nẵng"]
    # channels = ["whoisnikorain"]

    print ("Available cpus: ", os.cpu_count())
    if os.cpu_count() < 5:
        print ("""[INFO] [demo] Please modify the max_workers""")
        sys.exit()

    producer_thread = threading.Thread(target = producer_task, args = (keywords,))
    producer_thread.start()

    with ThreadPoolExecutor(max_workers = 4) as executor:
        for _ in range(4):
            executor.submit(consumer_task)

    producer_thread.join()