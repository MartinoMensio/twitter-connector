# Twitter FastAPI

REST FastAPI container for Twitter API

## Environment variables

Get them from dev.twitter.com and put in the `.env` file as:

```txt
TWITTER_KEY_0=
TWITTER_SECRET_0=
TWITTER_KEY_1=
TWITTER_SECRET_1=
TWITTER_KEY_2=
TWITTER_SECRET_2=
```

Add as many credentials as possible

## Docker commands

build the container: `docker build -t mm34834/twitter_connector .`

Run the container:

locally:
```
docker run -dit --restart always --name mm34834_twitter_connector --network=twitter_app_default -p 20200:8000 -e MONGO_HOST=mongo:27017 -v `pwd`:/app --link=twitter_app_mongo_1:mongo mm34834/twitter_connector
```

```
docker run -dit --restart always --name mm34834_twitter_connector -p 127.0.0.1:20200:8000 -e MONGO_HOST=mongo:27017 -v `pwd`:/app --link=mm34834_mongo:mongo mm34834/twitter_connector
```