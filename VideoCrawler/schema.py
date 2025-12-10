from pydantic import BaseModel, Field
from typing import Optional, List

class TikTokLinksSchema(BaseModel):
    link_list: Optional[List[str]] = Field(default_factory = list)

class TikTokVideoSchema(BaseModel):
    id: Optional[str] = ""
    author: Optional[str] = ""
    description: Optional[str] = ""
    date: Optional[str] = ""
    views: Optional[str] = ""
    likes: Optional[str] = ""
    comments: Optional[List[str]] = Field(default_factory = list)
    hashtag: Optional[List[str]] = Field(default_factory = list)

TIKTOK_HEADERS = {
    "accept": "*/*",
    "accept-language": "vi,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    "Referer": "https://www.tiktok.com/",
    "Accept-Encoding": "identity;q=1, *;q=0"
}

TIKTOK_COOKIES = {
    'tt_webid': '1' * 19,
    'tt_webid_v2': '1' * 19
}