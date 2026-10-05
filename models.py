from sqlalchemy import Column,Integer,String,Boolean,DateTime,ForeignKey,func
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):pass

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    name=Column(String)
    password=Column(String)
    refresh_token=Column(String, default='')
    
    messages=relationship('Message', back_populates='user')
    posts=relationship('Post', back_populates='user')

class Post(Base):
    __tablename__='posts'
    id=Column(Integer,primary_key=True)
    title=Column(String)
    publish_at=Column(DateTime,nullable=True)
    published=Column(Integer)
    user_id=Column(Integer,ForeignKey('users.id'))

    user=relationship('User', back_populates='posts')
    messages=relationship('Message', back_populates='post')

class Message(Base):
    __tablename__='messages'
    id=Column(Integer,primary_key=True)
    text=Column(String)
    created_at=Column(DateTime, default=func.now())
    user_id=Column(Integer, ForeignKey('users.id'))
    post_id=Column(Integer, ForeignKey('posts.id'))

    user=relationship('User', back_populates='messages')
    post=relationship('Post', back_populates='messages')