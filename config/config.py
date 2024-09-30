import os

DB_URL = os.getenv('DB_URL', 'postgresql+asyncpg://kramer:EVvbuGcRqM4DopujH4x5VSMZ0@45.88.104.249:2060/gpt_food')
SECRET_KEY = '456'
JWT_ALGORITHM = "HS256"
HASH_SECRET_KEY = '3OjRMH4i2V8QF6k4BqRfXSGUB'
AUTH_BY_TOKEN = False
APP_BOT_TOKEN = os.getenv('APP_BOT_TOKEN', '7289320383:AAErCSgKU9zFPCrWVaUBh8oH1LMOuJ-8ovU')
DATE_FORMAT: str = "%d-%m-%Y %H:%M"
