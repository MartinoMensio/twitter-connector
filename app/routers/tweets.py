from typing import List
from fastapi import APIRouter, HTTPException, Path

from ..service import entity_manager
from ..model import classes

router = APIRouter()


@router.get("/{tweet_id}", response_model=classes.Tweet)
def get_tweet(tweet_id: int = Path(..., title="The ID of the tweet to get")):
    tweet = entity_manager.get_tweet(tweet_id)
    if not tweet:
        raise HTTPException(404, "Tweet not found")
    return tweet
