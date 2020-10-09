import re
from dateutil import parser

from . import twitter, persistence


api = twitter.TwitterAPI()

def _user_add_fields(user):
    user['image'] = user['profile_image_url_https']
    user['image_full'] = re.sub(r'_normal(\.[a-zA-Z0-9]*)$',r'\1', user['profile_image_url_https'])

def _tweet_add_fields(tweet):
    #print(tweet)
    tweet['text'] = tweet.get('full_text', tweet.get('text', ''))
    tweet['links'] = [u['expanded_url'] for u in tweet['entities']['urls']]
    retweet = 'retweeted_status' in tweet
    tweet['retweet'] = retweet
    tweet['user_id'] = tweet['user']['id']
    tweet['user_screen_name'] = tweet['user']['screen_name']
    if retweet:
        _tweet_add_fields(tweet['retweeted_status'])
        tweet['retweet_source_tweet'] = tweet['retweeted_status']

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
    # from official API
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
    # print(user)
    friends_ids = get_friends_ids(user['id'], limit)
    return [get_user(user_id) for user_id in friends_ids]

def search_tweets_with_url(url):
    # see if we already have some tweets from previous search
    old_result = persistence.get_tweets_ids_by_url(url)
    if old_result:
        tweets_ids_already_here = old_result['tweets_ids']
    else:
        tweets_ids_already_here = []
    print('already', len(tweets_ids_already_here), 'tweets for', url)
    # use the date of the last search
    if tweets_ids_already_here:
        most_recent_datetime = old_result['updated']
    else:
        most_recent_datetime = None
    print('most_recent_date', most_recent_datetime)
    tweets_ids =  twitter.search(url, most_recent_datetime)
    print('retrieved', len(tweets_ids), 'for', url)
    # now merge the list of tweets_ids, removing duplicates (same boundary date)
    all_tweets_ids = list(set(tweets_ids_already_here + tweets_ids))
    persistence.save_tweets_ids_by_url(url, all_tweets_ids)
    print('saving', len(all_tweets_ids), 'tweets for', url)
    # should also sort by time?
    return get_tweets(all_tweets_ids)

def get_tweet(tweet_id):
    # tweets can't change, so cache always
    tweets = api.get_statuses_lookup([tweet_id])
    if not tweets:
        return None
    tweet = tweets[0]
    print(tweet)
    _tweet_add_fields(tweet)
    return tweet

def get_tweets(tweets_ids):
    tweets = api.get_statuses_lookup(tweets_ids)
    for t in tweets:
        if not t:
            continue
        _tweet_add_fields(t)
    return tweets
