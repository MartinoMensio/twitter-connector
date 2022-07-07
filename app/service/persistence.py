import os
from datetime import datetime
from typing import List
from pymongo import MongoClient, errors

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost:27017')
MONGO_USER = os.environ.get('MONGO_USER', None)
MONGO_PASS = os.environ.get('MONGO_PASS', None)
if MONGO_USER and MONGO_PASS:
    MONGO_URI = 'mongodb://{}:{}@{}'.format(MONGO_USER, MONGO_PASS, MONGO_HOST)
else:
    MONGO_URI = 'mongodb://{}'.format(MONGO_HOST)
print('MONGO_URI', MONGO_URI)
client = MongoClient(MONGO_URI)

db = client['twitter_connector']


tweets_collection = db['tweets']
tweets_collection_sns = db['tweets_sns']
timelines_collection = db['timelines']
users_collection = db['users']
tweets_by_url = db['by_url']
# v2 of API
users_collection_v2 = db['users_v2']
tweets_collection_v2 = db['tweets_v2']
since_id_collection_v2 = db['since_ids_v2']



def replace_safe(collection, document, key_property='_id'):
    document['updated'] = datetime.now()
    # the upsert sometimes fails, mongo does not perform it atomically
    # https://jira.mongodb.org/browse/SERVER-14322
    # https://stackoverflow.com/questions/29305405/mongodb-impossible-e11000-duplicate-key-error-dup-key-when-upserting
    try:
        collection.replace_one({'_id': document[key_property]}, document, upsert=True)
    except errors.DuplicateKeyError:
        collection.replace_one({'_id': document[key_property]}, document, upsert=True)


def save_tweets_from_user_id(tweets: List[dict], user_id: int):
    now = datetime.now()
    tweet_ids = []
    to_save = []
    for t in tweets:
        tweet_ids.append(t['id'])
        if '_id' not in t:
            # this tweet is new
            t['_id'] = t['id']
            to_save.append(t)
            tweets_collection.update_one({'_id': t['_id']}, t, upsert=True)
    # tweets_collection.insert_many(tweets)
    old_tweet_ids = get_tweets_ids_from_user_id(user_id)
    updated_tweet_ids = sorted(set(old_tweet_ids + tweet_ids), reverse=True)
    timelines_collection.update_one({'_id': user_id}, {
        '_id': user_id,
        'last_updated': now,
        'tweet_ids': updated_tweet_ids
    }, upsert=True)


def get_tweets_ids_from_user_id(user_id: int) -> List[int]:
    res = timelines_collection.find_one({'_id': user_id})
    if res:
        return res['tweet_ids']
    else:
        return []


def get_latest_update(user_id: int) -> datetime:
    res = timelines_collection.find_one({'_id': user_id})
    if res:
        return res['last_updated']
    else:
        return None

def get_latest_tweet_id(user_id: int) -> int:
    res = timelines_collection.find_one({'_id': user_id})
    if res:
        ids_int = [int(el) for el in res['tweet_ids']]
        return max(ids_int)
    else:
        return None

def get_oldest_tweet_id(user_id: int) -> int:
    res = timelines_collection.find_one({'_id': user_id})
    if res:
        ids_int = [int(el) for el in res['tweet_ids']]
        return min(ids_int)
    else:
        return None


def get_twitter_user(id):
    return users_collection.find_one({'_id': id})

def save_twitter_user(user):
    user['_id'] = user['id']
    return replace_safe(users_collection, user)

def get_tweet(tweet_id):
    return tweets_collection.find_one({'_id': tweet_id})

def save_tweet(tweet):
    tweet['_id'] = tweet['id']
    return replace_safe(tweets_collection, tweet)

# def save_new_tweets_sns(tweets):
#     to_save = []
#     for t in tweets:
#         if '_id' not in t:
#             t['_id'] = t['id']
#             to_save.append(t)
#             # tweets_collection.update_one({'_id': t['_id']}, t, upsert=True)
#     if to_save:

#         # return tweets_collection_sns.insert_many(to_save)
#     else:
#         return True

def get_tweets_ids_by_url(url):
    return tweets_by_url.find_one({'_id': url})

def save_tweets_ids_by_url(url, tweets_ids):
    document = {'_id': url, 'url': url, 'tweets_ids': tweets_ids, 'updated': datetime.now()}
    return tweets_by_url.replace_one({'_id': document['_id']}, document, upsert=True)


def save_twitter_user_v2(user: dict):
    user['_id'] = user['id']
    return replace_safe(users_collection_v2, user)

def get_since_id_v2(user_id):
    result = since_id_collection_v2.find_one({'_id': user_id})
    if result:
        return result['since_id']
    else:
        return None

def save_since_id_v2(user_id, since_id):
    item = {
        '_id': user_id,
        'since_id': since_id
    }
    return replace_safe(since_id_collection_v2, item)

def get_tweets_v2(user_id: str):
    user_id = str(user_id)
    return tweets_collection_v2.find({'author_id': user_id})

def save_tweets_v2(tweets):
    for t in tweets:
        if '_id' not in t:
            # this tweet is new
            t['_id'] = t['id']
            tweets_collection_v2.update_one({'_id': t['_id']}, t, upsert=True)
    return True

def ping_db():
    return db.command('ping')
