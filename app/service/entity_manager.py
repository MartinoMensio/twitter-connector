import re

from . import twitter


api = twitter.TwitterAPI()

def _user_add_fields(user):
    user['image'] = user['profile_image_url_https']
    user['image_full'] = re.sub(r'_normal(\.[a-zA-Z0-9]*)$',r'\1', user['profile_image_url_https'])

def _tweet_add_fields(tweet):
    #print(tweet)
    tweet['text'] = tweet.get('full_text', tweet.get('text', ''))
    tweet['links'] = [u['expanded_url'] for u in tweet['entities']['urls']]
    tweet['retweet'] = 'retweeted_status' in tweet

def get_user_from_screen_name(screen_name):
    user = api.get_user_from_screen_name(screen_name)
    _user_add_fields(user)
    # TODO add to persistence
    return user

def get_user(user_id):
    # TODO flag for cache
    users = api.get_users_lookup([user_id])
    if not users:
        return None
    user = users[0]
    _user_add_fields(user)
    return user

def get_user_tweets(user_id):
    tweets = api.get_user_tweets(user_id)
    for t in tweets:
        _tweet_add_fields(t)
    return tweets

def get_user_tweets_from_screen_name(screen_name):
    user = get_user_from_screen_name(screen_name)
    tweets = get_user_tweets(user['id'])
    return tweets

def get_friends_ids(user_id, limit):
    return api.get_friends_ids(user_id, limit)

def get_friends_from_screen_name(screen_name, limit):
    print(screen_name)
    user = get_user_from_screen_name(screen_name)
    print(user)
    friends_ids = get_friends_ids(user['id'], limit)
    return [get_user(user_id) for user_id in friends_ids]

def search_tweets_with_url(url):
    return twitter.search(url)

def get_tweet(tweet_id):
    # tweets can't change, so cache always
    tweets = api.get_statuses_lookup([tweet_id])
    if not tweets:
        return None
    tweet = tweets[0]
    print(tweet)
    _tweet_add_fields(tweet)
    return tweet
