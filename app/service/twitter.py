import os
import time

from requests.exceptions import HTTPError
import tqdm
import requests
import logging

# import snscrape.modules
# import twitterscraper

from . import persistence

logger = logging.getLogger("twitterscraper")
logger.setLevel(logging.WARNING)


class TwitterAPI(object):
    def __init__(self):
        # retrieve all the possible twitter API keys and put them in the .env file as TWITTER_KEY_x TWITTER_SECRET_x with x=0,1,2,3,...

        # the set of credentials
        self.credentials = []
        # the set of tokens corresponding to the credentials
        self.bearer_tokens = []
        # which credential is being used
        self.active = 0
        while True:
            key = os.environ.get("TWITTER_KEY_{}".format(self.active), None)
            if not key:
                break
            secret = os.environ["TWITTER_SECRET_{}".format(self.active)]
            self.credentials.append({"key": key, "secret": secret})
            token = self.get_bearer_token(key, secret)
            if token:
                self.bearer_tokens.append(token)
                self.alive = True
                self.active += 1
        if not self.bearer_tokens:
            print("you don't have twitter credentials in the environment!!!")
        print("twitter tokens available:", len(self.bearer_tokens))
        self.active = 0

    def get_bearer_token(self, key, secret):
        response = requests.post(
            "https://api.twitter.com/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=requests.auth.HTTPBasicAuth(key, secret),
        ).json()
        if "errors" in response:
            # disabled key or something else
            return None
        assert response["token_type"] == "bearer"
        return response["access_token"]

    # pylint: disable=E0213
    def _check_rate_limit_exceeded(func):
        """This decorator manages the rate exceeded of the API, switching token and trying again"""

        def magic(self, arg):
            retries_available = len(self.bearer_tokens)
            while retries_available:
                try:
                    # pylint: disable=not-callable
                    result = func(self, arg)
                    self.alive = True
                    return result
                except ValueError as e:
                    if str(e) == "88":
                        # try with another token
                        print("magically trying to handle exception")
                        retries_available -= 1
                        self.active = (self.active + 1) % len(self.bearer_tokens)
                    else:
                        # not my problem!
                        raise e
            self.alive = False
            raise Exception("Exceeded limits for the twitter API. Try later.")

        return magic

    def _cursor_request(
        self, url, headers={}, params={}, partial_field_name="ids", limit=None
    ):
        """
        This function handles cursored requests, combining the partial results and giving back the combined result
        Cursored requests are followers/ids, friends/ids
        partial_field_name is the name of the field where the partial results are.
        This function overwrites the params['cursor']
        """

        total_response = []
        params["cursor"] = -1
        while params["cursor"] != 0 and (not limit or len(total_response) < limit):
            try:
                response = self.perform_get(
                    {"url": url, "headers": headers, "params": params}
                )
            except:
                # some errors like private profile
                break
            params["cursor"] = response["next_cursor"]
            total_response.extend(response[partial_field_name])

        return total_response[:limit]

    @_check_rate_limit_exceeded
    def perform_get(self, parameters):
        """
        Parameters must contain the URL and the URL parameters:
        {'url': URL, 'params': {k: v of PARAMS}, 'headers': {k,v of HEADERS}}
        The header Authorization is retrieved from the self.bearer_tokens, so it will be overwritten
        This function is decorated so that on rate exceeded a new bearer token will be used
        """
        # print(parameters)
        token = self.bearer_tokens[self.active]
        url = parameters["url"]
        headers = parameters.get("headers", {})
        headers = {"Authorization": "Bearer {}".format(token)}
        params = parameters["params"]
        response = requests.get(url, headers=headers, params=params).json()
        if "errors" in response:
            for error in response["errors"]:
                if error["code"] == 88:
                    # rate limit exceeded, this is catched by the decorator
                    raise ValueError(88)
        if "errors" in response or "error" in response:
            if "errors" in response:
                response = {"error": response["errors"][0]}
            if "message" in response["error"]:
                raise Exception({"twitter": response["error"]})
            raise Exception({"twitter": {"message": response["error"]}})

        if not response:
            retries = parameters.get("retries", 0)
            if retries:
                print("empty, retrying", retries)
                parameters["retries"] -= 1
                time.sleep(1)
                return self.perform_get(parameters)
        return response

    def _cached_database_list(retrieve_item_from_db_fn, save_item_to_db_fn):
        """
        This decorator avoids querying all the items remotely, using a local database.
        It can be used over a function that has two arguments(self, ids) where ids is a list of id to be retrieved.
        The retrieve_item_from_db_fn is a function with one argument(id) that will try to find the id
        The save_item_to_db_fn is a function with one argument(item) that will save the new elements found by the decorated function.
        """

        def wrap(f):
            def wrapped_f(*args):
                # expand the arguments
                other, ids = args
                # use a dict to manage the merge between the cached values and the ones retrived by the decorated function
                all_results = {}
                # collect there the items that are not in the database yet
                new_ids = []
                for id in ids:
                    # pylint: disable=not-callable
                    item = retrieve_item_from_db_fn(id)
                    if item:
                        # can save to final result
                        all_results[id] = item
                    else:
                        # this has to be retrieved
                        new_ids.append(id)
                # call the decorated function on the reduced list of ids
                # print('crazy decorator: already there', len(all_results), 'to be retrieved', len(new_ids))
                new_args = (other, new_ids)
                new_results = f(*new_args)
                # and merge the results in the combined results
                for id, item in zip(new_ids, new_results):
                    all_results[id] = item
                    # saving them in the database too
                    save_item_to_db_fn(item)
                # return the merged results (there can be cases where the profiles do not exist anymore, just check that)
                return [all_results[id] for id in ids if id in all_results]

            return wrapped_f

        return wrap

    def get_user_tweets(self, user_id, catch=False):
        tweet_ids = persistence.get_tweets_ids_from_user_id(user_id)
        all_tweets = self.get_statuses_lookup(tweet_ids)
        print(len(all_tweets), "old tweets")
        oldest_found = None
        params = {
            "user_id": user_id,
            "count": 200,
            # 'trim_user': True, # lighter response
            "include_rts": 1,  # also native retweets
            "exclude_replies": "false",  # also replies to other tweets
            "tweet_mode": "extended",  # to get the full content and all the URLs
        }
        # limit backwards (if already collected)
        newest_saved = persistence.get_latest_tweet_id(user_id)
        if newest_saved:
            params["since_id"] = newest_saved
        while True:
            retries = 0
            if "max_id" in params or "since_id" in params:
                # with this parameter, sometimes the Twitter API provides empty results on some profiles (e.g., realDonaldTrump).
                # Retrying fixes it (then snscrape will think about the remaining if retries run out)
                retries = 5
            try:
                response = self.perform_get(
                    {
                        "url": "https://api.twitter.com/1.1/statuses/user_timeline.json",
                        "params": params,
                        "retries": retries,
                    }
                )
            except Exception as e:
                print(e)
                if not catch:
                    raise e
                return all_tweets, oldest_found

            print(".", end="", flush=True)
            # print(params)
            # print(response)
            print(len(response), "new")
            new_tweets = response
            # new_tweets = [t for t in response if t['id'] > newest_saved] # not necessary?
            if not len(new_tweets):
                break
            all_tweets.extend(new_tweets)
            # set the maximum id allowed from the last tweet, and -1 to avoid duplicates
            oldest_found = min(el["id"] for el in new_tweets)
            params["max_id"] = oldest_found - 1
        print("retrieved", len(all_tweets), "tweets")
        if all_tweets:
            # persistence.save_tweets_from_user_id(all_tweets, user_id)
            pass
        # return also the oldest tweet id just found, to manage data gaps with the other scraper
        return all_tweets, oldest_found

    def get_user_from_screen_name(self, screen_name):
        result = self.perform_get(
            {
                "url": "https://api.twitter.com/1.1/users/show.json",
                "params": {"screen_name": screen_name},
            }
        )
        # persistence.save_twitter_user(result)
        return result

    def get_friends_ids(self, user_id, limit=None):
        params = {"user_id": user_id, "count": limit}
        response = self._cursor_request(
            "https://api.twitter.com/1.1/friends/ids.json", params=params, limit=limit
        )
        return response

    # @_cached_database_list(persistence.get_twitter_user, persistence.save_twitter_user)
    def get_users_lookup(self, id_list):
        # TODO docs say to use POST for larger requests
        # TODO cache flag to disable old results!!!
        result = []
        for chunk in split_in_chunks(id_list, 100):
            params = {"user_id": ",".join([str(el) for el in chunk])}
            try:
                response = self.perform_get(
                    {
                        "url": "https://api.twitter.com/1.1/users/lookup.json",
                        "params": params,
                    }
                )
                result.extend(response)
            except:
                pass
        # print(result)
        return result

    @_cached_database_list(persistence.get_tweet, persistence.save_tweet)
    def get_statuses_lookup(self, tweet_ids):
        # TODO docs say to use POST for larger requests
        result = []
        for chunk in split_in_chunks(tweet_ids, 100):
            # print('retrieving chunk of tweets from API')
            params = {
                "id": ",".join([str(el) for el in chunk]),
                "tweet_mode": "extended",  # no truncated tweets
            }
            try:
                response = self.perform_get(
                    {
                        "url": "https://api.twitter.com/1.1/statuses/lookup.json",
                        "params": params,
                    }
                )
                result.extend(response)
            except:
                print("failed get_statuses_lookup", response)
                pass
        # print(result)
        return result


def split_in_chunks(iterable, chunk_size):
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i : i + chunk_size]


def search(query, after_datetime):
    if after_datetime:
        print("after_date", after_datetime)
        response = twitterscraper.query_tweets(query, begindate=after_datetime.date())
    else:
        response = twitterscraper.query_tweets(query)
    return [t.tweet_id for t in response]


def snscrape_get_tweets(screen_name, until=None, max_tweets=10000):
    print("snscrape called...")
    if until:
        query = f"from:@{screen_name} until:{until.year}-{until.month}-{until.day}"
    else:
        query = f"from:@{screen_name}"

    tweets = []
    for i, tweet in enumerate(
        tqdm.tqdm(
            snscrape.modules.twitter.TwitterSearchScraper(
                query, convert_tweets=False
            ).get_items()
        )
    ):
        if i >= max_tweets:
            break
        tweets.append(tweet)
    print("snscrape got", len(tweets), "more tweets")
    return tweets
