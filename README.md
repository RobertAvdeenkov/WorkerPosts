## Про что проект
Веб-приложение для публикации отложенных постов. Пользователь пишет текст, выбирает дату и воркер RabbitMQ отправляет его в заданное время автоматически.
Access/refresh токены хранятся в куках. 
Задеплоен при помощи Render.
В проекте использовался Python в бекенде и HTML.

## Архитектура:
.
 ├──.gitignore - список файлов и папок, не попавших в репозиторий
 ├──auth.py # создание JWT-токенов и поиск пользователя по нему
 ├──database.py - подключение к БД и создание сессии
 ├──main.py - запуск роутеров
 ├──models.py - модели
 ├──README.md - то, что ты сейчас читаешь
 ├──requirements.txt - необходимые библиотеки
 ├──tasks.py - эндпоинты
 ├──worker.py - RabbitMQ воркер
 └──templates/
    ├──login.html - страница логина
    ├──mainpage.html - страница главной
    └──register.html - страница регистрации

## Эндпоинты:
 GET / - страница логина
 GET /register - страница регистрации
 POST /login - логин
 POST /reg - регистрация
 POST /refresh - обновление access_token
 GET /mainpage - страница главной
 GET /posts - показ всех постов
 GET /posts/sheduled - показ отложенных постов
 POST /create - создать пост
 DELETE /posts/{id} - удалить пост

## Технологии:
1. FastAPI
2. RabbitMQ(asyncio)
3. Redis(asyncio)
4. Bcrypt
5. Python-jose
6. SQLAlchemy(asyncio)
7. Asyncio

## Что должно быть в .env:
1. DATABASE_URL - ссылка в БД
2. SECRET - пароль к JWT токенам
3. ALGORITHM - алгоритм шифрования JWT токенов
4. REDIS_URL - ссылка на Redis
5. RABBIT_MQ_URL - ссылка на RabbitMQ

## Требования:
1. Python 3.11+ (желательно 3.14)
2. Свободные порты(6379, 8000)
3. Наличие Docker Desktop

## Запуск:
1. Установите файлы
2. Перейдите в папку
3. Установите библиотеки: pip install --no-cache-dir -r requirements.txt
4. Запустите Redis и RabbitMQ через Docker Desktop:
    1) docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3.13 - запустить брокера
    2) docker run -p 6379:6379 --name redis -d redis:7-alpine - запустить Redis
4. В терминале введите: python -m uvicorn main:app --reload
5. Приложение будет доступно на http://127.0.0.1:8000

## Фичи:
1. Создание отложенных постов
2. Отмена публикации
3. Быстрая загрузка страницы с помощью кеширования
4. Страница, показывающая сообщения о публикации
