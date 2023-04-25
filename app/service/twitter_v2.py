import os
import requests


from . import persistence

twitter_token = os.environ["TWITTER_TOKEN_ACADEMIC"]
headers = {"Authorization": f"Bearer {twitter_token}"}


def get_user_from_username(screen_name: str):
    params = {
        "user.fields": "name,username,profile_image_url,verified,created_at,description,location,protected,public_metrics"
    }
    res = requests.get(
        f"https://api.twitter.com/2/users/by/username/{screen_name}",
        headers=headers,
        params=params,
    )
    res.raise_for_status()
    res_json = res.json()
    if "errors" in res_json:
        # TODO raise errors for NotFound, ...
        print(res_json)
        raise ValueError(res_json)
    result = res_json["data"]
    result["image_full"] = result["profile_image_url"].replace("_normal", "")
    persistence.save_twitter_user_v2(result)
    return result


def get_tweets(user_id: str, get_all=False, until_id=None):
    print(until_id)
    params = {
        "tweet.fields": "entities,created_at,lang,text,referenced_tweets,author_id",
        "max_results": 100,
    }
    if until_id:
        params["until_id"] = until_id
    since_id = persistence.get_since_id_v2(user_id)
    if since_id:
        params["since_id"] = since_id
    if since_id and until_id and int(until_id) < int(since_id):
        # just ignore when we are digging in an inexistent slice of time
        del params["until_id"]
    res = requests.get(
        f"https://api.twitter.com/2/users/{user_id}/tweets",
        params=params,
        headers=headers,
    )
    res.raise_for_status()
    res_json = res.json()
    if "errors" in res_json:
        # TODO raise errors for NotFound, ...
        print(res_json)
        raise ValueError(res_json)
    new_results = res_json.get("data", [])
    older_tweets = list(persistence.get_tweets_v2(user_id))
    if len(new_results):
        persistence.save_tweets_v2(new_results)
        next_until_id = min(int(el["id"]) for el in new_results)
        next_until_id = str(next_until_id)
    else:
        next_until_id = None
        # the end of reachable tweets
        if older_tweets:
            # find the most recent of the older tweets
            most_recent = max(int(el["id"]) for el in older_tweets)
            # remember this as the value to use as since_id next times (useless to re-check in the past)
            persistence.save_since_id_v2(user_id, most_recent)
    # merge (remove duplicates)
    all_tweets = {el["id"]: el for el in older_tweets + new_results}.values()
    if get_all:
        results = all_tweets
    else:
        results = new_results
    # sort by most recent first
    results = sorted(results, key=lambda el: int(el["id"]), reverse=True)
    # return the until_id of the new_results!!!! Before mixing with older tweets
    return {
        "next_until_id": next_until_id,
        "total_tweets": len(all_tweets),
        "tweets": results,
    }


def get_tweet(tweet_id: str):
    params = {
        "tweet.fields": "entities,created_at,lang,text,referenced_tweets,author_id",
        "expansions": "author_id",
        "user.fields": "name,username,profile_image_url,verified,created_at,description,location,protected,public_metrics",
    }
    res = requests.get(
        f"https://api.twitter.com/2/tweets/{tweet_id}",
        params=params,
        headers=headers,
    )
    res.raise_for_status()
    res_json = res.json()
    if "errors" in res_json:
        # TODO raise errors for NotFound, ...
        print(res_json)
        raise ValueError(res_json)
    result = res_json["data"]
    result["author"] = res_json["includes"]["users"][0]
    result["author"]["image_full"] = result["author"]["profile_image_url"].replace(
        "_normal", ""
    )
    # persistence.save_twitter_user_v2(result)
    return result


def ping_api():
    res = requests.get(
        f"https://api.twitter.com/2/tweets/search/recent",
        headers=headers,
        params={"query": "from:twitterdev", "max_results": 10},
    )
    res.raise_for_status()
    res_json = res.json()
    if "errors" in res_json:
        # TODO raise errors for NotFound, ...
        print(res_json)
        raise ValueError(res_json)
    return res_json


# def get_timeline(user_id: str):
#     user_id = str(user_id)
#     params = {
#         'tweet.fields': 'entities,created_at,lang,text,referenced_tweets',
#         'max_results': 100
#     }
#     # get already downloaded tweets
#     tweet_ids = persistence.get_tweets_ids_from_user_id(user_id)
#     all_tweets = get_statuses_lookup(tweet_ids)
#     print(len(all_tweets), 'old tweets')
#     # limit backwards (if already collected)
#     newest_saved = persistence.get_latest_tweet_id(user_id)
#     if newest_saved:
#         params['since_id'] = newest_saved
#     new_results = []
#     while True:
#         res = requests.get(f'https://api.twitter.com/2/users/{user_id}/tweets', params=params, headers=headers)
#         res.raise_for_status()
#         res_json = res.json()
#         # print(res_json)
#         new_tweets = res_json.get('data', [])
#         new_results.extend(new_tweets)
#         print(len(new_results), 'new tweets retrieved')
#         pagination_token = res_json['meta'].get('next_token')
#         if not pagination_token:
#             break
#         params['pagination_token'] = pagination_token
#     if new_results:
#         all_tweets.extend(new_results)
#         persistence.save_tweets_from_user_id(all_tweets, user_id)
#     return all_tweets
