from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import UrlStr

from ..service import entity_manager
from ..model import classes

router = APIRouter()

@router.get('/tweets', response_model=List[classes.Tweet])
async def search_tweets(screen_name: str = None, url: UrlStr = None):
    if screen_name:
        try:
            return entity_manager.get_user_tweets_from_screen_name(screen_name)
        except Exception as e:
            if not e.args:
                raise e
            error = e.args[0]
            print(error, type(error))
            # TODO fix TypeError: argument of type 'MaxRetryError' is not iterable
            if 'twitter' in error:
                # known error, comes from the twitter API
                raise HTTPException(404, error['twitter']['message'])
            else:
                # unhandled, something else
                raise e
    elif url:
        return entity_manager.search_tweets_with_url(url)

@router.get('/friends', response_model=List[classes.User])
async def search_friends(screen_name: str, limit: int = None):
    try:
        print(screen_name)
        result = entity_manager.get_friends_from_screen_name(screen_name, limit)
        return result
    except Exception as e:
        error = e.args[0]
        print(error, type(error))
        if 'twitter' in error:
            # known error, comes from the twitter API
            raise HTTPException(404, error['twitter']['message'])
        else:
            # unhandled, something else
            raise e

@router.get('/user', response_model=classes.User)
async def search_user(screen_name: str):
    try:
        print(screen_name)
        user = entity_manager.get_user_from_screen_name(screen_name)
        return user
    except Exception as e:
        error = e.args[0]
        print(error, type(error))
        if 'twitter' in error:
            # known error, comes from the twitter API
            raise HTTPException(404, error['twitter']['message'])
        else:
            # unhandled, something else
            raise e
