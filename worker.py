import aio_pika as pika
import asyncio
from database import SessionLocal
from sqlalchemy import text
import redis.asyncio as redis
from datetime import datetime
import json
import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get('/')
async def health():
    return {'status': 'ok'}

r=redis.from_url(str(os.getenv('REDIS_URL')))

async def callback(message:pika.IncomingMessage):
    async with message.process():
        async with SessionLocal() as db: #type:ignore
            body=json.loads(message.body.decode())
            await db.execute(text(f'''
            update posts set published=1
            where published=2
            '''))
            await db.commit()

            txt=''
            for i in body:
                txt+=f'("Ваш пост был отправлен", {i[-1]}, {i[0]}),'

            await db.execute(text(f'''
            INSERT INTO messages (text, user_id, post_id) values {txt[:-1:]}
            '''))
            await db.commit()

async def main():
    connection= await pika.connect_robust(str(os.getenv('RABBITMQ_URL')))
    async with connection:
        channel=await connection.channel()
        queue=await channel.declare_queue('message_delayed')

        await queue.consume(callback) #type:ignore
        print('started')
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            return

if __name__=='__main__':
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
    asyncio.run(main())