from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from .routers import users, tweets, search

app = FastAPI()

app.include_router(users.router, prefix='/users', tags=['users'])
app.include_router(tweets.router, prefix='/tweets', tags=['tweets'])
app.include_router(search.router, prefix='/search', tags=['search'])

@app.get('/')
async def root():
    return {
        'name': 'twitter_connector',
        'docs': '/docs'
    }