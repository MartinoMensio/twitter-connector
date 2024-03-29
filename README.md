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

build the container:

```bash
docker build -t martinomensio/twitter-connector .
```

Run the container:

locally:
```
docker run -it --restart always --name mm35626_twitter_connector -p 20200:8000 -e MONGO_HOST=mongo:27017 -v `pwd`/app:/app/app -v `pwd`/.env:/app/.env --link=mm35626_mongo:mongo martinomensio/twitter-connector
```

```
docker run -it --restart always --name mm35626_twitter_connector -p 127.0.0.1:20200:8000 -e MONGO_HOST=mongo:27017 -v `pwd`/.env:/app/.env --link=mm35626_mongo:mongo martinomensio/twitter-connector
```