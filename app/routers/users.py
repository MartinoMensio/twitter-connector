from typing import List
from fastapi import APIRouter, HTTPException

from ..service import entity_manager
from ..model import classes

router = APIRouter()


@router.get("/{user_id}", response_model=classes.User)
async def get_user(user_id: int):
    # TODO delete
    """Returns the user object corresponding to the user_id"""
    user = entity_manager.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found.")
    return user


@router.get("/{user_id}/tweets", response_model=List[classes.Tweet])
async def get_tweets_from_user(user_id: int):
    """Returns the tweets from the provided user_id"""
    try:
        return entity_manager.get_user_tweets(user_id)
    except Exception as e:
        error = e.args[0]
        print(error, type(error))
        if "twitter" in error:
            # known error, comes from the twitter API
            raise HTTPException(404, error["twitter"]["message"])
        else:
            # unhandled, something else
            raise e


@router.get("/{user_id}/friends")
async def get_friends_ids(user_id: int, limit: int = None):
    """Returns the list of id of the friends"""
    return entity_manager.get_friends_ids(user_id, limit)
