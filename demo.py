from VideoCrawler.providers.tiktok.tiktok_links_crawler import TikTokLinksCrawler
from VideoCrawler.providers.tiktok.tiktok_video_crawler import TikTokVideoCrawler

if __name__ == "__main__":
    keyword = "du lịch đà nẵng"
    username = "whoisnikorain"

    tiktok_links_scraper = TikTokLinksCrawler()
    links = tiktok_links_scraper.execute(keyword, username).link_list

    tiktok_video_scraper = TikTokVideoCrawler()
    for link in links:
        tiktok_video_scraper.execute(link)