from models import Base
from sqlalchemy import create_engine
from tasks import router
from fastapi import FastAPI
import os

app=FastAPI()

url=os.getenv('DATABASE_URL','sqlite:///workerposts.db')
if '+asyncpg' in url:
    url=url.replace('+asyncpg','')

engine=create_engine(url)
Base.metadata.create_all(engine)
app.include_router(router)
