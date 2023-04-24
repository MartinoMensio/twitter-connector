from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import AnyUrl

from ..service import entity_manager
from ..model import classes

router = APIRouter()

# TODO handle errors


@router.get("/users")
async def search_user(username: str):
    try:
        return entity_manager.get_user_from_username_v2(username)
    except Exception as e:
        raise ValueError("TODO")


@router.get("/tweets")
async def search_user(user_id: str, get_all=False, until_id: str = None):
    get_all = str(get_all).lower() not in ["f", "false", "no"]
    return entity_manager.get_user_tweets_v2(user_id, get_all, until_id)


@router.get("/tweets/{tweet_id}")
async def get_tweet(tweet_id: str):
    return entity_manager.get_tweet_v2(tweet_id)
