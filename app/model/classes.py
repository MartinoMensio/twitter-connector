from typing import List
from pydantic import BaseModel, UrlStr

class User(BaseModel):
    screen_name: str
    id: int
    image: UrlStr
    image_full: UrlStr

class Tweet(BaseModel):
    id: int
    text: str
    retweet: bool

class TweetWithLinks(Tweet):
    links: List[str] # just to be generic, because someone uses underscores in host name (e.g. https://mkdatahub_public_launch.eventbrite.co.uk)
