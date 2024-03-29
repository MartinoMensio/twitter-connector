from app.service import twitter_v2
import re
import email.utils
from dateutil import parser
from datetime import timedelta

from . import persistence  # , twitter

# TODO replace with twitter_v2, right now could be needed somewhere!!!
# api = twitter.TwitterAPI()


def _user_add_fields(user):
    # https://developer.twitter.com/en/docs/twitter-api/v1/accounts-and-users/user-profile-images-and-banners
    # normal (48x48), bigger (73x73), mini (24x24), original
    user["image"] = user["profile_image_url_https"]
    user["image_full"] = re.sub(
        r"_normal(\.[a-zA-Z0-9]*)$", r"\1", user["profile_image_url_https"]
    )


def _tweet_add_fields(tweet):
    # print(tweet)
    tweet["text"] = tweet.get("full_text", tweet.get("text", ""))
    tweet["links"] = [u["expanded_url"] for u in tweet["entities"]["urls"]]
    retweet = "retweeted_status" in tweet
    tweet["retweet"] = retweet
    tweet["user_id"] = tweet["user"]["id"]
    tweet["user_screen_name"] = tweet["user"]["screen_name"]
    if retweet:
        _tweet_add_fields(tweet["retweeted_status"])
        tweet["retweet_source_tweet"] = tweet["retweeted_status"]


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


def get_user_from_username_v2(username):
    return twitter_v2.get_user_from_username(username)


def get_user_tweets_v2(user_id, get_all, since_id):
    return twitter_v2.get_tweets(user_id, get_all, since_id)


def get_tweet_v2(tweet_id):
    return twitter_v2.get_tweet(tweet_id)


def get_user_tweets(user_id):
    # from official API
    user = get_user(user_id)
    screen_name = user["screen_name"]
    tweets, oldest_tweet_id = api.get_user_tweets(user_id)
    try:
        # from snscraper, go back in time
        max_total_tweets = 100000
        if (
            len(tweets) > 0 and len(tweets) < max_total_tweets and False
        ):  # and (5000 - len(tweets)):
            oldest_tweet_l = api.get_statuses_lookup([oldest_tweet_id])
            print(oldest_tweet_id, len(oldest_tweet_l))
            if oldest_tweet_l:
                oldest_tweet = oldest_tweet_l[0]
                oldest_tweet_datetime = email.utils.parsedate_to_datetime(
                    oldest_tweet["created_at"]
                )
                until = oldest_tweet_datetime + timedelta(days=1)
                print("now adding tweets until", until)
            else:
                print("until not specified")
                # error with that tweet? just search some tweets from this user
                until = None
            tweets_back = twitter.snscrape_get_tweets(
                screen_name, until, max_tweets=max_total_tweets
            )
            # # add missing fields
            # for t in tweets_back:
            #     t['user'] = {'id': user_id, 'screen_name': screen_name}
            # save to db
            print("saving extra tweets")
            tweets_corrected = api.get_statuses_lookup([el["id"] for el in tweets_back])
            # now merge the results, removing duplicates
            all_tweets = tweets + tweets_corrected
            persistence.save_tweets_from_user_id(all_tweets, user_id)
            tweets_by_id = {el["id"]: el for el in all_tweets}
            tweets = sorted(
                tweets_by_id.values(), key=lambda el: el["id"], reverse=True
            )

    except Exception as e:
        print("something wrong with snscrape, but continuing!")
    print("total tweets", len(tweets))
    for t in tweets:
        _tweet_add_fields(t)
    return tweets


def get_user_tweets_from_screen_name(screen_name):
    user = get_user_from_screen_name(screen_name)
    tweets = get_user_tweets(user["id"])
    return tweets


def get_friends_ids(user_id, limit):
    return api.get_friends_ids(user_id, limit)


def get_friends_from_screen_name(screen_name, limit):
    print(screen_name)
    user = get_user_from_screen_name(screen_name)
    # print(user)
    friends_ids = get_friends_ids(user["id"], limit)
    return [get_user(user_id) for user_id in friends_ids]


def search_tweets_with_url(url):
    # see if we already have some tweets from previous search
    old_result = persistence.get_tweets_ids_by_url(url)
    if old_result:
        tweets_ids_already_here = old_result["tweets_ids"]
    else:
        tweets_ids_already_here = []
    print("already", len(tweets_ids_already_here), "tweets for", url)
    # use the date of the last search
    if tweets_ids_already_here:
        most_recent_datetime = old_result["updated"]
    else:
        most_recent_datetime = None
    print("most_recent_date", most_recent_datetime)
    tweets_ids = twitter.search(url, most_recent_datetime)
    print("retrieved", len(tweets_ids), "for", url)
    # now merge the list of tweets_ids, removing duplicates (same boundary date)
    all_tweets_ids = list(set(tweets_ids_already_here + tweets_ids))
    persistence.save_tweets_ids_by_url(url, all_tweets_ids)
    print("saving", len(all_tweets_ids), "tweets for", url)
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
