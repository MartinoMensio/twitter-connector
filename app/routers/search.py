from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import UrlStr

from ..service import entity_manager
from ..model import classes

router = APIRouter()

@router.get('/tweets', response_model=List[classes.TweetWithLinks])
async def search_tweets(screen_name: str = None, link: UrlStr = None):
    if screen_name:
        try:
            return entity_manager.get_user_tweets_from_screen_name(screen_name)
        except Exception as e:
            error = e.args[0]
            print(error, type(error))
            if 'twitter' in error:
                # known error, comes from the twitter API
                raise HTTPException(404, error['twitter'])
            else:
                # unhandled, something else
                raise e
    elif link:
        raise NotImplementedError('AAAHHH')

@router.get('/friends', response_model=List[classes.User])
async def search_friends(screen_name: str, limit: int = None):
    try:
        print(screen_name)
        return entity_manager.get_friends_from_screen_name(screen_name, limit)
    except Exception as e:
        error = e.args[0]
        print(error, type(error))
        if 'twitter' in error:
            # known error, comes from the twitter API
            raise HTTPException(404, error['twitter'])
        else:
            # unhandled, something else
            raise e