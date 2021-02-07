from typing import List, Optional, ForwardRef
from pydantic import BaseModel, AnyUrl

class User(BaseModel):
    screen_name: str
    id: str
    image: str # some profiles can have an empty string (temporarily unavailable because it violates the Twitter Media Policy)
    image_full: str
    description: str

# https://pydantic-docs.helpmanual.io/#postponed-annotations for recursive model
ref = ForwardRef('Tweet')
class Tweet(BaseModel):
    id: str # serializing to string because otherwise the long id gets messed up
    text: str
    retweet: bool
    retweet_source_tweet: Optional[ref]# the ID of the tweet that has been retweeted (retweets with comments instead will have a http://t.co/ link)
    links: List[str] # just to be generic, because someone uses underscores in host name (e.g. https://mkdatahub_public_launch.eventbrite.co.uk)
    user_id: int
    user_screen_name: str
    created_at: str
    lang: str

Tweet.update_forward_refs()
