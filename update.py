from tasks import update_worker
import asyncio
from fastapi import FastAPI 
import uvicorn
import os

app=FastAPI()

@app.get('/')
async def health():
    return {'status': 'ok'}

@app.on_event('startup')
async def worker():
    asyncio.create_task(update_worker())

if __name__=='__main__':
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 10000)))