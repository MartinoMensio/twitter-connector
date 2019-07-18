from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import UrlStr

from ..service import entity_manager
from ..model import classes

router = APIRouter()

@router.get('/{tweet_id}', response_model=classes.TweetWithLinks)
def get_tweet_id(tweet_id):
    return entity_manager.get_tweet(tweet_id)
