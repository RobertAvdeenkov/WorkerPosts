from jose import jwt
from database import SessionLocal
from datetime import datetime,timedelta
import os
from sqlalchemy import select
from fastapi import HTTPException
from models import User
from jose.exceptions import JWTError,ExpiredSignatureError

SECRET=str(os.getenv('SECRET'))
ALGORITHM=str(os.getenv('ALGORITHM'))

def create_token(user:str, timedelta):
    payload={
        'sub':user,
        'exp':datetime.now()+timedelta
    }
    return jwt.encode(payload,SECRET,ALGORITHM)

async def get_by_token(token:str):
    try:
        name=jwt.decode(token,SECRET,algorithms=[ALGORITHM])['sub']
        async with SessionLocal() as db: #type:ignore
            result=(await db.execute(select(User).filter(User.name==name))).first()
            if not result:
                raise HTTPException(404,'Такого пользователя нет!')
            return result[0]
    except ExpiredSignatureError:
        raise HTTPException(401,'Токен протух!')
    except JWTError:
        raise HTTPException(401,'Проблема с токеном!')