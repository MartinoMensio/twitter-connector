from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from .routers import users, tweets, search, utils

app = FastAPI()

app.include_router(users.router, prefix='/users', tags=['users'])
app.include_router(tweets.router, prefix='/tweets', tags=['tweets'])
app.include_router(search.router, prefix='/search', tags=['search'])
app.include_router(utils.router, prefix='/utils', tags=['utils'])

@app.get('/')
async def root():
    return {
        'name': 'twitter_connector',
        'docs': '/docs'
    }