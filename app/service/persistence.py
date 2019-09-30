import os
import datetime
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

db_twitter = client['test_coinform']
twitter_tweets = db_twitter['twitter_tweets']
twitter_users = db_twitter['twitter_users']
tweets_by_url = db_twitter['tweets_id_by_url']

def replace_safe(collection, document, key_property='_id'):
    document['updated'] = datetime.datetime.now()
    # the upsert sometimes fails, mongo does not perform it atomically
    # https://jira.mongodb.org/browse/SERVER-14322
    # https://stackoverflow.com/questions/29305405/mongodb-impossible-e11000-duplicate-key-error-dup-key-when-upserting
    try:
        collection.replace_one({'_id': document[key_property]}, document, upsert=True)
    except errors.DuplicateKeyError:
        collection.replace_one({'_id': document[key_property]}, document, upsert=True)


def get_tweets_from_user_id(user_id):
    return twitter_tweets.find({'user.id': user_id})

def save_new_tweets(tweets):
    to_save = []
    for t in tweets:
        if '_id' not in t:
            t['_id'] = t['id']
            to_save.append(t)
    if to_save:
        return twitter_tweets.insert_many(to_save)
    else:
        return True

def get_twitter_user(id):
    return twitter_users.find_one({'_id': id})

def save_twitter_user(user):
    user['_id'] = user['id']
    return replace_safe(twitter_users, user)

def get_tweet(tweet_id):
    return twitter_tweets.find_one({'_id': tweet_id})

def save_tweet(tweet):
    tweet['_id'] = tweet['id']
    return replace_safe(twitter_tweets, tweet)

def get_tweets_ids_by_url(url):
    return tweets_by_url.find_one({'_id': url})

def save_tweets_ids_by_url(url, tweets_ids):
    document = {'_id': url, 'url': url, 'tweets_ids': tweets_ids, 'updated': datetime.datetime.now()}
    return tweets_by_url.replace_one({'_id': document['_id']}, document, upsert=True)
