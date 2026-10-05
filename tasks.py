from fastapi import Cookie,APIRouter,Body,Depends,HTTPException,Form
import aio_pika as pika
import redis.asyncio as redis
from auth import create_token,get_by_token
from database import get_db, SessionLocal
from models import User,Post,Message
from datetime import timedelta
from fastapi.responses import FileResponse,RedirectResponse,JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from sqlalchemy import select,text,update,desc
import json
from sqlalchemy.orm import selectinload
from datetime import datetime
import asyncio
import os

salt=bcrypt.gensalt()
router=APIRouter()
r=redis.from_url(str(os.getenv('REDIS_URL')))

async def update_worker(url):
    connection= await pika.connect_robust(os.getenv('RABBITMQ_URL',url))
    async with connection:
        channel=await connection.channel()
        queue=await channel.declare_queue('message_delayed')
        while True:
            async with SessionLocal() as db: #type:ignore
                result=(await db.execute(text(f'''
                select * from posts
                where published=0 and publish_at<=\'{datetime.now()}\'
                '''))).all()
                if result:
                    ids = [str(i[0]) for i in result]
                    await db.execute(text(f'''
                        update posts set published=2 where id in ({','.join(ids)})
                    '''))
                    await db.commit()
                    l=list()
                    for i in result:
                        l.append((f'{i[0]}',f'{i[-1]}'))
                    await channel.default_exchange.publish(message=pika.Message(json.dumps(l).encode()), routing_key='message_delayed')
                    l.clear()
            await asyncio.sleep(10)

@router.get('/')
async def login():
    return FileResponse('templates/login.html')

@router.get('/register')
async def register():
    return FileResponse('templates/register.html')

@router.post('/reg')
async def reg(db:AsyncSession=Depends(get_db), name=Form(), password=Form()):
    result=(await db.execute(select(User).filter(User.name==name))).first()
    if result:
        raise HTTPException(401,'Пользователь с таким именем уже есть!')
    target=User(name=name, password=bcrypt.hashpw(password.encode(), salt=salt).decode())
    db.add(target)
    await db.commit()
    return RedirectResponse('/', status_code=303)


@router.post('/login')
async def log(db:AsyncSession=Depends(get_db), name=Form(), password=Form()):
    result=(await db.execute(select(User).filter(User.name==name))).first()
    if not result:
        raise HTTPException(401,'Неправильный логин или пароль!')
    user=result[0]
    if not(bcrypt.checkpw(password.encode(), user.password.encode())):
        raise HTTPException(401,'Неправильный логин или пароль!')
    refresh=create_token(user.name, timedelta=timedelta(days=30))
    response=RedirectResponse('/mainpage',status_code=303)
    response.set_cookie('access_token',create_token(user.name, timedelta=timedelta(minutes=30)))
    response.set_cookie('refresh_token', refresh)
    user.refresh_token=refresh
    await db.commit()
    return response

@router.post('/refresh')
async def refresh(db:AsyncSession=Depends(get_db), refresh_token=Cookie()):
    user=await get_by_token(refresh_token)
    if user.refresh_token!=refresh_token or not(user.refresh_token):
        raise HTTPException(401,'Проблема с токеном!')
    response=JSONResponse({'status':'ok'})
    response.set_cookie('access_token', create_token(user.name, timedelta=timedelta(minutes=30)))
    return response

@router.get('/mainpage')
async def mainpage(access_token=Cookie()):
    return FileResponse('templates/mainpage.html')

@router.get('/posts')
async def posts(access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    data= await r.get('posts')
    if data:
        return {'posts':json.loads(data)}
    ex=text('''
    select posts.id, users.name, posts.title, posts.publish_at
    from posts
    inner join users on posts.user_id=users.id
    group by posts.id
    HAVING posts.published=1
    ORDER by posts.publish_at DESC
    ''')
    result=(await db.execute(ex)).all()
    all_posts=[]
    for i in result:
        all_posts.append({'author':i[1], 'text':i[2], 'published_at':str(i[3])})
    await r.setex('posts',60,json.dumps(all_posts))
    return {'posts':all_posts}

@router.get('/posts/scheduled')
async def sheduled_posts(access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_by_token(access_token)
    data=await r.get(f'{user.name}:schedule')
    if data:
        return {'posts':json.loads(data)}
    result=(await db.execute(select(Post).filter(Post.user_id==user.id, Post.published==False))).all()
    all_sheduled=[]
    for j in result:
        i=j[0]
        all_sheduled.append({'id':i.id,'text':i.title,'publish_at':str(i.publish_at)})
    await r.setex(f'{user.name}:schedule',60, json.dumps(all_sheduled))
    return {'posts':all_sheduled}

@router.post('/create')
async def create_post(access_token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    user= await get_by_token(access_token)
    try:
        date=datetime.fromisoformat(data['publish_at'])
        target=Post(title=data['text'], publish_at=date if date>datetime.now() else datetime.now(), user_id=user.id, published=False)
        db.add(target)
        await db.commit()
        await r.delete(f'{user.name}:schedule')
    except KeyError as e:
        target=Post(user_id=user.id, title=data['text'], publish_at=datetime.now(), published=True)
        db.add(target)
        await db.commit()
    finally:
        await r.delete('posts')

@router.delete('/posts/{id}')
async def delete_post(id:int, access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_by_token(access_token)
    result=(await db.execute(select(Post).filter(Post.id==id))).first()
    if not result:
        raise HTTPException(404,'Такого поста нет!')
    post=result[0]
    if post.published==True:
        raise HTTPException(400,'Пост уже опубликован!')
    if post.user_id!=user.id:
        raise HTTPException(404,'Такого поста нет!')
    await db.delete(post)
    await db.commit()
    await r.delete(f'{user.name}:schedule')

@router.get('/message')
async def message(access_token=Cookie()):
    return FileResponse('templates/messages.html')

@router.get('/messages')
async def message_show(access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_by_token(access_token)
    data= await r.get(f'{user.name}:messages')
    if data:
        return {'messages': json.loads(data)}
    messages=(await db.execute(select(Message).filter(Message.user_id==user.id).options(selectinload(Message.post)).order_by(desc(Message.created_at)))).all()
    all_messages=[]
    for i in messages:
        print(i[0].post.title,'gg')
        all_messages.append({'text':i[0].text, 'post_text':i[0].post.title, 'created_at':i[0].created_at})
    await r.setex(f'{user.name}:messages',60, json.dumps(all_messages))
    print(messages)
    print(all_messages)
    return {'messages': all_messages}